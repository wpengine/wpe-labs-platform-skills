---
name: wpe-labs:cache
description: Purge cache for WP Engine WordPress installations. Supports object cache, page cache, CDN edge cache, or all at once. Use after deployments, content updates, or when users report stale content. Requires WP Engine API credentials; no local tooling needed beyond curl and jq.
---

<objective>
Purge one or more cache layers for WP Engine WordPress installations via the API. Run after deployments, theme/plugin updates, or content publishing when users report stale content. Supports targeted purges (object, page, CDN) or a full flush of all cache types. Requires only curl and jq.
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
**Purge all cache for an install:**

```bash
INSTALL_ID="your-install-uuid"

curl -s -u "$WPE_USERNAME:$WPE_PASSWORD" \
  -H "User-Agent: ai-code-skill/wpe-labs:cache" \
  -H "Content-Type: application/json" \
  -X POST "https://api.wpengineapi.com/v1/installs/$INSTALL_ID/purge_cache" \
  -d '{"type": "all"}' | jq '.'
```
</quick_start>

<workflow>
**Step 1: Identify the install**

If you only have a site name, resolve to install_id:

```bash
curl -s -u "$WPE_USERNAME:$WPE_PASSWORD" \
  -H "User-Agent: ai-code-skill/wpe-labs:cache" \
  "https://api.wpengineapi.com/v1/installs" | \
  jq -r '.results[] | select(.name | test("mysite")) | "\(.id)\t\(.name)\t\(.environment)"'
```

A site name may match multiple installs (production, staging, development). Always clarify which environment to target before purging. If the user doesn't specify, default to **production** and state that assumption explicitly: *"Purging production cache for mysite — let me know if you meant staging."*

---

**Step 2: Choose the cache type**

| Type | What it clears | When to use |
|------|---------------|-------------|
| `object` | WordPress object cache (DB query cache) | Plugin options changed, user role changes |
| `page` | WP Engine full-page cache | Content published, theme updated |
| `cdn` | CDN edge cache (CloudFront/Fastly) | Assets changed (images, CSS, JS) |
| `all` | All of the above | After deployments, major changes |

When in doubt, use `all`.

---

**Step 3: Purge the cache**

```bash
INSTALL_ID="your-install-uuid"
CACHE_TYPE="all"  # object | page | cdn | all

curl -s -u "$WPE_USERNAME:$WPE_PASSWORD" \
  -H "User-Agent: ai-code-skill/wpe-labs:cache" \
  -H "Content-Type: application/json" \
  -X POST "https://api.wpengineapi.com/v1/installs/$INSTALL_ID/purge_cache" \
  -d "{\"type\": \"$CACHE_TYPE\"}"
```

Returns 200 on success.

---

**Step 4: Purge cache across multiple installs**

Common after deploying a change that affects all environments:

```bash
for INSTALL_ID in "$PROD_ID" "$STAGING_ID"; do
  echo "Purging cache for install: $INSTALL_ID"
  curl -s -u "$WPE_USERNAME:$WPE_PASSWORD" \
    -H "User-Agent: ai-code-skill/wpe-labs:cache" \
    -H "Content-Type: application/json" \
    -X POST "https://api.wpengineapi.com/v1/installs/$INSTALL_ID/purge_cache" \
    -d '{"type": "all"}'
  sleep 1
done
```
</workflow>

<api_reference>
**Base URL:** `https://api.wpengineapi.com/v1`
**Auth:** HTTP Basic Auth with credentials from https://my.wpengine.com/api_access

| Endpoint | Purpose |
|----------|---------|
| `POST /installs/{id}/purge_cache` | Purge cache (type: object \| page \| cdn \| all) |

**Request body:** `{"type": "all"}` — type is required.

**Cache types:**
- `object` — WordPress object cache
- `page` — WP Engine full-page cache
- `cdn` — CDN edge cache
- `all` — All cache types simultaneously
</api_reference>

<troubleshooting>
**Purge succeeds but users still see stale content** — CDN propagation can take 1–5 minutes globally. If content is still stale after 5 minutes, check whether the site uses an additional external CDN (Cloudflare, etc.) that needs a separate purge.

**Wrong install purged** — Always confirm the install name and environment before purging production. Use `GET /installs` to verify.

**429 Too Many Requests** — Add a 1-second delay between purges when iterating over multiple installs.

**Credentials fail** — Regenerate at https://my.wpengine.com/api_access. Note: these are separate from your portal login credentials.
</troubleshooting>

<success_criteria>
- Target install identified by name and environment confirmed
- Cache type selected (defaulting to `all` unless a specific type was requested)
- Purge submitted and 200 response confirmed
- User notified that CDN propagation may take 1–5 minutes
</success_criteria>
