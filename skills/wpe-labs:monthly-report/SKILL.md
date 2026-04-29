---
name: wpe-labs:monthly-report
description: Generate a complete monthly usage report across all WP Engine accounts, formatted for client delivery or internal review. Fetches usage metrics, plan limits, environment breakdown, and site counts, then produces a polished Markdown document ready to share. Requires WP Engine API credentials; no local tooling needed beyond curl and jq.
---

<objective>
Produce a complete, client-ready monthly usage report across all WP Engine accounts. For each account: fetch usage totals, compare against plan limits, show environment breakdown (production vs staging vs development), and count sites. Output as polished Markdown suitable for email, Notion, or Slack. Requires only curl and jq.
</objective>

<credentials>
Create API credentials at: **https://my.wpengine.com/api_access** → Generate credentials

Set as env vars before running:

```bash
export WPE_USERNAME="your-api-username"
export WPE_PASSWORD="your-api-password"
```

Or pass inline: `-u "your-api-username:your-api-password"`
</credentials>

<report_parameters>
Ask the user for the following before fetching data (or use defaults):

- **Period:** Default = previous calendar month. Accept natural language: "March 2025", "last month", "Q1 2025" (split into 31-day windows).
- **Accounts:** Default = all accounts. Accept specific account names to filter.
- **Format:** Default = full Markdown. Accept "summary only" (just the table), "flagged only" (accounts at >80%), or "email" (plain text).
- **Recipient:** Optional. If provided, open the report with "Prepared for [Name/Company]."

If the user runs `/wpe-labs:monthly-report` with no arguments, use defaults silently and proceed.
</report_parameters>

<workflow>
**Step 1: Determine the reporting period**

Convert the user's requested period to API date params. The API supports max 31-day windows.

```
"last month"     → first_date=YYYY-MM-01, last_date=YYYY-MM-{last day}
"March 2025"     → first_date=2025-03-01, last_date=2025-03-31
"Q1 2025"        → Run 3 separate queries (Jan, Feb, Mar) and sum the results
"last 30 days"   → first_date={today-30}, last_date={today}
```

---

**Step 2: List all accounts**

```bash
curl -s -u "$WPE_USERNAME:$WPE_PASSWORD" \
  -H "User-Agent: wpe-labs-skills/monthly-report" \
  "https://api.wpengineapi.com/v1/accounts?limit=100" | \
  jq -r '.results[] | "\(.id)\t\(.name)"'
```

Paginate if `count > 100`. If the user requested specific accounts, filter to those names only.

---

**Step 3: For each account, fetch in parallel**

Run all three requests concurrently per account:

```bash
ACCOUNT_ID="account-uuid"
FIRST_DATE="2025-03-01"
LAST_DATE="2025-03-31"

# Usage summary for the period
curl -s -u "$WPE_USERNAME:$WPE_PASSWORD" \
  -H "User-Agent: wpe-labs-skills/monthly-report" \
  "https://api.wpengineapi.com/v1/accounts/$ACCOUNT_ID/usage/summary?first_date=$FIRST_DATE&last_date=$LAST_DATE"

# Plan limits
curl -s -u "$WPE_USERNAME:$WPE_PASSWORD" \
  -H "User-Agent: wpe-labs-skills/monthly-report" \
  "https://api.wpengineapi.com/v1/accounts/$ACCOUNT_ID/limits"

# Environment breakdown
curl -s -u "$WPE_USERNAME:$WPE_PASSWORD" \
  -H "User-Agent: wpe-labs-skills/monthly-report" \
  "https://api.wpengineapi.com/v1/accounts/$ACCOUNT_ID/usage/insights?first_date=$FIRST_DATE&last_date=$LAST_DATE"

# Site count
curl -s -u "$WPE_USERNAME:$WPE_PASSWORD" \
  -H "User-Agent: wpe-labs-skills/monthly-report" \
  "https://api.wpengineapi.com/v1/sites?account_id=$ACCOUNT_ID&limit=1" | \
  jq '.count'
```

---

**Step 4: Parse usage data**

All byte values are int64 encoded as strings (proto3). Use `tonumber` in jq.

```bash
# From usage/summary response:
jq '{
  visits:          ((.visit_count.sum          // "0") | tonumber),
  billable_visits: ((.billable_visits.sum       // "0") | tonumber),
  bandwidth_gb:    ((.network_total_bytes.sum   // "0") | tonumber / 1073741824 | . * 100 | round / 100),
  file_storage_gb: ((.storage_file_bytes.latest.value   // "0") | tonumber / 1073741824 | . * 100 | round / 100),
  db_storage_gb:   ((.storage_database_bytes.latest.value // "0") | tonumber / 1073741824 | . * 100 | round / 100)
}'

# From limits response:
jq '{visitors, storage_gb: .storage, bandwidth_gb: .bandwidth}'

# From insights response:
jq '{
  visits: {
    production:  .visit_count.environment_types.production,
    staging:     .visit_count.environment_types.staging,
    development: .visit_count.environment_types.development
  },
  bandwidth_bytes: {
    production:  .network_total_bytes.environment_types.production,
    staging:     .network_total_bytes.environment_types.staging,
    development: .network_total_bytes.environment_types.development
  }
}'
```

---

**Step 5: Calculate utilization and flag thresholds**

For each metric with a plan limit:

```
utilization_pct = (used / limit) * 100
```

Thresholds:
- **>100%** — Over limit → flag with `🔴 Over limit`
- **>80%** — Approaching cap → flag with `⚠️ Approaching limit`
- **≤80%** — Healthy → no flag

Storage limits from the API are in GB (integer). Bandwidth limits from the API are in GB (integer). Visitor limits are raw count (integer).

---

**Step 6: Compose the report**

Structure the final Markdown output as follows:

```markdown
# WP Engine Usage Report — {Month Year}

**Period:** {first_date} – {last_date}
**Generated:** {today's date}
{If recipient: **Prepared for:** {Name/Company}}

---

## Summary

| Account | Visits (Billable) | Bandwidth | File Storage | DB Storage | Sites |
|---------|-------------------|-----------|--------------|------------|-------|
| Acme Corp | 45,200 / 50,000 | 120 GB / 200 GB | 18 GB / 50 GB | 4 GB | 3 |
| ⚠️ Beta Inc | 42,100 / 50,000 | 168 GB / 200 GB | 12 GB / 50 GB | 2 GB | 1 |

---

## Acme Corp

| Metric | Used | Limit | Utilization |
|--------|------|-------|-------------|
| Visits (billable) | 45,200 | 50,000 | 90% ⚠️ Approaching limit |
| Bandwidth | 120 GB | 200 GB | 60% |
| File Storage | 18 GB | 50 GB | 36% |
| DB Storage | 4 GB | — | — |

**Environment Breakdown**

| Environment | Visits | Bandwidth |
|-------------|--------|-----------|
| Production | 44,800 | 118 GB |
| Staging | 400 | 2 GB |
| Development | 0 | 0 GB |

**Sites:** 3

---

## Beta Inc

...

---

*Report generated by [wpe-labs:monthly-report](https://github.com/wpengine/labs-usage-skill)*
```

**Formatting rules:**
- Format large numbers with commas (45,200 not 45200)
- Round GB to 2 decimal places
- Show utilization as integer percentage
- Omit DB Storage limit column if the API returns no limit for it
- **Always** check file and DB storage values before rendering. If either shows 0 GB or null, do not display 0 as if it were correct — instead show: *(Storage data may be stale — say "refresh storage" to trigger a recalculation)*
- Sort accounts alphabetically in the summary table
- Put flagged accounts (⚠️ or 🔴) first in the summary table
- **Always include the Environment Breakdown table** when the user requests it or when the insights endpoint was called — do not fetch the data and then omit it from the report
</workflow>

<api_reference>
**Base URL:** `https://api.wpengineapi.com/v1`
**Auth:** HTTP Basic Auth with credentials from https://my.wpengine.com/api_access

| Endpoint | Purpose |
|----------|---------|
| `GET /accounts` | List all accounts (paginated, max 100/page) |
| `GET /accounts/{id}/usage/summary` | Usage rollup for period (visits, bandwidth, storage) |
| `GET /accounts/{id}/usage/insights` | Environment breakdown (production/staging/development) |
| `GET /accounts/{id}/limits` | Plan limits: visitors, storage (GB), bandwidth (GB) |
| `GET /sites` | Site count per account (filter by account_id) |

**Date params:** `first_date=YYYY-MM-DD&last_date=YYYY-MM-DD` (both required for custom ranges, max 31 days per query)

**UsageMetricsRollup semantics:**
- `.sum` → total for the period (use for visits, bandwidth)
- `.latest.value` → current snapshot (use for file and DB storage)
- Byte values are int64 encoded as strings — always apply `| tonumber` before arithmetic

**Byte conversion:** 1 GB = 1,073,741,824 bytes
</api_reference>

<troubleshooting>
**Storage shows 0 GB** — Storage data may be stale. Offer to trigger a refresh:

```bash
curl -s -u "$WPE_USERNAME:$WPE_PASSWORD" -X POST \
  -H "User-Agent: wpe-labs-skills/monthly-report" \
  "https://api.wpengineapi.com/v1/accounts/$ACCOUNT_ID/usage/refresh_disk_usage"
```

Then re-fetch the usage summary after 30–60 seconds.

**Period spans more than 31 days (e.g. Q1)** — Split into monthly windows, fetch each separately, and sum visits and bandwidth. Storage always uses the latest snapshot regardless of period.

**Zero visits** — Confirm date range is correct. The API returns 0 if `first_date`/`last_date` are outside the data retention window (max 13 months back).

**Multiple accounts with many installs** — Add 500ms delay between account requests to avoid 429 errors.

**Credentials fail** — Regenerate at https://my.wpengine.com/api_access. Note: these are separate from your portal login credentials.
</troubleshooting>

<success_criteria>
- Reporting period determined (defaulting to previous calendar month)
- All accounts fetched and filtered if requested
- Per account: usage summary, limits, environment breakdown, and site count all retrieved
- Utilization calculated and thresholds applied (>80% flagged, >100% marked over limit)
- Complete Markdown report generated with summary table + per-account detail sections
- Flagged accounts surfaced prominently
- Report is clean enough to paste directly into an email or Notion page
</success_criteria>
