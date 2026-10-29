---
name: lean-context
description: Use when working on a single function, class, or small isolated change.
---

## Context-gathering rules

1. Start narrow. Read only the function/class the user referenced.
2. Expand only on signal: explicit #file: refs, type definitions, or symbol tracing.
3. Never index the workspace for single-function tasks.
4. If you must expand: target file → direct imports → test files only.

## Output rules
- Quote ONLY the lines you're changing plus 2 lines above and below.
- Do not include unchanged sibling functions.
- Do not include imports unless modifying them.
