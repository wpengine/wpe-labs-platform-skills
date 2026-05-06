---
name: wpe-labs:account-usage
description: Fetches and displays total usage data (bandwidth, visits, file storage, database storage) across all WP Engine accounts using the REST API, compared against plan limits. Use when checking WP Engine resource consumption, traffic totals, storage, or limit headroom. Requires WP Engine API credentials; no local tooling needed beyond curl and jq.
---

<objective>
Summarize WP Engine resource usage—bandwidth, visits, file storage, database storage—across all accounts and compare against plan limits. Works for any WP Engine account holder with API credentials. Requires only curl and jq.
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

<quick_start>
**Verify credentials and list accounts:**

```bash
curl -s -u "$WPE_USERNAME:$WPE_PASSWORD" \
  -H "User-Agent: wpe-labs-skills/account-usage" \
  "https://api.wpengineapi.com/v1/accounts" | \
  jq '[.results[] | {id, name}]'
```

**Get usage summary for one account (last 30 days):**

```bash
ACCOUNT_ID="your-account-uuid"

curl -s -u "$WPE_USERNAME:$WPE_PASSWORD" \
  -H "User-Agent: wpe-labs-skills/account-usage" \
  "https://api.wpengineapi.com/v1/accounts/$ACCOUNT_ID/usage/summary" | \
  jq '{
    visits:         ((.visit_count.sum          // "0") | tonumber),
    billable_visits:((.billable_visits.sum       // "0") | tonumber),
    bandwidth_gb:   ((.network_total_bytes.sum   // "0") | tonumber / 1073741824 | . * 100 | round / 100),
    file_storage_gb:((.storage_file_bytes.latest.value   // "0") | tonumber / 1073741824 | . * 100 | round / 100),
    db_storage_gb:  ((.storage_database_bytes.latest.value // "0") | tonumber / 1073741824 | . * 100 | round / 100)
  }'
```
</quick_start>

<workflow>
**Step 1: List all accounts**

```bash
curl -s -u "$WPE_USERNAME:$WPE_PASSWORD" \
  -H "User-Agent: wpe-labs-skills/account-usage" \
  "https://api.wpengineapi.com/v1/accounts" | \
  jq -r '.results[] | "\(.id)\t\(.name)"'
```

If count > 100, paginate: add `?limit=100&offset=100`.

**Get details for a single account:**

```bash
curl -s -u "$WPE_USERNAME:$WPE_PASSWORD" \
  -H "User-Agent: wpe-labs-skills/account-usage" \
  "https://api.wpengineapi.com/v1/accounts/$ACCOUNT_ID" | jq .
```

---

**Step 2: Fetch usage summary + plan limits per account**

Run both in parallel for each account ID:

```bash
# Usage summary (default = last 30 days)
curl -s -u "$WPE_USERNAME:$WPE_PASSWORD" \
  -H "User-Agent: wpe-labs-skills/account-usage" \
  "https://api.wpengineapi.com/v1/accounts/$ACCOUNT_ID/usage/summary"

# Plan limits
curl -s -u "$WPE_USERNAME:$WPE_PASSWORD" \
  -H "User-Agent: wpe-labs-skills/account-usage" \
  "https://api.wpengineapi.com/v1/accounts/$ACCOUNT_ID/limits"
```

**Custom date range** (both params required, max 31 days, max 13 months back):

```bash
curl -s -u "$WPE_USERNAME:$WPE_PASSWORD" \
  -H "User-Agent: wpe-labs-skills/account-usage" \
  "https://api.wpengineapi.com/v1/accounts/$ACCOUNT_ID/usage/summary?first_date=2025-03-01&last_date=2025-03-31"
```

---

**Step 3: Parse and convert usage summary**

All byte values are int64 encoded as strings (proto3). Use `tonumber` to convert.

```bash
jq '{
  visits:          ((.visit_count.sum          // "0") | tonumber),
  billable_visits: ((.billable_visits.sum       // "0") | tonumber),
  bandwidth_gb:    ((.network_total_bytes.sum   // "0") | tonumber / 1073741824 | . * 100 | round / 100),
  cdn_gb:          ((.network_cdn_bytes.sum     // "0") | tonumber / 1073741824 | . * 100 | round / 100),
  origin_gb:       ((.network_origin_bytes.sum  // "0") | tonumber / 1073741824 | . * 100 | round / 100),
  file_storage_gb: ((.storage_file_bytes.latest.value     // "0") | tonumber / 1073741824 | . * 100 | round / 100),
  db_storage_gb:   ((.storage_database_bytes.latest.value // "0") | tonumber / 1073741824 | . * 100 | round / 100)
}'
```

Plan limits response fields: `visitors` (integer), `storage` (GB integer), `bandwidth` (GB integer).

---

**Step 4: Production vs staging breakdown (optional)**

The insights endpoint breaks usage down by environment type:

```bash
curl -s -u "$WPE_USERNAME:$WPE_PASSWORD" \
  -H "User-Agent: wpe-labs-skills/account-usage" \
  "https://api.wpengineapi.com/v1/accounts/$ACCOUNT_ID/usage/insights" | \
  jq '{
    visits: {
      production:  .visit_count.environment_types.production,
      staging:     .visit_count.environment_types.staging,
      development: .visit_count.environment_types.development,
      total:       .visit_count.total
    },
    bandwidth_bytes: {
      production:  .network_total_bytes.environment_types.production,
      staging:     .network_total_bytes.environment_types.staging,
      development: .network_total_bytes.environment_types.development
    }
  }'
```

---

**Step 5: Present the summary**

For each account show:

| Metric | Used | Limit | % Used |
|--------|------|-------|--------|
| Visits (billable) | X | plan limit | X% |
| Bandwidth | X GB | plan limit GB | X% |
| File Storage | X GB | plan limit GB | X% |
| DB Storage | X GB | — | — |

- Flag accounts at **>80% of any limit** as approaching cap
- Flag accounts at **>100%** as over limit
- Note production vs staging split if relevant
- Note: storage values use `.latest.value` (current snapshot); bandwidth/visits use `.sum` (period total)
</workflow>

<api_reference>
**Base URL:** `https://api.wpengineapi.com/v1`
**Auth:** HTTP Basic Auth with credentials from https://my.wpengine.com/api_access

| Endpoint | Purpose |
|----------|---------|
| `GET /accounts` | List all accounts (paginated, max 100/page) |
| `GET /accounts/{id}/usage/summary` | 30-day usage rollup across all installs |
| `GET /accounts/{id}/usage/insights` | Usage broken down by env type + site type |
| `GET /accounts/{id}/limits` | Plan limits: visitors, storage (GB), bandwidth (GB) |
| `GET /accounts/{id}` | Single account details |
| `GET /accounts/{id}/usage` | Per-environment daily metrics (paginated, `first_date`/`last_date`, `limit`/`offset`) |
| `GET /installs/{id}/usage` | Daily metrics for a single install (`first_date`/`last_date`) |
| `POST /installs/{id}/usage/refresh_disk_usage` | Trigger per-install disk usage recalculation |

**UsageMetricsRollup field semantics:**

| Field | `.sum` | `.average` | `.latest.value` |
|-------|--------|------------|-----------------|
| `visit_count` | Total visits (use this) | Avg/day | — |
| `billable_visits` | Total billable (use this) | Avg/day | — |
| `network_total_bytes` | Total CDN+origin bytes (use this) | Avg/day | — |
| `network_cdn_bytes` | CDN bytes (use this) | Avg/day | — |
| `network_origin_bytes` | Origin bytes (use this) | Avg/day | — |
| `storage_file_bytes` | — | — | Current snapshot (use this) |
| `storage_database_bytes` | — | — | Current snapshot (use this) |

**Byte conversion:** 1 GB = 1,073,741,824 bytes
</api_reference>

<troubleshooting>
**Null or zero storage** — Storage may be stale. Trigger a refresh:

```bash
curl -s -u "$WPE_USERNAME:$WPE_PASSWORD" -X POST \
  -H "User-Agent: wpe-labs-skills/account-usage" \
  "https://api.wpengineapi.com/v1/accounts/$ACCOUNT_ID/usage/refresh_disk_usage"
```

Then poll `/accounts/{id}/usage/summary` until `storage_file_bytes.latest` is populated.

**Zero visits for current period** — The API default is last 30 days, not the billing period. Specify billing period dates explicitly with `first_date` / `last_date`.

**Multiple accounts** — Fetch each account's summary separately and aggregate the GB/visit totals manually. There is no single cross-account rollup endpoint.

**429 Too Many Requests** — Add a short delay between requests when looping over many accounts.

**Credentials fail** — Regenerate at https://my.wpengine.com/api_access. Note: these are separate from your portal login credentials.
</troubleshooting>

<success_criteria>
- All accounts listed from `/accounts`
- Usage summary fetched per account: visits, billable visits, bandwidth GB, file storage GB, DB storage GB
- Plan limits fetched and % utilization calculated for each metric
- Accounts at >80% of any limit flagged
- Production vs staging visit/bandwidth split shown (via insights endpoint) if relevant
</success_criteria>
