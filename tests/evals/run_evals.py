#!/usr/bin/env python3
"""
tests/evals/run_evals.py — LLM eval runner for wpe-labs skills

For each test case:
  1. Load the skill's SKILL.md as system context
  2. Call Claude with the test prompt (skill executor)
  3. Call Claude once per case to judge ALL rubric criteria in one batch
  4. Report pass/fail per criterion and overall

Usage:
  pip install anthropic
  export ANTHROPIC_API_KEY="sk-ant-..."
  python tests/evals/run_evals.py                           # run all, print results
  python tests/evals/run_evals.py --output results.json     # write JSON to file
  python tests/evals/run_evals.py --skill monthly-report    # one skill
  python tests/evals/run_evals.py --id quarter-date-split   # one case
  python tests/evals/run_evals.py --tags edge-case          # by tag
"""

import argparse
import asyncio
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
    """Inject real WPE object names/IDs when available."""
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


def expand_prompt(prompt: str) -> str:
    """Substitute {VAR} placeholders in prompts with real env var values."""
    for key in ["WPE_ACCOUNT_NAME", "WPE_ACCOUNT_ID", "WPE_INSTALL_NAME", "WPE_INSTALL_ID"]:
        val = os.environ.get(key, "")
        if val:
            prompt = prompt.replace(f"{{{key}}}", val)
    return prompt


async def run_skill(client: anthropic.AsyncAnthropic, skill_md: str, prompt: str) -> str:
    context = build_context()
    system = f"""You are Claude Code running the following skill. Follow the skill's workflow exactly.

<skill>
{skill_md}
</skill>
{context}
Do not actually execute curl commands. Instead, describe precisely which API calls you would make, in what order, with what parameters, and what the final output to the user would look like. Be specific and complete.

For destructive operation guards, demonstrate the guard by stating the actual warning text and confirmation requirement — do not just say that a guard exists."""

    response = await client.messages.create(
        model=SKILL_MODEL,
        max_tokens=2048,
        system=system,
        messages=[{"role": "user", "content": prompt if prompt else "Run the skill with default settings."}],
    )
    return response.content[0].text


async def judge_all(client: anthropic.AsyncAnthropic, response: str, criteria: list[str]) -> list[dict]:
    """Evaluate all rubric criteria in a single judge call. Returns list of {criterion, passed, reasoning}."""
    numbered = "\n".join(f"{i+1}. {c}" for i, c in enumerate(criteria))
    prompt = f"""You are evaluating an AI assistant's response against a rubric. Score each criterion.

<response>
{response}
</response>

<criteria>
{numbered}
</criteria>

Reply with a raw JSON array — no markdown, no code fences — with one object per criterion in the same order:
[
  {{"criterion": "...", "passed": true, "reasoning": "one sentence"}},
  ...
]"""

    result = await client.messages.create(
        model=JUDGE_MODEL,
        max_tokens=1024,
        messages=[{"role": "user", "content": prompt}],
    )
    raw = result.content[0].text.strip()
    if raw.startswith("```"):
        raw = raw.split("\n", 1)[-1].rsplit("```", 1)[0]
    return json.loads(raw.strip())


async def run_case(client: anthropic.AsyncAnthropic, skill_name: str, skill_md: str, case: dict) -> dict:
    """Run a single eval case: one skill call + one batched judge call."""
    prompt = expand_prompt(case["prompt"])
    response = await run_skill(client, skill_md, prompt)
    judgements = await judge_all(client, response, case["rubric"])

    criteria_results = []
    for judgement in judgements:
        criteria_results.append({
            "criterion": judgement.get("criterion", ""),
            "passed": judgement.get("passed", False),
            "reasoning": judgement.get("reasoning", ""),
        })

    return {
        "skill": skill_name,
        "case_id": case["id"],
        "tags": case.get("tags", []),
        "passed": all(r["passed"] for r in criteria_results),
        "criteria": criteria_results,
    }


async def run_skill_cases(
    client: anthropic.AsyncAnthropic,
    skill_name: str,
    cases: list[dict],
) -> list[dict]:
    """Run all cases for a skill concurrently."""
    skill_md = load_skill(skill_name)
    tasks = [run_case(client, skill_name, skill_md, case) for case in cases]
    return await asyncio.gather(*tasks)


def print_results(all_results: list[dict]) -> tuple[int, int]:
    """Print results grouped by skill. Returns (total, passed)."""
    by_skill: dict[str, list[dict]] = {}
    for r in all_results:
        by_skill.setdefault(r["skill"], []).append(r)

    total = passed = 0
    for skill_name, results in by_skill.items():
        print(f"\n{'='*60}")
        print(f"Skill: wpe-labs:{skill_name}  ({len(results)} case(s))")
        print("=" * 60)
        for result in results:
            prompt_label = next(
                (c["prompt"] for c in [] if c.get("id") == result["case_id"]), ""
            )
            print(f"  [{result['case_id']}]")
            for cr in result["criteria"]:
                status = "pass" if cr["passed"] else "FAIL"
                label = cr["criterion"][:75] + ("..." if len(cr["criterion"]) > 75 else "")
                print(f"    {status}  {label}")
                if not cr["passed"]:
                    print(f"          → {cr['reasoning']}")
            total += 1
            if result["passed"]:
                passed += 1

    return total, passed


async def main_async(args: argparse.Namespace) -> int:
    api_key = os.environ.get("ANTHROPIC_API_KEY")
    if not api_key:
        print("Error: ANTHROPIC_API_KEY environment variable not set.")
        return 1

    async with anthropic.AsyncAnthropic(api_key=api_key) as client:
        # Discover skills
        if args.skill:
            skill_names = [args.skill]
        else:
            skill_names = sorted(
                f.stem.replace("_", "-")
                for f in CASES_DIR.glob("*.py")
                if not f.name.startswith("_")
            )

        all_results: list[dict] = []

        for skill_name in skill_names:
            try:
                cases = load_cases(skill_name)
            except FileNotFoundError as e:
                print(f"Error: {e}")
                return 1

            # Apply filters
            if args.id:
                cases = [c for c in cases if c["id"] == args.id]
            if args.tags:
                cases = [c for c in cases if args.tags in c.get("tags", [])]

            if not cases:
                print(f"\nNo cases match filters for {skill_name}.")
                continue

            print(f"Running wpe-labs:{skill_name} ({len(cases)} case(s))...", flush=True)
            results = await run_skill_cases(client, skill_name, cases)
            all_results.extend(results)

        total, passed = print_results(all_results)
        failed = total - passed

        print(f"\n{'='*60}")
        print(f"Results: {passed}/{total} cases passed  ({failed} failed)")
        print("=" * 60)

        if args.output:
            out_path = Path(args.output)
            out_path.write_text(json.dumps(all_results, indent=2))
            print(f"\nJSON results written to: {out_path}")

        return 0 if failed == 0 else 1


def main():
    parser = argparse.ArgumentParser(description="Run LLM evals for wpe-labs skills")
    parser.add_argument("--skill", help="Skill name (e.g. monthly-report)")
    parser.add_argument("--id", help="Run only the case with this ID")
    parser.add_argument("--tags", help="Run only cases with this tag")
    parser.add_argument("--output", help="Write JSON results to this file")
    args = parser.parse_args()
    sys.exit(asyncio.run(main_async(args)))


if __name__ == "__main__":
    main()
