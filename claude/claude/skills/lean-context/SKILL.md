---
name: lean-context
description: "Context guard for small isolated changes: read only the referenced function or class and expand only on explicit signal. Use when working on a single function, class, or small fix."
---

## Context-gathering rules

1. Start narrow. Read only the function/class the user referenced.
2. Expand only on signal: explicit  refs, type definitions, or symbol tracing.
3. Never index the workspace for single-function tasks.
4. If you must expand: target file → direct imports → test files only.

## Output rules
- Quote ONLY the lines you're changing plus 2 lines above and below.
- Do not include unchanged sibling functions.
- Do not include imports unless modifying them.
