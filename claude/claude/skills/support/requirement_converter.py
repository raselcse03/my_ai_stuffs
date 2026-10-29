#!/usr/bin/env python3
"""
Requirement Converter — Excel/Word Document → PDF + PNG

Converts Excel worksheets (.xlsx) and Word documents (.docx) to PDF and PNG
images, preserving shapes, arrows, charts, merged cells, and all visual formatting.

Pipeline:
  Excel (.xlsx) → per-sheet isolation → (LibreOffice headless) → PDF → (PyMuPDF) → PNG
  Word  (.docx) → (LibreOffice headless) → PDF → (PyMuPDF) → PNG

Dependencies (auto-installed by skill in .claude/skills/support/venv/):
  Python:  openpyxl, PyMuPDF, Pillow
  Local:   LibreOffice AppImage in .claude/skills/support/packages/libreoffice/

Usage:
  python requirement_converter.py <input_file> [--output DIR] [--dpi N]
  Supported formats: .xlsx, .docx
"""

import os
import sys
import re
import shutil
import subprocess
import argparse
import zipfile
import xml.etree.ElementTree as ET
from pathlib import Path

import openpyxl
import fitz  # PyMuPDF
from PIL import Image

# ── Paths ────────────────────────────────────────────────────────
SCRIPT_DIR = os.path.dirname(os.path.abspath(__file__))
PACKAGES_DIR = os.path.join(SCRIPT_DIR, 'packages', 'libreoffice')
DEFAULT_OUTPUT = os.path.abspath(os.path.join(SCRIPT_DIR, '..', 'docs', 'requirement-conversion'))

# ── OOXML Namespace Constants ────────────────────────────────────
_SPREADSHEET_NS = 'http://schemas.openxmlformats.org/spreadsheetml/2006/main'
_REL_ATTR_NS = 'http://schemas.openxmlformats.org/officeDocument/2006/relationships'


# ══════════════════════════════════════════════════════════════════
#  LibreOffice Discovery
# ══════════════════════════════════════════════════════════════════

def find_libreoffice() -> str:
    """Find LibreOffice: local AppImage first, then system fallback."""
    # 1. Local AppImage in .claude/skills/support/packages/libreoffice/
    if os.path.isdir(PACKAGES_DIR):
        for f in sorted(os.listdir(PACKAGES_DIR)):
            if f.lower().endswith('.appimage'):
                path = os.path.join(PACKAGES_DIR, f)
                if os.access(path, os.X_OK):
                    return path

    # 2. System fallback
    for cmd in ['libreoffice', 'soffice']:
        found = shutil.which(cmd)
        if found:
            return found

    raise FileNotFoundError(
        "LibreOffice not found.\n"
        f"  Expected: {PACKAGES_DIR}/<name>.AppImage\n"
        "  Download: https://www.libreoffice.org/download/appimage/\n"
        "  Then: chmod +x <filename>.AppImage"
    )


# ══════════════════════════════════════════════════════════════════
#  Excel Helpers
# ══════════════════════════════════════════════════════════════════

def get_sheet_names(excel_path: str) -> list:
    """Extract all worksheet names from the Excel file."""
    wb = openpyxl.load_workbook(excel_path, read_only=True, data_only=True)
    names = wb.sheetnames
    wb.close()
    return names


def sanitize_filename(name: str) -> str:
    """Remove/replace characters invalid in filenames."""
    for ch in r'\/:*?"<>|':
        name = name.replace(ch, '_')
    return name.strip()


# ══════════════════════════════════════════════════════════════════
#  XML Manipulation (single-sheet workbook creation)
# ══════════════════════════════════════════════════════════════════

def _register_xml_namespaces(xml_bytes):
    """Extract and register all namespace declarations to preserve prefixes."""
    text = xml_bytes.decode('utf-8') if isinstance(xml_bytes, bytes) else xml_bytes
    for prefix, uri in re.findall(r'xmlns(?::(\w+))?="([^"]+)"', text):
        ET.register_namespace(prefix, uri)


def _apply_fit_to_page(sheet_xml_bytes):
    """Modify worksheet XML to add fitToPage settings. Returns modified bytes."""
    _register_xml_namespaces(sheet_xml_bytes)
    root = ET.fromstring(sheet_xml_bytes)
    ns = _SPREADSHEET_NS

    # Find or create <sheetPr>
    sheet_pr = root.find(f'{{{ns}}}sheetPr')
    if sheet_pr is None:
        sheet_pr = ET.Element(f'{{{ns}}}sheetPr')
        root.insert(0, sheet_pr)

    # Find or create <pageSetUpPr> inside <sheetPr>
    page_setup_pr = sheet_pr.find(f'{{{ns}}}pageSetUpPr')
    if page_setup_pr is None:
        page_setup_pr = ET.SubElement(sheet_pr, f'{{{ns}}}pageSetUpPr')
    page_setup_pr.set('fitToPage', '1')

    # Find or create <pageSetup>
    page_setup = root.find(f'{{{ns}}}pageSetup')
    if page_setup is None:
        page_margins = root.find(f'{{{ns}}}pageMargins')
        if page_margins is not None:
            idx = list(root).index(page_margins) + 1
            page_setup = ET.Element(f'{{{ns}}}pageSetup')
            root.insert(idx, page_setup)
        else:
            page_setup = ET.SubElement(root, f'{{{ns}}}pageSetup')
    page_setup.set('fitToWidth', '1')
    page_setup.set('fitToHeight', '1')

    return ET.tostring(root, xml_declaration=True, encoding='UTF-8')


def _resolve_rel_path(rel_target, base_dir):
    """Resolve a relationship Target to a full ZIP path."""
    if rel_target.startswith('/'):
        return rel_target.lstrip('/')
    return (base_dir + '/' + rel_target).replace('//', '/')


def create_single_sheet_workbook(source_path: str, sheet_name: str, tmp_dir: str) -> str:
    """
    Manipulate the xlsx at ZIP/XML level to HIDE all sheets except the target
    and set fit-to-page. Uses regex for workbook.xml modifications to avoid
    ElementTree re-serialization which breaks LibreOffice compatibility.
    """
    safe_name = sanitize_filename(sheet_name)
    tmp_path = os.path.join(tmp_dir, f"{safe_name}.xlsx")

    ns = _SPREADSHEET_NS
    r_ns = _REL_ATTR_NS

    with zipfile.ZipFile(source_path, 'r') as zin:
        # --- read workbook.xml and find target sheet via ET (read-only) ---
        wb_bytes = zin.read('xl/workbook.xml')
        wb_root = ET.fromstring(wb_bytes)
        sheets_elem = wb_root.find(f'{{{ns}}}sheets')

        target_rid = None
        all_sheet_names = []
        remove_rids = []
        for sheet_el in sheets_elem.findall(f'{{{ns}}}sheet'):
            name = sheet_el.get('name')
            all_sheet_names.append(name)
            rid = sheet_el.get(f'{{{r_ns}}}id')
            if name == sheet_name:
                target_rid = rid
            else:
                remove_rids.append(rid)

        # --- find sheet file paths from rels (read-only) ---
        rels_bytes = zin.read('xl/_rels/workbook.xml.rels')
        rels_root = ET.fromstring(rels_bytes)
        target_sheet_path = None
        remove_paths = set()
        for rel in rels_root:
            rid = rel.get('Id')
            full_path = _resolve_rel_path(rel.get('Target'), 'xl')
            if rid == target_rid:
                target_sheet_path = full_path
            elif rid in remove_rids:
                remove_paths.add(full_path)
                parts = full_path.rsplit('/', 1)
                if len(parts) == 2:
                    remove_paths.add(f"{parts[0]}/_rels/{parts[1]}.rels")

        # --- modify workbook.xml via regex (preserves original XML) ---
        wb_text = wb_bytes.decode('utf-8')
        for name in all_sheet_names:
            escaped = re.escape(name)
            # Strip any existing state attribute first
            wb_text = re.sub(
                r'(<sheet\b[^>]*\bname="' + escaped + r'"[^>]*)\s+state="[^"]*"',
                r'\1', wb_text)
            if name != sheet_name:
                # Add state="veryHidden" to non-target sheets
                wb_text = re.sub(
                    r'(<sheet\b[^>]*\bname="' + escaped + r'")',
                    r'\1 state="veryHidden"', wb_text)
        modified_wb = wb_text.encode('utf-8')

        # --- write modified xlsx ---
        with zipfile.ZipFile(tmp_path, 'w', zipfile.ZIP_DEFLATED) as zout:
            for item in zin.infolist():
                if item.filename in remove_paths:
                    continue
                elif item.filename == 'xl/workbook.xml':
                    zout.writestr(item, modified_wb)
                elif target_sheet_path and item.filename == target_sheet_path:
                    sheet_bytes = zin.read(item.filename)
                    zout.writestr(item, _apply_fit_to_page(sheet_bytes))
                else:
                    zout.writestr(item, zin.read(item.filename))

    return tmp_path


# ══════════════════════════════════════════════════════════════════
#  Conversion Pipeline
# ══════════════════════════════════════════════════════════════════

def convert_to_pdf(input_path: str, output_dir: str) -> str:
    """Convert document to PDF via LibreOffice headless. Works for xlsx, docx, etc."""
    lo_cmd = find_libreoffice()
    cmd = [lo_cmd, '--headless', '--convert-to', 'pdf', '--outdir', output_dir, input_path]

    # AppImage may need APPIMAGE_EXTRACT_AND_RUN if FUSE is unavailable
    env = os.environ.copy()
    if lo_cmd.lower().endswith('.appimage'):
        env['APPIMAGE_EXTRACT_AND_RUN'] = '1'

    result = subprocess.run(cmd, capture_output=True, text=True, timeout=120, env=env)
    if result.returncode != 0:
        raise RuntimeError(
            f"LibreOffice conversion failed for {input_path}:\n{result.stderr}"
        )

    # LibreOffice names the PDF after the input file
    base = Path(input_path).stem
    pdf_path = os.path.join(output_dir, f"{base}.pdf")
    if not os.path.exists(pdf_path):
        # Fallback: find any PDF in the directory
        pdfs = [f for f in os.listdir(output_dir) if f.endswith('.pdf')]
        if not pdfs:
            raise FileNotFoundError(f"No PDF produced for {input_path}")
        pdf_path = os.path.join(output_dir, pdfs[0])
    return pdf_path


def pdf_to_images(pdf_path: str, images_dir: str, base_name: str, dpi: int = 200) -> list:
    """
    Convert PDF → PNG using PyMuPDF.
    Multi-page PDFs are stitched vertically into one seamless image.
    """
    os.makedirs(images_dir, exist_ok=True)
    img_path = os.path.join(images_dir, f"{base_name}.png")

    doc = fitz.open(pdf_path)
    zoom = dpi / 72.0
    mat = fitz.Matrix(zoom, zoom)

    page_images = []
    for page in doc:
        pix = page.get_pixmap(matrix=mat)
        img = Image.frombytes("RGB", [pix.width, pix.height], pix.samples)
        page_images.append(img)
    doc.close()

    if len(page_images) == 1:
        page_images[0].save(img_path, "PNG")
    else:
        # Stitch all pages vertically
        max_width = max(img.width for img in page_images)
        total_height = sum(img.height for img in page_images)
        stitched = Image.new('RGB', (max_width, total_height), 'white')
        y_offset = 0
        for img in page_images:
            stitched.paste(img, (0, y_offset))
            y_offset += img.height
        stitched.save(img_path, "PNG")

    return [img_path]


# ══════════════════════════════════════════════════════════════════
#  Main
# ══════════════════════════════════════════════════════════════════

def convert_excel(excel_path: str, output_root: str, dpi: int = 200) -> str:
    """Main conversion routine. Returns output folder path."""
    excel_path = os.path.abspath(excel_path)
    if not os.path.exists(excel_path):
        raise FileNotFoundError(f"Excel file not found: {excel_path}")

    excel_name = Path(excel_path).stem
    req_folder = os.path.join(output_root, sanitize_filename(excel_name))
    pdf_dir = os.path.join(req_folder, 'pdf')
    images_dir = os.path.join(req_folder, 'images')
    tmp_dir = os.path.join(req_folder, '_tmp')

    for d in [pdf_dir, images_dir, tmp_dir]:
        os.makedirs(d, exist_ok=True)

    sheet_names = get_sheet_names(excel_path)
    print(f"Found {len(sheet_names)} worksheet(s): {sheet_names}")

    for sheet_name in sheet_names:
        safe_name = sanitize_filename(sheet_name)
        print(f"\n→ Processing sheet: '{sheet_name}'")

        # 1. Create isolated workbook with only this sheet visible
        tmp_xlsx = create_single_sheet_workbook(excel_path, sheet_name, tmp_dir)

        # 2. Convert to PDF via LibreOffice
        print("  Converting to PDF…")
        raw_pdf = convert_to_pdf(tmp_xlsx, tmp_dir)

        # 3. Move PDF to final location
        final_pdf = os.path.join(pdf_dir, f"{safe_name}.pdf")
        shutil.move(raw_pdf, final_pdf)
        print(f"  ✔ PDF saved: {final_pdf}")

        # 4. Render PDF pages to PNG via PyMuPDF
        print("  Rendering image(s)…")
        imgs = pdf_to_images(final_pdf, images_dir, safe_name, dpi=dpi)
        for img in imgs:
            print(f"  ✔ Image saved: {img}")

    # Clean up temp files
    shutil.rmtree(tmp_dir, ignore_errors=True)
    print(f"\n✅ All done! Output folder: {req_folder}")
    return req_folder


def convert_docx(docx_path: str, output_root: str, dpi: int = 200) -> str:
    """Convert a Word document (.docx) to PDF + PNG."""
    docx_path = os.path.abspath(docx_path)
    if not os.path.exists(docx_path):
        raise FileNotFoundError(f"Document not found: {docx_path}")

    doc_name = Path(docx_path).stem
    req_folder = os.path.join(output_root, sanitize_filename(doc_name))
    pdf_dir = os.path.join(req_folder, 'pdf')
    images_dir = os.path.join(req_folder, 'images')
    tmp_dir = os.path.join(req_folder, '_tmp')

    for d in [pdf_dir, images_dir, tmp_dir]:
        os.makedirs(d, exist_ok=True)

    safe_name = sanitize_filename(doc_name)
    print(f"\n→ Processing document: '{doc_name}'")

    # 1. Convert to PDF via LibreOffice
    print("  Converting to PDF…")
    raw_pdf = convert_to_pdf(docx_path, tmp_dir)

    # 2. Move PDF to final location
    final_pdf = os.path.join(pdf_dir, f"{safe_name}.pdf")
    shutil.move(raw_pdf, final_pdf)
    print(f"  ✔ PDF saved: {final_pdf}")

    # 3. Render PDF pages to PNG via PyMuPDF
    print("  Rendering image(s)…")
    imgs = pdf_to_images(final_pdf, images_dir, safe_name, dpi=dpi)
    for img in imgs:
        print(f"  ✔ Image saved: {img}")

    # Clean up temp files
    shutil.rmtree(tmp_dir, ignore_errors=True)
    print(f"\n✅ All done! Output folder: {req_folder}")
    return req_folder


def main():
    parser = argparse.ArgumentParser(
        description="Convert Excel/Word documents to PDF and PNG images."
    )
    parser.add_argument(
        'input_file',
        help="Path to the input file (.xlsx or .docx)"
    )
    parser.add_argument(
        '--output', '-o',
        default=DEFAULT_OUTPUT,
        help=f"Output directory (default: {DEFAULT_OUTPUT})"
    )
    parser.add_argument(
        '--dpi',
        type=int,
        default=200,
        help="Image resolution in DPI (default: 200)"
    )
    args = parser.parse_args()

    ext = Path(args.input_file).suffix.lower()
    try:
        if ext == '.xlsx':
            convert_excel(args.input_file, args.output, dpi=args.dpi)
        elif ext == '.docx':
            convert_docx(args.input_file, args.output, dpi=args.dpi)
        else:
            print(f"❌ Unsupported file type: {ext}. Use .xlsx or .docx", file=sys.stderr)
            sys.exit(1)
    except Exception as e:
        print(f"\n❌ Error: {e}", file=sys.stderr)
        sys.exit(1)


if __name__ == '__main__':
    main()
