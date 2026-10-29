# PR Review — Compile, Deduplicate & Scoring Rubric

Merge/dedup rules, severity-tier mapping, verdict criteria, and EC-Cube checks — loaded at Step 6 (Compile and Deduplicate Results), once, after all 7 agents complete. Do not load earlier.

## 6.1 Merge Findings
Collect all findings from all agents into a unified list.

## 6.2 Deduplicate
When the same `file:line` is flagged by multiple agents:
- Keep the **highest severity** rating
- Merge insights from both agents into a single finding
- Credit both perspectives
- Priority: Security > Performance > Architecture > Code Quality

## 6.3 Group by Severity Tier

| Tier | Label | Emoji | Maps From | Merge Impact |
|------|-------|-------|-----------|--------------|
| **Tier 1** | High-Risk Issues (Must Fix) | 🔴 | Critical + High | Blocks merge |
| **Tier 2** | Medium-Risk Issues (Should Fix) | 🟡 | Medium | Should fix, doesn't block |
| **Tier 3** | Low-Risk / Suggestions (Nice-to-Have) | 🟢 | Low | Optional improvement |

Number findings sequentially across all tiers (1, 2, 3, … N).

## 6.4 Determine Verdict

| Verdict | Emoji | Criteria |
|---------|-------|----------|
| **Approve** | ✅ | No Tier 1 issues. All findings are Tier 2/3. |
| **Approve with Comments** | 🟡 | No Tier 1 issues but notable Tier 2 findings remain. |
| **Request Changes** | ⚠️ | Any Tier 1 issues present. |

## 6.5 EC-Cube-Specific Checks (only when IS_ECCUBE is true)

- [ ] No files modified under `src/Eccube/`
- [ ] All services use constructor dependency injection
- [ ] Parameterized queries only (no SQL string concatenation)
- [ ] Cache cleared after config changes
