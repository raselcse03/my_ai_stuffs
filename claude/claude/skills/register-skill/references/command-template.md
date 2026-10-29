# Command File Template

Verbatim template for the slash-command file `.claude/commands/{slug}.md` plus emoji conventions — loaded by Step 3 of the register-skill skill.

````markdown
---
description: "{emoji} [{Tag}] — {Short description}"
---
# {Skill Display Name}

Use the `{[Tag]}` action tag.{Optional: Add a `[Project-Tag]` for project-specific context.}

## Examples

```
{[Tag]} {example 1}
```

```
{[Tag]} {example 2}
```

## Skill Context

Read .claude/skills/core-essentials.md, for more details read .claude/skills/core-full.md and .claude/skills/{skill-name}/SKILL.md — follow the skill workflow. Load the skill's `references/*.md` files only when its steps point to them.

## Task

$ARGUMENTS
````

## Emoji Conventions

| Category | Emoji |
|----------|-------|
| Bug/Fix | 🐛 |
| Feature/New | 🆕 |
| Change Request | 📋 |
| Review/Audit | 🔍 |
| Testing | 🧪 |
| Documentation | 📝 |
| Analysis | 📊 |
| Generation | ⚙️ |
| Import/Export | 📥 📤 |
| DevOps/Infra | 🏗️ |
| Refactor | 🔧 |
| Security | 🔒 |
| Performance | ⚡ |
