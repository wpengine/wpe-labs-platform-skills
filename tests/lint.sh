#!/bin/bash
# tests/lint.sh — static validation for all skills and commands
# No credentials required. Run: bash tests/lint.sh

set -euo pipefail

ROOT="$(cd "$(dirname "$0")/.." && pwd)"
ERRORS=0

pass() { echo "  ok  $1"; }
fail() { echo "  FAIL $1"; ERRORS=$((ERRORS + 1)); }

# ── Skill files ────────────────────────────────────────────────────────────────

echo ""
echo "Skills"
echo "------"

SKILL_NAMES=()

for skill_dir in "$ROOT/skills"/*/; do
  skill_name=$(basename "$skill_dir")
  skill_file="$skill_dir/SKILL.md"
  SKILL_NAMES+=("$skill_name")

  # SKILL.md exists
  if [ ! -f "$skill_file" ]; then
    fail "$skill_name — SKILL.md missing"
    continue
  fi

  # Required frontmatter fields
  for field in name description; do
    if grep -q "^${field}:" "$skill_file"; then
      pass "$skill_name — frontmatter.$field"
    else
      fail "$skill_name — frontmatter.$field missing"
    fi
  done

  # Required sections
  for section in objective workflow api_reference success_criteria; do
    if grep -q "<${section}>" "$skill_file"; then
      pass "$skill_name — <$section>"
    else
      fail "$skill_name — <$section> section missing"
    fi
  done

  # User-Agent coverage: every curl call must have the matching header.
  # Match both standalone `curl -` and variable-assignment `$(curl -` forms.
  CURL_COUNT=$(grep -cE '(^\s*curl -|\$\(curl -)' "$skill_file" || true)
  UA_COUNT=$(grep -c "User-Agent: ai-code-skill/wpe-labs:" "$skill_file" || true)

  if [ "$CURL_COUNT" -eq 0 ]; then
    fail "$skill_name — no curl calls found (skill has no examples?)"
  elif [ "$CURL_COUNT" -eq "$UA_COUNT" ]; then
    pass "$skill_name — User-Agent on all $CURL_COUNT curl call(s)"
  else
    fail "$skill_name — $CURL_COUNT curl call(s) but $UA_COUNT User-Agent header(s)"
  fi

  # User-Agent value uses the short skill name (strip wpe-labs: prefix from dir name)
  short_name="${skill_name#wpe-labs:}"
  expected_ua="ai-code-skill/wpe-labs:${short_name}"
  if grep -q "User-Agent: ${expected_ua}" "$skill_file"; then
    pass "$skill_name — User-Agent value correct"
  else
    fail "$skill_name — User-Agent value should be '${expected_ua}'"
  fi
done

# ── Command files ──────────────────────────────────────────────────────────────

echo ""
echo "Commands"
echo "--------"

for cmd_file in "$ROOT/commands"/*.md; do
  cmd_name=$(basename "$cmd_file" .md)

  # Required frontmatter fields
  for field in description argument-hint allowed-tools; do
    if grep -q "^${field}:" "$cmd_file"; then
      pass "$cmd_name — $field"
    else
      fail "$cmd_name — $field missing"
    fi
  done

  # Referenced skill must exist
  skill_ref=$(grep 'allowed-tools:' "$cmd_file" | grep -o 'Skill([^)]*)' | sed 's/Skill(\(.*\))/\1/' || true)
  if [ -z "$skill_ref" ]; then
    fail "$cmd_name — no Skill() reference in allowed-tools"
  elif [ -d "$ROOT/skills/$skill_ref" ]; then
    pass "$cmd_name — skill '$skill_ref' exists"
  else
    fail "$cmd_name — references non-existent skill '$skill_ref'"
  fi
done

# ── install.sh coverage ────────────────────────────────────────────────────────

echo ""
echo "install.sh"
echo "----------"

for skill_name in "${SKILL_NAMES[@]}"; do
  if grep -q "\"${skill_name}\"" "$ROOT/install.sh"; then
    pass "$skill_name listed in install.sh"
  else
    fail "$skill_name NOT listed in install.sh"
  fi
done

# Every skill in install.sh must have a SKILL.md
while IFS= read -r line; do
  if [[ "$line" =~ \"(wpe-labs:[^\"]+)\" ]]; then
    listed="${BASH_REMATCH[1]}"
    if [ -f "$ROOT/skills/$listed/SKILL.md" ]; then
      pass "install.sh entry '$listed' has SKILL.md"
    else
      fail "install.sh lists '$listed' but skills/$listed/SKILL.md is missing"
    fi
  fi
done < "$ROOT/install.sh"

# ── Result ─────────────────────────────────────────────────────────────────────

echo ""
if [ "$ERRORS" -eq 0 ]; then
  echo "All checks passed."
  exit 0
else
  echo "$ERRORS check(s) failed."
  exit 1
fi
