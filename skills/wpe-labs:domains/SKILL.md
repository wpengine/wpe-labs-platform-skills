---
name: wpe-labs:domains
description: Manage domains and SSL certificates for WP Engine installs. Add/remove domains, bulk-add redirects, check DNS propagation status, and provision or import SSL certificates. Requires WP Engine API credentials; no local tooling needed beyond curl and jq.
---

<objective>
Manage domains and SSL certificates for WP Engine WordPress installations. Covers the full domain lifecycle: listing what's attached, adding new domains and redirects, bulk-adding during migrations, checking DNS propagation, and handling SSL (Let's Encrypt and third-party). Requires only curl and jq.
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
**List all domains for an install:**

```bash
INSTALL_ID="your-install-uuid"

curl -s -u "$WPE_USERNAME:$WPE_PASSWORD" \
  -H "User-Agent: wpe-labs-skills/domains" \
  "https://api.wpengineapi.com/v1/installs/$INSTALL_ID/domains" | \
  jq '[.results[] | {id, name, primary, redirect_to, type}]'
```

**Check SSL certificate status for a domain:**

```bash
DOMAIN_ID="your-domain-uuid"

curl -s -u "$WPE_USERNAME:$WPE_PASSWORD" \
  -H "User-Agent: wpe-labs-skills/domains" \
  "https://api.wpengineapi.com/v1/installs/$INSTALL_ID/domains/$DOMAIN_ID/ssl_certificate" | \
  jq '{status, expiry_date, issuer}'
```
</quick_start>

<workflow>
**Step 0: Resolve install name → install ID**

Users will refer to installs by name (e.g. "mysite production"), not by UUID. Always resolve the name first:

```bash
curl -s -u "$WPE_USERNAME:$WPE_PASSWORD" \
  -H "User-Agent: wpe-labs-skills/domains" \
  "https://api.wpengineapi.com/v1/installs" | \
  jq -r '.results[] | select(.name | test("mysite")) | "\(.id)\t\(.name)\t\(.environment)"'
```

If multiple installs match (e.g. production and staging), confirm which one with the user before proceeding.

---

**Step 1: List domains**

```bash
curl -s -u "$WPE_USERNAME:$WPE_PASSWORD" \
  -H "User-Agent: wpe-labs-skills/domains" \
  "https://api.wpengineapi.com/v1/installs/$INSTALL_ID/domains" | \
  jq -r '.results[] | "\(.id)\t\(.name)\t\(if .redirect_to then "redirect→"+.redirect_to else "primary" end)"'
```

To resolve a domain name → domain ID (needed for redirects and DELETE):

```bash
curl -s -u "$WPE_USERNAME:$WPE_PASSWORD" \
  -H "User-Agent: wpe-labs-skills/domains" \
  "https://api.wpengineapi.com/v1/installs/$INSTALL_ID/domains" | \
  jq -r '.results[] | select(.name == "example.com") | .id'
```

---

**Step 2: Add a domain**

```bash
# Add a primary domain — capture the returned ID for use in redirects
TARGET=$(curl -s -u "$WPE_USERNAME:$WPE_PASSWORD" \
  -H "User-Agent: wpe-labs-skills/domains" \
  -H "Content-Type: application/json" \
  -X POST "https://api.wpengineapi.com/v1/installs/$INSTALL_ID/domains" \
  -d '{"name": "www.example.com"}')

TARGET_DOMAIN_ID=$(echo "$TARGET" | jq -r '.id')

# Add a redirect (e.g. naked domain → www)
# redirect_to requires the target domain's UUID, not its name
curl -s -u "$WPE_USERNAME:$WPE_PASSWORD" \
  -H "User-Agent: wpe-labs-skills/domains" \
  -H "Content-Type: application/json" \
  -X POST "https://api.wpengineapi.com/v1/installs/$INSTALL_ID/domains" \
  -d "{\"name\": \"example.com\", \"redirect_to\": \"$TARGET_DOMAIN_ID\"}"
```

Note: for the single-domain endpoint, `redirect_to` takes the **domain UUID** (not the domain name). Use the bulk endpoint (`/domains/bulk`) when you want to specify redirects by name.

---

**Step 3: Bulk-add domains (up to 20 at once)**

Useful for migrations with many redirects.

```bash
curl -s -u "$WPE_USERNAME:$WPE_PASSWORD" \
  -H "User-Agent: wpe-labs-skills/domains" \
  -H "Content-Type: application/json" \
  -X POST "https://api.wpengineapi.com/v1/installs/$INSTALL_ID/domains/bulk" \
  -d '{
    "domains": [
      {"name": "www.example.com"},
      {"name": "example.com", "redirect_to": "www.example.com"},
      {"name": "shop.example.com"}
    ]
  }'
```

---

**Step 4: Check domain DNS propagation**

```bash
# Submit a status check (returns report_id)
REPORT=$(curl -s -u "$WPE_USERNAME:$WPE_PASSWORD" \
  -H "User-Agent: wpe-labs-skills/domains" \
  -X POST "https://api.wpengineapi.com/v1/installs/$INSTALL_ID/domains/$DOMAIN_ID/check_status")

REPORT_ID=$(echo "$REPORT" | jq -r '.id')

# Retrieve the status report
curl -s -u "$WPE_USERNAME:$WPE_PASSWORD" \
  -H "User-Agent: wpe-labs-skills/domains" \
  "https://api.wpengineapi.com/v1/installs/$INSTALL_ID/domains/check_status/$REPORT_ID" | \
  jq '{status, checks}'
```

---

**Step 5: SSL certificate management**

**List all SSL certs for an install:**

```bash
curl -s -u "$WPE_USERNAME:$WPE_PASSWORD" \
  -H "User-Agent: wpe-labs-skills/domains" \
  "https://api.wpengineapi.com/v1/installs/$INSTALL_ID/ssl_certificates" | \
  jq '[.results[] | {id, status, expiry_date, domains}]'
```

**Request a Let's Encrypt certificate for a domain (legacy network):**

```bash
curl -s -u "$WPE_USERNAME:$WPE_PASSWORD" \
  -H "User-Agent: wpe-labs-skills/domains" \
  -X POST "https://api.wpengineapi.com/v1/installs/$INSTALL_ID/domains/$DOMAIN_ID/ssl_certificate"
```

**Import a third-party SSL certificate:**

The API expects Base64-encoded PEM content for both fields.

```bash
curl -s -u "$WPE_USERNAME:$WPE_PASSWORD" \
  -H "User-Agent: wpe-labs-skills/domains" \
  -H "Content-Type: application/json" \
  -X POST "https://api.wpengineapi.com/v1/installs/$INSTALL_ID/ssl_certificates/third_party" \
  -d "{
    \"certificate\": \"$(base64 -i cert.pem)\",
    \"private_key\": \"$(base64 -i key.pem)\"
  }"
```

On Linux, use `base64 cert.pem` (no `-i` flag). Only `certificate` and `private_key` are accepted — there is no `ca_bundle` field; include any intermediate certificates in the `certificate` chain.

---

**Step 6: Update a domain**

Update a domain's primary status, redirect target, or HTTPS enforcement:

```bash
# Set as primary domain
curl -s -u "$WPE_USERNAME:$WPE_PASSWORD" \
  -H "User-Agent: wpe-labs-skills/domains" \
  -H "Content-Type: application/json" \
  -X PATCH "https://api.wpengineapi.com/v1/installs/$INSTALL_ID/domains/$DOMAIN_ID" \
  -d '{"primary": true}' | jq '{id, name, primary}'

# Force HTTPS for all URLs
curl -s -u "$WPE_USERNAME:$WPE_PASSWORD" \
  -H "User-Agent: wpe-labs-skills/domains" \
  -H "Content-Type: application/json" \
  -X PATCH "https://api.wpengineapi.com/v1/installs/$INSTALL_ID/domains/$DOMAIN_ID" \
  -d '{"secure_all_urls": true}' | jq '{id, name, secure_all_urls}'

# Remove a redirect (set redirect_to to "nil")
curl -s -u "$WPE_USERNAME:$WPE_PASSWORD" \
  -H "User-Agent: wpe-labs-skills/domains" \
  -H "Content-Type: application/json" \
  -X PATCH "https://api.wpengineapi.com/v1/installs/$INSTALL_ID/domains/$DOMAIN_ID" \
  -d '{"redirect_to": "nil"}' | jq '{id, name, redirect_to}'
```

**PATCH fields:** `primary` (bool), `redirect_to` (domain UUID or `"nil"` to remove redirect), `secure_all_urls` (bool — force HTTPS).

---

**Step 7: Remove a domain**

> ⚠️ **GUARD — confirm before deleting.**
> Removing a domain is immediate and irreversible. If it is the primary domain or has live DNS traffic pointing to it, removal will break the site for visitors.
>
> Before running DELETE, you MUST:
> 1. Show the user the domain name and install name you are about to remove
> 2. State explicitly: *"This will permanently remove [domain] from [install]. This cannot be undone. Confirm?"*
> 3. Wait for explicit confirmation ("yes", "confirm", "do it") — do NOT proceed on ambiguous input

```bash
curl -s -u "$WPE_USERNAME:$WPE_PASSWORD" \
  -H "User-Agent: wpe-labs-skills/domains" \
  -X DELETE "https://api.wpengineapi.com/v1/installs/$INSTALL_ID/domains/$DOMAIN_ID"
```
</workflow>

<api_reference>
**Base URL:** `https://api.wpengineapi.com/v1`
**Auth:** HTTP Basic Auth with credentials from https://my.wpengine.com/api_access

| Endpoint | Purpose |
|----------|---------|
| `GET /installs/{id}/domains` | List all domains for an install |
| `POST /installs/{id}/domains` | Add a domain or redirect |
| `POST /installs/{id}/domains/bulk` | Bulk-add up to 20 domains/redirects |
| `GET /installs/{id}/domains/{domain_id}` | Get domain details |
| `PATCH /installs/{id}/domains/{domain_id}` | Update domain (`primary`, `redirect_to`, `secure_all_urls`) |
| `DELETE /installs/{id}/domains/{domain_id}` | Remove domain |
| `POST /installs/{id}/domains/{domain_id}/check_status` | Submit DNS propagation check |
| `GET /installs/{id}/domains/check_status/{report_id}` | Get propagation report |
| `GET /installs/{id}/ssl_certificates` | List SSL certs |
| `GET /installs/{id}/domains/{domain_id}/ssl_certificate` | Get cert for domain |
| `POST /installs/{id}/domains/{domain_id}/ssl_certificate` | Request Let's Encrypt cert |
| `POST /installs/{id}/ssl_certificates/third_party` | Import PEM cert + key |

**Domain fields:** `id`, `name`, `primary` (bool), `redirect_to` (string or null), `type`
</api_reference>

<troubleshooting>
**Domain add returns 422** — Domain name must be a valid FQDN. Don't include `https://` or trailing slashes.

**`GET /ssl_certificates` returns 404** — The SSL certificates list endpoint is not available on all network types. Installs on WP Engine's modern network manage SSL differently; use the Portal for those. The endpoint works on legacy network installs.

**SSL request fails** — Let's Encrypt provisioning is only available on the legacy network. If this returns an error, the install may be on the modern network; import a cert via the third-party endpoint instead, or provision SSL through the Portal.

**DNS check shows not propagated** — Verify the domain's DNS A/CNAME record points to the install's `cname` or `ip` field (retrievable from `GET /installs/{id}`). Propagation can take up to 48 hours.

**Bulk add partially fails** — The response includes per-domain results; parse the array to identify which succeeded and which failed.

**429 Too Many Requests** — Add a short delay between requests when checking many domains.

**Credentials fail** — Regenerate at https://my.wpengine.com/api_access. Note: these are separate from your portal login credentials.
</troubleshooting>

<success_criteria>
- All domains listed for the target install with redirect relationships shown
- New domain or redirect successfully added
- DNS propagation status checked and reported
- SSL certificate status retrieved for each domain
- Let's Encrypt cert requested or third-party cert imported when asked
</success_criteria>
