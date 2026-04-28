---
name: wpe-labs:installs
description: List, inspect, create, and copy WordPress installations and sites across WP Engine environments. Use when managing sites/installs, checking environment details (PHP version, cname, IP), or copying production to staging. Requires WP Engine API credentials; no local tooling needed beyond curl and jq.
---

<objective>
List and manage WP Engine sites and WordPress installations. Covers the full lifecycle: browsing what exists, creating new sites and installs, and copying environments (e.g. production → staging). Works for any WP Engine account holder with API credentials. Requires only curl and jq.
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
**List all sites across all accounts:**

```bash
curl -s -u "$WPE_USERNAME:$WPE_PASSWORD" \
  -H "User-Agent: ai-code-skill/wpe-labs:installs" \
  "https://api.wpengineapi.com/v1/sites" | \
  jq '[.results[] | {id, name, account_id}]'
```

**List all installs with environment and cname:**

```bash
curl -s -u "$WPE_USERNAME:$WPE_PASSWORD" \
  -H "User-Agent: ai-code-skill/wpe-labs:installs" \
  "https://api.wpengineapi.com/v1/installs" | \
  jq '[.results[] | {id, name, environment, cname, php_version, site_id}]'
```
</quick_start>

<workflow>
**Step 1: List sites (optionally filtered by account)**

```bash
# All sites
curl -s -u "$WPE_USERNAME:$WPE_PASSWORD" \
  -H "User-Agent: ai-code-skill/wpe-labs:installs" \
  "https://api.wpengineapi.com/v1/sites" | \
  jq -r '.results[] | "\(.id)\t\(.name)\t\(.account_id)"'

# Filter by account
curl -s -u "$WPE_USERNAME:$WPE_PASSWORD" \
  -H "User-Agent: ai-code-skill/wpe-labs:installs" \
  "https://api.wpengineapi.com/v1/sites?account_id=$ACCOUNT_ID" | \
  jq -r '.results[] | "\(.id)\t\(.name)"'
```

If `count > 100`, paginate with `?limit=100&offset=100`.

---

**Step 2: List installs for a site**

```bash
SITE_ID="your-site-uuid"

curl -s -u "$WPE_USERNAME:$WPE_PASSWORD" \
  -H "User-Agent: ai-code-skill/wpe-labs:installs" \
  "https://api.wpengineapi.com/v1/installs?site_id=$SITE_ID" | \
  jq '[.results[] | {id, name, environment, cname, ip, php_version, wpe_version}]'
```

---

**Step 3: Get details on a specific install**

```bash
INSTALL_ID="your-install-uuid"

curl -s -u "$WPE_USERNAME:$WPE_PASSWORD" \
  -H "User-Agent: ai-code-skill/wpe-labs:installs" \
  "https://api.wpengineapi.com/v1/installs/$INSTALL_ID" | \
  jq '{id, name, environment, cname, ip, php_version, wpe_version, account_id, site_id}'
```

---

**Step 4: Create a new site + install**

```bash
# 1. Create the site
SITE=$(curl -s -u "$WPE_USERNAME:$WPE_PASSWORD" \
  -H "User-Agent: ai-code-skill/wpe-labs:installs" \
  -H "Content-Type: application/json" \
  -X POST "https://api.wpengineapi.com/v1/sites" \
  -d "{\"name\": \"my-new-site\", \"account_id\": \"$ACCOUNT_ID\"}")

SITE_ID=$(echo "$SITE" | jq -r '.id')

# 2. Create the production install on that site
curl -s -u "$WPE_USERNAME:$WPE_PASSWORD" \
  -H "User-Agent: ai-code-skill/wpe-labs:installs" \
  -H "Content-Type: application/json" \
  -X POST "https://api.wpengineapi.com/v1/installs" \
  -d "{
    \"name\": \"my-new-site\",
    \"account_id\": \"$ACCOUNT_ID\",
    \"site_id\": \"$SITE_ID\",
    \"environment\": \"production\"
  }"
```

---

**Step 5: Copy an install (e.g. production → staging)**

> **Before copying:** install_copy overwrites the destination — it cannot be undone without a backup. For a single install, confirm the source and destination. For bulk operations (copying all sites), always list the affected site pairs and wait for explicit user confirmation before submitting any request.

```bash
SOURCE_INSTALL_ID="prod-install-uuid"
DEST_INSTALL_ID="staging-install-uuid"

curl -s -u "$WPE_USERNAME:$WPE_PASSWORD" \
  -H "User-Agent: ai-code-skill/wpe-labs:installs" \
  -H "Content-Type: application/json" \
  -X POST "https://api.wpengineapi.com/v1/install_copy" \
  -d "{
    \"source_install_id\": \"$SOURCE_INSTALL_ID\",
    \"destination_install_id\": \"$DEST_INSTALL_ID\",
    \"options\": {
      \"include_files\": true,
      \"include_db\": true
    },
    \"notification_emails\": [\"you@example.com\"]
  }"
```

Returns 202 Accepted. The copy runs asynchronously — notify the user when emails confirm completion.

**Selective DB copy (specific tables only):**

```bash
-d "{
  \"source_install_id\": \"$SOURCE_INSTALL_ID\",
  \"destination_install_id\": \"$DEST_INSTALL_ID\",
  \"options\": {
    \"include_files\": false,
    \"include_db\": true,
    \"db_tables\": [\"wp_posts\", \"wp_postmeta\", \"wp_options\"]
  }
}"
```
</workflow>

<api_reference>
**Base URL:** `https://api.wpengineapi.com/v1`
**Auth:** HTTP Basic Auth with credentials from https://my.wpengine.com/api_access

| Endpoint | Purpose |
|----------|---------|
| `GET /sites` | List sites (paginated, filterable by account_id) |
| `POST /sites` | Create site (name, account_id) |
| `GET /sites/{site_id}` | Get site details |
| `PATCH /sites/{site_id}` | Update site name |
| `DELETE /sites/{site_id}` | Delete site |
| `GET /installs` | List installs (paginated, filterable by site_id, account_id) |
| `POST /installs` | Create install (name, account_id, site_id, environment) |
| `GET /installs/{install_id}` | Get install details |
| `PATCH /installs/{install_id}` | Update install |
| `DELETE /installs/{install_id}` | Delete install |
| `POST /install_copy` | Copy install between environments (async, 202) |

**Install fields:** `id`, `name`, `account_id`, `site_id`, `environment` (production/staging/development), `cname`, `ip`, `php_version`, `wpe_version`

**install_copy options:** `include_files` (bool), `include_db` (bool), `db_tables` (string array for selective table copy)
</api_reference>

<troubleshooting>
**install_copy returns 202 but nothing happens** — The copy is asynchronous. Wait for the notification email. Do not re-submit; duplicate copies can overwrite in-progress work.

**Can't find install_id** — Run `GET /installs` and filter by site name: `jq '.results[] | select(.name | test("mysite"))'`

**Create install fails with 422** — `name` must be lowercase letters, numbers, and hyphens only. `environment` must be exactly `production`, `staging`, or `development`.

**429 Too Many Requests** — Add a short delay between requests when iterating over many sites or installs.

**Credentials fail** — Regenerate at https://my.wpengine.com/api_access. Note: these are separate from your portal login credentials.
</troubleshooting>

<success_criteria>
- All sites listed from `/sites` with account association
- All installs listed per site with environment, cname, IP, and PHP version
- Specific install details retrievable by ID
- New site + install created when requested
- Install copy submitted with source/destination confirmed and user notified of async completion
</success_criteria>
