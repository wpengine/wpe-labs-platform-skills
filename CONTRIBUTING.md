# Contributing to WP Engine Labs Platform Skills

## Before you start

- All changes to `main` require a pull request
- The `lint` CI check must pass before a PR can be merged
- At least one approving review is required

---

## Adding a new skill

### File structure

Every skill is two files:

```
skills/wpe-labs:{name}/
  SKILL.md                    ← skill definition (the brain)
commands/
  wpe-labs:{name}.md          ← command registration
```

Add both to the `SKILLS` array in `install.sh` so the one-liner installer picks it up.

### SKILL.md structure

Required frontmatter:

```markdown
---
name: wpe-labs:{name}
description: {one-line description used by Claude to decide when to invoke this skill}
---
```

Required sections (enforced by `tests/lint.sh`):

```
<objective>   — what the skill does and who it's for
<workflow>    — step-by-step with curl examples
<api_reference> — endpoint table with field docs
<success_criteria> — what a correct execution looks like
<troubleshooting> — common failures and fixes (optional but encouraged)
```

### Command file structure

```markdown
---
description: {one-line shown in /command list}
argument-hint: [natural language hint]
allowed-tools: Skill(wpe-labs:{name})
---

Invoke the wpe-labs:{name} skill for: $ARGUMENTS
```

---

## Conventions

### User-Agent

Every `curl` call must include:

```bash
-H "User-Agent: wpe-labs-skills/{skill-name}"
```

Where `{skill-name}` is the short name without the `wpe-labs:` prefix (e.g. `account-usage`, not `wpe-labs:account-usage`). This is how WP Engine identifies Claude Code traffic in API access logs.

The lint check enforces this — every `curl` invocation in a SKILL.md must have a matching `User-Agent` header.

### Name→ID resolution

Skills accept names from users and resolve them to IDs via API lookup. Never assume the user knows or will provide a UUID.

Always document the lookup pattern:

```bash
# Resolve install name → ID
curl -s -u "$WPE_USERNAME:$WPE_PASSWORD" \
  -H "User-Agent: wpe-labs-skills/{name}" \
  "https://api.wpengineapi.com/v1/installs" | \
  jq -r '.results[] | select(.name | test("mysite")) | "\(.id)\t\(.name)\t\(.environment)"'
```

If multiple resources match a name (e.g. production and staging installs for the same site), always ask the user to confirm before proceeding.

### Destructive operation guards

Any operation that is irreversible or overwrites data must follow this pattern before executing:

1. **Identify** — resolve names to IDs, fetch the resource, show the user what will be affected
2. **State consequences** — explicitly say what will happen and that it cannot be undone
3. **Require confirmation** — wait for explicit confirmation; "yes" or "ok" is not enough for the most destructive operations (site/install deletion requires typing the resource name)

Mark destructive operations clearly in the SKILL.md with a `> ⚠️ GUARD` or `> 🔴 GUARD` blockquote before the curl example.

---

## Running the tests

### Layer 1 — Static lint (required, runs in CI)

```bash
bash tests/lint.sh
```

Checks every SKILL.md for:
- Required frontmatter fields (`name`, `description`)
- Required XML sections
- User-Agent header on every `curl` call
- Correct User-Agent value format
- Every command file references a skill that exists
- Every skill in `install.sh` has a `SKILL.md`
- `.env` is gitignored and not tracked by git
- No hardcoded Anthropic API keys in tracked files

This runs automatically on every push and every PR via GitHub Actions. The PR cannot be merged if it fails.

### Layer 2 — API smoke tests (run before merging)

```bash
bash tests/smoke.sh
```

Requires `WPE_USERNAME` and `WPE_PASSWORD`. Hits read-only endpoints for each skill against the live API and asserts HTTP 200 + expected JSON shape. Prints `export` hints for the object IDs it discovers — paste these into your `.env`.

### Layer 3 — LLM evals (run when adding or changing skills)

```bash
source .env
source .venv/bin/activate
python tests/evals/run_evals.py                          # all cases
python tests/evals/run_evals.py --skill monthly-report   # one skill
python tests/evals/run_evals.py --tags guard             # by tag
python tests/evals/run_evals.py --output results.json    # save output
```

Requires `ANTHROPIC_API_KEY`. Runs each skill with test prompts via the Claude API and uses a second Claude call as judge to score responses against a rubric.

When adding a new skill, add eval cases in `tests/evals/cases/{skill_name}.py`. Each case needs:
- `id` — unique string
- `prompt` — what the user types (supports `{WPE_INSTALL_NAME}` and `{WPE_ACCOUNT_NAME}` substitution)
- `tags` — list of labels (`happy-path`, `guard`, `name-resolution`, `edge-case`, etc.)
- `rubric` — list of criteria the judge checks; each must pass for the case to pass

Cover at minimum: one happy-path case, any guard behaviors, any name→ID resolution steps.

---

## Environment setup

```bash
cp .env.example .env
# Fill in your values
source .env

python -m venv .venv
source .venv/bin/activate
pip install -r tests/evals/requirements.txt
```

Run `bash tests/smoke.sh` once to discover your real account and install IDs — it prints `export` lines you can paste directly into `.env`.

---

## PR checklist

- [ ] `bash tests/lint.sh` passes
- [ ] New skill added to `install.sh`
- [ ] User-Agent header on every `curl` call
- [ ] Name→ID resolution documented for any install/domain/user/account lookups
- [ ] Destructive operations have guards
- [ ] Eval cases added in `tests/evals/cases/`
- [ ] `bash tests/smoke.sh` passes (if touching API calls)
