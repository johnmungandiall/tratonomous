# Run Agents

Orchestrate agents to work on a task. Uses the autonomous skill to plan,
spawn, coordinate, and collect results from multiple agents.

## Usage
/run-agents <task description>

## What it does
1. Checks existing agents in `.claude/agents/AGENTS.md`
2. Plans the execution (which agents, what order, what's parallel)
3. Spawns agents with the monitor watching progress
4. Coordinates handoffs between agents
5. Collects results and improves agent definitions
6. Updates WORK-SUMMARY.md

## Examples
- /run-agents research the auth system and propose improvements
- /run-agents build a REST API for user management
- /run-agents investigate and fix the failing tests in src/api/
