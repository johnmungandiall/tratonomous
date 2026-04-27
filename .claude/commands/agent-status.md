# Agent Status

Show the current state of the agent system — what agents exist, their roles,
recent activity, and the monitor's latest observations.

## What it does
1. Reads `.claude/agents/AGENTS.md` for the agent registry
2. Reads `.claude/agent-output/monitor/` for the latest status report
3. Reads `WORK-SUMMARY.md` for recent orchestration history
4. Summarizes everything in a quick overview
