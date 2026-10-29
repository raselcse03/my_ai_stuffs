#!/usr/bin/env python3
"""
BAT Excel Generator — Produces formatted Developer BAT .xlsx files.

Usage:
    python3 bat_excel_generator.py <json_input_file> <output_xlsx_path>

JSON Input Format:
{
    "sheet_name": "BAT Testcase - P1709-733",
    "test_cases": [
        {
            "tc_id": 1,
            "feature_test": "Store Reorder: Add to Cart and Validation",
            "main_menu": "Product Page",
            "sub_menu": "Add to Cart",
            "manager_access": "✕",
            "user_access": "○",
            "test_scenario": "Add to Cart Flow",
            "test_type": "Positive",
            "test_items": "Verify that single product add to cart works..."
        }
    ]
}

Formatting matches the sample at .claude/skills/sample/BAT Testcase - Sample.xlsx
"""

import json
import sys
import os

from openpyxl import Workbook
from openpyxl.styles import Font, PatternFill, Alignment, Border, Side
from openpyxl.worksheet.datavalidation import DataValidation
from openpyxl.formatting.rule import CellIsRule
from openpyxl.utils import get_column_letter


# ── Style Constants (matching sample) ────────────────────────────────────────

HEADER_FILL = PatternFill(start_color="FF5B9BD5", end_color="FF5B9BD5", fill_type="solid")
HEADER_FONT = Font(bold=True, color="FFFFFFFF", size=12)
DATA_FONT = Font(size=11)
THIN_BORDER = Border(
    left=Side(style="thin"),
    right=Side(style="thin"),
    top=Side(style="thin"),
    bottom=Side(style="thin"),
)
CENTER_ALIGN = Alignment(horizontal="center", vertical="center", wrap_text=True)
DATA_ALIGN = Alignment(vertical="center", wrap_text=True)
CENTER_V_ALIGN = Alignment(horizontal="center", vertical="center", wrap_text=True)

# Conditional formatting fills for Result columns
RESULT_FILL_OK = PatternFill(start_color="FF92D050", end_color="FF92D050", fill_type="solid")  # Green
RESULT_FILL_NG = PatternFill(start_color="FFFF0000", end_color="FFFF0000", fill_type="solid")  # Red
RESULT_FILL_NE = PatternFill(start_color="FFFFFF00", end_color="FFFFFF00", fill_type="solid")  # Yellow
RESULT_FONT_NG = Font(color="FFFFFFFF", size=11)  # White text on red background

# Column definitions: (header_text, width or None for default)
COLUMNS = [
    ("TC ID", None),            # A
    ("Feature Test", 19.13),    # B
    ("Main Menu", 11.2),        # C
    ("Sub Menu", 10.3),         # D
    ("Manager Acces", 9.0),     # E
    ("User Acces", 7.87),       # F
    ("Test Scenario", 20.87),   # G
    ("Test Type", None),        # H
    ("Test Items", 59.87),      # I
    ("Result (Dev1)", None),    # J
    ("Result (Reviewe)", 11.8), # K
    ("Result (PD)", None),      # L
    ("Comments", None),         # M
]

COL_COUNT = len(COLUMNS)  # 13


def build_workbook(data):
    """Create a formatted BAT workbook from structured data."""
    wb = Workbook()
    ws = wb.active
    ws.title = data.get("sheet_name", "BAT Testcase")

    # ── Row 1: Title (merged A1:M1) ──────────────────────────────────────
    ws.merge_cells(start_row=1, start_column=1, end_row=1, end_column=COL_COUNT)
    title_cell = ws.cell(row=1, column=1, value="Developer BAT Test Cases")
    title_cell.font = HEADER_FONT
    title_cell.fill = HEADER_FILL
    title_cell.alignment = CENTER_ALIGN
    title_cell.border = THIN_BORDER
    # Apply border to all merged cells in row 1
    for col in range(2, COL_COUNT + 1):
        c = ws.cell(row=1, column=col)
        c.border = THIN_BORDER
        c.fill = HEADER_FILL
    ws.row_dimensions[1].height = 23.25

    # ── Row 2: Headers ───────────────────────────────────────────────────
    for col_idx, (header_text, width) in enumerate(COLUMNS, start=1):
        cell = ws.cell(row=2, column=col_idx, value=header_text)
        cell.font = HEADER_FONT
        cell.fill = HEADER_FILL
        cell.alignment = CENTER_ALIGN
        cell.border = THIN_BORDER
        if width is not None:
            ws.column_dimensions[get_column_letter(col_idx)].width = width
    ws.row_dimensions[2].height = 31.5

    # ── Data Rows ────────────────────────────────────────────────────────
    test_cases = data.get("test_cases", [])
    if not test_cases:
        return wb

    row_num = 3
    # Track groups for merging: (feature_test value) → list of row numbers
    feature_groups = {}

    for tc in test_cases:
        tc_id = tc.get("tc_id", "")
        feature_test = tc.get("feature_test", "")
        main_menu = tc.get("main_menu", "")
        sub_menu = tc.get("sub_menu", "")
        manager_access = tc.get("manager_access", "")
        user_access = tc.get("user_access", "")
        test_scenario = tc.get("test_scenario", "")
        test_type = tc.get("test_type", "")
        test_items = tc.get("test_items", "")

        # Read auto-test results if present (from bat_test_runner.py)
        result_dev1 = tc.get("result_dev1", "")
        result_comment = tc.get("result_comment", "")

        row_values = [
            str(tc_id), feature_test, main_menu, sub_menu,
            manager_access, user_access, test_scenario, test_type,
            test_items, result_dev1, "", "", result_comment
        ]

        for col_idx, val in enumerate(row_values, start=1):
            cell = ws.cell(row=row_num, column=col_idx, value=val)
            cell.font = DATA_FONT
            cell.border = THIN_BORDER
            # Center-align specific columns: C, D, E, F
            if col_idx in (3, 4, 5, 6):
                cell.alignment = CENTER_V_ALIGN
            else:
                cell.alignment = DATA_ALIGN

        # Track feature groups for potential merging
        if feature_test:
            feature_groups.setdefault(feature_test, []).append(row_num)

        row_num += 1

    # ── Merge cells for rows sharing the same Feature Test ───────────────
    # Merge columns A (TC ID), B (Feature Test), C (Main Menu), D (Sub Menu),
    # E (Manager Access), F (User Access) when consecutive rows share the
    # same feature_test value AND tc_id
    _merge_consecutive_groups(ws, test_cases, start_data_row=3)

    # ── Data Validations ─────────────────────────────────────────────────
    last_data_row = row_num - 1
    if last_data_row >= 3:
        # Test Type dropdown (column H)
        dv_test_type = DataValidation(
            type="list",
            formula1='"Positive,Negative"',
            allow_blank=False,
            showErrorMessage=True,
        )
        dv_test_type.sqref = f"H3:H{last_data_row}"
        ws.add_data_validation(dv_test_type)

        # Result columns dropdown (columns J, K, L)
        dv_result = DataValidation(
            type="list",
            formula1='"OK,NG,NA,NE"',
            allow_blank=False,
            showErrorMessage=True,
        )
        dv_result.sqref = f"J3:L{last_data_row}"
        ws.add_data_validation(dv_result)

    # ── Conditional Formatting for Result columns (J, K, L) ──────────────
    if last_data_row >= 3:
        result_range = f"J3:L{last_data_row}"
        ws.conditional_formatting.add(
            result_range,
            CellIsRule(operator="equal", formula=['"OK"'], fill=RESULT_FILL_OK),
        )
        ws.conditional_formatting.add(
            result_range,
            CellIsRule(operator="equal", formula=['"NG"'], fill=RESULT_FILL_NG, font=RESULT_FONT_NG),
        )
        ws.conditional_formatting.add(
            result_range,
            CellIsRule(operator="equal", formula=['"NE"'], fill=RESULT_FILL_NE),
        )

    # ── Auto-fit row heights (estimate based on content) ─────────────────
    for r in range(3, row_num):
        test_items_val = ws.cell(row=r, column=9).value or ""
        # Rough estimate: ~80 chars per line at column I width
        lines = max(len(test_items_val) // 80, 1)
        ws.row_dimensions[r].height = max(30, min(lines * 15, 200))

    return wb


def _merge_consecutive_groups(ws, test_cases, start_data_row):
    """Merge cells in columns A-F for consecutive rows with same tc_id."""
    if not test_cases:
        return

    # Identify consecutive groups by tc_id
    groups = []
    current_group_start = 0
    current_tc_id = test_cases[0].get("tc_id")

    for i, tc in enumerate(test_cases):
        if tc.get("tc_id") != current_tc_id:
            if i - current_group_start > 1:
                groups.append((current_group_start, i - 1))
            current_group_start = i
            current_tc_id = tc.get("tc_id")

    # Don't forget last group
    if len(test_cases) - current_group_start > 1:
        groups.append((current_group_start, len(test_cases) - 1))

    # Merge columns A-F for each group
    merge_cols = [1, 2, 3, 4, 5, 6]  # A, B, C, D, E, F
    for group_start, group_end in groups:
        first_row = start_data_row + group_start
        last_row = start_data_row + group_end
        for col in merge_cols:
            if first_row < last_row:
                ws.merge_cells(
                    start_row=first_row, start_column=col,
                    end_row=last_row, end_column=col
                )


def main():
    if len(sys.argv) < 3:
        print("Usage: python3 bat_excel_generator.py <json_input> <output.xlsx>")
        sys.exit(1)

    json_path = sys.argv[1]
    output_path = sys.argv[2]

    with open(json_path, "r", encoding="utf-8") as f:
        data = json.load(f)

    wb = build_workbook(data)

    # Ensure output directory exists
    os.makedirs(os.path.dirname(output_path) or ".", exist_ok=True)
    wb.save(output_path)
    print(f"Generated: {output_path}")


if __name__ == "__main__":
    main()
