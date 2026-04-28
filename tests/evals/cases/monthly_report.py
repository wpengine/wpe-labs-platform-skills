"""
Eval test cases for wpe-labs:monthly-report.

Each case is a dict with:
  prompt   — what the user types after /wpe-labs:monthly-report
  rubric   — list of criteria the judge checks (all must pass)
  tags     — labels for filtering/reporting
"""

CASES = [
    {
        "id": "default-invocation",
        "prompt": "",
        "tags": ["happy-path"],
        "rubric": [
            "The response includes a Markdown heading with 'Usage Report' and a month/year.",
            "The response includes at least one table with columns for Visits, Bandwidth, and Storage.",
            "The response includes a 'Period:' line showing a date range.",
            "The response includes a 'Generated:' line with today's date or similar.",
        ],
    },
    {
        "id": "specific-month",
        "prompt": "March 2025",
        "tags": ["date-range"],
        "rubric": [
            "The response references the period 2025-03-01 to 2025-03-31 (or 'March 2025').",
            "The response does NOT use a different month as the primary period.",
            "The response includes a usage table per account.",
        ],
    },
    {
        "id": "quarter-date-split",
        "prompt": "Q1 2025",
        "tags": ["date-range", "edge-case"],
        "rubric": [
            "The response explains or implies that Q1 is split into monthly windows (Jan, Feb, Mar) because the API has a 31-day limit.",
            "The response covers January, February, and March 2025.",
            "The response shows aggregated or per-month totals, not a single 90-day query.",
        ],
    },
    {
        "id": "threshold-flagging",
        "prompt": "show only accounts over 80% of any limit",
        "tags": ["filtering", "threshold"],
        "rubric": [
            "The response filters to show only accounts that are at or above 80% utilization on at least one metric.",
            "The response does not show accounts that are well within limits as primary results.",
            "Flagged accounts are clearly marked (e.g. with ⚠️, 🔴, or text like 'Approaching limit').",
        ],
    },
    {
        "id": "client-recipient",
        "prompt": "last month prepared for Acme Corp",
        "tags": ["formatting"],
        "rubric": [
            "The response includes 'Prepared for: Acme Corp' or similar near the top.",
            "The response uses the previous calendar month as the reporting period.",
            "The report is formatted cleanly enough to send to a client (no raw JSON, no debug output).",
        ],
    },
    {
        "id": "environment-breakdown",
        "prompt": "include production vs staging breakdown",
        "tags": ["detail"],
        "rubric": [
            "The response includes a table or section showing production, staging, and development metrics separately.",
            "Both visits and bandwidth are broken out by environment.",
        ],
    },
    {
        "id": "stale-storage-note",
        "prompt": "",
        "tags": ["edge-case"],
        "rubric": [
            "If storage shows 0 GB or null, the response notes that storage data may be stale and offers to trigger a refresh.",
            "The response does not silently show 0 GB as if it were the correct value.",
        ],
    },
]
