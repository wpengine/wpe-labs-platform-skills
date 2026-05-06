# WP Engine Labs Platform Skills

Claude Code skills for managing WP Engine accounts, sites, and infrastructure through natural language — without opening Portal.

## Contents

- [Prerequisites](#prerequisites)
- [Install](#install)
- [Setup](#setup)
- [Skills at a glance](#skills-at-a-glance)
- [Skill reference](#skill-reference)
- [Safety and destructive operations](#safety-and-destructive-operations)
- [Contributing](#contributing)
- [Troubleshooting](#troubleshooting)

---

## Prerequisites

- [Claude Code](https://claude.ai/code) installed and running
- `curl` and `jq` — standard on macOS/Linux
  ```bash
  brew install jq       # macOS
  apt install jq        # Ubuntu/Debian
  ```
- WP Engine API credentials (see [Setup](#setup))

---

## Install

```bash
curl -fsSL https://raw.githubusercontent.com/wpengine/wpe-labs-platform-skills/main/install.sh | bash
```

Installs all 7 skills into `~/.claude/skills/` and all commands into `~/.claude/commands/`.

---

## Setup

### Get API credentials

1. Go to **[my.wpengine.com/api_access](https://my.wpengine.com/api_access)**
2. Click **Generate credentials**
3. Copy the username and password

> These are separate from your portal login credentials.

### Set environment variables

Copy the example file and fill in your values:

```bash
cp .env.example .env   # if working from this repo
# or create ~/.wpe-skills.env manually
```

```bash
# WP Engine API credentials
export WPE_USERNAME="your-api-username"
export WPE_PASSWORD="your-api-password"
```

To persist across sessions, add both lines to your `~/.zshrc` or `~/.bashrc`, then `source` it.

---

## Skills at a glance

| Skill | What it does | Risk |
|-------|-------------|------|
| [`/wpe-labs:account-usage`](#wpe-labsaccount-usage) | Fetch bandwidth, visits, and storage across all accounts | 🟢 Read-only |
| [`/wpe-labs:monthly-report`](#wpe-labsmonthly-report) | Generate a client-ready monthly usage report | 🟢 Read-only |
| [`/wpe-labs:backups`](#wpe-labsbackups) | Create on-demand backups and monitor progress | 🟡 Write |
| [`/wpe-labs:cache`](#wpe-labscache) | Purge object, page, or CDN cache layers | 🟡 Write |
| [`/wpe-labs:users`](#wpe-labsusers) | List, invite, update roles, and remove account users | 🟡 Write / 🔴 Destructive |
| [`/wpe-labs:domains`](#wpe-labsdomains) | Manage domains, redirects, DNS checks, and SSL | 🟡 Write / 🔴 Destructive |
| [`/wpe-labs:installs`](#wpe-labsinstalls) | List, create, update, and copy WordPress installations | 🟡 Write / 🔴 Destructive |
| [`/wpe-labs:offload`](#wpe-labsoffload) | Manage LargeFS media offload configuration | 🟡 Write |

**Risk levels:**
- 🟢 **Read-only** — no changes are made to your account
- 🟡 **Write** — creates or modifies resources; generally recoverable
- 🔴 **Destructive** — includes operations that cannot be undone; Claude will always ask for explicit confirmation before proceeding

---

## Skill reference

### `/wpe-labs:account-usage`

🟢 **Read-only**

Fetches bandwidth, visits, file storage, and database storage across all accounts, compared against plan limits. Accounts at >80% of any limit are flagged automatically.

```
/wpe-labs:account-usage
/wpe-labs:account-usage which accounts are closest to their bandwidth limit?
/wpe-labs:account-usage show me usage for March 2025
/wpe-labs:account-usage show me production traffic only
```

**What it returns:** visits (total and billable), bandwidth GB, file storage GB, DB storage GB — all vs plan limits. Supports custom date ranges up to 13 months back in 31-day windows. Can also return details for a single account or granular per-environment daily usage breakdowns.

---

### `/wpe-labs:monthly-report`

🟢 **Read-only**

Generates a complete monthly usage report across all accounts, formatted for client delivery or internal review. Composes usage totals, plan limit utilization, environment breakdown, and site counts into polished Markdown.

```
/wpe-labs:monthly-report
/wpe-labs:monthly-report March 2025
/wpe-labs:monthly-report last month prepared for Acme Corp
/wpe-labs:monthly-report Q1 2025
/wpe-labs:monthly-report show only accounts over 80% of any limit
```

**What it returns:** Markdown report with per-account tables, utilization percentages, production/staging/development breakdown, and automatic flagging of accounts approaching or over limits. Ready to paste into email, Notion, or Slack.

**Note:** Q1 and other multi-month ranges are automatically split into 31-day API windows and aggregated.

---

### `/wpe-labs:backups`

🟡 **Write** — creates backups; does not modify or delete anything

Creates on-demand backups for WordPress installations and monitors their progress. Run this before any major change — deployments, database migrations, plugin updates.

```
/wpe-labs:backups back up mysite production before deployment
/wpe-labs:backups check status of backup abc-123
```

**What it returns:** backup ID and status (`requested` → `initiated` → `completed` or `aborted`). Polls until completion and reports the final state before you proceed.

---

### `/wpe-labs:cache`

🟡 **Write** — purges cache; recovers automatically as pages are requested

Purges one or more cache layers for a WordPress installation. Supports targeted purges (`object`, `page`, `cdn`) or a full flush (`all`). Cache rebuilds automatically as users visit pages.

```
/wpe-labs:cache purge all cache for mysite production
/wpe-labs:cache clear CDN cache for mysite
/wpe-labs:cache purge cache on production and staging after deployment
```

**What it returns:** purge confirmation. Defaults to `all` when cache type is not specified. Notes that CDN propagation may take 1–5 minutes.

**Safeguard:** If the install name matches multiple environments (production, staging, development), Claude will ask which one you mean before purging.

---

### `/wpe-labs:users`

🟡 **Write** for listing, inviting, and role changes  
🔴 **Destructive** for removing users — access is revoked immediately

Lists, invites, updates roles, and removes users from WP Engine accounts. Supports cross-account audits.

```
/wpe-labs:users who has access to my account?
/wpe-labs:users invite jane@example.com as full user
/wpe-labs:users change jane@example.com to billing only
/wpe-labs:users audit all users across all accounts
/wpe-labs:users remove jane@example.com
```

**What it returns:** user list with email addresses and roles. Supports comma-separated role combinations (`full,billing`, `partial,billing`).

**Safeguards:**
- Removing a user: Claude will look up the user by email, show their current role, state that removal is immediate and cannot be undone without re-inviting, and require explicit confirmation
- Ambiguous requests ("remove the user") will prompt Claude to ask which user you mean

---

### `/wpe-labs:domains`

🟡 **Write** for adding domains and checking status  
🔴 **Destructive** for removing domains — may immediately break live traffic

Manages domains and SSL certificates for WordPress installations. Add primary domains and redirects, bulk-add during migrations, check DNS propagation, and provision or import SSL certificates.

```
/wpe-labs:domains list all domains for mysite
/wpe-labs:domains add www.example.com and redirect example.com to it
/wpe-labs:domains add these domains to mysite: shop.example.com, blog.example.com
/wpe-labs:domains check DNS propagation for www.example.com
/wpe-labs:domains show SSL certificate status for mysite
/wpe-labs:domains remove old.example.com from mysite
```

**What it returns:** domain list with redirect relationships, DNS propagation status, SSL certificate status and expiry. Supports updating domains to change primary status, redirect targets, or enforce HTTPS.

**Safeguards:**
- Removing a domain: Claude will resolve the domain name to its ID, show which domain and install will be affected, warn that removal may break live traffic if DNS is still pointing to it, and require explicit confirmation
- Single-domain redirects use the target domain's UUID (not its name); bulk adds use domain names — Claude handles this distinction automatically

**Note:** The SSL certificate list endpoint (`GET /ssl_certificates`) is not available on all WP Engine network types. If you see a 404, manage SSL through the Portal for that install.

---

### `/wpe-labs:installs`

🟡 **Write** for listing, creating sites and installs  
🔴 **Destructive** for copying environments (overwrites destination) and deleting sites or installs (permanent)

Lists, inspects, creates, and copies WordPress installations across environments. Covers the full lifecycle from browsing what exists to copying production to staging.

```
/wpe-labs:installs list all sites
/wpe-labs:installs show PHP version, cname, and IP for all production installs
/wpe-labs:installs create a new site called mysite
/wpe-labs:installs copy mysite production to staging
/wpe-labs:installs copy only wp_posts and wp_options from production to staging
```

**What it returns:** site and install details (name, environment, cname, IP, PHP version). Handles async install copy with email notification on completion. Also supports renaming sites, updating installs, and retrieving per-install daily usage metrics.

**Safeguards:**
- **Copying environments:** overwrites the destination install's files and/or database. Claude will resolve both install names, show the source→destination pair, state that existing data on the destination will be replaced, and require explicit confirmation before submitting. For bulk operations (all sites), Claude will list every pair and confirm the full list before any request is sent.
- **Deleting a site or install:** permanent — all files and database data are destroyed and cannot be recovered. Claude will verify the install exists, recommend creating a backup first, state the full consequences, and require you to type the install name (not just "yes") as confirmation.

---

### `/wpe-labs:offload`

🟡 **Write** — reads and updates configuration; does not delete data

Manages LargeFS media offload configuration for WordPress installations. LargeFS offloads WordPress media uploads to S3-compatible storage. Covers the full setup workflow: retrieving the S3 bucket validation file, reading current configuration, and creating or updating offload settings.

```
/wpe-labs:offload show offload config for mysite
/wpe-labs:offload get the LargeFS validation file for mysite
/wpe-labs:offload set up media offload for mysite
/wpe-labs:offload update the offload configuration for mysite
```

**What it returns:** current LargeFS configuration or the S3 validation file contents. POST and PATCH operations return 202 Accepted — configuration is applied asynchronously.

**Note:** Always fetch the current config before updating — the PATCH request requires the full config object, not just changed fields.

---

## Safety and destructive operations

Several skills can make irreversible changes. The skills enforce a consistent guard pattern for any destructive operation:

1. **Identify** — resolve names to IDs and confirm what will be affected
2. **State consequences** — explicitly describe what will happen and that it cannot be undone
3. **Require confirmation** — wait for explicit confirmation before proceeding; ambiguous replies do not count

For the most destructive operation (deleting a site or install), Claude requires you to **type the install name** as confirmation rather than just saying "yes."

If you are ever unsure whether a request will trigger a destructive action, ask Claude to describe what it would do before confirming.

---

## Contributing

### Adding a new skill

Each skill is a single `SKILL.md` file in `skills/wpe-labs:{name}/` plus a command definition in `commands/wpe-labs:{name}.md`. Follow the structure of an existing skill — required frontmatter fields and XML sections are enforced by the lint check.

### Conventions

- **User-Agent:** all curl calls must include `-H "User-Agent: wpe-labs-skills/{skill-name}"` so WP Engine can identify Claude Code traffic in API access logs. Grep for `wpe-labs-skills` to find all skill traffic; grep for `/account-usage` to find a specific skill.
- **Name→ID resolution:** skills accept names from users and resolve to IDs via API lookup. Never assume the user knows or will provide a UUID.
- **Guards:** any operation listed as destructive must include the full guard pattern (identify, state consequences, require confirmation).

### Running the tests

**Layer 1 — Static lint** (no credentials required, runs in CI):
```bash
bash tests/lint.sh
```
Checks frontmatter, required sections, User-Agent coverage on every curl call, command→skill references, and secret hygiene.

**Layer 2 — API smoke tests** (requires WP Engine credentials):
```bash
bash tests/smoke.sh
```
Hits read-only endpoints for each skill against the live API and asserts HTTP 200 + expected JSON shape. Prints `export` hints for the object IDs used.

**Layer 3 — LLM evals** (requires Anthropic API key):
```bash
pip install -r tests/evals/requirements.txt
python tests/evals/run_evals.py                          # all 40 cases
python tests/evals/run_evals.py --skill monthly-report   # one skill
python tests/evals/run_evals.py --tags guard             # by tag
python tests/evals/run_evals.py --output results.json    # save JSON
```
Runs each skill with a test prompt via the Claude API and uses a second Claude call as judge to score responses against a rubric. Tests cover happy paths, date ranges, name→ID resolution, threshold flagging, and guard behavior.

### Environment variables

Copy `.env.example` to `.env` and fill in your values. `.env` is gitignored — never commit credentials.

```bash
export WPE_USERNAME=your-api-username
export WPE_PASSWORD=your-api-password
export WPE_ACCOUNT_ID=your-account-uuid      # used by smoke tests and evals
export WPE_ACCOUNT_NAME=your-account-name    # used by evals
export WPE_INSTALL_ID=your-install-uuid      # used by smoke tests and evals
export WPE_INSTALL_NAME=your-install-name    # used by evals
export ANTHROPIC_API_KEY=sk-ant-...          # used by evals
```

Run `bash tests/smoke.sh` once to discover and print your real account and install IDs.

---

## Troubleshooting

**401 Unauthorized**
Regenerate credentials at [my.wpengine.com/api_access](https://my.wpengine.com/api_access). These are separate from your portal login.

**Storage shows zero or null**
Ask Claude to "refresh storage" — it will trigger a recalculation via the API and re-fetch once populated. Storage data is refreshed asynchronously and may take 30–60 seconds.

**Zero visits for current period**
The default window is the last 30 days, which may not align with your billing cycle. Ask Claude to fetch a specific date range: "show me usage for March 2025."

**`jq` not found**
```bash
brew install jq        # macOS
apt install jq         # Ubuntu/Debian
```

**SSL certificate list returns 404**
The `/ssl_certificates` endpoint is not available on all WP Engine network types. Use the Portal to manage SSL for installs on the modern network.

**install_copy returns 202 but nothing happens**
The copy is asynchronous — wait for the notification email. Do not re-submit; duplicate copies can overwrite work in progress.
