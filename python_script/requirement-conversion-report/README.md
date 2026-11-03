# Excel Worksheet Converter

Converts every worksheet in an Excel file into a **PDF** and a **PNG image**, preserving all visual elements — shapes, arrows, charts, merged cells, colors, and formatting.

---

## Folder Structure

```
python-script-directory/
├── converted requirements/
│   └── <excel-file-name>/
│       ├── pdf/
│       │   ├── Sheet1.pdf
│       │   └── Sheet2.pdf
│       └── images/
│           ├── Sheet1.png
│           └── Sheet2.png
├── venv/                  ← auto-created on first run
├── run.sh
├── setup.sh
├── python_script.py
└── README.md
```

---

## Quick Start

```bash
# 1. Clone / copy this folder to your machine

# 2. Run (setup happens automatically on first run)
bash run.sh path/to/requirements.xlsx

# Higher DPI for sharper images (default: 200)
bash run.sh path/to/requirements.xlsx --dpi 300
```

---

## Manual Setup (optional)

If you prefer to install dependencies separately before running:

```bash
bash setup.sh
```

---

## Requirements

| Dependency | Purpose |
|---|---|
| **LibreOffice** | Headless Excel → PDF conversion (preserves all visuals) |
| **poppler-utils** | PDF rendering backend for pdf2image |
| **Python 3.8+** | Runtime |
| **openpyxl** | Read worksheet names from Excel |
| **pdf2image** | Convert PDF pages to PNG images |
| **Pillow** | Image processing backend |

---

## How It Works

1. **Reads** all worksheet names from the Excel file.
2. For each sheet, **creates a temporary copy** of the workbook with only that sheet visible.
3. **LibreOffice headless** converts the temporary workbook to PDF — this preserves shapes, arrows, charts, and all formatting exactly as rendered in Excel.
4. **pdf2image** renders each PDF page to a high-resolution PNG image.
5. Both files are saved using the worksheet name under `converted requirements/<excel-name>/`.

---

## Platform Support

| Platform | Status |
|---|---|
| Ubuntu / Debian Linux | ✅ Fully supported |
| macOS (Homebrew) | ✅ Fully supported |
| Windows (WSL2) | ✅ Run inside WSL2 |
| Windows (native) | ⚠ Use WSL2 or install LibreOffice manually |

---

## Tips

- **DPI**: Use `--dpi 300` for documents that will be read by AI agents (sharper text recognition).
- **Large files**: Conversion time scales with sheet complexity. Sheets with many shapes may take 10–30 seconds each.
- **Sheet names with special characters** (`/ \ : * ? " < > |`) are automatically sanitized in output filenames.
