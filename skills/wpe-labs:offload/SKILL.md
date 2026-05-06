---
name: wpe-labs:offload
description: Manage media offload (LargeFS) settings for WP Engine WordPress installations. Retrieve the S3 validation file, read current offload configuration, and create or update offload settings. Use when configuring or auditing media offload for an install. Requires WP Engine API credentials; no local tooling needed beyond curl and jq.
---

<objective>
Read and manage LargeFS (media offload) configuration for WP Engine WordPress installations. LargeFS offloads WordPress media uploads to S3-compatible storage. This skill covers: retrieving the S3 bucket validation file, reading the current offload config, and creating or updating offload settings. Requires only curl and jq.
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
**Get current offload configuration for an install:**

```bash
INSTALL_ID="your-install-uuid"

curl -s -u "$WPE_USERNAME:$WPE_PASSWORD" \
  -H "User-Agent: wpe-labs-skills/offload" \
  "https://api.wpengineapi.com/v1/installs/$INSTALL_ID/offload_settings/files" | jq .
```

**Get the LargeFS S3 validation file:**

```bash
curl -s -u "$WPE_USERNAME:$WPE_PASSWORD" \
  -H "User-Agent: wpe-labs-skills/offload" \
  "https://api.wpengineapi.com/v1/installs/$INSTALL_ID/offload_settings/largefs_validation_file" | jq .
```
</quick_start>

<workflow>
**Step 0: Resolve install name → install ID**

Users will refer to installs by name, not UUID:

```bash
curl -s -u "$WPE_USERNAME:$WPE_PASSWORD" \
  -H "User-Agent: wpe-labs-skills/offload" \
  "https://api.wpengineapi.com/v1/installs" | \
  jq -r '.results[] | select(.name | test("mysite")) | "\(.id)\t\(.name)\t\(.environment)"'
```

If multiple installs match, confirm which one with the user before proceeding.

---

**Step 1: Get the LargeFS validation file**

Before configuring S3 offload, WP Engine requires placing a validation file in the S3 bucket. Retrieve the filename and contents to upload:

```bash
curl -s -u "$WPE_USERNAME:$WPE_PASSWORD" \
  -H "User-Agent: wpe-labs-skills/offload" \
  "https://api.wpengineapi.com/v1/installs/$INSTALL_ID/offload_settings/largefs_validation_file" | jq .
```

Upload the returned file to the root of your S3 bucket before proceeding with configuration.

---

**Step 2: Read current offload configuration**

```bash
curl -s -u "$WPE_USERNAME:$WPE_PASSWORD" \
  -H "User-Agent: wpe-labs-skills/offload" \
  "https://api.wpengineapi.com/v1/installs/$INSTALL_ID/offload_settings/files" | jq .
```

Returns the current `large_fs_config` object. Always read the existing config before making updates — use it as the base for any PATCH request.

---

**Step 3: Create offload configuration (first-time setup)**

Use POST when no offload configuration exists yet:

```bash
curl -s -u "$WPE_USERNAME:$WPE_PASSWORD" \
  -H "User-Agent: wpe-labs-skills/offload" \
  -H "Content-Type: application/json" \
  -X POST "https://api.wpengineapi.com/v1/installs/$INSTALL_ID/offload_settings/files" \
  -d '{
    "large_fs_config": {
      "...": "use the config structure returned by GET /offload_settings/files"
    }
  }'
```

Returns 202 Accepted — the configuration is applied asynchronously.

---

**Step 4: Update offload configuration**

Use PATCH to modify existing configuration. Always fetch the current config first (Step 2), then send the full modified object:

```bash
curl -s -u "$WPE_USERNAME:$WPE_PASSWORD" \
  -H "User-Agent: wpe-labs-skills/offload" \
  -H "Content-Type: application/json" \
  -X PATCH "https://api.wpengineapi.com/v1/installs/$INSTALL_ID/offload_settings/files" \
  -d '{
    "large_fs_config": {
      "...": "full config object with your changes applied"
    }
  }'
```

Returns 202 Accepted — applied asynchronously.
</workflow>

<api_reference>
**Base URL:** `https://api.wpengineapi.com/v1`
**Auth:** HTTP Basic Auth with credentials from https://my.wpengine.com/api_access

| Endpoint | Purpose |
|----------|---------|
| `GET /installs/{id}/offload_settings/largefs_validation_file` | Get S3 bucket validation filename and contents |
| `GET /installs/{id}/offload_settings/files` | Read current LargeFS offload configuration |
| `POST /installs/{id}/offload_settings/files` | Create initial offload configuration (async, 202) |
| `PATCH /installs/{id}/offload_settings/files` | Update existing offload configuration (async, 202) |

**Workflow:** Both POST and PATCH accept a `large_fs_config` body and return 202 Accepted — configuration is applied asynchronously. Always read the current config via GET before updating to avoid overwriting fields unintentionally.
</api_reference>

<troubleshooting>
**POST returns 409 Conflict** — Offload configuration already exists. Use PATCH to update instead.

**PATCH returns 404** — No offload configuration exists yet. Use POST to create it first.

**202 returned but offload not working** — Configuration is applied asynchronously. Wait 1–2 minutes then verify by checking `/offload_settings/files` again.

**Validation file not found in S3** — The LargeFS validation file must be uploaded to the root of your S3 bucket before configuration is accepted. Re-fetch it via `GET /offload_settings/largefs_validation_file` and upload it.

**Credentials fail** — Regenerate at https://my.wpengine.com/api_access. Note: these are separate from your portal login credentials.
</troubleshooting>

<success_criteria>
- Install identified by name or ID
- LargeFS validation file retrieved and user informed it must be uploaded to S3
- Current offload configuration read before any update
- POST used for first-time setup, PATCH used for updates
- 202 response confirmed and user informed configuration applies asynchronously
</success_criteria>
