---
name: wpe-labs:backups
description: Create and monitor backups for WP Engine WordPress installations. Use before major changes (deployments, migrations, plugin updates) or to verify a recent backup exists. Requires WP Engine API credentials; no local tooling needed beyond curl and jq.
---

<objective>
Create on-demand backups for WP Engine WordPress installations and monitor their progress to completion. Designed to be run before significant changes — deployments, database migrations, plugin/theme updates — and to confirm a clean backup exists before proceeding. Requires only curl and jq.
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
**Create a backup for an install:**

```bash
INSTALL_ID="your-install-uuid"

curl -s -u "$WPE_USERNAME:$WPE_PASSWORD" \
  -H "User-Agent: wpe-labs-skills/backups" \
  -H "Content-Type: application/json" \
  -X POST "https://api.wpengineapi.com/v1/installs/$INSTALL_ID/backups" \
  -d '{
    "description": "Pre-deployment backup",
    "notification_emails": ["you@example.com"]
  }' | jq '{id, status}'
```

**Check backup status:**

```bash
BACKUP_ID="your-backup-uuid"

curl -s -u "$WPE_USERNAME:$WPE_PASSWORD" \
  -H "User-Agent: wpe-labs-skills/backups" \
  "https://api.wpengineapi.com/v1/installs/$INSTALL_ID/backups/$BACKUP_ID" | \
  jq '{id, status, description, created_at}'
```
</quick_start>

<workflow>
**Step 1: Identify the install to back up**

If you only have a site name, resolve to install_id first:

```bash
curl -s -u "$WPE_USERNAME:$WPE_PASSWORD" \
  -H "User-Agent: wpe-labs-skills/backups" \
  "https://api.wpengineapi.com/v1/installs" | \
  jq -r '.results[] | select(.name | test("mysite")) | "\(.id)\t\(.name)\t\(.environment)"'
```

---

**Step 2: Create the backup**

```bash
INSTALL_ID="your-install-uuid"

BACKUP=$(curl -s -u "$WPE_USERNAME:$WPE_PASSWORD" \
  -H "User-Agent: wpe-labs-skills/backups" \
  -H "Content-Type: application/json" \
  -X POST "https://api.wpengineapi.com/v1/installs/$INSTALL_ID/backups" \
  -d "{
    \"description\": \"Pre-deployment backup - $(date +%Y-%m-%d)\",
    \"notification_emails\": [\"you@example.com\"]
  }")

BACKUP_ID=$(echo "$BACKUP" | jq -r '.id')
echo "Backup ID: $BACKUP_ID | Initial status: $(echo $BACKUP | jq -r '.status')"
```

---

**Step 3: Poll until complete**

Backup status progresses: `requested` → `initiated` → `completed` (or `aborted`)

Typical completion time: 2–10 minutes depending on install size.

```bash
while true; do
  STATUS=$(curl -s -u "$WPE_USERNAME:$WPE_PASSWORD" \
    -H "User-Agent: wpe-labs-skills/backups" \
    "https://api.wpengineapi.com/v1/installs/$INSTALL_ID/backups/$BACKUP_ID" | \
    jq -r '.status')
  echo "Status: $STATUS"
  [ "$STATUS" = "completed" ] || [ "$STATUS" = "aborted" ] && break
  sleep 30
done
```

---

**Step 4: Confirm and report**

```bash
curl -s -u "$WPE_USERNAME:$WPE_PASSWORD" \
  -H "User-Agent: wpe-labs-skills/backups" \
  "https://api.wpengineapi.com/v1/installs/$INSTALL_ID/backups/$BACKUP_ID" | \
  jq '{id, status, description, created_at}'
```

Report the backup ID and status to the user before proceeding with any destructive operation.
</workflow>

<api_reference>
**Base URL:** `https://api.wpengineapi.com/v1`
**Auth:** HTTP Basic Auth with credentials from https://my.wpengine.com/api_access

| Endpoint | Purpose |
|----------|---------|
| `POST /installs/{id}/backups` | Create a backup (description, notification_emails) |
| `GET /installs/{id}/backups/{backup_id}` | Get backup status |

**Backup status values:** `requested` → `initiated` → `completed` | `aborted`

**Backup request fields:**
- `description` (string) — label shown in Portal backup history
- `notification_emails` (string array) — addresses to notify on completion
</api_reference>

<troubleshooting>
**Backup returns `aborted`** — Typically caused by a timeout on very large installs or a transient infrastructure issue. Retry; if it fails again, check Portal for any site-level alerts.

**Don't know the install_id** — Query `GET /installs` and filter by name. Never guess; a backup to the wrong install is irreversible.

**Backup is taking longer than 15 minutes** — Large installs with many files or a large database can exceed typical times. Continue polling; do not re-submit.

**notification_emails not receiving anything** — Check spam filters. The email comes from a WP Engine system address. Alternatively, poll the status endpoint directly.

**Credentials fail** — Regenerate at https://my.wpengine.com/api_access. Note: these are separate from your portal login credentials.
</troubleshooting>

<success_criteria>
- Target install identified by name or ID
- Backup created with a meaningful description and notification email
- Backup ID captured and reported to the user
- Status polled until `completed` or `aborted`
- Final status and backup ID reported before any subsequent destructive operation
</success_criteria>
