#!/usr/bin/env python3
"""
JIRA Monthly Worklog Report Generator
Generates an Excel report with daily worklog details.
"""

import os
import sys
import re
import configparser
import calendar
from datetime import datetime, time
import requests

try:
    from jira import JIRA
    from openpyxl import Workbook
    from openpyxl.styles import (
        Font, Alignment, Border, Side, PatternFill
    )
    from autocorrect import Speller
except ImportError as e:
    print(f"❌ Missing dependency: {e}")
    print("   Run ./setup.sh first.")
    sys.exit(1)

_speller = Speller(lang='en')


def _fix_text(text):
    """Fix spelling while preserving acronyms and technical terms."""
    words = text.split()
    corrected = []
    for word in words:
        # Preserve acronyms (all uppercase), words with digits, and short uppercase
        if word.isupper() or any(c.isdigit() for c in word) or len(word) <= 2:
            corrected.append(word)
        else:
            corrected.append(_speller(word))
    return ' '.join(corrected)


def load_config():
    config = configparser.ConfigParser()
    config_path = os.path.join(os.path.dirname(os.path.abspath(__file__)), 'config.ini')
    if not os.path.exists(config_path):
        print("❌ config.ini not found!")
        sys.exit(1)
    config.read(config_path)
    return {
        'server': config.get('JIRA', 'server'),
        'email': config.get('JIRA', 'email'),
        'api_token': config.get('JIRA', 'api_token'),
        'project': config.get('REPORT', 'project'),
        'year': config.getint('REPORT', 'year'),
        'month': config.getint('REPORT', 'month'),
        'default_start': config.get('REPORT', 'default_start_time', fallback='08:00'),
        'approver': config.get('REPORT', 'approver', fallback=''),
        'reviewer': config.get('REPORT', 'reviewer', fallback=''),
        'company': config.get('REPORT', 'company', fallback=''),
        'target_email': config.get('REPORT', 'target_email', fallback=''),
    }


def connect_jira(cfg):
    print(f"🔗 Connecting to {cfg['server']}...")
    try:
        # Use API v3 instead of deprecated v2
        options = {'server': cfg['server'], 'rest_api_version': '3'}
        jira = JIRA(options=options, basic_auth=(cfg['email'], cfg['api_token']))
        myself = jira.myself()
        print(f"✅ Connected as: {myself['displayName']} ({myself['emailAddress']})")
        return jira, myself['displayName']
    except Exception as e:
        print(f"❌ Connection failed: {e}")
        sys.exit(1)


def search_issues_v3(cfg, jql, max_results=500):
    """Search issues using the new /rest/api/3/search/jql endpoint"""
    url = f"{cfg['server']}/rest/api/3/search/jql"
    auth = (cfg['email'], cfg['api_token'])
    
    all_issues = []
    start_at = 0
    
    while True:
        params = {
            'jql': jql,
            'startAt': start_at,
            'maxResults': min(100, max_results - len(all_issues)),
            'fields': 'summary,worklog'
        }
        
        response = requests.get(url, params=params, auth=auth)
        
        if response.status_code != 200:
            raise Exception(f"API Error {response.status_code}: {response.text}")
        
        data = response.json()
        issues = data.get('issues', [])
        all_issues.extend(issues)
        
        # Check if we have more results
        total = data.get('total', 0)
        if len(all_issues) >= total or len(all_issues) >= max_results:
            break
        
        start_at = len(all_issues)
    
    return all_issues


def fetch_worklogs(jira, cfg):
    """Fetch worklogs from JIRA - CURRENT USER ONLY"""
    year = cfg['year']
    month = cfg['month']
    project = cfg['project']
    last_day = calendar.monthrange(year, month)[1]
    start_date = f"{year}-{month:02d}-01"
    end_date = f"{year}-{month:02d}-{last_day}"

    # Get current user's account ID
    myself = jira.myself()
    my_account_id = myself['accountId']
    my_display_name = myself['displayName']
    my_email = myself.get('emailAddress', cfg['email'])

    # Determine target user (team member or self)
    target_email = cfg.get('target_email', '').strip()
    if target_email:
        # Search for the target user by email
        target_users = jira.search_users(query=target_email, maxResults=1)
        if not target_users:
            print(f"\n\u274c Could not find JIRA user with email: {target_email}")
            sys.exit(1)
        target_user = target_users[0]
        target_account_id = target_user.accountId
        target_display_name = target_user.displayName
        target_user_email = getattr(target_user, 'emailAddress', target_email)
        print(f"\n\U0001f465 Generating report for team member: {target_display_name} ({target_user_email})")
        print(f"   Account ID: {target_account_id}")
        jql_author = f'worklogAuthor = "{target_account_id}"'
    else:
        target_account_id = my_account_id
        target_display_name = my_display_name
        target_user_email = my_email
        print(f"\n\U0001f464 Filtering worklogs for: {my_display_name} ({my_email})")
        print(f"   Account ID: {my_account_id}")
        jql_author = 'worklogAuthor = currentUser()'

    jql = (
        f'project = {project} '
        f'AND worklogDate >= "{start_date}" '
        f'AND worklogDate <= "{end_date}" '
        f'AND {jql_author}'
    )

    print(f"\n🔍 JQL: {jql}")
    print(f"📅 Date Range: {start_date} to {end_date}")

    try:
        # Use new v3 search/jql endpoint
        issues_raw = search_issues_v3(cfg, jql, max_results=500)
        print(f"📋 Found {len(issues_raw)} issues with worklogs")
    except Exception as e:
        print(f"❌ JQL Error: {e}")
        sys.exit(1)

    # Group worklogs by date
    daily_worklogs = {}
    total_entries = 0
    skipped_entries = 0

    for issue_data in issues_raw:
        issue_key = issue_data['key']
        issue_title = issue_data['fields']['summary']
        print(f"   📌 {issue_key} - {issue_title}")

        for wl in jira.worklogs(issue_key):
            wl_date = datetime.strptime(wl.started[:10], '%Y-%m-%d')

            # ============================================
            # FILTER: Only current month
            # ============================================
            if wl_date.month != month or wl_date.year != year:
                continue

            # ============================================
            # FILTER: Only MY worklogs (by account ID)
            # ============================================
            wl_account_id = getattr(wl.author, 'accountId', None)
            wl_email = getattr(wl.author, 'emailAddress', '')
            wl_name = getattr(wl.author, 'name', '')
            wl_display = getattr(wl.author, 'displayName', '')

            is_mine = (
                wl_account_id == target_account_id or
                wl_email == target_user_email or
                wl_name == target_user_email
            )

            if not is_mine:
                skipped_entries += 1
                continue
            # ============================================

            date_str = wl_date.strftime('%Y-%m-%d')
            hours = wl.timeSpentSeconds / 3600
            comment_raw = getattr(wl, 'comment', '') or ''
            
            # Handle comment which might be a string or ADF (Atlassian Document Format) object
            if isinstance(comment_raw, str):
                comment = comment_raw.strip()
            elif hasattr(comment_raw, 'content'):
                # ADF format - extract text from content
                try:
                    comment_parts = []
                    for block in comment_raw.content:
                        if hasattr(block, 'content'):
                            for item in block.content:
                                if hasattr(item, 'text'):
                                    comment_parts.append(item.text)
                    comment = ' '.join(comment_parts).strip()
                except:
                    comment = str(comment_raw)
            else:
                comment = str(comment_raw) if comment_raw else ''

            # Get start time from worklog
            wl_start_time = datetime.strptime(wl.started[:16], '%Y-%m-%dT%H:%M')
            start_time_str = wl_start_time.strftime('%H:%M')

            entry = {
                'issue_key': issue_key,
                'issue_title': issue_title,
                'issue_full': f"{issue_key} - {issue_title}",
                'hours': hours,
                'time_spent': wl.timeSpent,
                'comment': comment.strip(),
                'start_time': start_time_str,
            }

            if date_str not in daily_worklogs:
                daily_worklogs[date_str] = []
            daily_worklogs[date_str].append(entry)
            total_entries += 1

    print(f"\n📊 Your worklog entries: {total_entries}")
    print(f"⏭️  Skipped (other users): {skipped_entries}")
    print(f"📅 Days with your worklogs: {len(daily_worklogs)}")

    return daily_worklogs, target_display_name


def _thin():
    s = Side(style='thin')
    return Border(left=s, right=s, top=s, bottom=s)

def _border(**kwargs):
    sides = {k: Side(style='thin') for k, v in kwargs.items() if v}
    return Border(**sides)


def generate_excel(daily_worklogs, cfg, employee_name):
    year = cfg['year']
    month = cfg['month']
    project = cfg['project']
    last_day = calendar.monthrange(year, month)[1]
    approver = cfg.get('approver', '')
    reviewer = cfg.get('reviewer', '')
    company = cfg.get('company', '')

    wb = Workbook()
    ws = wb.active
    ws.title = calendar.month_name[month]

    # ── Styles ──────────────────────────────────────────────
    arial = 'Arial'
    thin = _thin()
    gray_fill   = PatternFill('solid', fgColor='7F7F7F')   # header row
    weekend_comment_fill = PatternFill('solid', fgColor='AEABAB')  # weekend comments col
    holiday_fill = PatternFill('solid', fgColor='FFFF00')  # government holiday
    white_fill  = PatternFill('solid', fgColor='FFFFFF')

    center = Alignment(horizontal='center', vertical='center', wrap_text=True)
    left   = Alignment(horizontal='left',   vertical='center', wrap_text=True)
    right  = Alignment(horizontal='right',  vertical='center')

    # ── Column widths ────────────────────────────────────────
    ws.column_dimensions['A'].width = 2.7    # spacer
    ws.column_dimensions['B'].width = 14.0   # Date
    ws.column_dimensions['C'].width = 8.0    # Week
    ws.column_dimensions['D'].width = 60.0   # Description
    ws.column_dimensions['E'].width = 14.0   # Start-time
    ws.column_dimensions['F'].width = 14.0   # End-time
    ws.column_dimensions['G'].width = 18.0   # Working-time
    ws.column_dimensions['H'].width = 30.0   # Comments

    # ── White background for A1:H6 ──────────────────────────
    for row in range(1, 7):
        for col in range(1, 9):
            ws.cell(row=row, column=col).fill = white_fill

    # ── Row 2: Title + Company ───────────────────────────────
    ws.row_dimensions[2].height = 33
    ws['B2'].value = '作業実績報告'
    ws['B2'].font = Font(name=arial, bold=True, size=20)
    ws['B2'].alignment = Alignment(horizontal='left', vertical='center')

    ws['H2'].value = company
    ws['H2'].font = Font(name=arial, size=11)
    ws['H2'].alignment = right

    # ── Row 3: Subtitle + Approver ──────────────────────────
    ws.row_dimensions[3].height = 26.25
    ws['D3'].value = '本作業実績の通り作業が完了したことを報告します。'
    ws['D3'].font = Font(name=arial, size=14)
    ws['D3'].alignment = left

    ws['G3'].value = '承認者'
    ws['G3'].font = Font(name=arial, size=9)
    ws['G3'].alignment = center
    ws['G3'].border = thin

    ws['H3'].value = approver
    ws['H3'].font = Font(name=arial, size=9)
    ws['H3'].alignment = left
    ws['H3'].border = thin

    # ── Row 4: Reviewer ─────────────────────────────────────
    ws.row_dimensions[4].height = 26.25
    ws['G4'].value = '確認者'
    ws['G4'].font = Font(name=arial, size=9)
    ws['G4'].alignment = center
    ws['G4'].border = thin

    ws['H4'].value = reviewer
    ws['H4'].font = Font(name=arial, size=9)
    ws['H4'].alignment = left
    ws['H4'].border = thin

    # ── Row 5: Employee ─────────────────────────────────────
    ws.row_dimensions[5].height = 26.25
    ws['G5'].value = '作業者'
    ws['G5'].font = Font(name=arial, size=9)
    ws['G5'].alignment = center
    ws['G5'].border = thin

    ws['H5'].value = employee_name
    ws['H5'].font = Font(name=arial, bold=True, size=11, color='C00000')
    ws['H5'].alignment = left
    ws['H5'].border = thin

    # ── Row 7: Column headers ────────────────────────────────
    ws.row_dimensions[7].height = 35
    headers = [
        (2, 'Date'),
        (3, 'Week'),
        (4, 'Description'),
        (5, 'Start-time\n(hh:mm)'),
        (6, 'End-time\n(hh:mm)'),
        (7, 'Working-time\n(hh:mm)'),
        (8, 'Comments'),
    ]
    for col, label in headers:
        cell = ws.cell(row=7, column=col, value=label)
        cell.font = Font(name=arial, size=10, color='FFFFFF')
        cell.fill = gray_fill
        cell.border = thin
        cell.alignment = center

    # ── Data rows ────────────────────────────────────────────
    excel_row = 8
    for day in range(1, last_day + 1):
        current_date = datetime(year, month, day)
        date_str = current_date.strftime('%Y-%m-%d')
        is_weekend = current_date.weekday() >= 5
        ws.row_dimensions[excel_row].height = 18

        # Col B: Date
        b = ws.cell(row=excel_row, column=2, value=current_date)
        b.number_format = 'yyyy"-"mm"-"dd'
        b.font = Font(name=arial, size=10)
        b.alignment = center
        b.border = thin

        # Col C: Weekday formula
        c = ws.cell(row=excel_row, column=3, value=f'=TEXT(B{excel_row},"ddd")')
        c.font = Font(name=arial, size=10)
        c.alignment = center
        c.border = _border(left=True, top=True, bottom=True)

        # Col D: Description
        d = ws.cell(row=excel_row, column=4)
        d.font = Font(name=arial, size=10)
        d.alignment = left
        d.border = thin

        # Col E: Start-time
        e = ws.cell(row=excel_row, column=5)
        e.font = Font(name=arial, size=10)
        e.number_format = 'h:mm'
        e.alignment = center
        e.border = _border(right=True, top=True, bottom=True)

        # Col F: End-time
        f = ws.cell(row=excel_row, column=6)
        f.font = Font(name=arial, size=10)
        f.number_format = 'h:mm'
        f.fill = white_fill
        f.alignment = center
        f.border = thin

        # Col G: Working-time — [h]:mm to correctly show hours >= 24
        g = ws.cell(row=excel_row, column=7)
        g.font = Font(name=arial, size=10)
        g.number_format = '[h]:mm'
        g.alignment = center
        g.border = thin

        # Col H: Comments
        h = ws.cell(row=excel_row, column=8)
        h.font = Font(name=arial, size=10)
        h.alignment = left
        h.border = thin

        if date_str in daily_worklogs:
            entries = daily_worklogs[date_str]

            earliest_start = '23:59'
            day_total_seconds = 0

            for entry in entries:
                if entry['start_time'] < earliest_start:
                    earliest_start = entry['start_time']
                day_total_seconds += int(entry['hours'] * 3600)

            # Description (worklog comments as a single sentence)
            work_descs = []
            for entry in entries:
                if entry['comment']:
                    # Remove special characters (bullets, asterisks, hashes, etc.)
                    desc = re.sub(r'[^\w\s,\-/()]+', '', entry['comment'])
                    desc = re.sub(r'\s+', ' ', desc).strip()
                    if desc:
                        # Fix spelling while preserving acronyms
                        desc = _fix_text(desc)
                        # Lowercase the first letter for mid-sentence flow
                        work_descs.append(desc[0].lower() + desc[1:] if len(desc) > 1 else desc.lower())
            if work_descs:
                # Capitalize the first item
                work_descs[0] = work_descs[0][0].upper() + work_descs[0][1:] if len(work_descs[0]) > 1 else work_descs[0].upper()
                if len(work_descs) == 1:
                    d.value = work_descs[0] + '.'
                else:
                    d.value = ', '.join(work_descs[:-1]) + ' and ' + work_descs[-1] + '.'


            # Start time as Excel time value
            sh, sm = map(int, earliest_start.split(':'))
            e.value = time(sh, sm)

            # End time = start + JIRA hours + 1h overhead
            # The formula =MOD(F-E,1)-TIME(1,0,0) then cancels the overhead to give exact JIRA hours
            end_total_min = sh * 60 + sm + (day_total_seconds // 60) + 60
            eh = (end_total_min // 60) % 24
            em = end_total_min % 60
            f.value = time(eh, em)

            # Working time = (end - start) - 1h overhead = JIRA hours
            g.value = f'=MOD(F{excel_row} - E{excel_row}, 1) - TIME(1,0,0)'

            # Comments always empty for work days (including weekends with data)
            # Adjust row height for multiple entries
            ws.row_dimensions[excel_row].height = max(18, len(entries) * 18)

        elif is_weekend:
            for col in range(2, 9):
                ws.cell(row=excel_row, column=col).fill = weekend_comment_fill
            h.value = 'Weekend'

        else:
            # Weekday with no data → Leave
            h.value = 'Leave'

        excel_row += 1

    # ── Separator row (gray bar) ─────────────────────────────
    ws.row_dimensions[excel_row].height = 14
    for col in range(2, 9):
        cell = ws.cell(row=excel_row, column=col)
        cell.fill = weekend_comment_fill
        cell.border = thin
    excel_row += 1

    # ── Total row ────────────────────────────────────────────
    ws.row_dimensions[excel_row].height = 18
    total_row = excel_row
    g_total = ws.cell(row=total_row, column=7, value=f'=SUM(G8:G{total_row - 2})')
    g_total.number_format = '[h]:mm'
    g_total.font = Font(name=arial, bold=True, size=12)
    g_total.alignment = center
    g_total.border = thin
    excel_row += 1

    # ── Remarks ──────────────────────────────────────────────
    ws.row_dimensions[excel_row].height = 18
    ws.cell(row=excel_row, column=2, value='Remarks').font = Font(name=arial, size=10, bold=True)
    excel_row += 1

    ws.row_dimensions[excel_row].height = 18
    ws.merge_cells(f'B{excel_row}:H{excel_row}')
    remark = ws.cell(
        row=excel_row, column=2,
        value='各日：Description時間＋1時間Overheadを加算(Skype、Video、board操作etc)'
    )
    remark.font = Font(name=arial, size=9)

    # ── Freeze panes ────────────────────────────────────────
    ws.freeze_panes = 'B8'

    # ── Print settings ───────────────────────────────────────
    ws.sheet_properties.pageSetUpPr.fitToPage = True
    ws.page_setup.orientation = 'landscape'
    ws.page_setup.fitToWidth = 1
    ws.page_setup.fitToHeight = 0

    # ── Save ─────────────────────────────────────────────────
    script_dir = os.path.dirname(os.path.abspath(__file__))
    reports_dir = os.path.join(script_dir, 'reports')
    os.makedirs(reports_dir, exist_ok=True)
    first_name = employee_name.split()[0] if employee_name else 'Report'
    month_name = calendar.month_name[month]
    excel_file = os.path.join(reports_dir, f'(Monthly Report){first_name}_{month_name}_{year}.xlsx')
    wb.save(excel_file)

    # Compute totals for console output
    grand_total_seconds = sum(
        sum(int(e['hours'] * 3600) for e in entries)
        for entries in daily_worklogs.values()
    )
    total_h = grand_total_seconds // 3600
    total_m = (grand_total_seconds % 3600) // 60
    total_time_str = f"{total_h}:{total_m:02d}"
    working_days = len(daily_worklogs)
    return excel_file, total_time_str, working_days


def print_console_report(daily_worklogs, cfg):
    year = cfg['year']
    month = cfg['month']
    last_day = calendar.monthrange(year, month)[1]
    print(f"\n{'='*110}")
    print(f"{'Date':<14}{'Week':<7}{'Description':<50}{'Start':<9}{'End':<9}{'Hours':<9}{'Comments'}")
    print(f"{'='*110}")
    for day in range(1, last_day + 1):
        current_date = datetime(year, month, day)
        date_str = current_date.strftime('%Y-%m-%d')
        day_name = current_date.strftime('%a')
        is_weekend = current_date.weekday() >= 5
        if date_str in daily_worklogs:
            entries = daily_worklogs[date_str]
            first = True
            for e in entries:
                desc = f"{e['issue_key']} - {e['issue_title'][:35]}"
                comment = e['comment'][:30] if e['comment'] else ''
                if first:
                    print(f"{date_str:<14}{day_name:<7}{desc:<50}{e['start_time']:<9}{'--:--':<9}{e['time_spent']:<9}{comment}")
                    first = False
                else:
                    print(f"{'':<14}{'':<7}{desc:<50}{e['start_time']:<9}{'--:--':<9}{e['time_spent']:<9}{comment}")
        elif is_weekend:
            print(f"{date_str:<14}{day_name:<7}{'Weekend':<50}")
        else:
            print(f"{date_str:<14}{day_name:<7}{'':<50}")
    print(f"{'='*110}")


def main():
    print("🚀 JIRA Monthly Worklog Report Generator")
    print("=" * 45)
    cfg = load_config()
    print(f"📁 Project:  {cfg['project']}")
    print(f"📅 Period:   {calendar.month_name[cfg['month']]} {cfg['year']}")
    jira, employee_name = connect_jira(cfg)
    daily_worklogs, report_name = fetch_worklogs(jira, cfg)
    if not daily_worklogs:
        print("\n\u26a0\ufe0f  No worklogs found for the specified period!")
        sys.exit(0)
    print_console_report(daily_worklogs, cfg)
    print("\n\U0001f4dd Generating Excel report...")
    excel_file, total_time, working_days = generate_excel(daily_worklogs, cfg, report_name)
    print(f"\n{'='*45}")
    print(f"  ✅ Report Generated Successfully!")
    print(f"  📄 File: {excel_file}")
    print(f"  ⏱️  Total Hours: {total_time}")
    print(f"  📅 Working Days: {working_days}")
    print(f"{'='*45}")


if __name__ == '__main__':
    main()
