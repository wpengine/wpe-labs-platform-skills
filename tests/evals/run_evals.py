#!/usr/bin/env python3
"""
tests/evals/run_evals.py — LLM eval runner for wpe-labs skills

For each test case:
  1. Load the skill's SKILL.md as system context
  2. Call Claude with the test prompt
  3. Call Claude again as a judge to score the response against each rubric criterion
  4. Report pass/fail per criterion and overall

Usage:
  pip install anthropic
  export ANTHROPIC_API_KEY="sk-ant-..."
  python tests/evals/run_evals.py                         # run all
  python tests/evals/run_evals.py --skill monthly-report  # one skill
  python tests/evals/run_evals.py --id quarter-date-split # one case
  python tests/evals/run_evals.py --tags edge-case        # by tag
"""

import argparse
import importlib.util
import json
import os
import sys
from pathlib import Path

import anthropic

ROOT = Path(__file__).parent.parent.parent
SKILLS_DIR = ROOT / "skills"
CASES_DIR = Path(__file__).parent / "cases"

SKILL_MODEL = "claude-sonnet-4-6"
JUDGE_MODEL = "claude-haiku-4-5-20251001"


def load_skill(skill_name: str) -> str:
    skill_file = SKILLS_DIR / f"wpe-labs:{skill_name}" / "SKILL.md"
    if not skill_file.exists():
        raise FileNotFoundError(f"SKILL.md not found: {skill_file}")
    return skill_file.read_text()


def load_cases(skill_name: str) -> list[dict]:
    module_path = CASES_DIR / f"{skill_name.replace('-', '_')}.py"
    if not module_path.exists():
        raise FileNotFoundError(f"No eval cases for skill '{skill_name}': {module_path}")
    spec = importlib.util.spec_from_file_location("cases", module_path)
    mod = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(mod)
    return mod.CASES


def build_context() -> str:
    """Build optional context block from environment variables when real WPE objects are set."""
    lines = []
    if os.environ.get("WPE_ACCOUNT_NAME"):
        lines.append(f"Account name: {os.environ['WPE_ACCOUNT_NAME']}")
    if os.environ.get("WPE_ACCOUNT_ID"):
        lines.append(f"Account ID: {os.environ['WPE_ACCOUNT_ID']}")
    if os.environ.get("WPE_INSTALL_NAME"):
        lines.append(f"Install name: {os.environ['WPE_INSTALL_NAME']}")
    if os.environ.get("WPE_INSTALL_ID"):
        lines.append(f"Install ID: {os.environ['WPE_INSTALL_ID']}")
    if not lines:
        return ""
    return "\n<context>\nUse these real WP Engine objects in your response:\n" + "\n".join(lines) + "\n</context>\n"


def run_skill(client: anthropic.Anthropic, skill_md: str, prompt: str) -> str:
    """Run the skill with the given user prompt and return the assistant's response."""
    context = build_context()
    system = f"""You are Claude Code running the following skill. Follow the skill's workflow exactly.

<skill>
{skill_md}
</skill>
{context}
Do not actually execute curl commands. Instead, describe precisely which API calls you would make, in what order, with what parameters, and what the final output to the user would look like. Be specific and complete."""

    user = prompt if prompt else "Run the skill with default settings."

    response = client.messages.create(
        model=SKILL_MODEL,
        max_tokens=2048,
        system=system,
        messages=[{"role": "user", "content": user}],
    )
    return response.content[0].text


def judge_criterion(client: anthropic.Anthropic, response: str, criterion: str) -> tuple[bool, str]:
    """Use the judge model to evaluate one rubric criterion. Returns (passed, reasoning)."""
    prompt = f"""You are evaluating an AI assistant's response against a single criterion.

<response>
{response}
</response>

<criterion>
{criterion}
</criterion>

Does the response satisfy this criterion? Reply with a raw JSON object — no markdown, no code fences, no explanation outside the JSON:
{{"passed": true, "reasoning": "one sentence"}}
or
{{"passed": false, "reasoning": "one sentence"}}"""

    result = client.messages.create(
        model=JUDGE_MODEL,
        max_tokens=256,
        messages=[{"role": "user", "content": prompt}],
    )
    try:
        raw = result.content[0].text.strip()
        # Strip markdown code fence if present (```json ... ``` or ``` ... ```)
        if raw.startswith("```"):
            raw = raw.split("\n", 1)[-1]  # drop opening fence line
            raw = raw.rsplit("```", 1)[0]  # drop closing fence
        data = json.loads(raw.strip())
        return data["passed"], data["reasoning"]
    except (json.JSONDecodeError, KeyError):
        return False, f"Judge returned unparseable output: {result.content[0].text[:100]}"


def run_case(client: anthropic.Anthropic, skill_name: str, skill_md: str, case: dict) -> dict:
    """Run a single eval case. Returns result dict."""
    print(f"  [{case['id']}] prompt: {repr(case['prompt']) if case['prompt'] else '(default)'}")

    response = run_skill(client, skill_md, case["prompt"])

    results = []
    for criterion in case["rubric"]:
        passed, reasoning = judge_criterion(client, response, criterion)
        results.append({"criterion": criterion, "passed": passed, "reasoning": reasoning})
        status = "pass" if passed else "FAIL"
        print(f"    {status}  {criterion[:80]}{'...' if len(criterion) > 80 else ''}")
        if not passed:
            print(f"          → {reasoning}")

    overall = all(r["passed"] for r in results)
    return {
        "skill": skill_name,
        "case_id": case["id"],
        "tags": case.get("tags", []),
        "passed": overall,
        "criteria": results,
        "response_preview": response[:300],
    }


def main():
    parser = argparse.ArgumentParser(description="Run LLM evals for wpe-labs skills")
    parser.add_argument("--skill", help="Skill name (e.g. monthly-report, account-usage)")
    parser.add_argument("--id", help="Run only the case with this ID")
    parser.add_argument("--tags", help="Run only cases with this tag")
    parser.add_argument("--json", action="store_true", help="Output results as JSON")
    args = parser.parse_args()

    api_key = os.environ.get("ANTHROPIC_API_KEY")
    if not api_key:
        print("Error: ANTHROPIC_API_KEY environment variable not set.")
        sys.exit(1)

    client = anthropic.Anthropic(api_key=api_key)

    # Discover which skills have eval cases
    skill_names = []
    if args.skill:
        skill_names = [args.skill]
    else:
        for f in sorted(CASES_DIR.glob("*.py")):
            if not f.name.startswith("_"):
                skill_names.append(f.stem.replace("_", "-"))

    all_results = []
    total_cases = 0
    total_passed = 0

    for skill_name in skill_names:
        try:
            skill_md = load_skill(skill_name)
            cases = load_cases(skill_name)
        except FileNotFoundError as e:
            print(f"Error: {e}")
            sys.exit(1)

        # Apply filters
        if args.id:
            cases = [c for c in cases if c["id"] == args.id]
        if args.tags:
            cases = [c for c in cases if args.tags in c.get("tags", [])]

        if not cases:
            print(f"\nNo cases match filters for {skill_name}.")
            continue

        print(f"\n{'='*60}")
        print(f"Skill: wpe-labs:{skill_name}  ({len(cases)} case(s))")
        print("=" * 60)

        for case in cases:
            result = run_case(client, skill_name, skill_md, case)
            all_results.append(result)
            total_cases += 1
            if result["passed"]:
                total_passed += 1

    # Summary
    total_failed = total_cases - total_passed
    print(f"\n{'='*60}")
    print(f"Results: {total_passed}/{total_cases} cases passed  ({total_failed} failed)")
    print("=" * 60)

    if args.json:
        print(json.dumps(all_results, indent=2))

    sys.exit(0 if total_failed == 0 else 1)


if __name__ == "__main__":
    main()
