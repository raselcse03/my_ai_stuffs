---
name: register-skill
description: "Registers a new skill, action tag, and slash command across routing.md, the SKILL.md master index, CLAUDE.md, and .claude/commands/. Use when adding a new skill or tag to the orchestrator. Triggered by the [Register-Skill] tag or /register-skill."
---

# Register New Skill

**Prerequisites:** None — this skill is self-contained.

Register a new specialist skill in the Multi-Agent Orchestrator. This creates all required files and wiring so the skill is available via both `[Tag]` syntax and `/slash-command`.

## Usage

```
[Register-Skill]
[Register-Skill] Create a skill for database migration review
```

---

## What Gets Created / Updated

**Action skills:**

| # | File | Action | Purpose |
|---|------|--------|---------|
| 1 | `.claude/skills/{skill-name}/SKILL.md` | **Create** | The skill workflow file |
| 2 | `.claude/skills/{skill-name}/references/*.md` | **Create if needed** | Large templates, report formats, sub-agent prompts |
| 3 | `.claude/commands/{slug}.md` | **Create** | Slash command (`/slug`) |
| 4 | `CLAUDE.md` | **Update** | Row in Agent Routing Table |
| 5 | `.claude/skills/routing.md` | **Update** | Row in Quick Routing Table |
| 6 | `.claude/skills/SKILL.md` | **Update** | Row in master index skills table |

**Project skills** (requirement context files): create `.claude/skills/requirements/{project-name}.md` and add a row to the **Project Tag Routing** tables in `CLAUDE.md` and `routing.md`.

---

## Step 1: Gather Information

Ask the user via `AskUserQuestion`:

1. **Skill type** — Action Skill (a new workflow, like `[CR]`, `[Bug]`, `[Review]`) or Project Skill (a project-specific context file, like `[CR2-Phase2]`, `[CR5]`)
2. **Skill name** — e.g., "Database Migration Review" / "CR6 Phase1 Payment Gateway"
3. **Action tag** — `[PascalCase]` or `[Kebab-Case]`, e.g., `[DB-Review]`, `[CR6-Phase1]`
4. **Slash command slug** (action skills only) — lowercase kebab-case, no spaces, e.g., `db-review` → `/db-review`
5. **Description** — what the skill does, 1–2 sentences
6. **Scope** — Code generation / Code review / Documentation / Testing / Analysis / DevOps / Other

---

## Step 2: Create the Skill File

### For Action Skills

Create `.claude/skills/{skill-name}/SKILL.md`.

→ Read `references/skill-template.md` for the verbatim template and full authoring rules when you reach this step.

Enforce the project skill-authoring standard on every new skill:

- Frontmatter is **exactly two keys**: `name:` (kebab-case slug matching the directory name) and `description:` (double-quoted, third person: WHAT the skill does + "Use when …" triggers + "Triggered by the `[Tag]` tag or /slug."). No `role`/`primary_tools`/`scope` keys.
- SKILL.md **≤250 lines** — operational workflow only (usage, numbered steps, decision logic, commands, error handling, return contract).
- Large verbatim templates, report formats, and sub-agent prompts go in `references/{topic}.md` inside the skill directory, referenced by one-line pointers.

### For Project Skills

Create `.claude/skills/requirements/{project-name}.md` — **≤400 lines**, with overflow in a `{project-name}-deep.md` companion. Reference an existing project skill (e.g., `Read → .claude/skills/requirements/cr2-phase2-ac-installation.md`, lines 1-30) for the frontmatter and section structure.

---

## Step 3: Create the Command File (Action Skills Only)

Create `.claude/commands/{slug}.md`.

→ Read `references/command-template.md` for the verbatim template and emoji conventions when you reach this step.

---

## Step 4: Register in CLAUDE.md Routing Table

- **Action skills** — add a row to the **Agent Routing Table**, inserted in **alphabetical order** by tag:
  `| \`{[Tag]}\` | \`.claude/skills/{skill-name}/SKILL.md\` | {Agent Name} |`
- **Project skills** — add a row to the **Project Tag Routing** table:
  `| \`{[Project-Tag]}\` | \`.claude/skills/requirements/{project-name}.md\` |`

---

## Step 5: Register in routing.md (Quick Routing Table)

`.claude/skills/routing.md` is a separate, lighter-weight lookup read instead of the full `SKILL.md` index when a prompt has no `[Tag]`. It must stay in sync with `CLAUDE.md` — this step is easy to skip because it duplicates the same information, so treat it as **required, not optional**.

- **Action skills** — append to the **Quick Routing Table** (entries are chronological, not alphabetical):
  `| {Task type, one line} | \`{[Tag]}\` | \`{skill-name}/SKILL.md\` |`
- **Project skills** — add to its **Project Tag Routing** table:
  `| \`{[Project-Tag]}\` | \`requirements/{project-name}.md\` |`

---

## Step 6: Register in SKILL.md Master Index

Add **ONE ROW** to the skills table in `.claude/skills/SKILL.md`:

```markdown
| `{[Tag]}` | `{skill-name}/SKILL.md` | {One-line description} |
```

Do not add multi-line prose entries — the master index is a table (tag | skill path | one-line description).

---

## Step 7: Update readme.md (only if it exists)

This project does not currently ship a `readme.md` documenting the skill system — skip unless one has since been added. If present, update: the "Quick Prompts (Slash Commands)" table (`| /{slug} | {[Tag]} | {Agent Name} |`), the ACTION TAGS ASCII box, the action-tags detail table, and the delegation-flow mermaid diagram (`C -- "{[Tag]}" --> D{N}[...]`). Use `Grep` to find each location.

---

## Step 8: Verify Registration

```bash
# Files exist
test -f .claude/skills/{skill-name}/SKILL.md && echo "✅ Skill file" || echo "❌ Skill file MISSING"
test -f .claude/commands/{slug}.md && echo "✅ Command file" || echo "❌ Command file MISSING"

# Frontmatter delimiters intact + line budget respected (≤250)
grep -c '^---$' .claude/skills/{skill-name}/SKILL.md   # expect 2
wc -l .claude/skills/{skill-name}/SKILL.md

# Routing entries
grep "{[Tag]}" CLAUDE.md && echo "✅ CLAUDE.md routing" || echo "❌ CLAUDE.md routing MISSING"
grep "{[Tag]}" .claude/skills/routing.md && echo "✅ Quick routing" || echo "❌ Quick routing MISSING"
grep "{skill-name}" .claude/skills/SKILL.md && echo "✅ Master index row" || echo "❌ Master index row MISSING"

# readme.md (only if it exists — see Step 7)
test -f readme.md && grep "/{slug}" readme.md && echo "✅ readme.md" || echo "⏭️  no readme.md — skipped"
```

---

## Output Summary

After completion, present to the user:

```
✅ Skill Registration Complete

📄 Skill File: .claude/skills/{skill-name}/SKILL.md
⌨️ Slash Command: /{slug}
🏷️ Action Tag: {[Tag]}
📋 Command File: .claude/commands/{slug}.md

📝 Registration:
- ✅ Agent Routing Table updated (CLAUDE.md)
- ✅ Quick Routing Table updated (routing.md)
- ✅ SKILL.md master index row added

💡 Usage: /{slug} — or — {[Tag]} {your request} — or — {[Tag]}[{Project-Tag}] {your request}
```

---

## Notes

- Every action skill needs **5 things**: skill file + command file + CLAUDE.md routing row + routing.md row + master-index row
- Project skills need **2 things**: requirements file + Project Tag Routing entries
- Skill files stay **≤250 lines**; extract large templates to the skill's own `references/{topic}.md` and point to them with one line — each reference file starts with an H1 and one line saying what it is and which step loads it
- Use existing skills as reference — `Read` any similar skill to match the pattern
