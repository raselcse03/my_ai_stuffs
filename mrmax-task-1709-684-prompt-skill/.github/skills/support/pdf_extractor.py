#!/usr/bin/env python3
"""
PDF Extractor for Requirement Analysis Skill.

Extracts text and renders pages as images from PDF files.
All output goes to a temporary directory that MUST be cleaned up
by the calling agent after use.

Usage:
    python3 pdf_extractor.py <pdf_path> --output-dir <dir>

Output:
    <output-dir>/text_full.md   — extracted text (all pages)
    <output-dir>/page_1.png     — rendered page 1
    <output-dir>/page_2.png     — rendered page 2
    ...

Dependencies:
    pip install pymupdf
"""

import argparse
import os
import sys
import shutil

try:
    import fitz  # PyMuPDF
except ImportError:
    print(
        "ERROR: pymupdf is not installed.\n"
        "Run: pip install -r .github/skills/support/requirements.txt",
        file=sys.stderr,
    )
    sys.exit(1)


def extract_pdf(pdf_path: str, output_dir: str) -> None:
    """Extract text and page images from a PDF file."""
    if not os.path.isfile(pdf_path):
        print(f"ERROR: File not found: {pdf_path}", file=sys.stderr)
        sys.exit(1)

    # Create output directory (clean start)
    if os.path.exists(output_dir):
        shutil.rmtree(output_dir)
    os.makedirs(output_dir, exist_ok=True)

    doc = fitz.open(pdf_path)
    all_text_parts: list[str] = []

    for page_num in range(len(doc)):
        page = doc[page_num]
        page_index = page_num + 1

        # --- Text extraction ---
        text = page.get_text("text")
        if text.strip():
            all_text_parts.append(f"## Page {page_index}\n\n{text.strip()}")

        # --- Page-to-image rendering ---
        # 2x zoom for readable resolution
        matrix = fitz.Matrix(2.0, 2.0)
        pixmap = page.get_pixmap(matrix=matrix)
        image_path = os.path.join(output_dir, f"page_{page_index}.png")
        pixmap.save(image_path)

    total_pages = len(doc)
    doc.close()

    # --- Write combined text ---
    text_path = os.path.join(output_dir, "text_full.md")
    with open(text_path, "w", encoding="utf-8") as f:
        if all_text_parts:
            f.write("# Extracted PDF Text\n\n")
            f.write("\n\n---\n\n".join(all_text_parts))
            f.write("\n")
        else:
            f.write("# Extracted PDF Text\n\n")
            f.write("*No extractable text found. The PDF may contain only images.*\n")
            f.write("*Use view_image on the page_N.png files for visual analysis.*\n")

    # --- Summary ---
    image_files = [f for f in os.listdir(output_dir) if f.endswith(".png")]
    print(f"Extraction complete:")
    print(f"  Pages: {total_pages}")
    print(f"  Text file: {text_path}")
    print(f"  Images: {len(image_files)} page(s) rendered")
    print(f"  Output dir: {output_dir}")
    print()
    print("⚠️  REMINDER: Delete this directory after use:")
    print(f"    rm -rf {output_dir}")


def main() -> None:
    parser = argparse.ArgumentParser(
        description="Extract text and page images from a PDF for requirement analysis."
    )
    parser.add_argument("pdf_path", help="Path to the PDF file")
    parser.add_argument(
        "--output-dir",
        required=True,
        help="Directory to write extracted text and images",
    )
    args = parser.parse_args()

    extract_pdf(args.pdf_path, args.output_dir)


if __name__ == "__main__":
    main()
