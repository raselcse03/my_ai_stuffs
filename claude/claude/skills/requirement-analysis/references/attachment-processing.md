# Requirement Analysis — Attachment Processing

Full conversion/extraction procedure for Step 1 (1b–1e) — loaded when preparing attachments (Excel/Word/PDF/images) into `RAW_REQUIREMENTS`. Do not load earlier.

## 1b: Convert Excel & Word Files (if any)

For each `.xlsx` or `.docx` attachment, ensure `[Req-Convert]` dependencies are ready:

```bash
echo "=== Dependency Check ==="
test -d .claude/skills/support/venv && echo "✔ venv" || echo "✘ venv MISSING"
.claude/skills/support/venv/bin/python -c "import openpyxl, fitz, PIL" 2>/dev/null && echo "✔ Python packages" || echo "✘ Python packages MISSING"
ls .claude/skills/support/packages/libreoffice/*.AppImage 2>/dev/null && echo "✔ LibreOffice" || echo "✘ LibreOffice MISSING"
echo "========================"
```

If any dependency is missing, follow the setup in `requirement-conversion.md`.

Then convert each file (use `--dpi 300` for best AI analysis quality):

```bash
.claude/skills/support/venv/bin/python .claude/skills/support/requirement_converter.py \
  "<file_path>" \
  --output .github/docs/requirement-conversion \
  --dpi 300
```

Collect output paths for each converted file:
- **PDFs:** `.github/docs/requirement-conversion/{file-name}/pdf/*.pdf`
- **PNGs:** `.github/docs/requirement-conversion/{file-name}/images/*.png`

## 1c: Extract Text from All PDFs

For **every** PDF — both original attachments AND converted outputs from Step 1b:

```bash
python3 .claude/skills/support/pdf_extractor.py "<path-to-pdf>" --output-dir /tmp/req-analysis-$$
```

This produces:
- `/tmp/req-analysis-$$/text_full.md` — extracted text (all pages)
- `/tmp/req-analysis-$$/page_N.png` — rendered page images (for diagrams/tables)

Read the extracted text:
```
Read → /tmp/req-analysis-$$/text_full.md
```

## 1d: View All Images

For **best visual fidelity**, use `view_image` on:

1. **Converted PNGs from Step 1b** — these preserve shapes, arrows, charts that may not survive text extraction. These are higher quality than re-rendered PDF page images.
2. **Original image attachments** (PNG, JPG, etc.)
3. **Page images from pdf_extractor** — for pages with diagrams/tables in original PDFs

> 💡 **Performance tip:** For Excel/Word sources, prefer converted PNGs over pdf_extractor
> page images. The converted PNGs are rendered directly from LibreOffice at high DPI.

## 1e: Compile RAW_REQUIREMENTS

Combine all extracted text and image references into a single `RAW_REQUIREMENTS` variable.
Include source file attribution for each section:

```
=== Source: {filename} (type: xlsx → converted) ===
{extracted text from converted PDF}

=== Source: {filename} (type: docx → converted) ===
{extracted text from converted PDF}

=== Source: {filename} (type: pdf → original) ===
{extracted text from pdf_extractor}

=== Source: {filename} (type: image → viewed directly) ===
[Image viewed via view_image — visual content integrated above]
```
