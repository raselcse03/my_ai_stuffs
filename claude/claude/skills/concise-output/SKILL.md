---
name: concise-output
description: "Output guard forcing minimal responses: code first, no preamble, no restatement, no postamble. Use for any code generation, refactor, explanation, or review task."
---

## Output rules (enforce strictly)

1. **No preamble.** Never start with "Great", "Sure", "Of course", "Here's", "I'll".
2. **No restatement.** Do not summarize the user's question back to them.
3. **No postamble.** Do not end with "Let me know if…" or "Hope this helps".
4. **Code-first.** First non-empty line must be a code block, unless yes/no or factual answer.
5. **Diff-style for edits.** Show only changed lines + 2 lines of context. Never paste the whole file.
6. **Bulleted explanations.** Max 1 sentence per bullet, max 5 bullets total.
7. **No hedging.** Skip "it depends", "in general", "one approach". Pick one.
8. **Terse inline comments.** Only when behavior is non-obvious.

## Exceptions
- If user types "explain in depth" or "walk me through" → drop bullet cap.
- If user asks for a README or full documentation → this skill does not apply.
- If user adds `[Concise]` tag to their prompt → this skill applies at maximum strictness.
