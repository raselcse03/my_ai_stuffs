# Sprint Report Generator

Generates the PMO_BU1 Mr Max DEV Labo sprint monitoring report for any sprint by
pulling data from Jira (`bjit.atlassian.net`, project P1709).

## Project layout

```
sprint-report-generator/
├── generate_sprint_report.py    # main script
├── report_config.json           # Jira URL, statuses, classification patterns
├── PMO_BU1_Mr Max DEV Labo_Monitoring_DevShare 1.xlsx   # template workbook
├── requirements.txt
├── ANALYSIS_AND_PLAN.md         # workbook analysis & design notes
└── README.md
```

## Setup (once)

```bash
pip install -r requirements.txt
```

(Dependencies also auto-install on first run if missing.)

Create a Jira API token at https://id.atlassian.com/manage-profile/security/api-tokens,
then put your credentials in the `auth` section of `report_config.json`:

```json
"auth": {
  "email": "pavel.parvej@bjitgroup.com",
  "token": "<your token>"
}
```

Alternatively, environment variables work too and override the config file:

```bash
export JIRA_EMAIL="pavel.parvej@bjitgroup.com"
export JIRA_TOKEN="<your token>"
```

> Note: the token grants access to your Jira account — don't commit
> `report_config.json` with a real token to a shared repository.

## Calibrate (recommended first run)

Verify the script reproduces known Sprint 7/8 numbers before trusting it on new sprints:

```bash
python generate_sprint_report.py --sprint 8 --dry-run
```

Compare the printed metrics against the existing `Sprint 8` sheet
(103 tasks, 625.8 hrs, 81 dev tasks, 103 completed, 0 defects…).
If counts differ, tune `classification` patterns / `statuses` in `report_config.json`
(status names, dev-task exclude patterns, etc. — see ANALYSIS_AND_PLAN.md §4).

## Generate a report

```bash
python generate_sprint_report.py --sprint 9
# with manual QA/CI numbers:
python generate_sprint_report.py --sprint 9 --test-cases 689 --executed-tests 564 --passed-tests 564
```

Output: `reports/PMO_BU1_Mr Max DEV Labo_Monitoring_Dev.xlsx` — a single
**cumulative** report (paths configurable via `reports_dir` / `output_name`
in `report_config.json`, or `--output`).

### Cumulative behaviour

The report always contains **every sprint from 7 up to the requested one**:

- First run with `--sprint 11` → fetches and adds Sprint 9, 10, and 11
  on top of the template's existing Sprint 7 & 8.
- If `reports/...Monitoring_Dev.xlsx` already exists, it is used as the
  source, so already-generated sprints are kept and skipped — e.g. if it
  contains up to Sprint 9, running `--sprint 11` only adds 10 and 11.
- Requesting a sprint that's already in the file exits with "Nothing to do".

Each added sprint gets its own `Sprint N` sheet, one row on each dashboard
(Sprint Overview, Health Dashboard, Margin_Deviation, Quality_Status,
Capacity_Dashboard), placeholder rows in PMO Observations / Risk Register,
and the Project Overview pointer switches to the newest sprint.

Note: CLI overrides (`--test-cases`, `--working-days`, …) apply only to the
requested sprint; backfilled sprints use config defaults — edit their cells
manually afterwards if needed.

### Sprint duration

Sprint length is NOT fixed — days (B3) come straight from the Jira sprint's
start/end dates (May 15 → May 30 = 15 days; sprints can be 7, 15, 30, …).
PV, BAC, Actual Cost, Revenue, and Capacity formulas in generated sheets are
scaled by that duration (`B3 / days_per_month`, default 30 in
`report_config.json`) instead of the template's fixed half-month `/2`.

## After generating — manual steps

1. **Sprint N sheet**: fill the risk table (E:I) — risk scores in col I drive B45/B46.
2. **Sprint Overview**: col G (PMO summary), O/P (GDM compliance score).
3. **Quality_Status**: col G (QA gate compliance narrative).
4. **PMO Observations / Risk Register**: replace TBD placeholder rows.
5. **Team sheet**: update if team composition/FTE changed.
6. Open in Excel once so all formulas recalculate.

## Useful options

| Option | Purpose |
|---|---|
| `--dry-run` | Print metrics only, no file written |
| `--working-days N` | Override B3 (days otherwise taken from Jira sprint start/end dates) |
| `--post-release-defects N` | Override B27 |
| `--cicd-commits/--cicd-passed N` | B37/B38 |
| `--save-jira-json f.json` | Cache Jira data; replay later with `--offline f.json` |
| `--template / --output` | Custom file paths |
| `--update-durations` | Refresh B3/B4 (working days & duration) on every existing `Sprint N` sheet from live Jira sprint dates, without adding new sprints |

Jira sprint start/end timestamps are UTC; they're converted to the timezone in
`jira.timezone` (`report_config.json`, default `Asia/Dhaka`) before being
turned into calendar dates, so sprint boundaries that land on local midnight
don't get reported a day early.
