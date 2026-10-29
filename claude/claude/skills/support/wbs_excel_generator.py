#!/usr/bin/env python3
"""
WBS Excel Generator — Produces formatted WBS .xlsx files from WBS markdown.

Usage:
    python3 wbs_excel_generator.py <wbs_markdown_file> <output_xlsx_path> [--cr "CR Name"] [--assignees "Name1,Name2"]

The output format matches the sample at .claude/skills/sample/WBS-Sample.xlsx

Columns: A=SL, B=CR, C=Module Name, D=Story List, E=Backlog ID, F=Redmine ID,
         G=Assignee, H=Status, I=Reviewed by JP side, J=Reviewer(PIC),
         K=Development Effort (Man-hour), L=Verification Effort (Man-hour),
         M=Start Date, N=Planned End Date, O=End Date, P=Remarks
"""

import re
import sys
import os
import argparse

from openpyxl import Workbook
from openpyxl.styles import Font, PatternFill, Alignment, Border, Side
from openpyxl.worksheet.datavalidation import DataValidation
from openpyxl.utils import get_column_letter


# ── Style Constants (matching WBS-Sample.xlsx) ───────────────────────────────

# Header row: black background, white bold font
HEADER_FILL = PatternFill(start_color="FF000000", end_color="FF000000", fill_type="solid")
HEADER_FONT = Font(bold=True, color="FFFFFFFF", size=12)

# Story row: green background, bold font
STORY_FILL = PatternFill(start_color="FF93C47D", end_color="FF93C47D", fill_type="solid")
STORY_FONT = Font(bold=True, size=12)

# Subtask row: light green background, normal font
SUBTASK_FILL = PatternFill(start_color="FFD9EAD3", end_color="FFD9EAD3", fill_type="solid")
SUBTASK_FONT = Font(size=11)

THIN_BORDER = Border(
    left=Side(style="thin"),
    right=Side(style="thin"),
    top=Side(style="thin"),
    bottom=Side(style="thin"),
)

WRAP_ALIGN = Alignment(vertical="center", wrap_text=True)
CENTER_ALIGN = Alignment(horizontal="center", vertical="center", wrap_text=True)

# Column definitions: (header_text, width)
COLUMNS = [
    ("SL", 5.0),                                # A
    ("CR", 18.2),                               # B
    ("Module Name", 19.3),                      # C
    ("Stroy List", 59.9),                       # D  (matches sample typo)
    ("Backlog ID", 9.14),                       # E
    ("Redmine ID", 9.14),                       # F
    ("Assignee", 16.8),                         # G
    ("Status", 22.4),                           # H
    ("Reviewed by JP side", 21.3),              # I
    ("Reviewer(PIC)", 14.4),                    # J
    ("Development Effort\n(Man-hour)", 14.4),   # K
    ("Verification Effort\n(Man-hour)", 18.9),  # L
    ("Start Date", 12.0),                       # M
    ("Planned End Date", 14.0),                 # N
    ("End Date", 12.0),                         # O
    ("Remarks", 48.9),                          # P
]

COL_COUNT = len(COLUMNS)  # 16

# Default status options
STATUS_OPTIONS = "Pending,In Progress,Partial,Submitted,Completed,Done,Closed"
REVIEW_OPTIONS = "Open,In Progress,Done"
DEFAULT_ASSIGNEES = ["Dev 1", "Dev 2", "Dev 3", "Dev 4"]

# ── Japanese → English Translation Dictionary ────────────────────────────────
# Domain-specific terms commonly found in WBS documents.
# Longer phrases must come before shorter ones to avoid partial replacements.
JP_TO_EN = {
    "EC依頼リスト_伊勢崎拠点": "EC Request List (Isesaki)",
    "EC依頼リスト_宗像拠点": "EC Request List (Munakata)",
    "EC依頼リスト": "EC Request List",
    "EC依頼": "EC Request",
    "商品手配中": "Arranging",
    "受取可能": "Ready for Pickup",
    "店舗受取": "Store Pickup",
    "宗像拠点": "Munakata Base",
    "伊勢崎拠点": "Isesaki Base",
    "宗像": "Munakata",
    "伊勢崎": "Isesaki",
    "更新": "Update",
    "注文一覧": "Order List",
    "注文詳細": "Order Detail",
    "出荷状況": "Shipping Status",
    "配送状況": "Delivery Status",
    "取り消し": "Cancel",
    "確認": "Confirm",
    "保存": "Save",
    "削除": "Delete",
    "検索": "Search",
    "一覧": "List",
    "詳細": "Detail",
    "管理": "Management",
    "設定": "Settings",
    "登録": "Register",
    "編集": "Edit",
    "追加": "Add",
    "変更": "Change",
    "完了": "Complete",
    "処理中": "Processing",
    "未処理": "Unprocessed",
    "発送済み": "Shipped",
    "入金済み": "Paid",
    "未入金": "Unpaid",
    "対応中": "In Progress",
    "対応済み": "Resolved",
}


def translate_jp(text):
    """Replace Japanese terms with English equivalents."""
    if not text or not isinstance(text, str):
        return text
    for jp, en in JP_TO_EN.items():
        text = text.replace(jp, en)
    return text


# ── WBS Markdown Parser ──────────────────────────────────────────────────────

def parse_wbs_markdown(filepath):
    """Parse WBS markdown file and extract stories with sub-tasks.

    Returns:
        dict: {
            "feature_name": str,
            "stories": [
                {
                    "number": int,
                    "title": str,
                    "subtasks": [
                        {"number": str, "title": str, "estimate": str, "skill": str}
                    ]
                }
            ]
        }
    """
    with open(filepath, "r", encoding="utf-8") as f:
        content = f.read()

    result = {"feature_name": "", "stories": []}

    # Translate Japanese text to English
    content = translate_jp(content)

    # Extract feature name from Epic or top-level heading
    epic_match = re.search(r"## Epic:\s*(.+)", content)
    if epic_match:
        result["feature_name"] = epic_match.group(1).strip()
    else:
        # Fallback: first H1 or H2
        h_match = re.search(r"^#{1,2}\s+(?:Work Breakdown Structure.*?—\s*)?(.+)", content, re.MULTILINE)
        if h_match:
            result["feature_name"] = h_match.group(1).strip()

    # Extract stories — support multiple heading formats:
    #   ### Story 1: Title
    #   ## **STORY 1: Title**
    #   ## **Story 1: Title**
    story_pattern = re.compile(
        r"^#{2,3}\s+\*{0,2}\s*(?:STORY|Story)\s+(\d+):\s*\*{0,2}\s*(.+?)(?:\*{0,2})\s*$",
        re.MULTILINE | re.IGNORECASE
    )

    stories = list(story_pattern.finditer(content))

    for i, story_match in enumerate(stories):
        story_num = int(story_match.group(1))
        story_title = story_match.group(2).strip()

        # Get content between this story and next story (or end)
        start = story_match.end()
        end = stories[i + 1].start() if i + 1 < len(stories) else len(content)
        story_content = content[start:end]

        subtasks = []

        # Parse sub-task list (checkbox format): - [ ] N.M — Title (Skill, hours)
        checklist_pattern = re.compile(
            r"-\s*\[[ x]\]\s*(\d+\.\d+)\s*[—–-]\s*(.+?)(?:\(([^)]*)\))?\s*$",
            re.MULTILINE
        )
        for st_match in checklist_pattern.finditer(story_content):
            st_number = st_match.group(1)
            st_title = st_match.group(2).strip().rstrip(" —–-")
            paren_content = st_match.group(3) or ""

            # Parse skill and estimate from parenthetical
            skill = ""
            estimate = ""
            if paren_content:
                parts = [p.strip() for p in paren_content.split(",")]
                for p in parts:
                    if re.match(r"\d+h?$", p):
                        estimate = p
                    else:
                        skill = p

            subtasks.append({
                "number": st_number,
                "title": st_title,
                "estimate": estimate,
                "skill": skill,
            })

        # If no checklist found, try sub-task table format:
        #   | 1.1 | Title | Layer | 4h | Depends |
        if not subtasks:
            table_pattern = re.compile(
                r"^\|\s*(\d+\.\d+)\s*\|\s*(.+?)\s*\|\s*(.+?)\s*\|\s*(\d+)h?\s*\|",
                re.MULTILINE
            )
            for tb_match in table_pattern.finditer(story_content):
                st_number = tb_match.group(1)
                st_title = tb_match.group(2).strip()
                skill = tb_match.group(3).strip()
                estimate = tb_match.group(4).strip() + "h"
                subtasks.append({
                    "number": st_number,
                    "title": st_title,
                    "estimate": estimate,
                    "skill": skill,
                })

        # If still no subtasks, try detailed sub-task headers:
        #   ##### Sub-task 1.1: Title
        #   ### **Sub-Task 1.1: Title**
        if not subtasks:
            detail_pattern = re.compile(
                r"#{3,5}\s+\*{0,2}\s*Sub-[Tt]ask\s+(\d+\.\d+):\s*\*{0,2}\s*(.+?)(?:\*{0,2})\s*$",
                re.MULTILINE
            )

        # Try #### header format with backtick estimate:
        #   #### **3.1 Backend: Title** `[ 3h ]`
        if not subtasks:
            h4_pattern = re.compile(
                r"^####\s+\*{0,2}\s*(\d+\.\d+)\s+(.+?)\*{0,2}\s*`\[\s*(\d+)h?\s*\]`",
                re.MULTILINE
            )
            for h4_match in h4_pattern.finditer(story_content):
                st_number = h4_match.group(1)
                st_title = h4_match.group(2).strip().rstrip("*").strip()
                estimate = h4_match.group(3).strip() + "h"
                # Extract skill from title prefix (e.g., "Backend: ...")
                skill = ""
                if ":" in st_title:
                    skill = st_title.split(":")[0].strip()
                subtasks.append({
                    "number": st_number,
                    "title": st_title,
                    "estimate": estimate,
                    "skill": skill,
                })

        # Try numbered list format:
        #   1. **Backend: SCSlipService Implementation** — 6h
        if not subtasks:
            numlist_pattern = re.compile(
                r"^\d+\.\s+\*\*(.+?)\*\*\s*[—–-]\s*(\d+)h",
                re.MULTILINE
            )
            seq = 1
            for nl_match in numlist_pattern.finditer(story_content):
                st_title = nl_match.group(1).strip()
                estimate = nl_match.group(2).strip() + "h"
                st_number = f"{story_num}.{seq}"
                skill = ""
                if ":" in st_title:
                    skill = st_title.split(":")[0].strip()
                subtasks.append({
                    "number": st_number,
                    "title": st_title,
                    "estimate": estimate,
                    "skill": skill,
                })
                seq += 1
            for dt_match in detail_pattern.finditer(story_content):
                st_number = dt_match.group(1)
                st_title = dt_match.group(2).strip()

                # Try to get estimate from the line after
                after_idx = dt_match.end()
                estimate_match = re.search(
                    r"\*\*Estimate:\*\*\s*(\d+h?)",
                    story_content[after_idx:after_idx + 200]
                )
                skill_match = re.search(
                    r"\*\*Skill:\*\*\s*(.+?)(?:\s*\||\s*$)",
                    story_content[after_idx:after_idx + 200]
                )

                subtasks.append({
                    "number": st_number,
                    "title": st_title,
                    "estimate": estimate_match.group(1) if estimate_match else "",
                    "skill": skill_match.group(1).strip() if skill_match else "",
                })

        result["stories"].append({
            "number": story_num,
            "title": story_title,
            "subtasks": subtasks,
        })

    return result


# ── Excel Builder ────────────────────────────────────────────────────────────

def build_workbook(wbs_data, cr_name="", assignees=None):
    """Create a formatted WBS workbook from parsed data."""
    wb = Workbook()
    ws = wb.active

    feature = wbs_data.get("feature_name", "WBS")
    # Sanitize sheet title: remove characters invalid in Excel sheet names
    safe_title = re.sub(r'[:\\/?*\[\]]', '', feature).strip()
    ws.title = safe_title[:31] if len(safe_title) > 31 else safe_title

    # ── Row 1: Headers ───────────────────────────────────────────────────
    for col_idx, (header_text, width) in enumerate(COLUMNS, start=1):
        cell = ws.cell(row=1, column=col_idx, value=header_text)
        cell.font = HEADER_FONT
        cell.fill = HEADER_FILL
        cell.alignment = CENTER_ALIGN
        cell.border = THIN_BORDER
        ws.column_dimensions[get_column_letter(col_idx)].width = width

    ws.row_dimensions[1].height = 30

    # ── Data Rows ────────────────────────────────────────────────────────
    stories = wbs_data.get("stories", [])
    if not stories:
        return wb

    row_num = 2
    story_sl = 1

    for story in stories:
        # Story row
        story_title = f"Story {story['number']}: {story['title']}"

        row_values = [
            story_sl,       # A: SL
            cr_name,        # B: CR
            "",             # C: Module Name
            story_title,    # D: Story List
            "",             # E: Backlog ID
            "",             # F: Redmine ID
            "",             # G: Assignee
            "Pending",      # H: Status
            "",             # I: Reviewed by JP side
            "",             # J: Reviewer(PIC)
            "",             # K: Dev Effort
            "",             # L: Verification Effort
            "",             # M: Start Date
            "",             # N: Planned End Date
            "",             # O: End Date
            "",             # P: Remarks
        ]

        for col_idx, val in enumerate(row_values, start=1):
            cell = ws.cell(row=row_num, column=col_idx, value=val)
            cell.font = STORY_FONT
            cell.fill = STORY_FILL
            cell.border = THIN_BORDER
            cell.alignment = WRAP_ALIGN

        row_num += 1

        # Sub-task rows
        for st in story.get("subtasks", []):
            st_title = st["title"]
            estimate = st.get("estimate", "")

            # Parse hours as numeric if possible
            dev_hours = None
            if estimate:
                h_match = re.match(r"(\d+)h?", estimate)
                if h_match:
                    dev_hours = int(h_match.group(1))

            st_values = [
                "",             # A: SL (blank for subtasks)
                "",             # B: CR
                "",             # C: Module Name
                st_title,       # D: Story List (subtask description)
                "",             # E: Backlog ID
                "",             # F: Redmine ID
                "",             # G: Assignee
                "Pending",      # H: Status
                "",             # I: Reviewed by JP side
                "",             # J: Reviewer(PIC)
                dev_hours,      # K: Dev Effort
                "",             # L: Verification Effort
                "",             # M: Start Date
                "",             # N: Planned End Date
                "",             # O: End Date
                "",             # P: Remarks
            ]

            for col_idx, val in enumerate(st_values, start=1):
                cell = ws.cell(row=row_num, column=col_idx, value=val)
                cell.font = SUBTASK_FONT
                cell.fill = SUBTASK_FILL
                cell.border = THIN_BORDER
                cell.alignment = WRAP_ALIGN

            row_num += 1

        story_sl += 1

    # ── Data Validations ─────────────────────────────────────────────────
    last_row = row_num - 1

    # Status dropdown (column H)
    status_dv = DataValidation(
        type="list",
        formula1=f'"{STATUS_OPTIONS}"',
        allow_blank=True,
    )
    status_dv.error = "Please select a valid status"
    status_dv.errorTitle = "Invalid Status"
    ws.add_data_validation(status_dv)
    status_dv.add(f"H2:H{last_row}")

    # Reviewed by JP side dropdown (column I)
    review_dv = DataValidation(
        type="list",
        formula1=f'"{REVIEW_OPTIONS}"',
        allow_blank=True,
    )
    review_dv.error = "Please select a valid review status"
    review_dv.errorTitle = "Invalid Review Status"
    ws.add_data_validation(review_dv)
    review_dv.add(f"I2:I{last_row}")

    # Assignee dropdown (column G)
    assignee_names = assignees if assignees else DEFAULT_ASSIGNEES
    assignee_list = ",".join(assignee_names)
    assignee_dv = DataValidation(
        type="list",
        formula1=f'"{assignee_list}"',
        allow_blank=True,
    )
    assignee_dv.error = "Please select an assignee"
    assignee_dv.errorTitle = "Invalid Assignee"
    ws.add_data_validation(assignee_dv)
    assignee_dv.add(f"G2:G{last_row}")

    # ── Freeze panes (freeze header row) ─────────────────────────────────
    ws.freeze_panes = "A2"

    return wb


# ── Main ─────────────────────────────────────────────────────────────────────

def main():
    parser = argparse.ArgumentParser(description="Generate WBS Excel from WBS markdown")
    parser.add_argument("wbs_file", help="Path to the WBS markdown file")
    parser.add_argument("output_file", help="Path for the output .xlsx file")
    parser.add_argument("--cr", default="", help="CR name (e.g., 'CR5 (Phase-1)')")
    parser.add_argument("--assignees", default="", help="Comma-separated list of assignees for dropdown")

    args = parser.parse_args()

    if not os.path.isfile(args.wbs_file):
        print(f"Error: WBS file not found: {args.wbs_file}", file=sys.stderr)
        sys.exit(1)

    # Ensure output directory exists
    output_dir = os.path.dirname(args.output_file)
    if output_dir:
        os.makedirs(output_dir, exist_ok=True)

    # Parse WBS markdown
    wbs_data = parse_wbs_markdown(args.wbs_file)

    if not wbs_data["stories"]:
        print("Error: No stories found in WBS markdown file", file=sys.stderr)
        sys.exit(1)

    # Parse assignees
    assignees = [a.strip() for a in args.assignees.split(",") if a.strip()] if args.assignees else None

    # Build workbook
    wb = build_workbook(wbs_data, cr_name=args.cr, assignees=assignees)

    # Save
    wb.save(args.output_file)

    story_count = len(wbs_data["stories"])
    subtask_count = sum(len(s["subtasks"]) for s in wbs_data["stories"])
    print(f"✓ WBS Excel generated: {args.output_file}")
    print(f"  Stories: {story_count}, Sub-tasks: {subtask_count}")


if __name__ == "__main__":
    main()
