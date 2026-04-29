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
  UA_COUNT=$(grep -c "User-Agent: wpe-labs-skills/" "$skill_file" || true)

  if [ "$CURL_COUNT" -eq 0 ]; then
    fail "$skill_name — no curl calls found (skill has no examples?)"
  elif [ "$CURL_COUNT" -eq "$UA_COUNT" ]; then
    pass "$skill_name — User-Agent on all $CURL_COUNT curl call(s)"
  else
    fail "$skill_name — $CURL_COUNT curl call(s) but $UA_COUNT User-Agent header(s)"
  fi

  # User-Agent value: wpe-labs-skills/{short-name}
  short_name="${skill_name#wpe-labs:}"
  expected_ua="wpe-labs-skills/${short_name}"
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

# ── Secret hygiene ────────────────────────────────────────────────────────────

echo ""
echo "Secret hygiene"
echo "--------------"

# .gitignore must exist
if [ ! -f "$ROOT/.gitignore" ]; then
  fail ".gitignore is missing"
else
  pass ".gitignore exists"

  # .env must be gitignored
  if grep -q '^\s*\.env\s*$' "$ROOT/.gitignore"; then
    pass ".env is gitignored"
  else
    fail ".env is NOT in .gitignore — credentials could be committed"
  fi

  # .envrc must be gitignored
  if grep -q '^\s*\.envrc\s*$' "$ROOT/.gitignore"; then
    pass ".envrc is gitignored"
  else
    fail ".envrc is NOT in .gitignore"
  fi
fi

# .env.example must exist (documents required vars without leaking values)
if [ -f "$ROOT/.env.example" ]; then
  pass ".env.example exists"
else
  fail ".env.example is missing — contributors won't know what vars to set"
fi

# .env must not be committed (check git if inside a repo)
if git -C "$ROOT" rev-parse --git-dir >/dev/null 2>&1; then
  if git -C "$ROOT" ls-files --error-unmatch .env >/dev/null 2>&1; then
    fail ".env is tracked by git — credentials may be committed"
  else
    pass ".env is not tracked by git"
  fi
fi

# No raw credential patterns in committed files.
# Checks for Anthropic key prefix (sk-ant-api0) which is distinct enough to
# never appear in docs/examples. WPE credentials have no detectable prefix so
# rely on .env gitignore + GitHub secret scanning for those.
if git -C "$ROOT" rev-parse --git-dir >/dev/null 2>&1; then
  ANT_KEY_PATTERN="sk-ant""-api0"
  CRED_HITS=$(git -C "$ROOT" grep -l \
    -e "$ANT_KEY_PATTERN" \
    -- ':!.env.example' ':!tests/lint.sh' 2>/dev/null || true)
  if [ -z "$CRED_HITS" ]; then
    pass "no hardcoded Anthropic API keys found in tracked files"
  else
    fail "Anthropic API key found hardcoded in: $CRED_HITS"
  fi
fi

# ── Result ─────────────────────────────────────────────────────────────────────

echo ""
if [ "$ERRORS" -eq 0 ]; then
  echo "All checks passed."
  exit 0
else
  echo "$ERRORS check(s) failed."
  exit 1
fi
