# PMO Sprint Monitoring Report — Analysis & Automation Plan

Workbook analyzed: `PMO_BU1_Mr Max DEV Labo_Monitoring_DevShare 1.xlsx`
Project: **Mr Max DEV Labo** · Jira: `bjit.atlassian.net` · Jira project key: **P1709** · Sprint length: 2 weeks

---

## 1. Workbook structure

| Sheet | Role | Per-sprint? |
|---|---|---|
| `Sprint 7`, `Sprint 8` | Raw sprint data + risk table + scoring config | **Yes — one sheet per sprint (the core input)** |
| `Sprint Overview` | 1 summary row per sprint (formulas → sprint sheets + dashboards) | Yes — new row per sprint |
| `Health Dashboard` | SPI/CPI/EAC/health status per sprint (formulas → sprint sheets) | Yes — new row per sprint |
| `Margin_Deviation` | Margin variance per sprint (formulas) | Yes — new row per sprint |
| `Quality_Status` | Quality metrics + trend per sprint (formulas) | Yes — new row per sprint |
| `Capacity_Dashboard` | Utilization/delivery predictability per sprint (formulas) | Yes — new row per sprint |
| `PMO Observations` | Narrative observations (~7 rows per sprint) | Yes — narrative |
| `Risk Register` | Detailed risk rows per sprint | Yes — narrative |
| `Project Overview` | Executive snapshot; reads `Project_Master` + latest-sprint row pointer (`S10`) | Pointer update only |
| `Team` | Resource roster, costs, FTE, revenue (source: resource XLSX, **not Jira**) | Static / manual |
| `Rank Wise Cost`, `Project_Master` | Config/master data | Static |

**Key insight:** all dashboards are formula-driven off the per-sprint sheet. To add Sprint N the script only needs to (a) create a correct `Sprint N` sheet, (b) append one formula row per dashboard retargeted at `'Sprint N'`, (c) add narrative placeholders, (d) bump the latest-row pointer `Project Overview!S10`.

---

## 2. `Sprint N` sheet — cell-by-cell classification

### Column A/B block (rows 1–52)

| Cell | Field | Source | How |
|---|---|---|---|
| B2 | Sprint name | **Jira** | Sprint entity `name` |
| B3 | Effective Working Days | **Computed** | Business days between sprint `startDate`–`endDate` (CLI override for holidays) |
| B4 | Duration | **Jira** | Formatted `startDate – endDate` (e.g. "May 15 – May 30, 2026") |
| B5 | PV (hrs) | Formula | `=(Team!P14*8*20)/2` — keep as formula |
| B6 | EV (hrs) | Formula | `=B5*(B41/100)` |
| B7 | **Actual Spent (hrs)** | **Jira** | Σ `timespent` (or worklogs) of all sprint issues, seconds→hrs |
| B8–B14 | Variance, BAC, AC, Revenue, Burn Rate, Margin | Formula | Keep (reference Team! and B-cells) |
| B15 | **Total Requests/Tasks** | **Jira** | Count of all issues in sprint (Sprint 7=92, Sprint 8=103 — matches CSV row counts incl. sub-tasks) |
| B16 | **Total Development Tasks** | **Jira** | Count of dev-type issues (sub-tasks/tasks classified as development; see §4 heuristics) |
| B17 | **Task without Dev Testing** | **Jira** | Coding stories with no UT/BAT sub-task |
| B18 | **Tasks with proper review** | **Jira** | Issues with merged PRs (dev-status field) / review sub-task |
| B19–B22 | Total / Approved / Billable / Completed CR | **Jira** | Issues labeled/typed as CR (0 in both sprints; JQL on label or issuetype) |
| B23 | Carried-forward CR | Formula | `=B20-B22` |
| B24 | **Total Defects** | **Jira** | Count issuetype=Bug in sprint |
| B25 | **Open Defects** | **Jira** | Bugs not Closed/Resolved |
| B26 | **Reopened Defects** | **Jira** | Bugs with a Reopened transition (changelog) |
| B27 | Post Release Defects | **Jira/manual** | Bugs labeled post-release (override available) |
| B28–B30 | Test Cases / Executed / Passed | **Manual** | Not in Jira (from QA test files) → CLI/config override, default 0 |
| B31–B36 | QA/Dev coverage % | Formula | Keep |
| B37–B38 | CI/CD Commit / Passed | **Manual** | CLI/config override, default 0 |
| B39 | CI/CD Success % | Formula | Keep |
| B40 | **Completed** | **Jira** | Issues with status Closed/Done |
| B41 | Done % | Formula | Keep |
| B42 | **Under QA** | **Jira** | Issues in QA-type status (Resolved/In QA) |
| B43–B46 | Quality/Risk Score & Summary | Formula | Keep (XLOOKUP against weight tables) |
| B47–B52 | Resource/capacity | Formula | Keep (reference Team!) |
| A54 | "Data Evidence" | Label | Keep |

### Risk table (E1:I~15) — **narrative** → placeholder rows (`R-01`, TBD text, risk level default `Low`, score 1). Note: `B45 = AVERAGE(I2:I86)` so placeholder scores must be intentional or left blank until filled.

### Config blocks (rows 60–82) — **static template** (quality-metric weights, score→summary lookup tables, dev-coverage weights). Copied verbatim. Note the weights differ between Sprint 7 and Sprint 8 (e.g., Completion Rate 0.15→0.9 when QA metrics are N/A) — script copies from the **latest** sprint sheet and you can adjust per sprint.

---

## 3. Dashboard rows to append per sprint (all formulas, retargeted `'Sprint 7'` → `'Sprint N'`)

- **Sprint Overview** row: A=`='Sprint N'!B2`, B–F/I–N formula refs into dashboards; **G (PMO Observations) and O/P (GDM score) are manual** → placeholder `TBA`; T=`Not Collected Yet`.
- **Health Dashboard** row: SPI `='Sprint N'!B6/'Sprint N'!B5`, CPI, EAC, statuses — pure formulas.
- **Margin_Deviation** row: Baseline Margin B=0.3 (constant), rest formulas; G (Root Cause) manual.
- **Quality_Status** row: formulas + trend vs previous row (`J=((H_new-H_prev)/H_prev)*100`); **G (QA Gate Compliance) is narrative** → placeholder.
- **Capacity_Dashboard** row: formulas (note existing quirk: Sprint 8 utilization divides by `'Sprint 7'!B52` — actual capacity fallback when no resource file; script targets the new sprint's own B52).
- **PMO Observations / Risk Register**: append placeholder narrative rows tagged `Sprint N`.
- **Project Overview!S10**: set to the new latest row number in Sprint Overview (drives all the "latest sprint" array formulas).

---

## 4. Jira data mapping & heuristics

Auth: Jira Cloud REST API, Basic auth with `JIRA_EMAIL` + `JIRA_TOKEN` env vars.

| Step | API |
|---|---|
| Find board | `GET /rest/agile/1.0/board?projectKeyOrId=P1709&type=scrum` |
| Find sprint by name/number | `GET /rest/agile/1.0/board/{boardId}/sprint?state=active,closed,future` → match "Sprint 9" |
| Sprint dates | Sprint entity `startDate`/`endDate` → B4, B3 |
| Issues in sprint | `GET /rest/agile/1.0/sprint/{sprintId}/issue` (paginated, `fields=summary,issuetype,status,timespent,labels,parent,subtasks,...customfields`) |
| Merged-PR / review info | `GET /rest/dev-status/1.0/issue/detail?issueId=..&applicationType=...&dataType=pullrequest` (best-effort; falls back to heuristic) |
| Reopened detection | `expand=changelog` on search, count transitions into Reopened |

Classification heuristics (configurable in `report_config.json`):

- **Development task**: sub-task/task whose summary or Task Type field matches `Coding|Development|Implementation|UT|BAT|Fix` — the workbook's "Total Development Tasks" (71/92, 81/103) suggests all non-planning/QA/release items. Tune `dev_task_patterns` after first run against a known sprint.
- **Dev testing pair**: a Coding story is "without dev testing" if none of its sub-tasks match `UT|BAT|Unit Test`.
- **Proper review**: issue has ≥1 merged PR (dev-status) or a Review sub-task.
- **CR**: label/summary matches `CR\d+` AND issuetype/Task Type = Change Request (both sprints had 0; heuristic kept simple and configurable).
- **Completed**: status in `Closed, Done`; **Under QA**: status in `Resolved, In QA, QA`.
- **Custom fields** (Task Type, % Done, Is Billable): discovered at runtime via `GET /rest/api/3/field` by name — no hard-coded IDs.

### Calibration step (important)
Field names/status names may differ from my assumptions. The script has `--dry-run` mode that prints every computed metric next to the known Sprint 7/8 values so you can verify counts (92/103 tasks, 745.5/625.8 hrs, 90/103 completed, 2/0 defects…) before generating a real report. Adjust `report_config.json` patterns until Sprint 7/8 reproduce, then run for Sprint 9+.

---

## 5. Script design

```
generate_sprint_report.py --sprint 9 [options]

Options:
  --sprint N              (required) sprint number, e.g. 9
  --template FILE         source workbook (default: template path in config)
  --output FILE           output path (default: adds _Sprint9 suffix)
  --config FILE           report_config.json (Jira URL, project, patterns, thresholds)
  --working-days N        override effective working days (B3)
  --test-cases / --executed-tests / --passed-tests N     QA overrides (B28–B30)
  --cicd-commits / --cicd-passed N                       CI/CD overrides (B37–B38)
  --post-release-defects N
  --dry-run               fetch + compute + print metrics, don't write the file
  --offline FILE.json     use saved Jira JSON instead of live API (testing)

Env: JIRA_EMAIL, JIRA_TOKEN
```

Pipeline:

1. Load config → connect to Jira → resolve board → resolve sprint "Sprint {N}" → fetch all issues (paginated) + changelogs + dev-status.
2. Compute the metrics table (§2).
3. Open template with `openpyxl`: copy latest `Sprint M` sheet → rename `Sprint N` (openpyxl `copy_worksheet` preserves formulas/styles), overwrite Jira-fed cells, blank the narrative risk rows to placeholders, keep config blocks.
4. Append one row to each dashboard sheet by cloning the previous row's formulas with sheet-name/row-number rewriting (regex on `'Sprint M'` and relative row refs), insert placeholders for manual cells.
5. Append narrative placeholder rows to `PMO Observations` and `Risk Register`.
6. Update `Project Overview!S10` and the reporting date.
7. Save; print a summary + list of cells left as TBD for manual completion.

Decisions you confirmed: narrative cells = placeholders; Team sheet reused as-is; manual metrics via CLI/config with computed working-days default; Jira Cloud API token auth.
