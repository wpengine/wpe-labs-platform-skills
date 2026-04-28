---
name: wpe-labs:users
description: Manage WP Engine account users — list who has access, invite new users with specific roles, update roles, and remove access. Use for onboarding/offboarding or auditing account permissions. Requires WP Engine API credentials; no local tooling needed beyond curl and jq.
---

<objective>
List and manage users on WP Engine accounts. Covers the full access lifecycle: auditing who has access and what role, inviting new users, updating roles when responsibilities change, and revoking access. Requires only curl and jq.
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
**List all users on an account:**

```bash
ACCOUNT_ID="your-account-uuid"

curl -s -u "$WPE_USERNAME:$WPE_PASSWORD" \
  -H "User-Agent: wpe-labs-skills/users" \
  "https://api.wpengineapi.com/v1/accounts/$ACCOUNT_ID/account_users" | \
  jq '[.results[] | {id, email: .user.email, first_name: .user.first_name, last_name: .user.last_name, roles}]'
```
</quick_start>

<workflow>
**Step 1: Get the account_id**

If you don't have it:

```bash
curl -s -u "$WPE_USERNAME:$WPE_PASSWORD" \
  -H "User-Agent: wpe-labs-skills/users" \
  "https://api.wpengineapi.com/v1/accounts" | \
  jq -r '.results[] | "\(.id)\t\(.name)"'
```

---

**Step 2: List users and their roles**

```bash
curl -s -u "$WPE_USERNAME:$WPE_PASSWORD" \
  -H "User-Agent: wpe-labs-skills/users" \
  "https://api.wpengineapi.com/v1/accounts/$ACCOUNT_ID/account_users" | \
  jq -r '.results[] | "\(.user.email)\t\(.roles | join(", "))"'
```

If `count > 100`, paginate with `?limit=100&offset=100`.

---

**Step 3: Invite a new user**

```bash
curl -s -u "$WPE_USERNAME:$WPE_PASSWORD" \
  -H "User-Agent: wpe-labs-skills/users" \
  -H "Content-Type: application/json" \
  -X POST "https://api.wpengineapi.com/v1/accounts/$ACCOUNT_ID/account_users" \
  -d '{
    "user": {
      "account_id": "'"$ACCOUNT_ID"'",
      "email": "newuser@example.com",
      "first_name": "Jane",
      "last_name": "Smith",
      "roles": "full"
    }
  }' | jq '{id}'
```

**Available roles** (pass as a string, not an array):
- `"owner"` — Full control including billing and account deletion
- `"full"` — All access except billing and account deletion
- `"full,billing"` — Full access plus billing management
- `"partial"` — Limited access (install-level permissions, set via `install_ids`)
- `"partial,billing"` — Partial access plus billing management

---

**Step 4: Update a user's role**

```bash
USER_ID="your-user-uuid"

curl -s -u "$WPE_USERNAME:$WPE_PASSWORD" \
  -H "User-Agent: wpe-labs-skills/users" \
  -H "Content-Type: application/json" \
  -X PATCH "https://api.wpengineapi.com/v1/accounts/$ACCOUNT_ID/account_users/$USER_ID" \
  -d '{"roles": "partial"}' | jq '.'
```

---

**Step 5: Remove a user**

> ⚠️ **GUARD — confirm before removing.**
> Removing a user immediately revokes all their access. This cannot be undone without re-inviting them.
>
> Before running DELETE, you MUST:
> 1. Look up and show the user's email address and current role
> 2. State explicitly: *"This will permanently remove [email] ([role]) from [account]. They will lose all access immediately. Confirm?"*
> 3. Wait for explicit confirmation ("yes", "confirm", "do it") — do NOT proceed on ambiguous input

```bash
curl -s -u "$WPE_USERNAME:$WPE_PASSWORD" \
  -H "User-Agent: wpe-labs-skills/users" \
  -X DELETE "https://api.wpengineapi.com/v1/accounts/$ACCOUNT_ID/account_users/$USER_ID"
```

Returns 204 No Content on success.

---

**Audit: list all users across all accounts**

```bash
# Get all account IDs first
ACCOUNTS=$(curl -s -u "$WPE_USERNAME:$WPE_PASSWORD" \
  -H "User-Agent: wpe-labs-skills/users" \
  "https://api.wpengineapi.com/v1/accounts" | jq -r '.results[] | .id')

# For each account, list users
for ACCOUNT_ID in $ACCOUNTS; do
  echo "=== Account: $ACCOUNT_ID ==="
  curl -s -u "$WPE_USERNAME:$WPE_PASSWORD" \
    -H "User-Agent: wpe-labs-skills/users" \
    "https://api.wpengineapi.com/v1/accounts/$ACCOUNT_ID/account_users" | \
    jq -r '.results[] | "\(.user.email)\t\(.roles | join(", "))"'
done
```
</workflow>

<api_reference>
**Base URL:** `https://api.wpengineapi.com/v1`
**Auth:** HTTP Basic Auth with credentials from https://my.wpengine.com/api_access

| Endpoint | Purpose |
|----------|---------|
| `GET /accounts/{id}/account_users` | List users on an account |
| `POST /accounts/{id}/account_users` | Invite a new user with role |
| `GET /accounts/{id}/account_users/{user_id}` | Get a specific user |
| `PATCH /accounts/{id}/account_users/{user_id}` | Update user role |
| `DELETE /accounts/{id}/account_users/{user_id}` | Remove user from account |

**Roles:** `owner`, `full`, `partial`, `billing`

**User fields:** `id`, `user.email`, `user.first_name`, `user.last_name`, `roles` (array)
</api_reference>

<troubleshooting>
**Invite returns 422** — Email address must be valid. The user will receive an invitation email; they must accept before appearing as active.

**Can't remove the last owner** — WP Engine requires at least one owner on every account. Assign another owner first.

**User shows up but can't access installs** — `partial` role requires install-level permissions configured separately in Portal. The API manages account-level roles only.

**429 Too Many Requests** — Add a short delay between requests when iterating over many accounts for an audit.

**Credentials fail** — Regenerate at https://my.wpengine.com/api_access. Note: these are separate from your portal login credentials.
</troubleshooting>

<success_criteria>
- All users listed per account with email and role clearly shown
- New user invited with correct role when requested
- Role updated and confirmed
- User removed when requested (after confirming intent)
- Cross-account audit completed when asked
</success_criteria>
