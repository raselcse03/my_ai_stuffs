#!/usr/bin/env python3
"""
Excel Worksheet Converter
Converts each worksheet in an Excel file to both PDF and PNG image.
Preserves shapes, arrows, charts, and all visual elements via LibreOffice.
"""

import os
import sys
import re
import shutil
import subprocess
import argparse
import glob
import zipfile
import xml.etree.ElementTree as ET
from pathlib import Path

import openpyxl
from pdf2image import convert_from_path
from PIL import Image

# OOXML namespace constants
_SPREADSHEET_NS = 'http://schemas.openxmlformats.org/spreadsheetml/2006/main'
_REL_ATTR_NS = 'http://schemas.openxmlformats.org/officeDocument/2006/relationships'


def get_sheet_names(excel_path: str) -> list[str]:
    """Extract all worksheet names from the Excel file."""
    wb = openpyxl.load_workbook(excel_path, read_only=True, data_only=True)
    names = wb.sheetnames
    wb.close()
    return names


def sanitize_filename(name: str) -> str:
    """Remove or replace characters that are invalid in filenames."""
    invalid = r'\/:*?"<>|'
    for ch in invalid:
        name = name.replace(ch, "_")
    return name.strip()


def _register_xml_namespaces(xml_bytes):
    """Extract and register all namespace declarations to preserve prefixes on write."""
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
    and set fit-to-page.  Uses regex for workbook.xml modifications to avoid
    ElementTree re-serialization which breaks LibreOffice compatibility.
    """
    safe_name = sanitize_filename(sheet_name)
    tmp_path = os.path.join(tmp_dir, f"{safe_name}.xlsx")

    ns = _SPREADSHEET_NS
    r_ns = _REL_ATTR_NS

    with zipfile.ZipFile(source_path, 'r') as zin:
        # --- read workbook.xml and find target sheet path via ET (read-only) ---
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
                # Also mark the sheet's rels file for removal
                parts = full_path.rsplit('/', 1)
                if len(parts) == 2:
                    remove_paths.add(f"{parts[0]}/_rels/{parts[1]}.rels")

        # --- modify workbook.xml via regex (preserves original XML byte-for-byte
        #     except for the targeted attribute changes) ---
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

        # --- write modified xlsx: hide other sheets AND remove their files ---
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


def _find_libreoffice() -> str:
    """Locate the LibreOffice/soffice binary, handling macOS cask installs."""
    # Prefer whatever is on PATH first
    for name in ("libreoffice", "soffice"):
        path = shutil.which(name)
        if path:
            return path
    # macOS cask default location
    mac_path = "/Applications/LibreOffice.app/Contents/MacOS/soffice"
    if os.path.isfile(mac_path):
        return mac_path
    raise FileNotFoundError(
        "LibreOffice not found. Install it with: brew install --cask libreoffice"
    )


def convert_xlsx_to_pdf_libreoffice(xlsx_path: str, output_dir: str) -> str:
    """
    Use LibreOffice headless to convert an xlsx file to PDF.
    Returns the path to the generated PDF.
    """
    cmd = [
        _find_libreoffice(),
        "--headless",
        "--convert-to", "pdf",
        "--outdir", output_dir,
        xlsx_path,
    ]
    result = subprocess.run(cmd, capture_output=True, text=True, timeout=120)
    if result.returncode != 0:
        raise RuntimeError(
            f"LibreOffice conversion failed for {xlsx_path}:\n{result.stderr}"
        )

    # LibreOffice names the PDF after the input file
    base = Path(xlsx_path).stem
    pdf_path = os.path.join(output_dir, f"{base}.pdf")
    if not os.path.exists(pdf_path):
        # Try to find any PDF produced
        pdfs = glob.glob(os.path.join(output_dir, "*.pdf"))
        if not pdfs:
            raise FileNotFoundError(f"No PDF produced for {xlsx_path}")
        pdf_path = pdfs[0]
    return pdf_path


def pdf_to_images(pdf_path: str, images_dir: str, base_name: str, dpi: int = 200):
    """
    Convert a PDF to a single PNG image.
    If the PDF has multiple pages, stitch them vertically into one seamless image.
    """
    os.makedirs(images_dir, exist_ok=True)
    pages = convert_from_path(pdf_path, dpi=dpi)

    img_path = os.path.join(images_dir, f"{base_name}.png")

    if len(pages) == 1:
        pages[0].save(img_path, "PNG")
    else:
        # Stitch all pages vertically into one image
        max_width = max(p.width for p in pages)
        total_height = sum(p.height for p in pages)
        stitched = Image.new('RGB', (max_width, total_height), 'white')
        y_offset = 0
        for p in pages:
            stitched.paste(p, (0, y_offset))
            y_offset += p.height
        stitched.save(img_path, "PNG")

    return [img_path]


def convert_excel(excel_path: str, output_root: str, dpi: int = 200):
    """Main conversion routine."""
    excel_path = os.path.abspath(excel_path)
    if not os.path.exists(excel_path):
        raise FileNotFoundError(f"Excel file not found: {excel_path}")

    excel_name = Path(excel_path).stem
    req_folder = os.path.join(output_root, sanitize_filename(excel_name))
    pdf_dir    = os.path.join(req_folder, "pdf")
    images_dir = os.path.join(req_folder, "images")
    tmp_dir    = os.path.join(req_folder, "_tmp")

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
        print(f"  Converting to PDF…")
        raw_pdf = convert_xlsx_to_pdf_libreoffice(tmp_xlsx, tmp_dir)

        # 3. Move PDF to final location with sheet name
        final_pdf = os.path.join(pdf_dir, f"{safe_name}.pdf")
        shutil.move(raw_pdf, final_pdf)
        print(f"  ✔ PDF saved: {final_pdf}")

        # 4. Render PDF pages to PNG images
        print(f"  Rendering image(s)…")
        imgs = pdf_to_images(final_pdf, images_dir, safe_name, dpi=dpi)
        for img in imgs:
            print(f"  ✔ Image saved: {img}")

    # Clean up temp files
    shutil.rmtree(tmp_dir, ignore_errors=True)
    print(f"\n✅ All done! Output folder: {req_folder}")


def main():
    parser = argparse.ArgumentParser(
        description="Convert Excel worksheets to PDF and PNG images."
    )
    parser.add_argument(
        "excel_file",
        help="Path to the input Excel file (.xlsx / .xls)"
    )
    parser.add_argument(
        "--output", "-o",
        default="converted requirements",
        help="Root output directory (default: 'converted requirements')"
    )
    parser.add_argument(
        "--dpi",
        type=int,
        default=200,
        help="Image resolution in DPI (default: 200)"
    )
    args = parser.parse_args()

    try:
        convert_excel(args.excel_file, args.output, dpi=args.dpi)
    except Exception as e:
        print(f"\n❌ Error: {e}", file=sys.stderr)
        sys.exit(1)


if __name__ == "__main__":
    main()
