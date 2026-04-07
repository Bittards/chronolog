# Chronolog

**Contextual time awareness for AI agents.**

Most AI agents have no sense of time. They don't know if it's 3am or 3pm. They can't tell you what happened 2 hours ago. They don't know a deadline is tomorrow.

Chronolog fixes that with six capabilities:

| Capability | What it does |
|-----------|-------------|
| **Current Time** | Always knows the exact time and timezone |
| **Event Timeline** | Running log of what happened and when |
| **Time-Aware Behavior** | Won't ping you at 2am, knows when businesses are open |
| **Deadline Tracking** | Flags upcoming deadlines, warns when things are overdue |
| **Session Duration** | Knows how long it's been running, flags stale context |
| **Timezone Awareness** | Converts times for multi-location work |

## Quick Start

```bash
# Install
mkdir -p ~/.chronolog
echo '{"default_timezone": "America/New_York"}' > ~/.chronolog/config.json
touch ~/.chronolog/timeline.jsonl
echo '[]' > ~/.chronolog/deadlines.json

# Copy the skill
cp SKILL.md ~/.claude/skills/chronolog/SKILL.md
```

## Why?

The existing `temporal-awareness` skill runs `date`. That's it. One command.

Chronolog gives your agent **contextual** time awareness:

- "It's Monday 10am -- businesses just opened, good time for outreach"
- "You sent those emails 6 hours ago -- too early to follow up"
- "Follow-up emails are due in 3 days"
- "This session has been running for 14 hours -- context may be stale"
- "It's 2am -- suppressing non-urgent notifications"

Time isn't just a number. It's context.

## Compatibility

Works with any agent that supports the [Agent Skills specification](https://agentskills.io):
- Claude Code
- Codex CLI
- OpenCode
- Cursor (via skills)
- Any MCP-compatible agent

## Data Format

**Timeline** (`~/.chronolog/timeline.jsonl`):
```json
{"ts": "2026-04-06T12:00:00-04:00", "event": "sent 21 outreach emails", "category": "outreach"}
{"ts": "2026-04-06T18:30:00-04:00", "event": "voice engine rate limit hit", "category": "error"}
{"ts": "2026-04-06T22:50:00-04:00", "event": "first client onboarding email sent", "category": "milestone"}
```

**Deadlines** (`~/.chronolog/deadlines.json`):
```json
[
  {"deadline": "2026-04-10T10:00:00-04:00", "description": "Follow-up emails to prospects", "status": "pending"},
  {"deadline": "2026-05-06T00:00:00-04:00", "description": "Free trial expires", "status": "pending"}
]
```

## License

MIT

---

Built because an AI agent forgot there was a war going on and quoted 3-month-old prices as current. Time awareness matters.
