"""
JIRA Story & Sub-task Creator — Dynamic WBS Markdown Parser
============================================================
Reads any WBS .md file and creates JIRA Stories + Sub-tasks in backlog.
No Epic, no Sprint, no Assignee — just Stories with Sub-tasks.

Config (config.ini):
    [JIRA]
    server    = https://your-domain.atlassian.net
    email     = your-email@example.com
    api_token = your-api-token
    project   = CR5

Usage:
    python create_jira_from_wbs.py --wbs wbs-cr5-vpoint-card-linkage.md
    python create_jira_from_wbs.py --wbs wbs-cr5-vpoint-card-linkage.md --dry-run
"""

import os
import re
import sys
import time
import json
import logging
import argparse
import configparser
from dataclasses import dataclass, field
from typing import Optional

import requests

logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s [%(levelname)s] %(message)s",
)
log = logging.getLogger(__name__)

# ---------------------------------------------------------------------------
# Config — reads from config.ini
# ---------------------------------------------------------------------------

def _load_config() -> configparser.ConfigParser:
    cfg = configparser.ConfigParser()
    if os.path.isfile("config.ini"):
        cfg.read("config.ini")
        log.info("Loaded config.ini")
    return cfg

def _get(cfg: configparser.ConfigParser, section: str, key: str,
         default: str = "") -> str:
    """Return value from config.ini, or default."""
    try:
        val = cfg.get(section, key).strip()
        if val and "your-domain" not in val and "your-email" not in val:
            return val
    except (configparser.NoSectionError, configparser.NoOptionError):
        pass
    return default

_CFG = _load_config()

JIRA_BASE_URL      = _get(_CFG, "JIRA", "server").rstrip("/")
JIRA_EMAIL         = _get(_CFG, "JIRA", "email")
JIRA_API_TOKEN     = _get(_CFG, "JIRA", "api_token")
JIRA_PROJECT_KEY   = _get(_CFG, "JIRA", "project")
STORY_POINTS_FIELD = _get(_CFG, "JIRA", "story_points_field", "customfield_10016")
STORY_ISSUE_TYPE   = _get(_CFG, "BEHAVIOUR", "story_type",   "Story")
SUBTASK_ISSUE_TYPE = _get(_CFG, "BEHAVIOUR", "subtask_type", "Sub-task")

try:
    SUBTASK_DELAY  = float(_get(_CFG, "BEHAVIOUR", "subtask_delay", "0.2"))
    STORY_DELAY    = float(_get(_CFG, "BEHAVIOUR", "story_delay",   "0.3"))
except ValueError:
    SUBTASK_DELAY, STORY_DELAY = 0.2, 0.3

_extra_labels_raw = _get(_CFG, "LABELS", "extra_labels", "")
EXTRA_LABELS = [l.strip() for l in _extra_labels_raw.split(",") if l.strip()]


# ---------------------------------------------------------------------------
# Data models
# ---------------------------------------------------------------------------

@dataclass
class SubTask:
    summary: str


@dataclass
class Story:
    name: str                          # e.g. "Story 1"
    summary: str
    priority: str = "Medium"
    story_points: Optional[int] = None
    acceptance_criteria: list[str] = field(default_factory=list)
    subtasks: list[SubTask] = field(default_factory=list)
    labels: list[str] = field(default_factory=list)


@dataclass
class WBSDocument:
    epic_title: str = ""
    epic_description: str = ""
    stories: list[Story] = field(default_factory=list)


# ---------------------------------------------------------------------------
# Markdown parser
# ---------------------------------------------------------------------------

def parse_wbs_markdown(md_text: str) -> WBSDocument:
    """
    Parse a WBS markdown file into a WBSDocument.

    Recognised patterns
    -------------------
    Epic title  : ## Epic: <title>   OR   # <title>
    Story block : ### Story N: <summary>   (### heading)
    Priority    : **Priority:** <value>
    Points      : **Story Points:** <int>
    AC items    : lines inside an Acceptance Criteria block starting with "- [ ]" or "- "
    Sub-tasks   : lines inside a Sub-tasks block starting with "- [ ]" or "- "
    """
    doc = WBSDocument()
    lines = md_text.splitlines()

    # ── Pass 1: locate epic title ─────────────────────────────────────────
    for line in lines:
        m = re.match(r"^##\s+Epic:\s*(.+)", line)
        if m:
            doc.epic_title = m.group(1).strip()
            break
    if not doc.epic_title:
        # Fallback: first H1 or H2
        for line in lines:
            m = re.match(r"^#{1,2}\s+(.+)", line)
            if m:
                doc.epic_title = m.group(1).strip()
                break

    # ── Pass 2: split into story blocks by "### " headings ───────────────
    story_blocks: list[list[str]] = []
    current: list[str] = []

    for line in lines:
        if re.match(r"^###\s+", line):
            if current:
                story_blocks.append(current)
            current = [line]
        else:
            if current:
                current.append(line)

    if current:
        story_blocks.append(current)

    # ── Pass 3: parse each story block ───────────────────────────────────
    for block in story_blocks:
        header = block[0]

        # Must look like "### Story N: ..." or "### <anything>"
        story_name = ""
        story_summary = ""

        m = re.match(r"^###\s+(Story\s+\d+)\s*[:\-–]\s*(.+)", header)
        if m:
            story_name    = m.group(1).strip()
            story_summary = m.group(2).strip()
        else:
            m2 = re.match(r"^###\s+(.+)", header)
            if m2:
                story_name    = m2.group(1).strip()
                story_summary = story_name
            else:
                continue  # not a story heading

        story = Story(name=story_name, summary=story_summary)

        # Detect sections inside the block
        section = None   # "ac" | "subtasks" | None

        for line in block[1:]:
            stripped = line.strip()

            # ── Priority ──────────────────────────────────────────────
            # Handles: **Priority:** High  |  Priority: High
            m = re.search(r"Priority\*{0,2}:\*{0,2}\s+([A-Za-z]+)", stripped)
            if m:
                story.priority = m.group(1).strip()
                section = None
                continue

            # ── Story Points ──────────────────────────────────────────
            # Handles: **Story Points:** 13  |  Story Points: 13
            m = re.search(r"Story Points\*{0,2}:\*{0,2}\s+(\d+)", stripped)
            if m:
                story.story_points = int(m.group(1))
                section = None
                continue

            # ── Section headers ────────────────────────────────────────
            if re.match(r"#{3,5}\s+Sub[- ]?tasks?", stripped, re.IGNORECASE):
                section = "subtasks"
                continue
            if re.match(r"#{3,5}\s+Acceptance\s+Criteria", stripped, re.IGNORECASE):
                section = "ac"
                continue
            # Bold section header variant: **Sub-tasks:**
            if re.match(r"\*{1,2}Sub[- ]?tasks?\*{1,2}", stripped, re.IGNORECASE):
                section = "subtasks"
                continue
            if re.match(r"\*{1,2}Acceptance\s+Criteria\*{1,2}", stripped, re.IGNORECASE):
                section = "ac"
                continue

            # ── Horizontal rule / separator — reset section ────────────
            if re.match(r"^-{3,}$", stripped):
                section = None
                continue

            # ── Blank line — keep section context ──────────────────────
            if not stripped:
                continue

            # ── List items ─────────────────────────────────────────────
            # Match "- [ ] text", "- [x] text", "- text"
            item_match = re.match(r"^-\s+(?:\[.?\]\s+)?(.+)", stripped)
            if item_match:
                item_text = item_match.group(1).strip()
                # Strip trailing size markers like " — M" or " — S/L"
                item_text = re.sub(r"\s+[—–-]\s+[SMxl]+$", "", item_text).strip()

                if section == "subtasks":
                    story.subtasks.append(SubTask(summary=item_text))
                elif section == "ac":
                    story.acceptance_criteria.append(item_text)
                # If section is unknown but line looks like a numbered item, ignore
                continue

        doc.stories.append(story)

    return doc


# ---------------------------------------------------------------------------
# JIRA API helpers
# ---------------------------------------------------------------------------

def get_session() -> requests.Session:
    s = requests.Session()
    s.auth = (JIRA_EMAIL, JIRA_API_TOKEN)
    s.headers.update({"Content-Type": "application/json", "Accept": "application/json"})
    return s


def validate_env() -> None:
    required = {
        "JIRA_BASE_URL": JIRA_BASE_URL,
        "JIRA_EMAIL": JIRA_EMAIL,
        "JIRA_API_TOKEN": JIRA_API_TOKEN,
        "JIRA_PROJECT_KEY": JIRA_PROJECT_KEY,
    }
    missing = [k for k, v in required.items() if not v]
    if missing:
        log.error("Missing environment variables: %s", ", ".join(missing))
        sys.exit(1)


def post_issue(session: requests.Session, payload: dict, dry_run: bool) -> Optional[str]:
    if dry_run:
        log.info("[DRY-RUN] %s", json.dumps(payload, ensure_ascii=False, indent=2))
        return f"DRY-{payload['fields']['issuetype']['name'][:3].upper()}-???"

    url = f"{JIRA_BASE_URL}/rest/api/3/issue"
    resp = session.post(url, json=payload)
    if resp.status_code == 201:
        key = resp.json()["key"]
        log.info("  ✓ Created %s", key)
        return key
    else:
        log.error("  ✗ %s — %s", resp.status_code, resp.text[:300])
        return None


def text_to_adf(text: str) -> dict:
    """Wrap plain text in Atlassian Document Format (ADF)."""
    return {
        "version": 1,
        "type": "doc",
        "content": [
            {
                "type": "paragraph",
                "content": [{"type": "text", "text": text}],
            }
        ],
    }


def ac_list_to_adf(items: list[str]) -> dict:
    """Build an ADF document with a heading + bullet list for AC items."""
    bullet_items = [
        {
            "type": "listItem",
            "content": [
                {
                    "type": "paragraph",
                    "content": [{"type": "text", "text": item}],
                }
            ],
        }
        for item in items
    ]
    content: list[dict] = []
    if items:
        content.append({
            "type": "heading",
            "attrs": {"level": 3},
            "content": [{"type": "text", "text": "Acceptance Criteria"}],
        })
        content.append({"type": "bulletList", "content": bullet_items})
    return {"version": 1, "type": "doc", "content": content}


def build_story_payload(story: Story, project_labels: list[str]) -> dict:
    fields: dict = {
        "project": {"key": JIRA_PROJECT_KEY},
        "summary": story.summary,
        "issuetype": {"name": STORY_ISSUE_TYPE},
        "priority": {"name": story.priority},
        "description": ac_list_to_adf(story.acceptance_criteria),
        "labels": list(set(project_labels + EXTRA_LABELS)),
    }

    if story.story_points is not None:
        fields[STORY_POINTS_FIELD] = story.story_points

    return {"fields": fields}


def build_subtask_payload(subtask: SubTask, parent_key: str, project_labels: list[str]) -> dict:
    return {
        "fields": {
            "project": {"key": JIRA_PROJECT_KEY},
            "summary": subtask.summary,
            "issuetype": {"name": SUBTASK_ISSUE_TYPE},
            "parent": {"key": parent_key},
            "labels": list(set(project_labels + EXTRA_LABELS)),
        }
    }


# ---------------------------------------------------------------------------
# Orchestrator
# ---------------------------------------------------------------------------

def run(wbs_path: str, dry_run: bool) -> None:
    # 1. Read & parse markdown
    log.info("Reading WBS: %s", wbs_path)
    with open(wbs_path, encoding="utf-8") as f:
        md_text = f.read()

    doc = parse_wbs_markdown(md_text)
    log.info("Parsed Epic : %s", doc.epic_title)
    log.info("Parsed Stories: %d", len(doc.stories))
    total_subtasks = sum(len(s.subtasks) for s in doc.stories)
    log.info("Parsed Sub-tasks: %d", total_subtasks)

    if not dry_run:
        validate_env()

    session = get_session()

    # Derive labels from the project key
    raw_label = re.sub(r"[^a-zA-Z0-9\-]", "-", JIRA_PROJECT_KEY or "WBS").strip("-")
    project_labels = [raw_label]

    # 2. Create Stories + Sub-tasks (no Epic — stories go to backlog)
    results = []
    for story in doc.stories:
        log.info("Creating Story — %s: %s", story.name, story.summary)
        story_payload = build_story_payload(story, project_labels)
        story_key = post_issue(session, story_payload, dry_run)

        if not story_key:
            log.warning("Skipping sub-tasks for '%s' (story creation failed).", story.name)
            results.append({"story": story.name, "key": None, "subtasks": []})
            continue

        subtask_keys = []
        for subtask in story.subtasks:
            st_payload = build_subtask_payload(subtask, story_key, project_labels)
            st_key = post_issue(session, st_payload, dry_run)
            if st_key:
                subtask_keys.append(st_key)
            if not dry_run:
                time.sleep(SUBTASK_DELAY)  # rate-limit safety

        results.append({
            "story": story.name,
            "summary": story.summary,
            "key": story_key,
            "subtasks": subtask_keys,
        })

        if not dry_run:
            time.sleep(STORY_DELAY)

    # 3. Summary
    print("\n" + "=" * 65)
    print("CREATION SUMMARY")
    print("=" * 65)
    print(f"Project : {JIRA_PROJECT_KEY}  (backlog)")
    print()
    total_created = 0
    for r in results:
        status = r["key"] or "FAILED"
        print(f"  {status:<14} {r.get('summary', r['story'])}")
        for sk in r.get("subtasks", []):
            print(f"      └─ {sk}")
        total_created += (1 if r["key"] else 0) + len(r.get("subtasks", []))
    print()
    print(f"Total issues created : {total_created}")
    print(f"Stories              : {len([r for r in results if r['key']])}")
    print(f"Sub-tasks            : {sum(len(r.get('subtasks', [])) for r in results)}")


# ---------------------------------------------------------------------------
# Entry point
# ---------------------------------------------------------------------------

if __name__ == "__main__":
    parser = argparse.ArgumentParser(
        description="Parse a WBS .md file and create JIRA Stories + Sub-tasks."
    )
    parser.add_argument(
        "--wbs",
        required=True,
        help="Path to the WBS markdown file (e.g. wbs-cr5-vpoint-card-linkage.md)",
    )
    parser.add_argument(
        "--dry-run",
        action="store_true",
        help="Print payloads without making any JIRA API calls",
    )
    args = parser.parse_args()

    if not os.path.isfile(args.wbs):
        log.error("File not found: %s", args.wbs)
        sys.exit(1)

    run(wbs_path=args.wbs, dry_run=args.dry_run)
