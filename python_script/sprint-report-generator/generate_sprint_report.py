#!/usr/bin/env python3
"""
PMO Sprint Monitoring Report generator.

Fetches sprint data from Jira and produces a new "Sprint N" sheet plus one
summary row on every dashboard sheet, in the exact format of the existing
PMO_BU1 monitoring workbook (Sprint 7 / Sprint 8 reference).

Usage:
    export JIRA_EMAIL="you@company.com"
    export JIRA_TOKEN="<api token from id.atlassian.com>"
    python generate_sprint_report.py --sprint 9
    python generate_sprint_report.py --sprint 9 --dry-run
    python generate_sprint_report.py --sprint 9 --test-cases 120 --executed-tests 100 --passed-tests 98

Offline testing (no Jira access needed):
    python generate_sprint_report.py --sprint 9 --offline sprint9_data.json
"""

import argparse
import copy as copymod
import datetime as dt
import importlib
import json
import os
import re
import subprocess
import sys
from zoneinfo import ZoneInfo

# --------------------------------------------------------------------------- #
# Auto-install missing dependencies
# --------------------------------------------------------------------------- #

def _ensure_dependencies():
    required = {"requests": "requests>=2.28", "openpyxl": "openpyxl>=3.1"}
    missing = []
    for module, spec in required.items():
        try:
            importlib.import_module(module)
        except ImportError:
            missing.append(spec)
    if not missing:
        return
    print(f"Installing missing dependencies: {', '.join(missing)} ...")
    base_cmd = [sys.executable, "-m", "pip", "install", *missing]
    for extra in ([], ["--user"], ["--break-system-packages"]):
        try:
            subprocess.check_call(base_cmd + extra,
                                  stdout=subprocess.DEVNULL)
            break
        except subprocess.CalledProcessError:
            continue
    else:
        sys.exit("Could not install dependencies automatically. "
                 "Run manually:  pip install " + " ".join(missing))
    importlib.invalidate_caches()
    for module in required:
        importlib.import_module(module)  # fail loudly if still missing
    print("Dependencies installed.\n")


_ensure_dependencies()

import requests
from openpyxl import load_workbook
from openpyxl.formula.translate import Translator
from openpyxl.worksheet.formula import ArrayFormula

# --------------------------------------------------------------------------- #
# Config / CLI
# --------------------------------------------------------------------------- #

def load_config(path):
    with open(path, encoding="utf-8") as fh:
        return json.load(fh)


def parse_args():
    p = argparse.ArgumentParser(description="Generate PMO sprint monitoring report from Jira")
    p.add_argument("--sprint", type=int, default=None, help="Sprint number, e.g. 9")
    p.add_argument("--config", default="report_config.json")
    p.add_argument("--template", default=None, help="Source workbook (default from config)")
    p.add_argument("--output", default=None, help="Output workbook path")
    p.add_argument("--working-days", type=int, default=None, help="Override effective working days (B3)")
    p.add_argument("--test-cases", type=int, default=None)
    p.add_argument("--executed-tests", type=int, default=None)
    p.add_argument("--passed-tests", type=int, default=None)
    p.add_argument("--cicd-commits", type=int, default=None)
    p.add_argument("--cicd-passed", type=int, default=None)
    p.add_argument("--post-release-defects", type=int, default=None)
    p.add_argument("--dry-run", action="store_true", help="Print metrics, do not write workbook")
    p.add_argument("--offline", default=None, help="JSON file with saved Jira data (skip live API)")
    p.add_argument("--save-jira-json", default=None, help="Save fetched Jira data to JSON (for --offline reuse)")
    p.add_argument("--update-durations", action="store_true",
                   help="Refresh working days/duration (B3/B4) on all existing "
                        "'Sprint N' sheets from current Jira sprint dates, "
                        "without adding new sprints")
    args = p.parse_args()
    if not args.update_durations and args.sprint is None:
        p.error("--sprint is required unless --update-durations is used")
    return args


# --------------------------------------------------------------------------- #
# Jira client
# --------------------------------------------------------------------------- #

class JiraClient:
    def __init__(self, base_url, email, token):
        self.base = base_url.rstrip("/")
        self.sess = requests.Session()
        self.sess.auth = (email, token)
        self.sess.headers["Accept"] = "application/json"

    def get(self, path, **params):
        r = self.sess.get(self.base + path, params=params, timeout=60)
        r.raise_for_status()
        return r.json()

    # -- discovery -----------------------------------------------------------
    def find_board(self, project_key, board_id=None):
        if board_id:
            return board_id
        data = self.get("/rest/agile/1.0/board", projectKeyOrId=project_key, type="scrum")
        boards = data.get("values", [])
        if not boards:
            sys.exit(f"No scrum board found for project {project_key}")
        if len(boards) > 1:
            print(f"[warn] {len(boards)} boards found; using '{boards[0]['name']}' "
                  f"(id={boards[0]['id']}). Set jira.board_id in config to override.")
        return boards[0]["id"]

    def find_sprint(self, board_id, sprint_number, name_patterns):
        wanted = [p.format(n=sprint_number).lower() for p in name_patterns]
        start = 0
        while True:
            data = self.get(f"/rest/agile/1.0/board/{board_id}/sprint",
                            startAt=start, maxResults=50, state="active,closed,future")
            for s in data.get("values", []):
                if s["name"].strip().lower() in wanted:
                    return s
            if data.get("isLast", True):
                break
            start += 50
        sys.exit(f"Sprint {sprint_number} not found on board {board_id} "
                 f"(tried names: {wanted})")

    def field_map(self, wanted_names):
        """Map friendly custom-field names -> field ids (customfield_xxxxx)."""
        fields = self.get("/rest/api/3/field")
        out = {}
        for key, name in wanted_names.items():
            for f in fields:
                if f["name"].strip().lower() == name.strip().lower():
                    out[key] = f["id"]
                    break
        return out

    def sprint_issues(self, sprint_id, extra_fields):
        base_fields = ["summary", "issuetype", "status", "timespent",
                       "aggregatetimespent", "labels", "parent", "subtasks",
                       "resolution", "created"]
        fields = ",".join(base_fields + list(extra_fields))
        issues, start = [], 0
        while True:
            data = self.get(f"/rest/agile/1.0/sprint/{sprint_id}/issue",
                            startAt=start, maxResults=100,
                            fields=fields, expand="changelog")
            issues.extend(data.get("issues", []))
            total = data.get("total", 0)
            start += len(data.get("issues", []))
            if start >= total or not data.get("issues"):
                break
        return issues

    def pr_summary(self, issue_id):
        """Best-effort merged-PR detection via dev-status API."""
        try:
            data = self.get("/rest/dev-status/latest/issue/summary", issueId=issue_id)
            pr = data.get("summary", {}).get("pullrequest", {}).get("overall", {})
            return int(pr.get("count") or 0), (pr.get("state") or "")
        except Exception:
            return 0, ""


# --------------------------------------------------------------------------- #
# Metric computation
# --------------------------------------------------------------------------- #

def sprint_days(start, end):
    """Sprint duration in days, straight from the Jira sprint start/end
    datetimes (e.g. May 15 -> May 30 = 15 days). Sprints may be any
    length (7, 15, 30, ...)."""
    return (end - start).days


def parse_jira_date(iso_str, tz_name="UTC"):
    """Jira returns sprint start/endDate as UTC ISO-8601 timestamps.
    Convert to the project's local timezone before taking the calendar
    date, since sprint boundaries land on local midnight (e.g. 18:00 UTC
    the day before == 00:00 local for UTC+6), otherwise the reported
    date is off by one day."""
    ts = dt.datetime.fromisoformat(iso_str.replace("Z", "+00:00"))
    ts = ts.astimezone(ZoneInfo(tz_name))
    return ts.date()


def fmt_duration(start, end):
    if start.year == end.year:
        return f"{start.strftime('%b %-d')} – {end.strftime('%b %-d, %Y')}"
    return f"{start.strftime('%b %-d, %Y')} – {end.strftime('%b %-d, %Y')}"


def _match_any(text, patterns):
    return any(re.search(p, text, re.IGNORECASE) for p in patterns)


def compute_metrics(sprint, issues, cfg, args, sprint_number,
                    apply_overrides=True, jira=None, cf_map=None):
    cls = cfg["classification"]
    statuses = cfg["statuses"]
    ph = cfg["defaults"]

    def opt(name):
        """CLI override value — only honoured for the target sprint."""
        return getattr(args, name) if apply_overrides else None

    tz_name = cfg.get("jira", {}).get("timezone", "UTC")
    start = parse_jira_date(sprint["startDate"], tz_name)
    end = parse_jira_date(sprint["endDate"], tz_name)

    m = {}
    m["sprint_name"] = f"Sprint {sprint_number}"
    m["duration"] = fmt_duration(start, end)
    m["working_days"] = opt("working_days") or sprint_days(start, end)

    def status_of(i): return i["fields"]["status"]["name"]
    def type_of(i): return i["fields"]["issuetype"]["name"]
    def summary_of(i): return i["fields"].get("summary") or ""
    def task_type_of(i):
        if cf_map and "task_type" in cf_map:
            v = i["fields"].get(cf_map["task_type"])
            if isinstance(v, dict):
                return v.get("value") or v.get("name") or ""
            return str(v) if v else ""
        return ""

    # -- effort ---------------------------------------------------------------
    total_seconds = sum(i["fields"].get("timespent") or 0 for i in issues)
    m["actual_spent"] = round(total_seconds / 3600, 1)

    # -- counts ---------------------------------------------------------------
    m["total_tasks"] = len(issues)
    m["completed"] = sum(1 for i in issues if status_of(i) in statuses["completed"])
    m["under_qa"] = sum(1 for i in issues if status_of(i) in statuses["under_qa"])

    # -- development tasks ----------------------------------------------------
    def is_dev(i):
        text = f"{summary_of(i)} {task_type_of(i)}"
        if type_of(i) in cfg["issue_types"]["defect"]:
            return False
        return not _match_any(text, cls["dev_task_exclude_patterns"])
    m["dev_tasks"] = sum(1 for i in issues if is_dev(i))

    # -- coding stories without dev testing -----------------------------------
    by_key = {i["key"]: i for i in issues}
    coding_stories, no_dev_test = 0, 0
    for i in issues:
        subs = i["fields"].get("subtasks") or []
        if not subs:
            continue
        sub_texts = []
        for s in subs:
            k = s.get("key")
            full = by_key.get(k)
            sub_texts.append(summary_of(full) if full else s.get("fields", {}).get("summary", ""))
        has_coding = any(_match_any(t, cls["coding_patterns"]) for t in sub_texts)
        has_test = any(_match_any(t, cls["dev_testing_patterns"]) for t in sub_texts)
        if has_coding:
            coding_stories += 1
            if not has_test:
                no_dev_test += 1
    m["coding_stories"] = coding_stories
    m["tasks_without_dev_testing"] = no_dev_test

    # -- proper review (merged PRs via dev-status API, fallback: review subtask)
    reviewed = 0
    if jira and cfg.get("use_dev_status_api", True):
        for i in issues:
            if i["fields"].get("subtasks") or type_of(i) != "Sub-task":
                cnt, state = jira.pr_summary(i["id"])
                if cnt > 0:
                    reviewed += 1
    if reviewed == 0:  # fallback heuristic
        for i in issues:
            if _match_any(summary_of(i), cls["review_patterns"]):
                reviewed += 1
    m["tasks_with_review"] = reviewed

    # -- CRs -------------------------------------------------------------------
    def is_cr(i):
        return (type_of(i) in cls["cr_issue_types"]
                or any(_match_any(l, cls["cr_patterns"]) for l in (i["fields"].get("labels") or [])))
    crs = [i for i in issues if is_cr(i)]
    m["total_cr"] = len(crs)
    m["approved_cr"] = len(crs)
    m["billable_cr"] = 0
    m["completed_cr"] = sum(1 for i in crs if status_of(i) in statuses["completed"])

    # -- defects ---------------------------------------------------------------
    bugs = [i for i in issues if type_of(i) in cfg["issue_types"]["defect"]]
    m["total_defects"] = len(bugs)
    done_like = set(statuses["completed"]) | set(statuses["under_qa"])
    m["open_defects"] = sum(1 for b in bugs if status_of(b) not in done_like)

    reopened = 0
    for b in bugs:
        for h in (b.get("changelog", {}) or {}).get("histories", []):
            for it in h.get("items", []):
                if it.get("field") == "status" and \
                        (it.get("toString") or "") in statuses["reopened_names"]:
                    reopened += 1
                    break
            else:
                continue
            break
    m["reopened_defects"] = reopened

    if opt("post_release_defects") is not None:
        m["post_release_defects"] = opt("post_release_defects")
    else:
        m["post_release_defects"] = sum(
            1 for b in bugs
            if any(l.lower() in [x.lower() for x in cls["post_release_defect_labels"]]
                   for l in (b["fields"].get("labels") or [])))

    # -- manual / override metrics ---------------------------------------------
    for key in ("test_cases", "executed_tests", "passed_tests"):
        m[key] = opt(key) if opt(key) is not None else ph[key]
    m["cicd_commits"] = opt("cicd_commits") if opt("cicd_commits") is not None else ph["cicd_commits"]
    m["cicd_passed"] = opt("cicd_passed") if opt("cicd_passed") is not None else ph["cicd_passed"]
    return m


# Sprint-sheet cell map: metric key -> cell
SPRINT_CELLS = {
    "sprint_name": "B2", "working_days": "B3", "duration": "B4",
    "actual_spent": "B7",
    "total_tasks": "B15", "dev_tasks": "B16",
    "tasks_without_dev_testing": "B17", "tasks_with_review": "B18",
    "total_cr": "B19", "approved_cr": "B20", "billable_cr": "B21", "completed_cr": "B22",
    "total_defects": "B24", "open_defects": "B25", "reopened_defects": "B26",
    "post_release_defects": "B27",
    "test_cases": "B28", "executed_tests": "B29", "passed_tests": "B30",
    "cicd_commits": "B37", "cicd_passed": "B38",
    "completed": "B40", "under_qa": "B42",
}


# --------------------------------------------------------------------------- #
# Workbook manipulation
# --------------------------------------------------------------------------- #

SPRINT_SHEET_RE = re.compile(r"^Sprint (\d+)$")
SPRINT_REF_RE = re.compile(r"'Sprint (\d+)'!")


def latest_sprint_sheet(wb):
    nums = [(int(m.group(1)), n) for n in wb.sheetnames
            if (m := SPRINT_SHEET_RE.match(n))]
    if not nums:
        sys.exit("No 'Sprint N' sheets found in template")
    return max(nums)  # (number, name)


def formula_text(value):
    return value.text if isinstance(value, ArrayFormula) else value


def translate_row(src_ws, dst_ws, src_row, dst_row, sheet_rename):
    """Clone src_row -> dst_row translating formulas.

    Same-sheet relative refs shift by (dst_row - src_row); refs into
    'Sprint N' sheets are protected from row shifting and renamed via
    sheet_rename (old sheet name -> new sheet name)."""
    for src_cell in src_ws[src_row]:
        dst_cell = dst_ws.cell(row=dst_row, column=src_cell.column)
        val = src_cell.value
        if val is not None and isinstance(formula_text(val), str) \
                and formula_text(val).startswith("="):
            text = formula_text(val)
            # protect cross-sheet sprint refs (whole ref token incl. cell)
            tokens = {}
            def protect(match_obj):
                key = f"__SREF{len(tokens)}__"
                tokens[key] = match_obj.group(0)
                return key
            protected = re.sub(r"'Sprint \d+'![$]?[A-Z]{1,3}[$]?\d+", protect, text)
            translated = Translator(protected, origin=src_cell.coordinate)\
                .translate_formula(dst_cell.coordinate)
            for key, orig in tokens.items():
                for old, new in sheet_rename.items():
                    orig = orig.replace(f"'{old}'!", f"'{new}'!")
                translated = translated.replace(key, orig)
            if isinstance(val, ArrayFormula):
                dst_cell.value = ArrayFormula(dst_cell.coordinate, translated)
            else:
                dst_cell.value = translated
        else:
            dst_cell.value = val
        if src_cell.has_style:
            dst_cell._style = copymod.copy(src_cell._style)
        dst_cell.number_format = src_cell.number_format


def find_sprint_row(ws, sheet_name_latest, col="A"):
    """Row in a dashboard sheet whose col-A formula/text references the latest sprint."""
    for row in ws.iter_rows(min_col=1, max_col=1):
        c = row[0]
        t = formula_text(c.value)
        if isinstance(t, str) and (f"'{sheet_name_latest}'" in t or t == sheet_name_latest):
            return c.row
    return None


def update_sprint_durations(wb, jira, board_id, cfg):
    """Refresh B3 (working days) and B4 (duration) on every existing
    'Sprint N' sheet using the current Jira sprint start/end dates.
    Downstream formulas (B5, B10, B11, B12, B51, B52) reference B3
    directly, so they recalculate automatically once Excel opens."""
    tz_name = cfg.get("jira", {}).get("timezone", "UTC")
    updated = []
    for name in list(wb.sheetnames):
        m = SPRINT_SHEET_RE.match(name)
        if not m:
            continue
        n = int(m.group(1))
        sprint = jira.find_sprint(board_id, n, cfg["jira"]["sprint_name_patterns"])
        start = parse_jira_date(sprint["startDate"], tz_name)
        end = parse_jira_date(sprint["endDate"], tz_name)
        new_days, new_dur = sprint_days(start, end), fmt_duration(start, end)
        ws = wb[name]
        old_days, old_dur = ws["B3"].value, ws["B4"].value
        ws["B3"] = new_days
        ws["B4"] = new_dur
        updated.append((name, old_days, old_dur, new_days, new_dur))
    return updated


def add_sprint_to_workbook(wb, metrics, sprint_number, cfg):
    """Add one 'Sprint N' sheet + dashboard rows to an open workbook."""
    latest_num, latest_name = latest_sprint_sheet(wb)
    new_name = f"Sprint {sprint_number}"
    if new_name in wb.sheetnames:
        print(f"[skip] Sheet '{new_name}' already exists")
        return {}

    ph_text = cfg.get("narrative_placeholder", "TBD")
    # sheet-name mapping for cross-sheet formula refs:
    #   latest sprint -> new sprint; any older sprint ref -> latest sprint
    def sheet_rename_map(text_names):
        rename = {latest_name: new_name}
        for n in text_names:
            if n != latest_name:
                rename[n] = latest_name
        return rename
    all_sprint_names = [n for n in wb.sheetnames if SPRINT_SHEET_RE.match(n)]
    rename = sheet_rename_map(all_sprint_names)

    # ---- 1. copy latest sprint sheet ---------------------------------------
    src = wb[latest_name]
    new_ws = wb.copy_worksheet(src)
    new_ws.title = new_name
    # position it before the latest sprint sheet (descending order convention)
    wb.move_sheet(new_name, offset=wb.sheetnames.index(latest_name) - wb.sheetnames.index(new_name))

    # ---- 2. write Jira-derived metrics --------------------------------------
    for key, cell in SPRINT_CELLS.items():
        new_ws[cell] = metrics[key]

    # ---- 2b. duration-scaled formulas ----------------------------------------
    # The template formulas assume a fixed half-month sprint (".../2").
    # Sprints can be any length (7/15/30 days), so scale monthly figures by
    # the sprint's Jira duration: fraction of month = B3 / days_per_month.
    dpm = cfg.get("days_per_month", 30)
    for cell, formula in {
        "B5":  f"=(Team!P14*8*20)*(B3/{dpm})",   # PV - Planned Value (hrs)
        "B10": f"=Team!S14*(B3/{dpm})",           # BAC (Budget)
        "B11": f"=Team!O14*(B3/{dpm})",           # AC - Actual Cost
        "B12": f"=Team!S14*(B3/{dpm})",           # Revenue
        "B51": f"=(Team!N14*8*20)*(B3/{dpm})",   # Planned Capacity (hrs)
        "B52": f"=(Team!M14*8*20)*(B3/{dpm})",   # Actual Capacity
    }.items():
        new_ws[cell] = formula

    # ---- 3. reset the risk table (E:I) to placeholders ----------------------
    for r in range(2, 60):
        for col in "EFGHI":
            new_ws[f"{col}{r}"] = None
    new_ws["E2"], new_ws["F2"] = "R-01", ph_text
    new_ws["G2"] = ph_text
    new_ws["H2"], new_ws["I2"] = "Low", 1

    # ---- 4. append dashboard rows -------------------------------------------
    dash_sheets = ["Sprint Overview", "Health Dashboard", "Margin_Deviation",
                   "Quality_Status", "Capacity_Dashboard"]
    new_rows = {}
    for name in dash_sheets:
        ws = wb[name]
        src_row = find_sprint_row(ws, latest_name)
        if src_row is None:
            print(f"[warn] could not locate latest-sprint row in '{name}', skipping")
            continue
        dst_row = src_row + 1
        translate_row(ws, ws, src_row, dst_row, rename)
        new_rows[name] = dst_row

    # manual/narrative cells on the new dashboard rows
    r = new_rows.get("Sprint Overview")
    if r:
        ws = wb["Sprint Overview"]
        ws[f"G{r}"] = ph_text                      # PMO Observations summary
        ws[f"O{r}"], ws[f"P{r}"] = "TBA", "TBA"    # GDM compliance
        ws[f"T{r}"] = "Not Collected Yet"
    r = new_rows.get("Margin_Deviation")
    if r:
        wb["Margin_Deviation"][f"G{r}"] = "N/A"    # Root cause
    r = new_rows.get("Quality_Status")
    if r:
        wb["Quality_Status"][f"G{r}"] = ph_text    # QA gate compliance narrative
    r = new_rows.get("Health Dashboard")
    if r:
        wb["Health Dashboard"][f"O{r}"] = "N/A"    # CR status

    # ---- 5. narrative placeholder rows --------------------------------------
    ws = wb["PMO Observations"]
    nr = ws.max_row + 1
    for area in ["Governance", "Delivery", "Quality"]:
        ws[f"A{nr}"], ws[f"B{nr}"] = metrics["sprint_name"], area
        ws[f"C{nr}"], ws[f"D{nr}"] = ph_text, ph_text
        nr += 1

    ws = wb["Risk Register"]
    nr = ws.max_row + 1
    ws[f"A{nr}"], ws[f"B{nr}"] = metrics["sprint_name"], f"R-{nr - 1:02d}"
    for col in "CDEFG":
        ws[f"{col}{nr}"] = ph_text
    ws[f"H{nr}"] = "Low"

    # ---- 6. Project Overview: latest-row pointer + reporting date -----------
    po = wb["Project Overview"]
    if new_rows.get("Sprint Overview"):
        po["S10"] = new_rows["Sprint Overview"]
    po["K2"] = f"  Reporting Date:  {dt.date.today().isoformat()}"

    return new_rows


# --------------------------------------------------------------------------- #
# Main
# --------------------------------------------------------------------------- #

def resolve_paths(args, cfg):
    """Returns (source_workbook, output_path).

    Output is a fixed cumulative file in reports_dir. If it already exists,
    it becomes the source (so previously generated sprints are kept);
    otherwise the template is the source."""
    if args.output:
        output = args.output
        os.makedirs(os.path.dirname(output) or ".", exist_ok=True)
    else:
        reports_dir = cfg.get("reports_dir", "reports")
        os.makedirs(reports_dir, exist_ok=True)
        output = os.path.join(reports_dir,
                              cfg.get("output_name", "PMO_BU1_Mr Max DEV Labo_Monitoring_Dev.xlsx"))
    if args.template:
        source = args.template
    elif os.path.exists(output):
        source = output
        print(f"Using existing report as source: {output}")
    else:
        source = cfg["template"]
        print(f"Using template as source: {source}")
    return source, output


def load_offline(path):
    """Offline JSON: either a single blob {sprint, issues, field_map} or a
    multi-sprint dict {"9": blob, "10": blob, ...}."""
    with open(path, encoding="utf-8") as fh:
        blob = json.load(fh)
    if "sprint" in blob and "issues" in blob:
        return {None: blob}          # single, sprint number unknown
    return {int(k): v for k, v in blob.items()}


def main():
    args = parse_args()
    cfg = load_config(args.config)
    source, output = resolve_paths(args, cfg)

    if args.update_durations:
        wb = load_workbook(source)
        auth_cfg = cfg.get("auth", {})
        email = os.environ.get("JIRA_EMAIL") or auth_cfg.get("email") or ""
        token = os.environ.get("JIRA_TOKEN") or auth_cfg.get("token") or ""
        if not email or not token:
            sys.exit("Jira credentials missing. Either fill the \"auth\" section "
                     "(email, token) in report_config.json, or set JIRA_EMAIL and "
                     "JIRA_TOKEN environment variables. Create a token at "
                     "https://id.atlassian.com/manage-profile/security/api-tokens")
        jira = JiraClient(cfg["jira"]["base_url"], email, token)
        board_id = jira.find_board(cfg["jira"]["project_key"], cfg["jira"].get("board_id"))
        updated = update_sprint_durations(wb, jira, board_id, cfg)
        if not updated:
            print("No 'Sprint N' sheets found to update.")
            return
        for name, old_days, old_dur, new_days, new_dur in updated:
            changed = " (changed)" if (old_days, old_dur) != (new_days, new_dur) else ""
            print(f"{name}: {old_dur!r} ({old_days}d) -> {new_dur!r} ({new_days}d){changed}")
        if args.dry_run:
            print("\n--dry-run: workbook not written.")
            return
        wb.save(output)
        print(f"\nSaved: {output}")
        return

    # ---- which sprints are missing? ------------------------------------------
    wb = load_workbook(source)
    latest_num, latest_name = latest_sprint_sheet(wb)
    if args.sprint <= latest_num:
        if args.dry_run:
            todo = [args.sprint]
            print(f"Sprint {args.sprint} already in workbook — dry-run "
                  "calibration mode (compare printed metrics with the sheet).")
        else:
            sys.exit(f"Nothing to do: workbook already contains sprints up to "
                     f"'{latest_name}' (requested Sprint {args.sprint}).")
    else:
        todo = list(range(latest_num + 1, args.sprint + 1))
        print(f"Existing sheets up to {latest_name}; generating: "
              + ", ".join(f"Sprint {n}" for n in todo))

    # ---- data source ----------------------------------------------------------
    jira, cf_map, board_id, offline = None, {}, None, None
    if args.offline:
        offline = load_offline(args.offline)
        if None in offline and len(todo) > 1:
            sys.exit("Offline file has a single sprint but multiple sprints are "
                     "missing. Provide a multi-sprint JSON: {\"9\": {...}, \"10\": {...}}")
    else:
        auth_cfg = cfg.get("auth", {})
        email = os.environ.get("JIRA_EMAIL") or auth_cfg.get("email") or ""
        token = os.environ.get("JIRA_TOKEN") or auth_cfg.get("token") or ""
        if not email or not token:
            sys.exit("Jira credentials missing. Either fill the \"auth\" section "
                     "(email, token) in report_config.json, or set JIRA_EMAIL and "
                     "JIRA_TOKEN environment variables. Create a token at "
                     "https://id.atlassian.com/manage-profile/security/api-tokens")
        jira = JiraClient(cfg["jira"]["base_url"], email, token)
        board_id = jira.find_board(cfg["jira"]["project_key"], cfg["jira"].get("board_id"))
        cf_map = jira.field_map(cfg["custom_field_names"])

    # ---- generate each missing sprint -----------------------------------------
    saved_blobs, all_new_rows = {}, {}
    for n in todo:
        print(f"\n########## Sprint {n} ##########")
        if offline is not None:
            blob = offline.get(n) or offline.get(None)
            if not blob:
                sys.exit(f"Offline file has no data for sprint {n}")
            sprint, issues = blob["sprint"], blob["issues"]
            cf_map = blob.get("field_map", cf_map)
        else:
            sprint = jira.find_sprint(board_id, n, cfg["jira"]["sprint_name_patterns"])
            tz_name = cfg.get("jira", {}).get("timezone", "UTC")
            local_start = parse_jira_date(sprint["startDate"], tz_name) if sprint.get("startDate") else "?"
            local_end = parse_jira_date(sprint["endDate"], tz_name) if sprint.get("endDate") else "?"
            print(f"Found sprint: {sprint['name']} (id={sprint['id']}, "
                  f"{local_start} → {local_end})")
            issues = jira.sprint_issues(sprint["id"], list(cf_map.values()))
            print(f"Fetched {len(issues)} issues")
            saved_blobs[n] = {"sprint": sprint, "issues": issues, "field_map": cf_map}

        # CLI overrides (QA/CI-CD numbers, working days) apply to the
        # requested sprint only; backfilled sprints use config defaults.
        metrics = compute_metrics(sprint, issues, cfg, args, sprint_number=n,
                                  apply_overrides=(n == args.sprint),
                                  jira=jira, cf_map=cf_map)

        print(f"=== Computed metrics — Sprint {n} ===")
        for key, cell in SPRINT_CELLS.items():
            print(f"  {cell:<4} {key:<28} {metrics[key]}")

        if not args.dry_run:
            rows = add_sprint_to_workbook(wb, metrics, n, cfg)
            all_new_rows[f"Sprint {n}"] = rows

    if args.save_jira_json and saved_blobs:
        with open(args.save_jira_json, "w", encoding="utf-8") as fh:
            json.dump({str(k): v for k, v in saved_blobs.items()}, fh)
        print(f"\nSaved Jira data → {args.save_jira_json}")

    if args.dry_run:
        print("\n--dry-run: workbook not written.")
        return

    wb.save(output)
    print(f"\nSaved: {output}")
    print("Dashboard rows added:", all_new_rows)
    print("\nManual follow-ups (placeholders written as "
          f"'{cfg.get('narrative_placeholder','TBD')}'):")
    print("  • New sprint sheets: risk table E2:I2+ (add real risks; "
          "each needs a Risk score in col I)")
    print("  • Sprint Overview: col G (PMO summary), O/P (GDM score)")
    print("  • Quality_Status: col G (QA gate compliance)")
    print("  • PMO Observations + Risk Register: placeholder rows")
    print("  • QA test cases / CI-CD numbers if not passed as CLI options")
    print("  • Team sheet: update if resources changed")
    print("\nOpen the file in Excel to recalculate all formulas.")


if __name__ == "__main__":
    main()
