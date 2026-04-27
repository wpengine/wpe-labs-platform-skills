#!/bin/bash
set -e

BASE_URL="https://raw.githubusercontent.com/wpengine/labs-usage-skill/main"
SKILLS_DIR="$HOME/.claude/skills/wpe-labs:account-usage"
COMMANDS_DIR="$HOME/.claude/commands"

# Check dependencies
for cmd in curl jq; do
  if ! command -v $cmd &>/dev/null; then
    echo "Error: '$cmd' is required but not installed."
    [ "$cmd" = "jq" ] && echo "  Install with: brew install jq (macOS) or apt install jq (Linux)"
    exit 1
  fi
done

echo "Installing wpe-labs:account-usage..."

mkdir -p "$SKILLS_DIR" "$COMMANDS_DIR"

curl -fsSL "$BASE_URL/skills/wpe-labs:account-usage/SKILL.md" -o "$SKILLS_DIR/SKILL.md"
curl -fsSL "$BASE_URL/commands/wpe-labs:account-usage.md"     -o "$COMMANDS_DIR/wpe-labs:account-usage.md"

echo ""
echo "✓ Installed to ~/.claude/skills/wpe-labs:account-usage/"
echo ""
echo "Next: set your WP Engine API credentials"
echo ""
echo "  export WPE_USERNAME=\"your-api-username\""
echo "  export WPE_PASSWORD=\"your-api-password\""
echo ""
echo "Get them at: https://my.wpengine.com/api_access"
echo ""
echo "Then in Claude Code, run: /wpe-labs:account-usage"
