# wpe-labs:account-usage

A Claude Code skill that fetches bandwidth, visits, and storage totals across all your WP Engine accounts — without opening Portal.

## Prerequisites

- [Claude Code](https://claude.ai/code) installed and running
- `curl` and `jq` — standard on macOS/Linux (`brew install jq` if missing)
- WP Engine API credentials (see Setup below)

## Install

```bash
curl -fsSL https://raw.githubusercontent.com/wpengine/labs-usage-skill/main/install.sh | bash
```

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

## Usage

Open Claude Code and run:

```
/wpe-labs:account-usage
```

Claude will fetch all your accounts, pull usage for each (last 30 days by default), compare against plan limits, and flag anything approaching the cap.

**Ask follow-up questions naturally:**

```
/wpe-labs:account-usage which accounts are closest to their bandwidth limit?
/wpe-labs:account-usage show me production traffic only
/wpe-labs:account-usage give me a summary I can send to a client
```

## What you get

For each account:

| Metric | Details |
|--------|---------|
| **Visits** | Total visits + billable visits, last 30 days |
| **Bandwidth** | GB used vs plan limit + % utilized |
| **File storage** | Current GB (live snapshot) |
| **DB storage** | Current GB (live snapshot) |
| **Environment split** | Production vs staging vs development |

Accounts at **>80% of any limit** are flagged automatically.

### Custom date ranges

Usage defaults to the last 30 days. To specify a range:

> "Show me usage for March 2025"

The API supports up to 13 months of history in 31-day windows.

## Troubleshooting

**Storage shows zero or null**
Ask Claude to "refresh storage" — it will trigger a recalculation and re-fetch.

**401 Unauthorized**
Regenerate credentials at [my.wpengine.com/api_access](https://my.wpengine.com/api_access).

**`jq` not found**
```bash
brew install jq        # macOS
apt install jq         # Ubuntu/Debian
```

**Zero visits for current period**
The default 30-day window may not align with your billing cycle. Ask Claude to fetch a specific date range instead.
