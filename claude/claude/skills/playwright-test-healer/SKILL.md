---
name: playwright-test-healer
description: "Delegates to the playwright-test-healer subagent to run and fix failing Playwright tests, iterating test_run/test_debug/edit against the Playwright MCP server until they pass. Use when asked to fix, heal, or debug failing e2e tests. Triggered by /healer."
---

# Playwright Test Healer

Delegates entirely to the `playwright-test-healer` subagent defined in `.claude/agents/playwright-test-healer.md` — do not debug or edit test files yourself.

## Workflow

1. Determine scope: a specific spec file/test the user named, or "all" if unspecified.
2. Call the `Task` tool with `subagent_type: playwright-test-healer`, passing the scope as the prompt.
3. The subagent runs the suite via `test_run`, debugs failures with `test_debug` and browser inspection tools, edits the spec file, and reruns until it passes — or marks it `test.fixme()` with an explanatory comment if it can't be fixed.
4. Report back a short pass/fail summary and which files were edited.

## Notes

- Requires the `playwright-test` MCP server declared in `.mcp.json` to be approved and running.
