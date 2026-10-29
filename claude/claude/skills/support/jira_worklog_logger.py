"""
JIRA Daily Worklog Logger
=========================
Fetches a ticket's description + Task Estimation Time, then (after the
calling skill drafts a short comment and the user confirms) logs a worklog
entry and sets the AI Contribution / %Done custom fields.

Config (jira_config.ini):
    [JIRA]
    server    = https://your-domain.atlassian.net
    email     = your-email@example.com
    api_token = your-api-token
    project   = P1709

    task_estimation_time_field = customfield_10806   # plain number field
    ai_contribution_field      = customfield_10193   # select field, options "0".."100"
                                                       # --ai-contribution is ADDED to the ticket's
                                                       # current value (sum capped at 100), not set directly
    done_pct_field             = customfield_10101   # select field, options "0%".."100%" (10% steps)

Usage:
    python jira_worklog_logger.py --fetch P1709-2144 --config /path/jira_config.ini
    python jira_worklog_logger.py --submit P1709-2144 --minutes 45 --ai-contribution 7 \
        --done-pct 80 --date "2026/07/09 08:00" --comment-file /path/comment.txt --config /path/jira_config.ini
    # --date is 24-hour time in Bangladesh Standard Time (UTC+6)
    python jira_worklog_logger.py --submit P1709-2144 --minutes 45 --ai-contribution 7 \
        --comment-file /path/comment.txt --config /path/jira_config.ini --dry-run
"""

import os
import sys
import json
import math
import argparse
import configparser
from datetime import datetime, timezone
from typing import Optional

import requests


# ---------------------------------------------------------------------------
# Config
# ---------------------------------------------------------------------------

def _load_config(config_path: str = "") -> configparser.ConfigParser:
    cfg = configparser.ConfigParser()
    script_dir = os.path.dirname(os.path.abspath(__file__))
    candidates = []
    if config_path:
        candidates.append(config_path)
    candidates.append(os.path.join(script_dir, "jira_config.ini"))
    candidates.append(os.path.join(script_dir, "config.ini"))
    candidates.append("config.ini")
    for path in candidates:
        if os.path.isfile(path):
            cfg.read(path)
            return cfg
    print("ERROR: No config file found — expected jira_config.ini next to script or use --config", file=sys.stderr)
    sys.exit(1)


def _get(cfg: configparser.ConfigParser, section: str, key: str, default: str = "") -> str:
    try:
        val = cfg.get(section, key).strip()
        if val and "your-domain" not in val and "your-email" not in val:
            return val
    except (configparser.NoSectionError, configparser.NoOptionError):
        pass
    return default


# ---------------------------------------------------------------------------
# ADF helpers (plain text descriptions/comments — no headings/bullets needed
# for short worklog narratives)
# ---------------------------------------------------------------------------

def adf_to_text(adf: Optional[dict]) -> str:
    """Flatten an Atlassian Document Format body into plain text."""
    if not adf or not isinstance(adf, dict):
        return ""

    lines: list[str] = []

    def walk(node: dict):
        node_type = node.get("type")
        if node_type == "text":
            lines.append(node.get("text", ""))
            return
        content = node.get("content", [])
        if node_type == "listItem":
            lines.append("- ")
        for child in content:
            walk(child)
        if node_type in ("paragraph", "heading", "listItem"):
            lines.append("\n")

    for block in adf.get("content", []):
        walk(block)

    text = "".join(lines)
    while "\n\n\n" in text:
        text = text.replace("\n\n\n", "\n\n")
    return text.strip()


def text_to_adf(text: str) -> dict:
    """Wrap short plain-text worklog comments in ADF as an unordered bullet list, one item per line."""
    lines = [l.strip() for l in text.strip().splitlines() if l.strip()]
    if not lines:
        lines = [text.strip()]
    items = [l[2:].strip() if l.startswith("- ") else l for l in lines]
    return {
        "version": 1,
        "type": "doc",
        "content": [
            {
                "type": "bulletList",
                "content": [
                    {
                        "type": "listItem",
                        "content": [
                            {"type": "paragraph", "content": [{"type": "text", "text": item}]}
                        ],
                    }
                    for item in items
                ],
            }
        ],
    }


# ---------------------------------------------------------------------------
# JIRA API
# ---------------------------------------------------------------------------

def get_session(email: str, api_token: str) -> requests.Session:
    s = requests.Session()
    s.auth = (email, api_token)
    s.headers.update({"Content-Type": "application/json", "Accept": "application/json"})
    return s


def fetch_issue(session: requests.Session, base_url: str, key: str, estimate_field: str) -> dict:
    fields = f"summary,description,{estimate_field}"
    resp = session.get(f"{base_url}/rest/api/3/issue/{key}", params={"fields": fields})
    if resp.status_code != 200:
        print(f"ERROR: {resp.status_code} — {resp.text[:300]}", file=sys.stderr)
        sys.exit(1)
    data = resp.json()["fields"]
    return {
        "key": key,
        "summary": data.get("summary", ""),
        "description_text": adf_to_text(data.get("description")),
        "estimate_hours": data.get(estimate_field),
    }


def fetch_current_ai_contribution(session: requests.Session, base_url: str, key: str, ai_field: str) -> int:
    """Read the ticket's current AI Contribution value (0 if unset) so new entries can be added on top."""
    resp = session.get(f"{base_url}/rest/api/3/issue/{key}", params={"fields": ai_field})
    if resp.status_code != 200:
        print(f"ERROR: {resp.status_code} — {resp.text[:300]}", file=sys.stderr)
        sys.exit(1)
    field_val = resp.json().get("fields", {}).get(ai_field)
    raw = field_val.get("value") if isinstance(field_val, dict) else field_val
    try:
        return int(raw)
    except (TypeError, ValueError):
        return 0


def resolve_option_id(session: requests.Session, base_url: str, key: str,
                       field_id: str, target_value: str) -> Optional[str]:
    """Look up the option id for a select-field value via the issue's editmeta."""
    resp = session.get(f"{base_url}/rest/api/3/issue/{key}/editmeta")
    if resp.status_code != 200:
        print(f"ERROR: editmeta {resp.status_code} — {resp.text[:300]}", file=sys.stderr)
        sys.exit(1)
    field_meta = resp.json().get("fields", {}).get(field_id)
    if not field_meta:
        print(f"ERROR: field {field_id} not editable on {key}", file=sys.stderr)
        sys.exit(1)
    for opt in field_meta.get("allowedValues", []):
        if str(opt.get("value")).strip() == str(target_value).strip():
            return opt.get("id")
    available = [o.get("value") for o in field_meta.get("allowedValues", [])]
    print(f"ERROR: '{target_value}' is not a valid option for {field_id}. Available: {available}", file=sys.stderr)
    sys.exit(1)


def nearest_done_pct(value: float) -> str:
    """Snap an arbitrary 0-100 done value to the nearest 10% option label (ties round up)."""
    snapped = max(0, min(100, int(math.floor(value / 10.0 + 0.5)) * 10))
    return f"{snapped}%"


def parse_worklog_date(value: str) -> str:
    """Parse a 24-hour 'YYYY/MM/DD HH:MM' (or date-only) string, interpreted as Bangladesh
    Standard Time (UTC+6, no DST), into JIRA's started timestamp format."""
    for fmt in ("%Y/%m/%d %H:%M", "%Y/%m/%d"):
        try:
            dt = datetime.strptime(value.strip(), fmt)
            return dt.strftime("%Y-%m-%dT%H:%M:%S.%f")[:-3] + "+0600"
        except ValueError:
            continue
    print(f"ERROR: --date '{value}' must be 24-hour 'YYYY/MM/DD HH:MM' or 'YYYY/MM/DD'", file=sys.stderr)
    sys.exit(1)


def submit_worklog(session: requests.Session, base_url: str, key: str, minutes: int,
                    comment_text: str, ai_contribution: Optional[int], done_pct: Optional[float],
                    ai_field: str, done_field: str, dry_run: bool,
                    started: Optional[str] = None) -> dict:
    fields_payload: dict = {}
    ai_previous: Optional[int] = None
    ai_total: Optional[int] = None

    if ai_contribution is not None:
        ai_previous = fetch_current_ai_contribution(session, base_url, key, ai_field)
        ai_total = min(100, ai_previous + ai_contribution)
        opt_id = None if dry_run else resolve_option_id(session, base_url, key, ai_field, str(ai_total))
        fields_payload[ai_field] = {"id": opt_id} if opt_id else {"value": str(ai_total)}

    if done_pct is not None:
        label = nearest_done_pct(done_pct)
        opt_id = None if dry_run else resolve_option_id(session, base_url, key, done_field, label)
        fields_payload[done_field] = {"id": opt_id} if opt_id else {"value": label}

    worklog_payload = {
        "started": started or datetime.now(timezone.utc).strftime("%Y-%m-%dT%H:%M:%S.%f")[:-3] + "+0000",
        "timeSpentSeconds": minutes * 60,
        "comment": text_to_adf(comment_text),
    }

    if dry_run:
        return {
            "dry_run": True,
            "issue": key,
            "field_update": fields_payload,
            "worklog": worklog_payload,
            "ai_contribution": None if ai_contribution is None else {
                "previous": ai_previous, "added": ai_contribution, "total": ai_total,
            },
        }

    if fields_payload:
        resp = session.put(f"{base_url}/rest/api/3/issue/{key}", json={"fields": fields_payload})
        if resp.status_code != 204:
            print(f"ERROR: field update {resp.status_code} — {resp.text[:300]}", file=sys.stderr)
            sys.exit(1)

    resp = session.post(f"{base_url}/rest/api/3/issue/{key}/worklog", json=worklog_payload)
    if resp.status_code != 201:
        print(f"ERROR: worklog post {resp.status_code} — {resp.text[:300]}", file=sys.stderr)
        sys.exit(1)

    return {
        "dry_run": False,
        "issue": key,
        "worklog_id": resp.json().get("id"),
        "time_logged_minutes": minutes,
        "ai_contribution": None if ai_contribution is None else {
            "previous": ai_previous, "added": ai_contribution, "total": ai_total,
        },
        "done_pct": None if done_pct is None else nearest_done_pct(done_pct),
    }


# ---------------------------------------------------------------------------
# Entry point
# ---------------------------------------------------------------------------

def main() -> None:
    parser = argparse.ArgumentParser(description="Fetch a JIRA ticket or submit a daily worklog entry.")
    parser.add_argument("--config", default="", help="Path to jira_config.ini")
    group = parser.add_mutually_exclusive_group(required=True)
    group.add_argument("--fetch", metavar="KEY", help="Fetch ticket summary/description/estimate")
    group.add_argument("--submit", metavar="KEY", help="Submit a worklog entry + field updates")
    parser.add_argument("--minutes", type=int, help="Time spent, in minutes (required with --submit)")
    parser.add_argument("--ai-contribution", type=int,
                         help="AI Contribution to ADD to the ticket's current value (0-100, sum capped at 100)")
    parser.add_argument("--done-pct", type=float, help="Done percent (0-100, snapped to nearest 10%%)")
    parser.add_argument("--date", help="Worklog start date/time, 24-hour 'YYYY/MM/DD HH:MM', "
                                        "Bangladesh Standard Time (defaults to now)")
    parser.add_argument("--comment-file", help="Path to a text file containing the worklog comment")
    parser.add_argument("--dry-run", action="store_true", help="Print payloads without calling the JIRA API")
    args = parser.parse_args()

    cfg = _load_config(args.config)
    base_url = _get(cfg, "JIRA", "server").rstrip("/")
    email = _get(cfg, "JIRA", "email")
    token = _get(cfg, "JIRA", "api_token")
    if not all([base_url, email, token]):
        print("ERROR: JIRA server/email/api_token missing in config", file=sys.stderr)
        sys.exit(1)

    estimate_field = _get(cfg, "JIRA", "task_estimation_time_field", "customfield_10806")
    ai_field = _get(cfg, "JIRA", "ai_contribution_field", "customfield_10193")
    done_field = _get(cfg, "JIRA", "done_pct_field", "customfield_10101")

    session = get_session(email, token)

    if args.fetch:
        result = fetch_issue(session, base_url, args.fetch, estimate_field)
        print(json.dumps(result, ensure_ascii=False, indent=2))
        return

    if not args.minutes:
        print("ERROR: --minutes is required with --submit", file=sys.stderr)
        sys.exit(1)
    if not args.comment_file or not os.path.isfile(args.comment_file):
        print("ERROR: --comment-file is required and must exist", file=sys.stderr)
        sys.exit(1)

    with open(args.comment_file, encoding="utf-8") as f:
        comment_text = f.read()

    started = parse_worklog_date(args.date) if args.date else None

    result = submit_worklog(
        session, base_url, args.submit, args.minutes, comment_text,
        args.ai_contribution, args.done_pct, ai_field, done_field, args.dry_run,
        started=started,
    )
    print(json.dumps(result, ensure_ascii=False, indent=2))


if __name__ == "__main__":
    main()
