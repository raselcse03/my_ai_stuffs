---
name: playwright-test-planner
description: "Delegates to the playwright-test-planner subagent to explore a live page or flow via the Playwright MCP server and save a Playwright test plan as markdown in specs/. Use when asked to plan out browser/E2E test coverage for a page or flow. Triggered by /planner."
---

# Playwright Test Planner

Delegates entirely to the `playwright-test-planner` subagent defined in `.claude/agents/playwright-test-planner.md` — do not explore the app or write the plan yourself.

## Workflow

1. Call the `Task` tool with `subagent_type: playwright-test-planner`, passing the user's request as the prompt verbatim.
2. The subagent sets up the page via `planner_setup_page`, explores the app through the `playwright-test` MCP server's `browser_*` tools, and saves the finished plan to `specs/` via `planner_save_plan`.
3. Report back only the path of the saved plan file (e.g. `specs/<name>.md`).

## Notes

- Requires the `playwright-test` MCP server declared in `.mcp.json` to be approved and running.
- If the user's request doesn't name a page or flow, ask which one to plan before delegating.
