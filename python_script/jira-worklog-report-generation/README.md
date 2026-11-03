# JIRA Monthly Worklog Report Generator

Generates a formatted Excel report of your monthly JIRA worklogs.

## Output Format

| Date       | Week | Description                              | Start-time | End-time | Working-time | Comments              |
|------------|------|------------------------------------------|------------|----------|-------------|-----------------------|
| 2026-04-01 | Wed  | P1709-101 - Login Module [3h]            | 08:00      | 17:00    | 8:00        | Fixed login bug       |
| 2026-04-02 | Thu  | P1709-205 - Code Review [4h]             | 09:00      | 17:00    | 8:00        | Reviewed module X     |
| 2026-04-03 | Fri  | Weekend                                  |            |          |             |                       |

## Setup (bash)

    chmod +x setup.sh run.sh
    ./setup.sh

## Configuration

Edit `config.ini`:

    [JIRA]
    server = https://your-domain.atlassian.net
    email = your-email@example.com
    api_token = your-api-token

    [REPORT]
    project = P1709
    year = 2026
    month = 4

## Get API Token

1. Go to: https://id.atlassian.com/manage-profile/security/api-tokens
2. Click "Create API Token"
3. Copy and paste into config.ini

## Run

    ./run.sh

## Output

Excel file: `Rreport/Worklog_P1709_2026_04.xlsx`