"""
Eval test cases for wpe-labs:cache.
"""

CASES = [
    {
        "id": "purge-all",
        "prompt": "clear all cache for mysite production",
        "tags": ["happy-path"],
        "rubric": [
            "The response identifies the target install — either by resolving the name via GET /installs, or by using a known install ID from context — and states which install it is purging.",
            "The response uses POST /installs/{id}/purge_cache with type set to 'all'.",
            "The response notes that CDN propagation may take 1–5 minutes.",
        ],
    },
    {
        "id": "targeted-cache-type",
        "prompt": "purge only the CDN cache for mysite",
        "tags": ["happy-path"],
        "rubric": [
            "The response uses type 'cdn', not 'all'.",
            "The response does not purge object or page cache when only CDN was requested.",
        ],
    },
    {
        "id": "confirm-environment",
        "prompt": "purge cache for mysite",
        "tags": ["edge-case"],
        "rubric": [
            "The response asks which environment to purge (production, staging, development) if the install name is ambiguous, OR defaults to production and states that assumption clearly.",
            "The response does not purge all environments without confirming.",
        ],
    },
    {
        "id": "post-deployment-purge",
        "prompt": "we just deployed to production and staging — clear cache on both",
        "tags": ["workflow"],
        "rubric": [
            "The response purges cache for both production and staging installs.",
            "The response uses separate POST /purge_cache calls for each install.",
            "The response uses type 'all' for a post-deployment scenario.",
        ],
    },
]
