# WP Engine Labs Skills

Claude Code skills for managing WP Engine accounts, sites, and infrastructure — without opening Portal.

## Prerequisites

- [Claude Code](https://claude.ai/code) installed and running
- `curl` and `jq` — standard on macOS/Linux (`brew install jq` if missing)
- WP Engine API credentials (see Setup below)

## Install

```bash
curl -fsSL https://raw.githubusercontent.com/wpengine/labs-usage-skill/main/install.sh | bash
```

Installs all 7 skills at once.

## Setup: Get API Credentials

1. Go to **[my.wpengine.com/api_access](https://my.wpengine.com/api_access)**
2. Click **Generate credentials**
3. Copy the username and password shown

> These are separate from your portal login.

Set them as environment variables:

```bash
export WPE_USERNAME="your-api-username"
export WPE_PASSWORD="your-api-password"
```

To persist across sessions, add both lines to your `~/.zshrc` or `~/.bashrc` and `source` it.

---

## Skills

### `/wpe-labs:account-usage`

Fetch bandwidth, visits, and storage totals across all accounts — compared against plan limits.

```
/wpe-labs:account-usage
/wpe-labs:account-usage which accounts are closest to their bandwidth limit?
/wpe-labs:account-usage show me usage for March 2025
```

**Returns:** visits, billable visits, bandwidth GB, file storage GB, DB storage GB, vs plan limits. Accounts at >80% of any limit are flagged automatically.

---

### `/wpe-labs:installs`

List, inspect, create, and copy WordPress sites and installations across environments.

```
/wpe-labs:installs list all sites for Acme Corp
/wpe-labs:installs show me the PHP version and IP for mysite production
/wpe-labs:installs copy mysite production to staging
```

**Returns:** site and install details (name, environment, cname, IP, PHP version). Handles async install copy with notification.

---

### `/wpe-labs:domains`

Manage domains and SSL certificates — add, remove, bulk-add, check DNS propagation, provision SSL.

```
/wpe-labs:domains list all domains for mysite
/wpe-labs:domains add www.example.com and redirect example.com to it
/wpe-labs:domains check DNS propagation for www.example.com
/wpe-labs:domains request SSL for www.example.com
```

**Returns:** domain list with redirect relationships, DNS propagation status, SSL certificate status and expiry.

---

### `/wpe-labs:backups`

Create on-demand backups and monitor their progress.

```
/wpe-labs:backups back up mysite production before deployment
/wpe-labs:backups check status of backup abc-123
```

**Returns:** backup ID and status. Polls until `completed` or `aborted`. Always run before major changes.

---

### `/wpe-labs:users`

List, invite, update, and remove users across WP Engine accounts.

```
/wpe-labs:users list all users on Acme Corp
/wpe-labs:users invite jane@example.com as full user on Acme Corp
/wpe-labs:users audit all users across all accounts
/wpe-labs:users remove jane@example.com from Acme Corp
```

**Returns:** user list with roles. Supports cross-account audits.

---

### `/wpe-labs:cache`

Purge object, page, CDN, or all cache layers for any install.

```
/wpe-labs:cache purge all cache for mysite production
/wpe-labs:cache clear CDN cache for mysite
```

**Returns:** purge confirmation. Defaults to `all` cache types when not specified.

---

### `/wpe-labs:monthly-report`

Generate a complete monthly usage report across all accounts, formatted for client delivery or internal review.

```
/wpe-labs:monthly-report
/wpe-labs:monthly-report March 2025
/wpe-labs:monthly-report last month prepared for Acme Corp
/wpe-labs:monthly-report show only accounts over 80% of any limit
```

**Returns:** Markdown report with per-account usage tables, plan limit utilization, environment breakdown (production/staging/development), site counts, and automatic flagging of accounts approaching or over limits. Ready to paste into email, Notion, or Slack.

---

## Troubleshooting

**401 Unauthorized**
Regenerate credentials at [my.wpengine.com/api_access](https://my.wpengine.com/api_access).

**Storage shows zero or null**
Ask Claude to "refresh storage" — it will trigger a recalculation and re-fetch.

**Zero visits for current period**
The default 30-day window may not align with your billing cycle. Ask Claude to fetch a specific date range instead.

**`jq` not found**
```bash
brew install jq        # macOS
apt install jq         # Ubuntu/Debian
```
