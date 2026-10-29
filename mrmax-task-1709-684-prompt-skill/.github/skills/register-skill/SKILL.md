---
name: "Skill Registrar"
role: "Guide the user through registering a new skill, action tag, and slash command in the Multi-Agent Orchestrator"
primary_tools: [read_file, create_file, replace_string_in_file, vscode_askQuestions]
scope: ".github/"
---

# Register New Skill

**Prerequisites:** None — this skill is self-contained.

Register a new specialist skill in the Multi-Agent Orchestrator. This creates all
required files and wiring so the skill is available via both `[Tag]` syntax and `/slash-command`.

## Usage

```
@workspace [Register-Skill]
@workspace [Register-Skill] Create a skill for database migration review
```

---

## What Gets Created / Updated

| # | File | Action | Purpose |
|---|------|--------|---------|
| 1 | `.github/skills/{skill-name}.md` | **Create** | The skill workflow file |
| 2 | `.github/prompts/{slug}.prompt.md` | **Create** | Slash command (`/slug`) |
| 3 | `.github/copilot-instructions.md` | **Update** | Add row to Agent Routing Table |
| 4 | `.github/skills/SKILL.md` | **Update** | Add entry to master index |
| 5 | `readme.md` | **Update** | Add to slash command table, action tags, and mermaid diagram |

For **project-specific** skills (requirement context files):

| # | File | Action | Purpose |
|---|------|--------|---------|
| 1 | `.github/skills/requirements/{project-name}.md` | **Create** | Project context file |
| 2 | `.github/copilot-instructions.md` | **Update** | Add row to Project Tag Routing table |

---

## Step 1: Gather Information

Ask the user via `vscode_askQuestions`:

### Question 1: Skill Type
**"What type of skill are you registering?"**
- **Action Skill** — A new workflow (like `[CR]`, `[Bug]`, `[Review]`)
- **Project Skill** — A project-specific context file (like `[CR2-Phase2]`, `[CR5]`)

### Question 2: Skill Name
**"What is the skill name?"**
- For action skills: e.g., "Database Migration Review", "API Documentation"
- For project skills: e.g., "CR6 Phase1 Payment Gateway"

### Question 3: Action Tag
**"What action tag should trigger this skill?"**
- Must be in `[PascalCase]` or `[Kebab-Case]` format
- Examples: `[DB-Review]`, `[API-Doc]`, `[CR6-Phase1]`

### Question 4: Slash Command Slug
**"What slash command should invoke this skill?"** (action skills only)
- Must be lowercase kebab-case, no spaces
- Examples: `db-review`, `api-doc`
- This becomes the `/db-review` command

### Question 5: Description
**"Describe what this skill does in 1-2 sentences."**

### Question 6: Scope
**"What is the primary focus?"**
- Options: Code generation, Code review, Documentation, Testing, Analysis, DevOps, Other

---

## Step 2: Create the Skill File

### For Action Skills

Create `.github/skills/{skill-name}.md` using this template:

```markdown
---
name: "{Skill Display Name}"
role: "{One-line description of what this agent does}"
primary_tools: [{list relevant tools: read_file, grep_search, run_in_terminal, create_file, replace_string_in_file, runSubagent}]
scope: "{target directory or full-repository}"
---

# {Skill Display Name}

**Prerequisites:** Review `core-essentials` for critical rules. For full architecture details, see `core-full`.

{2-3 sentence description of what this skill does and when to use it.}

## Usage

Trigger with the `{[Tag]}` action tag:

\`\`\`
@workspace {[Tag]} {example usage}
\`\`\`

---

## Step 1: {First Step Name}

{Step instructions...}

---

## Step 2: {Second Step Name}

{Step instructions...}

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
```

**Guidelines for the skill file:**
- Target **200-400 lines** — agents read the entire file
- Use **numbered steps** with clear instructions
- Include **code examples** where applicable (or reference an `examples/` file for large templates)
- Add **error handling** table for common failures
- Use **tables over prose** — agents parse structured data faster

### For Project Skills

Create `.github/skills/requirements/{project-name}.md` using the structure from existing project skills.

Reference: `read_file → .github/skills/requirements/cr2-phase2-ac-installation.md (lines 1-30)` for the YAML frontmatter and section structure.

---

## Step 3: Create the Prompt File (Action Skills Only)

Create `.github/prompts/{slug}.prompt.md`:

```markdown
---
description: "{emoji} [{Tag}] — {Short description}"
---
# {Skill Display Name}

Use the `{[Tag]}` action tag.{Optional: Add a `[Project-Tag]` for project-specific context.}

## Examples

\`\`\`
@workspace {[Tag]} {example 1}
\`\`\`

\`\`\`
@workspace {[Tag]} {example 2}
\`\`\`

## Skill Context

Read #file:.github/skills/core-essentials.md, for more details read #file:.github/skills/core-full.md and #file:.github/skills/{skill-name}.md — follow the skill workflow.

## Your prompt

@workspace {[Tag]} 
```

**Emoji conventions:**

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

---

## Step 4: Register in Routing Table

### For Action Skills

Edit `.github/copilot-instructions.md` — add a new row to the **Agent Routing Table**:

```markdown
| `{[Tag]}` | `.github/skills/{skill-name}.md` | {Agent Name} |
```

Insert in **alphabetical order** by tag name within the table.

### For Project Skills

Edit `.github/copilot-instructions.md` — add a new row to the **Project Tag Routing** table:

```markdown
| `{[Project-Tag]}` | `.github/skills/requirements/{project-name}.md` |
```

---

## Step 5: Register in SKILL.md Master Index

Edit `.github/skills/SKILL.md` — add the new skill entry under the appropriate category section.

Use this format:

```markdown
### **{N}. {Skill Display Name}**
**Skill:** `{skill-name}`  
**Use when:** {1-line description of when to use this skill}

✨ **You'll Learn:**
- {Capability 1}
- {Capability 2}
- {Capability 3}
```

---

## Step 6: Update readme.md

The readme serves as the team's user guide. Update these sections:

### 6a: Slash Command Table (Section 0 — Setup)

Add a row to the "Quick Prompts (Slash Commands)" table:

```markdown
| `/{slug}` | `{[Tag]}` | {Agent Name} |
```

### 6b: Action Tags ASCII Box (Section 3)

Add a line to the ASCII tag list:

```markdown
│   {emoji} {[Tag]}        {Short description}              │
```

### 6c: Action Tags Detail Table (Section 3)

Add a row to the full action tags table:

```markdown
| `{[Tag]}` | {emoji} | {Agent Name} | {When to Use} | {Example Keywords} |
```

### 6d: Delegation Flow Mermaid Diagram (Section 5)

Add a new node in the mermaid flowchart:

```markdown
C -- "{[Tag]}" --> D{N}["{emoji} {Agent Name}<br>{Short description}"]
D{N} --> E
```

> 💡 Use `grep_search` to find exact locations: search for "Slash Command" table, "ACTION TAGS" box, and the mermaid `flowchart TD` block.

---

## Step 7: Verify Registration

Run these checks:

### 7a: File Existence
```bash
test -f .github/skills/{skill-name}.md && echo "✅ Skill file" || echo "❌ Skill file MISSING"
test -f .github/prompts/{slug}.prompt.md && echo "✅ Prompt file" || echo "❌ Prompt file MISSING"
```

### 7b: Routing Table Entry
```bash
grep "{[Tag]}" .github/copilot-instructions.md && echo "✅ Routing entry" || echo "❌ Routing entry MISSING"
```

### 7c: SKILL.md Entry
```bash
grep "{skill-name}" .github/skills/SKILL.md && echo "✅ SKILL.md entry" || echo "❌ SKILL.md entry MISSING"
```

### 7d: readme.md Entry
```bash
grep "/{slug}" readme.md && echo "✅ readme.md slash command" || echo "❌ readme.md MISSING"
grep "{[Tag]}" readme.md && echo "✅ readme.md action tag" || echo "❌ readme.md action tag MISSING"
```

---

## Output Summary

After completion, present to the user:

```
✅ Skill Registration Complete

📄 Skill File: .github/skills/{skill-name}.md
⌨️ Slash Command: /{slug}
🏷️ Action Tag: {[Tag]}
📋 Prompt File: .github/prompts/{slug}.prompt.md

📝 Registration:
- ✅ Agent Routing Table updated (copilot-instructions.md)
- ✅ SKILL.md master index updated
- ✅ readme.md updated (slash commands, action tags, mermaid diagram)

💡 Usage:
- Slash command: /{slug}
- Tag syntax: @workspace {[Tag]} {your request}
- With project context: @workspace {[Tag]}[{Project-Tag}] {your request}
```

---

## Quick Reference: File Locations

```
.github/
├── copilot-instructions.md          ← Routing table (add row here)
├── instructions/
│   └── core-essentials.instructions.md  ← Auto-applied rules (don't touch)
├── prompts/
│   └── {slug}.prompt.md             ← Slash command file (create)
└── skills/
    ├── SKILL.md                     ← Master index (add entry here)
    ├── {skill-name}.md              ← Skill workflow file (create)
    ├── agents/                      ← Sub-agent prompts (if needed)
    ├── examples/                    ← Code templates (if needed)
    ├── requirements/                ← Project-specific skills (create here)
    ├── sample/                      ← Sample files (Excel templates, etc.)
    └── support/                     ← Python scripts, venv, tools
```

---

## Notes

- Skill files should be **200-400 lines** — the agent reads the entire file each time
- If a skill needs large code templates, extract them to `.github/skills/examples/{name}-templates.md` and reference with "see `.github/skills/examples/...`"
- Every action skill needs **3 things**: skill file + prompt file + routing table entry
- Project skills need **2 things**: requirements file + project tag routing entry
- Use existing skills as reference — `read_file` any similar skill to match the pattern
