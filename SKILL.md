---
name: chronolog
description: "Contextual time awareness for AI agents. Not just the clock -- knows what happened, what's coming, and how time affects decisions. Maintains a running event timeline, deadline tracker, and time-aware behavior rules."
version: 0.1.0
author: chronolog
license: MIT
---

# Chronolog -- Contextual Time Awareness for AI Agents

Most AI agents have no sense of time. They don't know if it's 3am or 3pm, whether they've been running for 10 minutes or 10 hours, or that a deadline is tomorrow. Chronolog fixes that.

## What It Does

Chronolog gives your agent six time superpowers:

### 1. Current Time (the basics)
Run `date "+%A, %B %d, %Y %I:%M %p %Z"` at the start of every response to know the exact time.

### 2. Event Timeline
Maintain a running log of significant events at `~/.chronolog/timeline.jsonl`. Each entry:
```json
{"ts": "2026-04-06T12:00:00-04:00", "event": "sent 21 outreach emails", "category": "outreach"}
```
Before responding to any question about "when did we..." or "how long ago...", read the timeline.

### 3. Time-Aware Behavior Rules
Check the hour before taking actions:
- **Late night (11pm-7am):** Suppress non-urgent notifications. Don't message the user unless something is broken.
- **Business hours (9am-5pm weekdays):** Outreach, calls, and client-facing work is appropriate.
- **After hours (5pm-11pm weekdays, weekends):** Internal work, building, planning. Don't cold-email businesses.
- **Early morning (7am-9am):** Good for prep work. People check email but don't want calls yet.

### 4. Deadline Tracking
Maintain active deadlines at `~/.chronolog/deadlines.json`:
```json
[
  {"deadline": "2026-04-10T10:00:00-04:00", "description": "Follow-up emails to Wave 3 prospects", "status": "pending"},
  {"deadline": "2026-05-06T00:00:00-04:00", "description": "Alvaro free month expires", "status": "pending"}
]
```
When asked about upcoming work or priorities, check deadlines and flag anything due within 48 hours.

### 5. Session Duration
Track when the current session started. If the session has been running for 8+ hours, note it -- context may be stale, memory may need refreshing.

### 6. Timezone Awareness
Default timezone is set in `~/.chronolog/config.json`. When discussing businesses in other timezones, convert automatically:
```json
{"default_timezone": "America/New_York", "known_locations": {"TC Studio": "America/New_York", "client_west_coast": "America/Los_Angeles"}}
```

## How to Use

### Log an event
When something significant happens (email sent, client onboarded, system crashed, meeting scheduled):
```bash
chronolog log "sent 21 outreach emails" -c outreach
chronolog log "voice engine rate limit hit" -c error
chronolog log "first client onboarding email sent" -c milestone
```
Categories: `outreach`, `client`, `system`, `build`, `meeting`, `milestone`, `error`, `note`

### Check recent events
```bash
chronolog recent          # Last 24 hours
chronolog recent 2        # Last 2 hours
```

### Add a deadline
```bash
chronolog add-deadline "Follow-up emails to prospects" -d 2026-04-10T10:00:00-04:00
```

### Check deadlines
```bash
chronolog deadlines                    # Show all pending + overdue
chronolog deadlines --show-completed   # Include completed
```

### Mark a deadline done
```bash
chronolog complete-deadline 0          # By index from 'deadlines' output
```

### Full status (time + recent + deadlines)
```bash
chronolog status
```

### Check quiet hours before notifying
```bash
chronolog quiet   # Returns whether it's quiet hours (11pm-7am)
```

### Archive old events
```bash
chronolog prune        # Archive events older than 7 days
chronolog prune 14     # Archive events older than 14 days
```

## When to Trigger

Activate this skill when:
- The user asks about time, dates, deadlines, or "when did we..."
- Before sending any notification or message (check if it's an appropriate hour)
- At the start of complex tasks (log the start time)
- When completing tasks (log the event)
- When the user asks about priorities (check deadlines)
- When discussing businesses (check their timezone/hours)

## Installation

```bash
# Clone the repo
git clone https://github.com/Bittards/chronolog.git
cd chronolog

# Make the CLI available (pick one)
chmod +x chronolog.py
ln -s $(pwd)/chronolog.py /usr/local/bin/chronolog
# OR just run with: python3 chronolog.py <command>

# First run auto-initializes ~/.chronolog/ with config, timeline, and deadlines
chronolog status
```

### Claude Code
Copy this skill to `~/.claude/skills/chronolog/SKILL.md`

### Codex CLI
Copy to `~/.codex/skills/chronolog/SKILL.md`

### Any Agent
This skill follows the [Agent Skills specification](https://agentskills.io). Copy to your agent's skills directory.

## Why This Matters

AI agents are temporally blind. They don't know:
- That it's 2am and they shouldn't ping their user
- That a deadline is tomorrow and they should prioritize it
- That they sent an email 6 hours ago and it's too early to follow up
- That their session has been running for 16 hours and their context might be stale

Chronolog gives agents the temporal awareness that humans take for granted. It's the difference between a useful assistant and an always-on partner that respects your time.

## License

MIT
