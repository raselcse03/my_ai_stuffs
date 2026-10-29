---
description: "🎭 /generator — Generate a Playwright spec file from a test plan"
---
# Playwright Test Generator

## Examples

```
/generator build tests from specs/authenticated-shopping-page-test-plan.md
```

```
/generator generate the "Add Valid Todo" scenario from specs/plan.md
```

## Skill Context

Read .claude/skills/playwright-test-generator/SKILL.md — follow the skill workflow. It delegates to the `playwright-test-generator` subagent (`.claude/agents/playwright-test-generator.md`), which writes the spec into `e2e/`.

## Task

$ARGUMENTS
