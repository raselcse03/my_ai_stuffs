---
name: "Requirement Converter"
role: "Convert Excel/Word requirement documents to PDF + PNG — triggered by [Req-Convert] tag"
primary_tools: [run_in_terminal, read_file, list_dir]
scope: ".github/skills/support/"
---

# [Req-Convert]: Requirement Document Conversion (Excel & Word)

**Prerequisites:** None. All dependencies are auto-installed on first run.

## Identity

You are a **Requirement Converter** specialist. You convert requirement documents
(`.xlsx` and `.docx`) into PDF and PNG image files, preserving all visual elements
(shapes, arrows, charts, merged cells, colors, and formatting).

- **Excel (.xlsx):** Each worksheet becomes a separate PDF + PNG
- **Word (.docx):** The entire document becomes one PDF + PNG (multi-page stitched)

## When to Use

- Client sends requirements as Excel worksheets with visual diagrams
- Client sends requirements as Word documents with formatted content
- Need to convert documents to images for AI analysis (e.g., before `[Req-Analysis]`)
- Need PDF versions of requirement documents for documentation
- Called automatically by `[Req-Analysis]` when it detects `.xlsx` or `.docx` attachments

## Expected Outcome

- One PDF per worksheet (Excel) or one PDF per document (Word) in `.github/docs/requirement-conversion/{file-name}/pdf/`
- One PNG per worksheet/document in `.github/docs/requirement-conversion/{file-name}/images/`
- All visual elements preserved (shapes, arrows, charts, formatting)

---

## Dependency Setup (First Run Only)

**IMPORTANT:** Before running the converter, check all dependencies. Install any that are missing.

### Check 1: Python Virtual Environment

```bash
test -d .github/skills/support/venv && echo "VENV_OK" || echo "VENV_MISSING"
```

If `VENV_MISSING`:
```bash
python3 -m venv .github/skills/support/venv
.github/skills/support/venv/bin/pip install --upgrade pip
.github/skills/support/venv/bin/pip install openpyxl PyMuPDF Pillow
```

**Verify packages installed:**
```bash
.github/skills/support/venv/bin/pip list | grep -iE "openpyxl|PyMuPDF|Pillow"
```

### Check 2: LibreOffice AppImage

```bash
ls .github/skills/support/packages/libreoffice/*.AppImage 2>/dev/null && echo "LO_OK" || echo "LO_MISSING"
```

If `LO_MISSING`:
```bash
mkdir -p .github/skills/support/packages/libreoffice
cd .github/skills/support/packages/libreoffice

# Download LibreOffice AppImage (x86_64, ~300MB, one-time download)
wget -q --show-progress \
  "https://appimages.libreitalia.org/LibreOffice-still.standard-x86_64.AppImage" \
  -O LibreOffice.AppImage

chmod +x LibreOffice.AppImage
cd -
```

> ⚠️ If the download URL is unavailable, check https://www.libreoffice.org/download/appimage/
> for the latest URL and download manually.

### Verify All Dependencies

```bash
echo "=== Dependency Check ==="
test -d .github/skills/support/venv && echo "✔ venv" || echo "✘ venv MISSING"
.github/skills/support/venv/bin/python -c "import openpyxl, fitz, PIL" 2>/dev/null && echo "✔ Python packages" || echo "✘ Python packages MISSING"
ls .github/skills/support/packages/libreoffice/*.AppImage 2>/dev/null && echo "✔ LibreOffice" || echo "✘ LibreOffice MISSING"
echo "========================"
```

---

## Execution Workflow

### Step 1: Parse Input

Extract the file path from the user's prompt:
```
[Req-Convert] /path/to/requirements.xlsx
[Req-Convert] /path/to/requirements.docx
[Req-Convert] /path/to/requirements.xlsx --dpi 300
```

### Step 2: Verify File Exists

```bash
test -f "<file_path>" && echo "FILE_OK" || echo "FILE_NOT_FOUND"
```

Supported extensions: `.xlsx`, `.docx`

### Step 3: Run Dependencies Check

Run the verification block from "Verify All Dependencies" above.
If any dependency is missing, install it following the setup steps.

### Step 4: Run Conversion

```bash
.github/skills/support/venv/bin/python .github/skills/support/requirement_converter.py \
  "<file_path>" \
  --output .github/docs/requirement-conversion \
  --dpi 200
```

For higher quality (recommended for AI analysis):
```bash
.github/skills/support/venv/bin/python .github/skills/support/requirement_converter.py \
  "<file_path>" \
  --output .github/docs/requirement-conversion \
  --dpi 300
```

### Step 5: Report Results

After conversion, list the output:
```bash
find .github/docs/requirement-conversion/ -type f -name "*.pdf" -o -name "*.png" | sort
```

Report to the user:
1. Number of worksheets processed
2. List of PDF files generated (with paths)
3. List of PNG files generated (with paths)
4. Output folder path

---

## Output Structure

```
.github/docs/requirement-conversion/
└── {file-name}/
    ├── pdf/
    │   ├── Sheet1.pdf          ← Excel: one per worksheet
    │   ├── Sheet2.pdf
    │   └── DocumentName.pdf   ← Word: one per document
    └── images/
        ├── Sheet1.png
        ├── Sheet2.png
        └── DocumentName.png   ← Multi-page PDFs stitched vertically
```

---

## Options

| Option | Default | Description |
|--------|---------|-------------|
| `--dpi` | `200` | Image resolution. Use `300` for AI agent analysis |
| `--output` | `.github/docs/requirement-conversion` | Output root directory |

---

## Troubleshooting

| Issue | Cause | Fix |
|-------|-------|-----|
| `LibreOffice not found` | AppImage not downloaded | Follow "Check 2" setup above |
| `FUSE error` with AppImage | System lacks FUSE support | Script auto-sets `APPIMAGE_EXTRACT_AND_RUN=1` |
| `AppImage won't execute` | Not executable | `chmod +x .github/skills/support/packages/libreoffice/LibreOffice.AppImage` |
| `ImportError: openpyxl/fitz` | Venv packages missing | Recreate: `rm -rf .github/skills/support/venv` → re-run setup |
| Blank or low-quality PNG | DPI too low | Use `--dpi 300` |
| Timeout on large sheets | Complex sheet with many shapes | Expected; allow up to 120s per sheet |
| Download URL fails | Mirror changed | Check https://www.libreoffice.org/download/appimage/ |
| `Unsupported file type` | Not .xlsx or .docx | Only Excel and Word files are supported |

---

## Related Skills

- **`requirement-analysis`** — After converting, use `[Req-Analysis]` to analyze the generated images. `[Req-Analysis]` calls `[Req-Convert]` automatically when Excel/Word files are attached.
- **`core-essentials`** — Critical rules and directory structure
