# Skill File Template

Verbatim template for a new action skill's `SKILL.md` — loaded by Step 2 of the register-skill skill. Copy it, replace the `{placeholders}`, and enforce the authoring rules below.

````markdown
---
name: {skill-name}
description: "{What this skill does, third person — e.g., 'Reviews database migration scripts for safety and rollback coverage.'} Use when {trigger scenario(s)}. Triggered by the {[Tag]} tag or /{slug}."
---

# {Skill Display Name}

**Prerequisites:** Review `core-essentials` for critical rules. For full architecture details, see `core-full`.

{2-3 sentence description of what this skill does and when to use it.}

## Usage

```
{[Tag]} {example usage}
```

---

## Step 1: {First Step Name}

{Step instructions...}

---

## Step 2: {Second Step Name}

{Step instructions...}

{If a step needs a large verbatim template, report format, or sub-agent prompt, do NOT inline it — put it in references/{topic}.md and add a one-line pointer:}
→ Read `references/{topic}.md` when you reach this step.

---

## Output

{What the skill produces — files, reports, code changes, etc.}

---

## Error Handling

| Error | Action |
|-------|--------|
| {common error} | {how to handle} |

---

## Notes

- {Important note 1}
- {Important note 2}
````

## Authoring Rules (project skill-authoring standard)

- **Frontmatter is exactly two keys** — `name:` and `description:`. No `role`, `primary_tools`, or `scope` keys.
  - `name:` — kebab-case slug that MUST match the skill directory name (`.claude/skills/{skill-name}/`).
  - `description:` — double-quoted, third person; states WHAT the skill does + "Use when …" trigger scenarios + "Triggered by the `[Tag]` tag or /slug."
- **SKILL.md stays ≤250 lines** — it holds only the operational workflow: usage, numbered steps, decision logic, commands, error handling, return contract.
- **Large verbatim templates, report formats, and sub-agent prompts** live in `references/{topic}.md` inside the skill directory, loaded on demand via one-line pointers ("→ Read `references/x.md` when you reach this step").
- Each `references/{topic}.md` file starts with an H1 and one line saying what it is and which step loads it.
- **Project requirement skills** (`.claude/skills/requirements/*.md`) stay ≤400 lines, with overflow in a `{name}-deep.md` companion file.
- Use **numbered steps**, **tables over prose**, and code examples where applicable — agents parse structured data faster.
