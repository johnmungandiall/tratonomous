# Improve Agents

Review agent definitions and improve them based on past performance.
Reads the improvement log and recent outputs to find patterns.

## What it does
1. Reads `.claude/skills/autonomous-improvements/IMPROVEMENTS.md`
2. Reviews each agent definition in `.claude/agents/`
3. Checks recent outputs in `.claude/agent-output/` for quality signals
4. Updates agent definitions with better instructions, clearer outputs, or model changes
5. Updates commands if new patterns suggest better workflows
6. Logs all changes to IMPROVEMENTS.md and each agent's Change Log
