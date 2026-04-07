#!/usr/bin/env python3
"""
Chronolog -- Contextual time awareness for AI agents.

Not just a clock. Knows what happened, what's coming, and when to shut up.

Usage:
    chronolog now                          # Current time + context
    chronolog log "sent 21 emails" -c outreach   # Log an event
    chronolog recent [HOURS]               # Show recent events (default: 24h)
    chronolog deadlines                    # Show upcoming deadlines
    chronolog add-deadline "Follow up" -d 2026-04-10T10:00  # Add deadline
    chronolog complete-deadline ID         # Mark deadline done
    chronolog status                       # Full status: time + recent + deadlines
    chronolog quiet                        # Am I in quiet hours?
    chronolog prune [DAYS]                 # Archive events older than N days (default: 7)
"""

import argparse
import json
import os
import subprocess
import sys
from datetime import datetime, timezone, timedelta
from pathlib import Path

# ============================================================
# CONFIG
# ============================================================

CHRONOLOG_DIR = Path.home() / ".chronolog"
TIMELINE_FILE = CHRONOLOG_DIR / "timeline.jsonl"
DEADLINES_FILE = CHRONOLOG_DIR / "deadlines.json"
CONFIG_FILE = CHRONOLOG_DIR / "config.json"
ARCHIVE_DIR = CHRONOLOG_DIR / "archive"

# Default quiet hours (suppress non-urgent notifications)
QUIET_START = 23  # 11pm
QUIET_END = 7     # 7am

# Business hours
BIZ_START = 9
BIZ_END = 17

CATEGORIES = ["outreach", "client", "system", "build", "meeting", "milestone", "error", "note"]


def ensure_init():
    """Initialize chronolog directory if it doesn't exist."""
    CHRONOLOG_DIR.mkdir(exist_ok=True)
    ARCHIVE_DIR.mkdir(exist_ok=True)
    if not TIMELINE_FILE.exists():
        TIMELINE_FILE.touch()
    if not DEADLINES_FILE.exists():
        DEADLINES_FILE.write_text("[]")
    if not CONFIG_FILE.exists():
        CONFIG_FILE.write_text(json.dumps({
            "default_timezone": "America/New_York",
            "quiet_hours": {"start": QUIET_START, "end": QUIET_END},
            "known_locations": {},
        }, indent=2))


def get_config():
    """Load config."""
    ensure_init()
    return json.loads(CONFIG_FILE.read_text())


def now_local():
    """Get current time as a timezone-aware datetime."""
    # Use system date command for accuracy
    try:
        result = subprocess.run(
            ["date", "+%Y-%m-%dT%H:%M:%S%z"],
            capture_output=True, text=True, timeout=5,
        )
        return datetime.fromisoformat(result.stdout.strip())
    except Exception:
        return datetime.now().astimezone()


def format_relative(dt):
    """Format a datetime as relative time (e.g., '3h ago', 'in 2d')."""
    now = now_local()
    delta = now - dt
    if delta.total_seconds() < 0:
        # Future
        delta = -delta
        if delta.days > 0:
            return f"in {delta.days}d"
        hours = delta.seconds // 3600
        if hours > 0:
            return f"in {hours}h"
        mins = delta.seconds // 60
        return f"in {mins}m"
    else:
        # Past
        if delta.days > 0:
            return f"{delta.days}d ago"
        hours = delta.seconds // 3600
        if hours > 0:
            return f"{hours}h ago"
        mins = delta.seconds // 60
        return f"{mins}m ago"


# ============================================================
# COMMANDS
# ============================================================

def cmd_now(args):
    """Show current time with context."""
    t = now_local()
    hour = t.hour
    day = t.strftime("%A")

    # Time context
    if QUIET_START <= hour or hour < QUIET_END:
        context = "QUIET HOURS -- suppress non-urgent notifications"
        emoji = "🌙"
    elif BIZ_START <= hour < BIZ_END and day not in ("Saturday", "Sunday"):
        context = "Business hours -- good for outreach and client-facing work"
        emoji = "📞"
    elif hour < BIZ_START:
        context = "Early morning -- prep time, people check email but don't want calls"
        emoji = "🌅"
    else:
        context = "After hours -- internal work, building, planning"
        emoji = "🔧"

    print(f"{emoji} {t.strftime('%A, %B %d, %Y %I:%M %p %Z')}")
    print(f"   {context}")

    # Show next deadline if any
    deadlines = _load_deadlines()
    pending = [d for d in deadlines if d.get("status") == "pending"]
    if pending:
        pending.sort(key=lambda d: d["deadline"])
        next_dl = pending[0]
        dl_dt = datetime.fromisoformat(next_dl["deadline"])
        print(f"   Next deadline: {next_dl['description']} ({format_relative(dl_dt)})")


def cmd_log(args):
    """Log an event to the timeline."""
    ensure_init()
    t = now_local()
    entry = {
        "ts": t.isoformat(),
        "event": args.message,
        "category": args.category or "note",
    }
    with open(TIMELINE_FILE, "a") as f:
        f.write(json.dumps(entry) + "\n")
    print(f"✓ Logged: [{entry['category']}] {entry['event']}")


def cmd_recent(args):
    """Show recent events."""
    ensure_init()
    hours = args.hours or 24
    cutoff = now_local() - timedelta(hours=hours)

    events = []
    with open(TIMELINE_FILE) as f:
        for line in f:
            line = line.strip()
            if not line:
                continue
            try:
                entry = json.loads(line)
                ts = datetime.fromisoformat(entry["ts"])
                if ts >= cutoff:
                    events.append((ts, entry))
            except (json.JSONDecodeError, KeyError, ValueError):
                continue

    if not events:
        print(f"No events in the last {hours} hours.")
        return

    events.sort(key=lambda x: x[0])
    print(f"Events in the last {hours} hours ({len(events)} total):\n")
    for ts, entry in events:
        rel = format_relative(ts)
        cat = entry.get("category", "?")
        print(f"  {rel:>8s}  [{cat:10s}]  {entry['event']}")


def _load_deadlines():
    """Load deadlines from file."""
    ensure_init()
    try:
        return json.loads(DEADLINES_FILE.read_text())
    except (json.JSONDecodeError, FileNotFoundError):
        return []


def _save_deadlines(deadlines):
    """Save deadlines to file."""
    DEADLINES_FILE.write_text(json.dumps(deadlines, indent=2))


def cmd_deadlines(args):
    """Show all deadlines."""
    deadlines = _load_deadlines()
    if not deadlines:
        print("No deadlines set.")
        return

    now = now_local()
    overdue = []
    upcoming = []
    done = []

    for i, d in enumerate(deadlines):
        if d.get("status") == "completed":
            done.append((i, d))
            continue
        dt = datetime.fromisoformat(d["deadline"])
        delta = dt - now
        if delta.total_seconds() < 0:
            overdue.append((i, d, delta))
        else:
            upcoming.append((i, d, delta))

    if overdue:
        print("🔴 OVERDUE:")
        for i, d, delta in overdue:
            print(f"   [{i}] {d['description']} ({format_relative(datetime.fromisoformat(d['deadline']))})")

    if upcoming:
        upcoming.sort(key=lambda x: x[2])
        print("📅 UPCOMING:")
        for i, d, delta in upcoming:
            dt = datetime.fromisoformat(d["deadline"])
            urgency = "⚠️ " if delta.days < 2 else "  "
            print(f"  {urgency}[{i}] {d['description']} ({format_relative(dt)})")

    if done and args.show_completed:
        print(f"\n✅ COMPLETED: {len(done)}")
        for i, d in done[-5:]:
            print(f"   [{i}] {d['description']}")


def cmd_add_deadline(args):
    """Add a new deadline."""
    deadlines = _load_deadlines()
    entry = {
        "deadline": args.date,
        "description": args.description,
        "status": "pending",
        "created": now_local().isoformat(),
    }
    deadlines.append(entry)
    _save_deadlines(deadlines)
    dt = datetime.fromisoformat(args.date)
    print(f"✓ Deadline added: {args.description} ({format_relative(dt)})")


def cmd_complete(args):
    """Mark a deadline as completed."""
    deadlines = _load_deadlines()
    idx = args.id
    if idx < 0 or idx >= len(deadlines):
        print(f"Invalid deadline ID: {idx}")
        return
    deadlines[idx]["status"] = "completed"
    deadlines[idx]["completed_at"] = now_local().isoformat()
    _save_deadlines(deadlines)
    print(f"✓ Completed: {deadlines[idx]['description']}")


def cmd_status(args):
    """Full status: time + recent events + deadlines."""
    cmd_now(args)
    print()

    # Recent events (last 6 hours)
    hours = 6
    cutoff = now_local() - timedelta(hours=hours)
    events = []
    with open(TIMELINE_FILE) as f:
        for line in f:
            line = line.strip()
            if not line:
                continue
            try:
                entry = json.loads(line)
                ts = datetime.fromisoformat(entry["ts"])
                if ts >= cutoff:
                    events.append((ts, entry))
            except (json.JSONDecodeError, KeyError, ValueError):
                continue

    if events:
        events.sort(key=lambda x: x[0])
        print(f"Recent ({len(events)} events in last {hours}h):")
        for ts, entry in events[-5:]:
            rel = format_relative(ts)
            print(f"  {rel:>8s}  {entry['event']}")
        if len(events) > 5:
            print(f"  ... and {len(events) - 5} more")

    print()
    args.show_completed = False
    cmd_deadlines(args)


def cmd_quiet(args):
    """Check if we're in quiet hours."""
    t = now_local()
    hour = t.hour
    config = get_config()
    q_start = config.get("quiet_hours", {}).get("start", QUIET_START)
    q_end = config.get("quiet_hours", {}).get("end", QUIET_END)

    is_quiet = q_start <= hour or hour < q_end
    if is_quiet:
        print(f"🌙 YES -- quiet hours ({q_start}:00 - {q_end}:00). Suppress non-urgent notifications.")
    else:
        print(f"🔔 NO -- active hours. Next quiet period starts at {q_start}:00.")
    return is_quiet


def cmd_prune(args):
    """Archive events older than N days."""
    days = args.days or 7
    cutoff = now_local() - timedelta(days=days)

    keep = []
    archive = []
    with open(TIMELINE_FILE) as f:
        for line in f:
            line = line.strip()
            if not line:
                continue
            try:
                entry = json.loads(line)
                ts = datetime.fromisoformat(entry["ts"])
                if ts >= cutoff:
                    keep.append(line)
                else:
                    archive.append(line)
            except (json.JSONDecodeError, KeyError, ValueError):
                keep.append(line)  # Keep unparseable lines

    if archive:
        # Save to archive
        archive_file = ARCHIVE_DIR / f"archive_{datetime.now().strftime('%Y%m%d')}.jsonl"
        with open(archive_file, "a") as f:
            for line in archive:
                f.write(line + "\n")

        # Rewrite timeline with only recent events
        with open(TIMELINE_FILE, "w") as f:
            for line in keep:
                f.write(line + "\n")

        print(f"✓ Archived {len(archive)} events older than {days} days")
        print(f"  Kept {len(keep)} recent events")
        print(f"  Archive: {archive_file}")
    else:
        print(f"Nothing to prune. All {len(keep)} events are within {days} days.")


# ============================================================
# CLI
# ============================================================

def main():
    parser = argparse.ArgumentParser(
        description="Chronolog -- Contextual time awareness for AI agents",
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog=__doc__,
    )
    sub = parser.add_subparsers(dest="command")

    # now
    sub.add_parser("now", help="Current time with context")

    # log
    log_p = sub.add_parser("log", help="Log an event")
    log_p.add_argument("message", help="Event description")
    log_p.add_argument("-c", "--category", choices=CATEGORIES, default="note", help="Event category")

    # recent
    recent_p = sub.add_parser("recent", help="Show recent events")
    recent_p.add_argument("hours", nargs="?", type=float, default=24, help="Hours to look back (default: 24)")

    # deadlines
    dl_p = sub.add_parser("deadlines", help="Show deadlines")
    dl_p.add_argument("--show-completed", action="store_true", help="Include completed deadlines")

    # add-deadline
    add_p = sub.add_parser("add-deadline", help="Add a deadline")
    add_p.add_argument("description", help="What's due")
    add_p.add_argument("-d", "--date", required=True, help="ISO datetime (e.g., 2026-04-10T10:00:00-04:00)")

    # complete
    comp_p = sub.add_parser("complete-deadline", help="Mark deadline done")
    comp_p.add_argument("id", type=int, help="Deadline index from 'deadlines' command")

    # status
    sub.add_parser("status", help="Full status overview")

    # quiet
    sub.add_parser("quiet", help="Check quiet hours")

    # prune
    prune_p = sub.add_parser("prune", help="Archive old events")
    prune_p.add_argument("days", nargs="?", type=int, default=7, help="Keep events from last N days (default: 7)")

    args = parser.parse_args()

    if not args.command:
        cmd_status(args)
        return

    commands = {
        "now": cmd_now,
        "log": cmd_log,
        "recent": cmd_recent,
        "deadlines": cmd_deadlines,
        "add-deadline": cmd_add_deadline,
        "complete-deadline": cmd_complete,
        "status": cmd_status,
        "quiet": cmd_quiet,
        "prune": cmd_prune,
    }

    fn = commands.get(args.command)
    if fn:
        fn(args)
    else:
        parser.print_help()


if __name__ == "__main__":
    main()
