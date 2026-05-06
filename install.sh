#!/bin/bash
set -e

BASE_URL="https://raw.githubusercontent.com/wpengine/labs-usage-skill/main"
SKILLS_DIR="$HOME/.claude/skills"
COMMANDS_DIR="$HOME/.claude/commands"

SKILLS=(
  "wpe-labs:account-usage"
  "wpe-labs:installs"
  "wpe-labs:domains"
  "wpe-labs:backups"
  "wpe-labs:users"
  "wpe-labs:cache"
  "wpe-labs:monthly-report"
  "wpe-labs:offload"
)

# Check dependencies
for cmd in curl jq; do
  if ! command -v $cmd &>/dev/null; then
    echo "Error: '$cmd' is required but not installed."
    [ "$cmd" = "jq" ] && echo "  Install with: brew install jq (macOS) or apt install jq (Linux)"
    exit 1
  fi
done

mkdir -p "$COMMANDS_DIR"

echo "Installing WP Engine Labs skills..."
echo ""

for SKILL in "${SKILLS[@]}"; do
  mkdir -p "$SKILLS_DIR/$SKILL"
  curl -fsSL "$BASE_URL/skills/$SKILL/SKILL.md"   -o "$SKILLS_DIR/$SKILL/SKILL.md"
  curl -fsSL "$BASE_URL/commands/$SKILL.md"        -o "$COMMANDS_DIR/$SKILL.md"
  echo "  ✓ $SKILL"
done

echo ""
echo "Installed ${#SKILLS[@]} skills to ~/.claude/skills/"
echo ""
echo "Next: set your WP Engine API credentials"
echo ""
echo "  export WPE_USERNAME=\"your-api-username\""
echo "  export WPE_PASSWORD=\"your-api-password\""
echo ""
echo "Get them at: https://my.wpengine.com/api_access"
echo ""
echo "Then in Claude Code, run any skill:"
echo ""
for SKILL in "${SKILLS[@]}"; do
  echo "  /$SKILL"
done
echo ""
