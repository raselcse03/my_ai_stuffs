---
description: "📄 [Req-Convert] — Convert Excel/Word requirement documents to PDF + PNG images"
---

Convert an Excel (.xlsx) or Word (.docx) requirement document into PDF and PNG files.
Preserves all visual elements: shapes, arrows, charts, merged cells, formatting.

**Usage:**
- `[Req-Convert] /path/to/requirements.xlsx` — Convert Excel at default 200 DPI
- `[Req-Convert] /path/to/requirements.docx` — Convert Word document
- `[Req-Convert] /path/to/requirements.xlsx --dpi 300` — Higher quality for AI analysis

**Output:** `.github/docs/requirement-conversion/{file-name}/pdf/` + `images/`

**Examples:**
```
[Req-Convert] /home/user/Desktop/requirements/CR5-specs.xlsx
[Req-Convert] /home/user/Desktop/requirements/CR5-specs.docx
[Req-Convert] /home/user/Desktop/requirements/CR5-specs.xlsx --dpi 300
```

## Skill Context

Read #file:.github/skills/core-essentials.md and #file:.github/skills/requirement-conversion/SKILL.md — follow the skill workflow.

## Your prompt

@workspace [Req-Convert] 
