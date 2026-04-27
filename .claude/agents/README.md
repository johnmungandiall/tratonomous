# Project Agents

How agents work in this project and how to use them.

## Quick Start

To orchestrate agents, use the `autonomous` skill or ask Claude to
"run agents on [task]". Agents are defined in this folder as `.md` files.

You can also use project commands:
- `/run-agents` — orchestrate agents on a task
- `/agent-status` — check what agents exist and their recent activity
- `/improve-agents` — review and improve agent definitions
- `/list-agents` — quick list of all available agents

## Available Agents

(none yet — agents are created as needed for tasks)

## How Agents Communicate

Agents pass work to each other through files in `.claude/agent-output/`.
Each agent writes its results there, and the next agent reads from it.
The monitor agent observes all agents and reports on progress.

## Adding a New Agent

1. Create `<name>.md` in `.claude/agents/`
2. Add it to the table in AGENTS.md
3. Update this README with a description

## Performance Notes

(updated after each orchestration run)
