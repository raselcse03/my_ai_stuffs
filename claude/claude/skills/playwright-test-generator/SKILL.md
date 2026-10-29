---
name: playwright-test-generator
description: "Delegates to the playwright-test-generator subagent to turn a test plan from specs/ into a real Playwright spec file in e2e/, by driving the browser live via the Playwright MCP server. Use when asked to generate or build test code from an existing plan. Triggered by /generator."
---

# Playwright Test Generator

Delegates entirely to the `playwright-test-generator` subagent defined in `.claude/agents/playwright-test-generator.md` — do not write the test file yourself.

## Workflow

1. Identify which plan to generate from. If the user names a plan, use it; if they don't and only one file exists under `specs/`, use that; otherwise ask which plan to generate from.
2. Call the `Task` tool with `subagent_type: playwright-test-generator`, passing the plan file path (and any scenario the user singled out) as the prompt.
3. The subagent executes each planned step live against the browser via the `playwright-test` MCP server's `browser_*`/`generator_*` tools, then writes the resulting spec into `e2e/` via `generator_write_test`.
4. Report back only the path of the generated spec file.

## Notes

- Requires the `playwright-test` MCP server declared in `.mcp.json` to be approved and running.
- `playwright.config.ts` sets `testDir: './e2e'` in this repo — generated specs land there, not `tests/`.
