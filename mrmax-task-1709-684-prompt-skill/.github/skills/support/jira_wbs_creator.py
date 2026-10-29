"""
JIRA Story & Sub-task Creator — Dynamic WBS Markdown Parser
============================================================
Reads any WBS .md file and creates JIRA Stories + Sub-tasks in backlog.
No Epic, no Sprint, no Assignee — just Stories with Sub-tasks.

Config (jira_config.ini):
    [JIRA]
    server    = https://your-domain.atlassian.net
    email     = your-email@example.com
    api_token = your-api-token
    project   = CR5

Usage:
    python jira_wbs_creator.py --wbs wbs-feature.md --config /path/to/jira_config.ini
    python jira_wbs_creator.py --wbs wbs-feature.md --config /path/to/jira_config.ini --dry-run
    python jira_wbs_creator.py --wbs wbs-feature.md  # falls back to config.ini in script dir
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

def _load_config(config_path: str = "") -> configparser.ConfigParser:
    """Load config.ini from the specified path, or fall back to the script directory."""
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
            log.info("Loaded config: %s", path)
            return cfg
    log.warning("No config file found — expected jira_config.ini next to script or use --config")
    return cfg

def _get(cfg: configparser.ConfigParser, section: str, key: str,
         default: str = "") -> str:
    """Return value from config file, or default."""
    try:
        val = cfg.get(section, key).strip()
        if val and "your-domain" not in val and "your-email" not in val:
            return val
    except (configparser.NoSectionError, configparser.NoOptionError):
        pass
    return default

# Pre-parse --config so module-level constants are loaded from the right file
_pre_parser = argparse.ArgumentParser(add_help=False)
_pre_parser.add_argument("--config", default="")
_pre_args, _ = _pre_parser.parse_known_args()
_CFG = _load_config(_pre_args.config)

JIRA_BASE_URL      = _get(_CFG, "JIRA", "server").rstrip("/")
JIRA_EMAIL         = _get(_CFG, "JIRA", "email")
JIRA_API_TOKEN     = _get(_CFG, "JIRA", "api_token")
JIRA_PROJECT_KEY   = _get(_CFG, "JIRA", "project")
STORY_POINTS_FIELD = _get(_CFG, "JIRA", "story_points_field", "customfield_10016")
TASK_ESTIMATION_TIME_FIELD = _get(_CFG, "JIRA", "task_estimation_time_field", "")
STORY_ISSUE_TYPE   = _get(_CFG, "BEHAVIOUR", "story_type",   "Story")
SUBTASK_ISSUE_TYPE = _get(_CFG, "BEHAVIOUR", "subtask_type", "Sub-task")

try:
    SUBTASK_DELAY  = float(_get(_CFG, "BEHAVIOUR", "subtask_delay", "0.2"))
    STORY_DELAY    = float(_get(_CFG, "BEHAVIOUR", "story_delay",   "0.3"))
except ValueError:
    SUBTASK_DELAY, STORY_DELAY = 0.2, 0.3

_extra_labels_raw = _get(_CFG, "LABELS", "extra_labels", "")
EXTRA_LABELS = [l.strip() for l in _extra_labels_raw.split(",") if l.strip()]


def _parse_checklist_items(raw: str) -> list[str]:
    """Parse checklist items from config (multiline or pipe-separated)."""
    if not raw:
        return []

    chunks = raw.splitlines() if "\n" in raw else raw.split("|")
    items: list[str] = []
    for chunk in chunks:
        item = re.sub(r"^-\s*(?:\[.?\]\s*)?", "", chunk.strip())
        if item:
            items.append(item)
    return items


# Full MrMax Coding Conventions — reformatted as ADF sections
FULL_CODING_CONVENTIONS = {
    "1. Scope and Architecture": [
        "Do custom development in app/Customize/, app/Plugin/, app/config/, and app/template/.",
        "Do not modify src/Eccube/ directly.",
        "Keep controllers thin; place business logic in service classes.",
        "Use repositories for data access and services for orchestration.",
    ],
    "2. Non-Negotiable Rules": [
        "Never modify src/Eccube/.",
        "Never generate or run Doctrine migrations in this project.",
        "Use manual SQL scripts for schema changes.",
        "Use dependency injection (constructor injection) for services.",
        "Use parameterized queries; never concatenate SQL strings.",
        "Validate input at system boundaries.",
        "Use transactions for multi-step write operations.",
        "Clear cache after configuration changes.",
    ],
    "3. Directory and Layer Conventions": [
        "Controllers: app/Customize/Controller/",
        "Services: app/Customize/Service/",
        "Repositories: app/Customize/Repository/",
        "Entities: app/Customize/Entity/",
        "Form Types / Validators: app/Customize/Form/",
        "Templates: app/template/",
        "Service wiring: app/config/eccube/services.yaml",
        "Security/firewall config: app/config/eccube/packages/security.yaml",
    ],
    "4. Naming Conventions": [
        "Service class: {Domain}Service (e.g., SpFileDownloadService)",
        "Repository class: {Domain}Repository (e.g., VpointRedeemResultRepository)",
        "Controller class: {Feature}Controller (e.g., SpFileDownloadController)",
        "Form class: {Domain}Type",
        "Route name: {scope}_{feature}_{action}",
    ],
    "5. Security Conventions": [
        "Keep sensitive values in environment variables.",
        "Use constant-time comparisons for credential checks.",
        "For firewall patterns, prefer exact route matching if endpoint must be isolated.",
        "Do not allow accidental prefix route bypass for security: false firewalls.",
    ],
    "6. SQL & Data Conventions": [
        "Use Doctrine repositories/query builder where possible.",
        "Use parameter binding in all queries.",
        "No raw interpolated SQL.",
        "For schema evolution: manual SQL only, no generated migrations.",
    ],
    "7. API Conventions": [
        "Use consistent HTTP status semantics: 200 (success with payload), 204 (success no payload), 400 (bad request), 401 (auth failure), 403 (forbidden), 500 (internal failure), 503 (service unavailable).",
        "Standard API error format: { \"error\": { \"message\": \"...\" } }",
    ],
    "8. Logging Conventions": [
        "Use structured context in logs (file, source, backup, error, ip, etc.).",
        "Log at appropriate level: info (lifecycle), warning (invalid requests/auth), error (operation failure), critical (misconfiguration/security).",
    ],
}

DEFAULT_CODING_CONVENTION_CHECKLIST = [
    "No changes in src/Eccube (use app/Customize, app/Plugin, app/config, app/template)",
    "No Doctrine migrations; use manual SQL scripts for schema changes",
    "Controllers stay thin and delegate business logic to services",
    "Use constructor dependency injection for services",
    "Use parameterized queries; never concatenate SQL strings",
    "Validate input at system boundaries",
    "Use transactions for multi-step write operations",
    "Run cache clear and validation commands for touched modules",
]

_cc_enabled = _get(_CFG, "CODING_CONVENTION", "enabled", "true").lower() not in {
    "0",
    "false",
    "no",
    "off",
}
_cc_items_raw = _get(_CFG, "CODING_CONVENTION", "checklist_items", "")
_cc_items_from_config = _parse_checklist_items(_cc_items_raw)
CODING_CONVENTION_CHECKLIST: list[str] = []
if _cc_enabled:
    CODING_CONVENTION_CHECKLIST = _cc_items_from_config or DEFAULT_CODING_CONVENTION_CHECKLIST

# PR Review sub-task generation (auto-added to each story)
_pr_review_enabled = _get(_CFG, "PR_REVIEW", "enabled", "true").lower() not in {
    "0",
    "false",
    "no",
    "off",
}
PR_REVIEW_SUBTASK_ENABLED: bool = _pr_review_enabled
PR_REVIEW_SUBTASK_SUMMARY: str = _get(_CFG, "PR_REVIEW", "summary", "PR Review & Code Quality")
PR_REVIEW_SUBTASK_DESCRIPTION: str = _get(
    _CFG,
    "PR_REVIEW",
    "description",
    "Code review, testing coverage verification, static analysis, and documentation validation.",
)
try:
    PR_REVIEW_ESTIMATE_HOURS: float = float(_get(_CFG, "PR_REVIEW", "estimate_hours", "8"))
except ValueError:
    PR_REVIEW_ESTIMATE_HOURS = 8.0


# ---------------------------------------------------------------------------
# Data models
# ---------------------------------------------------------------------------

@dataclass
class SubTask:
    summary: str
    description: str = ""
    estimate_hours: Optional[float] = None
    acceptance_criteria: list[str] = field(default_factory=list)
    definition_of_done: list[str] = field(default_factory=list)


@dataclass
class Story:
    name: str                          # e.g. "Story 1"
    summary: str
    priority: str = "Medium"
    story_points: Optional[int] = None
    summary_text: str = ""             # Story Overview
    affected_components: str = ""      # Affected Components
    acceptance_criteria: list[str] = field(default_factory=list)
    corner_cases: list[str] = field(default_factory=list)
    risks: list[str] = field(default_factory=list)
    notes: list[str] = field(default_factory=list)
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

def _collect_section_text(lines: list[str]) -> str:
    """Join non-empty, non-metadata lines into a paragraph."""
    parts = []
    for line in lines:
        stripped = line.strip()
        if stripped and not re.match(r"^-\s+\*{2}", stripped):
            parts.append(stripped)
    return "\n".join(parts)


def _extract_list_items(lines: list[str]) -> list[str]:
    """Extract list items (- [ ] text or - text) from lines."""
    items = []
    for line in lines:
        stripped = line.strip()
        m = re.match(r"^-\s+(?:\[.?\]\s+)?(.+)", stripped)
        if m:
            items.append(m.group(1).strip())
    return items


def _extract_metadata_value(lines: list[str], key: str) -> str:
    """Extract value from '- **Key:** value' metadata line."""
    for line in lines:
        m = re.match(rf"^-\s+\*{{2}}{re.escape(key)}:?\*{{2}}\s*(.*)", line.strip())
        if m:
            return m.group(1).strip()
    return ""


def _parse_table_data_rows(lines: list[str]) -> list[str]:
    """Extract data rows from markdown tables as formatted strings."""
    rows = []
    past_separator = False
    for line in lines:
        stripped = line.strip()
        if not stripped.startswith("|"):
            continue
        if re.match(r"^[\s|:-]+$", stripped):
            past_separator = True
            continue
        if not past_separator:
            continue
        cells = [c.strip() for c in stripped.strip("|").split("|")]
        cells = [c for c in cells if c]
        if cells:
            rows.append(" | ".join(cells))
    return rows


def _parse_subtask_blocks(lines: list[str]) -> list[SubTask]:
    """Parse ##### Sub-task headings within the Sub-tasks section."""
    # Split into individual sub-task blocks
    blocks: list[tuple[str, list[str]]] = []
    current_title = ""
    current_lines: list[str] = []

    for line in lines:
        stripped = line.strip()
        m = re.match(r"^#{5}\s+Sub[- ]?task\s+[\d.]+\s*[:\-–]\s*(.+)", stripped)
        if m:
            if current_title:
                blocks.append((current_title, current_lines))
            current_title = m.group(1).strip()
            current_lines = []
            continue
        if current_title:
            current_lines.append(line)

    if current_title:
        blocks.append((current_title, current_lines))

    return [_build_subtask_from_block(t, c) for t, c in blocks]


def _parse_estimate_hours(lines: list[str]) -> Optional[float]:
    """Extract estimated hours from **Estimate:** or **Type:** metadata lines."""
    for line in lines:
        stripped = line.strip()
        m = re.search(r"Estimate\*{0,2}:?\*{0,2}\s+(\d+(?:\.\d+)?)\s*h", stripped, re.IGNORECASE)
        if m:
            return float(m.group(1))
    return None


def _build_subtask_from_block(title: str, lines: list[str]) -> SubTask:
    """Build a SubTask from its content lines (v1 ###### sections or v2 **Description:**)."""
    subtask = SubTask(summary=title)
    subtask.estimate_hours = _parse_estimate_hours(lines)
    has_h6 = any(re.match(r"^#{6}\s+", l.strip()) for l in lines)

    if has_h6:
        # v1 format: split by ###### sections
        sections: dict[str, list[str]] = {}
        cur = "_meta"
        sections[cur] = []
        for line in lines:
            m = re.match(r"^#{6}\s+(.+)", line.strip())
            if m:
                cur = m.group(1).strip().lower()
                sections[cur] = []
                continue
            sections.setdefault(cur, []).append(line)

        if "summary" in sections:
            subtask.description = _collect_section_text(sections["summary"])
        if not subtask.description and "requirement details" in sections:
            subtask.description = _collect_section_text(sections["requirement details"])

        for key in sections:
            if "acceptance criteria" in key:
                subtask.acceptance_criteria = _extract_list_items(sections[key])
                break
        for key in sections:
            if "definition of done" in key:
                subtask.definition_of_done = _extract_list_items(sections[key])
                break
    else:
        # v2 format: **Description:** block + - **Definition of Done:** checklist
        desc_lines: list[str] = []
        section = None  # None | "description" | "dod"

        for line in lines:
            stripped = line.strip()
            if re.match(r"^\*{2}(Type|Estimate|Assignee)", stripped):
                section = None
                continue
            if re.match(r"\*{2}Description:?\*{2}", stripped, re.IGNORECASE):
                section = "description"
                continue
            if re.match(r"^-?\s*\*{2}Definition of Done:?\*{2}", stripped, re.IGNORECASE):
                section = "dod"
                continue
            if re.match(r"^-\s+\*{2}(Affected Files|Parent Story)", stripped):
                section = None
                continue
            if re.match(r"^-{3,}$", stripped):
                section = None
                continue

            if section == "description":
                desc_lines.append(stripped)
            elif section == "dod":
                m = re.match(r"^-\s+(?:\[.?\]\s+)?(.+)", stripped)
                if m:
                    subtask.definition_of_done.append(m.group(1).strip())

        subtask.description = _collect_section_text(desc_lines)

    return subtask


def parse_wbs_markdown(md_text: str) -> WBSDocument:
    """
    Parse a WBS markdown file into a WBSDocument.

    Recognised patterns (v2 format)
    --------------------------------
    Epic title       : ## Epic: <title>   OR   # <title>
    Story block      : ### Story N: <summary>
    Metadata         : **Priority:** / **Points:** in header area
    #### Summary     : paragraph → story.summary_text
    #### Requirement Details : paragraph → story.requirement_details
    #### Acceptance Criteria : "- [ ]" items
    #### Sub-tasks   : ##### Sub-task blocks with **Description:**
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
        for line in lines:
            m = re.match(r"^#{1,2}\s+(.+)", line)
            if m:
                doc.epic_title = m.group(1).strip()
                break

    # ── Pass 2: split into story blocks by "### Story" headings only ────
    story_blocks: list[list[str]] = []
    current: list[str] = []

    for line in lines:
        if re.match(r"^###\s+Story\s+\d+", line):  # only "### Story N"
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

        story_name = ""
        story_summary = ""

        # Match: ### Story 4 (SL4): Title  or  ### Story 1: Title
        m = re.match(r"^###\s+(Story\s+\d+)\s*(?:\([^)]*\))?\s*[:\-–]\s*(.+)", header)
        if m:
            story_name    = m.group(1).strip()
            story_summary = m.group(2).strip()
        else:
            continue  # skip non-matching headings

        story = Story(name=story_name, summary=story_summary)

        # Split block into #### sections
        sections: dict[str, list[str]] = {}
        current_section = "_header"
        sections[current_section] = []

        for line in block[1:]:
            # Detect #### section headings
            m = re.match(r"^####\s+(.+)", line)
            if m:
                current_section = m.group(1).strip().lower()
                sections[current_section] = []
                continue
            sections.setdefault(current_section, []).append(line)

        # ── Parse header metadata (Priority, Points) ──────────────────
        priority_map = {"H": "High", "M": "Medium", "L": "Low"}
        for line in sections.get("_header", []):
            stripped = line.strip()
            pm = re.search(r"Priority\*{0,2}:\*{0,2}\s+([A-Za-z]+)", stripped)
            if pm:
                raw = pm.group(1).strip()
                story.priority = priority_map.get(raw, raw)
            sp = re.search(r"Points\*{0,2}:\*{0,2}\s+(\d+)", stripped)
            if sp:
                story.story_points = int(sp.group(1))

        # ── Summary / Story Overview ──────────────────────────────────
        for key in ("summary", "story overview"):
            if key in sections:
                story.summary_text = _collect_section_text(sections[key])
                if not story.affected_components:
                    story.affected_components = _extract_metadata_value(
                        sections[key], "Affected Components"
                    )
                break

        # ── Affected Components from Requirement Details ──────────────
        if "requirement details" in sections and not story.affected_components:
            story.affected_components = _extract_metadata_value(
                sections["requirement details"], "Affected Components"
            )

        # ── Acceptance Criteria ────────────────────────────────────────
        for k in sections:
            if "acceptance criteria" in k:
                story.acceptance_criteria = _extract_list_items(sections[k])
                break

        # ── Corner Cases & Edge Scenarios ──────────────────────────────
        for k in sections:
            if "corner case" in k:
                story.corner_cases = _parse_table_data_rows(sections[k])
                break

        # ── Risks ─────────────────────────────────────────────────────
        for k in sections:
            if k == "risks":
                story.risks = _parse_table_data_rows(sections[k])
                break

        # ── Notes / Additional Information ────────────────────────────
        for k in sections:
            if "notes" in k:
                story.notes = _extract_list_items(sections[k])
                break

        # ── Sub-tasks section ─────────────────────────────────────────
        # Prefer sections with ##### Sub-task headings over plain lists
        subtask_key = None
        subtask_fallback = None
        for k in sections:
            if "sub-task" in k or "sub task" in k or "subtask" in k:
                has_headings = any(
                    re.match(r"^#{5}\s+Sub[- ]?task", l.strip())
                    for l in sections[k]
                )
                if has_headings:
                    subtask_key = k
                    break
                elif subtask_fallback is None:
                    subtask_fallback = k
        if subtask_key is None:
            subtask_key = subtask_fallback
        if subtask_key:
            subtask_lines = sections[subtask_key]
            # Check if v2 format (##### headings present)
            has_subtask_headings = any(
                re.match(r"^#{5}\s+Sub[- ]?task", l.strip()) for l in subtask_lines
            )
            if has_subtask_headings:
                story.subtasks = _parse_subtask_blocks(subtask_lines)
            else:
                # Fallback: v1 list format
                for line in subtask_lines:
                    stripped = line.strip()
                    item_match = re.match(r"^-\s+(?:\[.?\]\s+)?(.+)", stripped)
                    if item_match:
                        item_text = item_match.group(1).strip()
                        # Extract hours from format like "(Backend, 16h)"
                        hours_match = re.search(r"\(\s*[^,]+,\s*(\d+(?:\.\d+)?)\s*h\s*\)", item_text)
                        est_hours = float(hours_match.group(1)) if hours_match else None
                        item_text = re.sub(r"\s+[—–-]\s+[SMxl]+$", "", item_text).strip()
                        story.subtasks.append(SubTask(summary=item_text, estimate_hours=est_hours))

        # ── Auto-append PR Review sub-task if enabled ──────────────────
        if PR_REVIEW_SUBTASK_ENABLED:
            pr_review = SubTask(
                summary=PR_REVIEW_SUBTASK_SUMMARY,
                description=PR_REVIEW_SUBTASK_DESCRIPTION,
                estimate_hours=PR_REVIEW_ESTIMATE_HOURS,
            )
            story.subtasks.append(pr_review)

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


def resolve_task_estimation_field(session: requests.Session) -> None:
    """Validate configured task estimation field for Sub-task creation.

    If the configured field is not available on the Sub-task create screen,
    auto-switch to the field named "Task Estimation Time" when present.
    """
    global TASK_ESTIMATION_TIME_FIELD

    configured_field = (TASK_ESTIMATION_TIME_FIELD or "").strip()
    if not configured_field:
        return

    url = f"{JIRA_BASE_URL}/rest/api/3/issue/createmeta"
    params = {
        "projectKeys": JIRA_PROJECT_KEY,
        "issuetypeNames": SUBTASK_ISSUE_TYPE,
        "expand": "projects.issuetypes.fields",
    }

    try:
        resp = session.get(url, params=params, timeout=30)
    except requests.RequestException as exc:
        log.warning("Could not validate task estimation field '%s': %s", configured_field, exc)
        return

    if resp.status_code != 200:
        log.warning(
            "Could not validate task estimation field '%s' (createmeta %s): %s",
            configured_field,
            resp.status_code,
            resp.text[:200],
        )
        return

    data = resp.json()
    projects = data.get("projects", [])
    fields: dict = {}
    if projects:
        issue_types = projects[0].get("issuetypes", [])
        if issue_types:
            fields = issue_types[0].get("fields", {})

    if configured_field in fields:
        log.info("Using sub-task estimation field: %s", configured_field)
        return

    fallback_id = ""
    fallback_name = ""
    for field_id, meta in fields.items():
        field_name = (meta.get("name") or "").strip()
        if field_name.lower() == "task estimation time":
            fallback_id = field_id
            fallback_name = field_name
            break

    if fallback_id:
        log.warning(
            "Configured task_estimation_time_field '%s' is not available for %s in project %s. "
            "Auto-correcting to '%s' (%s).",
            configured_field,
            SUBTASK_ISSUE_TYPE,
            JIRA_PROJECT_KEY,
            fallback_id,
            fallback_name,
        )
        TASK_ESTIMATION_TIME_FIELD = fallback_id
        return

    log.warning(
        "Configured task_estimation_time_field '%s' is not available for %s in project %s. "
        "No fallback field named 'Task Estimation Time' was found; skipping this field.",
        configured_field,
        SUBTASK_ISSUE_TYPE,
        JIRA_PROJECT_KEY,
    )
    TASK_ESTIMATION_TIME_FIELD = ""


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


def _adf_heading(text: str, level: int = 3) -> dict:
    return {
        "type": "heading",
        "attrs": {"level": level},
        "content": [{"type": "text", "text": text}],
    }


def _parse_inline_marks(text: str) -> list[dict]:
    """Parse markdown inline formatting (**bold**, `code`) into ADF text nodes."""
    nodes: list[dict] = []
    # Split by **bold** and `code` patterns
    pattern = re.compile(r"(\*\*(.+?)\*\*|`(.+?)`)")
    last_end = 0

    for m in pattern.finditer(text):
        # Add plain text before this match
        if m.start() > last_end:
            plain = text[last_end:m.start()]
            if plain:
                nodes.append({"type": "text", "text": plain})

        if m.group(2):  # **bold**
            nodes.append({"type": "text", "text": m.group(2), "marks": [{"type": "strong"}]})
        elif m.group(3):  # `code`
            nodes.append({"type": "text", "text": m.group(3), "marks": [{"type": "code"}]})

        last_end = m.end()

    # Add remaining plain text
    if last_end < len(text):
        remaining = text[last_end:]
        if remaining:
            nodes.append({"type": "text", "text": remaining})

    # If no formatting found, return single plain text node
    if not nodes:
        nodes.append({"type": "text", "text": text})

    return nodes


def _adf_paragraph(text: str) -> dict:
    return {
        "type": "paragraph",
        "content": _parse_inline_marks(text),
    }


def _adf_bullet_list(items: list[str]) -> dict:
    return {
        "type": "bulletList",
        "content": [
            {
                "type": "listItem",
                "content": [_adf_paragraph(item)],
            }
            for item in items
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
                    "content": _parse_inline_marks(item),
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


def build_story_description_adf(story: "Story") -> dict:
    """Build ADF description with story context and full coding conventions."""
    content: list[dict] = []

    if story.summary_text:
        content.append(_adf_heading("Story Overview", 3))
        content.append(_adf_paragraph(story.summary_text))

    if story.affected_components:
        content.append(_adf_heading("Affected Components", 3))
        content.append(_adf_paragraph(story.affected_components))

    # Add full coding conventions as detailed sections
    if CODING_CONVENTION_CHECKLIST and _cc_enabled:
        content.append(_adf_heading("Coding Conventions", 2))
        for section_title, items in FULL_CODING_CONVENTIONS.items():
            content.append(_adf_heading(section_title, 3))
            content.append(_adf_bullet_list(items))

    if not content:
        content.append(_adf_paragraph(story.summary))

    return {"version": 1, "type": "doc", "content": content}


def build_subtask_description_adf(subtask: "SubTask", story: "Story") -> dict:
    """Build ADF description for a sub-task with all required sections."""
    content: list[dict] = []

    # Task Estimated Hours
    if subtask.estimate_hours is not None:
        hours_text = f"Task Estimated Hours: {subtask.estimate_hours:g}h (Including Unit test and review)"
        content.append(_adf_paragraph(hours_text))

    # Summary (sub-task's own description)
    if subtask.description:
        content.append(_adf_heading("Summary", 3))
        content.append(_adf_paragraph(subtask.description))

    # Acceptance Criteria (sub-task's own if available, else story's)
    ac = subtask.acceptance_criteria or story.acceptance_criteria
    if ac:
        content.append(_adf_heading("Acceptance Criteria", 3))
        content.append(_adf_bullet_list(ac))

    # Definition of Done (sub-task's own)
    if subtask.definition_of_done:
        content.append(_adf_heading("Definition of Done", 3))
        content.append(_adf_bullet_list(subtask.definition_of_done))

    # Corner Cases (from parent story)
    if story.corner_cases:
        content.append(_adf_heading("Corner Cases", 3))
        content.append(_adf_bullet_list(story.corner_cases))

    # Risks (from parent story)
    if story.risks:
        content.append(_adf_heading("Risks", 3))
        content.append(_adf_bullet_list(story.risks))

    # Notes (from parent story)
    if story.notes:
        content.append(_adf_heading("Notes", 3))
        content.append(_adf_bullet_list(story.notes))

    if not content:
        content.append(_adf_paragraph(subtask.summary))

    return {"version": 1, "type": "doc", "content": content}


def build_story_payload(story: Story) -> dict:
    fields: dict = {
        "project": {"key": JIRA_PROJECT_KEY},
        "summary": story.summary,
        "issuetype": {"name": STORY_ISSUE_TYPE},
        "priority": {"name": story.priority},
        "description": build_story_description_adf(story),
    }

    if story.story_points is not None:
        fields[STORY_POINTS_FIELD] = story.story_points

    # Original estimate = sum of all sub-task hours (JIRA uses seconds)
    total_hours = sum(st.estimate_hours for st in story.subtasks if st.estimate_hours)
    if total_hours > 0:
        fields["timetracking"] = {"originalEstimate": f"{total_hours:g}h"}

    return {"fields": fields}


def build_subtask_payload(subtask: SubTask, parent_key: str, story: Story) -> dict:
    fields = {
        "project": {"key": JIRA_PROJECT_KEY},
        "summary": subtask.summary,
        "issuetype": {"name": SUBTASK_ISSUE_TYPE},
        "parent": {"key": parent_key},
        "description": build_subtask_description_adf(subtask, story),
    }

    # ALWAYS add Task Estimation Time custom field if configured
    # Use estimate_hours if available, otherwise use 0 as default
    if TASK_ESTIMATION_TIME_FIELD:
        fields[TASK_ESTIMATION_TIME_FIELD] = subtask.estimate_hours if subtask.estimate_hours is not None else 0

    return {"fields": fields}


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

    # Validate task estimation field against Sub-task create metadata when credentials are available.
    if TASK_ESTIMATION_TIME_FIELD and JIRA_BASE_URL and JIRA_EMAIL and JIRA_API_TOKEN:
        resolve_task_estimation_field(session)

    # 2. Create Stories + Sub-tasks (no Epic — stories go to backlog)
    results = []
    for story in doc.stories:
        log.info("Creating Story — %s: %s", story.name, story.summary)
        story_payload = build_story_payload(story)
        story_key = post_issue(session, story_payload, dry_run)

        if not story_key:
            log.warning("Skipping sub-tasks for '%s' (story creation failed).", story.name)
            results.append({"story": story.name, "key": None, "subtasks": []})
            continue

        subtask_keys = []
        for subtask in story.subtasks:
            st_payload = build_subtask_payload(subtask, story_key, story)
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
        help="Path to the WBS markdown file (e.g. docs/wbs/wbs-feature.md)",
    )
    parser.add_argument(
        "--config",
        default="",
        help="Path to config.ini (default: jira_config.ini next to script)",
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
