"""
Eval test cases for wpe-labs:account-usage.
"""

CASES = [
    {
        "id": "default-invocation",
        "prompt": "",
        "tags": ["happy-path"],
        "rubric": [
            "The response describes or shows usage data for at least one account — concrete values or a well-structured template with labelled placeholders are both acceptable.",
            "The response includes visits, bandwidth, and storage metrics.",
            "The response compares metrics against plan limits or notes when limits are unavailable.",
        ],
    },
    {
        "id": "bandwidth-approaching-limit",
        "prompt": "which accounts are closest to their bandwidth limit?",
        "tags": ["filtering"],
        "rubric": [
            "The response ranks or highlights accounts by bandwidth utilization percentage.",
            "The response shows bandwidth used vs limit for each account mentioned.",
        ],
    },
    {
        "id": "date-range-natural-language",
        "prompt": "show me usage for March 2025",
        "tags": ["date-range"],
        "rubric": [
            "The response references March 2025 or the date range 2025-03-01 to 2025-03-31.",
            "The response does not default to the last 30 days when a specific month was requested.",
        ],
    },
    {
        "id": "production-only",
        "prompt": "show me production traffic only",
        "tags": ["filtering"],
        "rubric": [
            "The response uses the insights endpoint or environment breakdown to show production-only metrics.",
            "The response distinguishes production from staging and development.",
        ],
    },
    {
        "id": "stale-storage-refresh",
        "prompt": "storage shows zero — please refresh",
        "tags": ["edge-case"],
        "rubric": [
            "The response triggers or offers to trigger the refresh_disk_usage endpoint.",
            "The response explains that storage data is refreshed asynchronously.",
        ],
    },
    {
        "id": "single-account-detail",
        "prompt": "show me the details for my account",
        "tags": ["happy-path"],
        "rubric": [
            "The response calls GET /accounts/{id} for a specific account, not just GET /accounts.",
            "The response identifies the account by name or uses the known account ID from context.",
        ],
    },
    {
        "id": "daily-granular-usage",
        "prompt": "show me daily usage breakdown for March 2025",
        "tags": ["date-range"],
        "rubric": [
            "The response uses GET /accounts/{id}/usage (not /usage/summary) to get daily granular data.",
            "The response includes first_date and last_date parameters for March 2025.",
            "The response explains that this returns per-environment daily metrics, not a rolled-up summary.",
        ],
    },
]
