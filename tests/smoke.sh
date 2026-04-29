#!/bin/bash
# tests/smoke.sh — read-only API smoke tests against live WP Engine API
#
# Requires:
#   export WPE_USERNAME="your-api-username"
#   export WPE_PASSWORD="your-api-password"
#
# Run: bash tests/smoke.sh

set -euo pipefail

BASE="https://api.wpengineapi.com/v1"
UA="wpe-labs-skills/smoke-test"
ERRORS=0

pass() { echo "  ok  $1"; }
fail() { echo "  FAIL $1"; ERRORS=$((ERRORS + 1)); }

# ── Preflight ──────────────────────────────────────────────────────────────────

if [ -z "${WPE_USERNAME:-}" ] || [ -z "${WPE_PASSWORD:-}" ]; then
  echo "Error: WPE_USERNAME and WPE_PASSWORD must be set."
  echo "  export WPE_USERNAME=\"your-api-username\""
  echo "  export WPE_PASSWORD=\"your-api-password\""
  exit 1
fi

for cmd in curl jq; do
  if ! command -v "$cmd" &>/dev/null; then
    echo "Error: '$cmd' is required but not installed."
    exit 1
  fi
done

wpe_get() {
  curl -s -w "\n%{http_code}" \
    -u "$WPE_USERNAME:$WPE_PASSWORD" \
    -H "User-Agent: $UA" \
    "$BASE/$1"
}

# Check status + HTTP code, assert JSON satisfies jq expression
check() {
  local label="$1"
  local path="$2"
  local jq_check="$3"

  response=$(wpe_get "$path")
  http_code=$(echo "$response" | tail -1)
  body=$(echo "$response" | sed '$d')

  if [ "$http_code" != "200" ]; then
    fail "$label — HTTP $http_code"
    return
  fi

  if echo "$body" | jq -e "$jq_check" >/dev/null 2>&1; then
    pass "$label"
  else
    fail "$label — response missing expected field ($jq_check)"
  fi
}

# Like check(), but treats 404 as a skip instead of a failure.
# Use for endpoints that may not be available on all install network types.
check_or_skip() {
  local label="$1"
  local path="$2"
  local jq_check="$3"

  response=$(wpe_get "$path")
  http_code=$(echo "$response" | tail -1)
  body=$(echo "$response" | sed '$d')

  if [ "$http_code" = "404" ]; then
    echo "  skip  $label — 404 (not available for this install)"
    return
  fi

  if [ "$http_code" != "200" ]; then
    fail "$label — HTTP $http_code"
    return
  fi

  if echo "$body" | jq -e "$jq_check" >/dev/null 2>&1; then
    pass "$label"
  else
    fail "$label — response missing expected field ($jq_check)"
  fi
}

# ── Discover account and install IDs ──────────────────────────────────────────

echo ""
echo "Discovering accounts..."

ACCOUNTS_RESP=$(wpe_get "accounts")
ACCOUNTS_CODE=$(echo "$ACCOUNTS_RESP" | tail -1)
ACCOUNTS_BODY=$(echo "$ACCOUNTS_RESP" | sed '$d')

if [ "$ACCOUNTS_CODE" != "200" ]; then
  echo "Error: GET /accounts returned HTTP $ACCOUNTS_CODE — check credentials."
  exit 1
fi

ACCOUNT_ID=$(echo "$ACCOUNTS_BODY" | jq -r '.results[0].id // empty')
ACCOUNT_NAME=$(echo "$ACCOUNTS_BODY" | jq -r '.results[0].name // empty')

if [ -z "$ACCOUNT_ID" ]; then
  echo "Error: No accounts found. Check that your credentials have account access."
  exit 1
fi

echo "  Using account: $ACCOUNT_NAME ($ACCOUNT_ID)"
echo "  → export WPE_ACCOUNT_ID=$ACCOUNT_ID"
echo "  → export WPE_ACCOUNT_NAME=$ACCOUNT_NAME"

# Discover an install ID for install-scoped tests
INSTALLS_RESP=$(wpe_get "installs?limit=1")
INSTALL_ID=$(echo "$INSTALLS_RESP" | sed '$d' | jq -r '.results[0].id // empty')
INSTALL_NAME=$(echo "$INSTALLS_RESP" | sed '$d' | jq -r '.results[0].name // empty')

if [ -n "$INSTALL_ID" ]; then
  echo "  Using install: $INSTALL_NAME ($INSTALL_ID)"
  echo "  → export WPE_INSTALL_ID=$INSTALL_ID"
  echo "  → export WPE_INSTALL_NAME=$INSTALL_NAME"
fi

# ── wpe-labs:account-usage ────────────────────────────────────────────────────

echo ""
echo "wpe-labs:account-usage"
echo "----------------------"

check "GET /accounts returns results array" \
  "accounts" \
  '.results | type == "array"'

check "GET /accounts/{id}/usage/summary returns visit_count" \
  "accounts/$ACCOUNT_ID/usage/summary" \
  '.visit_count != null'

check "GET /accounts/{id}/limits returns a limits object" \
  "accounts/$ACCOUNT_ID/limits" \
  'type == "object" and (.bandwidth != null or .storage != null)'

check "GET /accounts/{id}/usage/insights returns visit_count.environment_types" \
  "accounts/$ACCOUNT_ID/usage/insights" \
  '.visit_count.environment_types != null'

# ── wpe-labs:installs ─────────────────────────────────────────────────────────

echo ""
echo "wpe-labs:installs"
echo "-----------------"

check "GET /sites returns results array" \
  "sites" \
  '.results | type == "array"'

check "GET /installs returns results array" \
  "installs" \
  '.results | type == "array"'

if [ -n "$INSTALL_ID" ]; then
  check "GET /installs/{id} returns environment field" \
    "installs/$INSTALL_ID" \
    '.environment != null'
else
  echo "  skip  GET /installs/{id} — no installs found"
fi

# ── wpe-labs:domains ──────────────────────────────────────────────────────────

echo ""
echo "wpe-labs:domains"
echo "----------------"

if [ -n "$INSTALL_ID" ]; then
  check "GET /installs/{id}/domains returns results array" \
    "installs/$INSTALL_ID/domains" \
    '.results | type == "array"'

  check_or_skip "GET /installs/{id}/ssl_certificates returns results array" \
    "installs/$INSTALL_ID/ssl_certificates" \
    '.results | type == "array"'
else
  echo "  skip  domains checks — no installs found"
fi

# ── wpe-labs:users ────────────────────────────────────────────────────────────

echo ""
echo "wpe-labs:users"
echo "--------------"

check "GET /accounts/{id}/account_users returns results array" \
  "accounts/$ACCOUNT_ID/account_users" \
  '.results | type == "array"'

# ── wpe-labs:backups ──────────────────────────────────────────────────────────
# No read-only GET /backups list endpoint — skip list check.
# We do not create a backup in smoke tests (write op with side effects).

echo ""
echo "wpe-labs:backups"
echo "----------------"
echo "  skip  no read-only list endpoint (backup creation is a write op)"

# ── wpe-labs:cache ────────────────────────────────────────────────────────────
# No read-only endpoint — cache purge is write-only.

echo ""
echo "wpe-labs:cache"
echo "--------------"
echo "  skip  no read-only endpoint (purge is write-only)"

# ── wpe-labs:monthly-report ───────────────────────────────────────────────────

echo ""
echo "wpe-labs:monthly-report"
echo "-----------------------"

# Re-uses account-usage + installs endpoints; just verify site count endpoint
check "GET /sites?account_id={id} returns count field" \
  "sites?account_id=$ACCOUNT_ID&limit=1" \
  '.count != null'

# ── Result ─────────────────────────────────────────────────────────────────────

echo ""
if [ "$ERRORS" -eq 0 ]; then
  echo "All smoke tests passed."
  exit 0
else
  echo "$ERRORS smoke test(s) failed."
  exit 1
fi
