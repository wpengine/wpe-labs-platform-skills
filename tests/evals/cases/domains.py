"""
Eval test cases for wpe-labs:domains.
"""

CASES = [
    {
        "id": "list-domains",
        "prompt": "list all domains for mysite",
        "tags": ["happy-path"],
        "rubric": [
            "The response identifies the correct install — either by looking up by name via GET /installs, or by using a known install ID from context.",
            "The response calls GET /installs/{id}/domains.",
            "The response shows domain names and whether each is a primary domain or redirect.",
        ],
    },
    {
        "id": "add-domain-with-redirect",
        "prompt": "add www.example.com to mysite and redirect example.com to it",
        "tags": ["happy-path"],
        "rubric": [
            "The response adds www.example.com as a primary domain.",
            "The response adds example.com as a redirect pointing to www.example.com.",
            "The response makes two separate POST /domains calls (or one bulk call), not one.",
        ],
    },
    {
        "id": "dns-propagation-check",
        "prompt": "check if www.example.com has propagated for mysite",
        "tags": ["workflow"],
        "rubric": [
            "The response submits a status check via POST /domains/{id}/check_status.",
            "The response retrieves the report via GET /domains/check_status/{report_id}.",
            "The response reports the propagation status clearly to the user.",
        ],
    },
    {
        "id": "ssl-404-handling",
        "prompt": "show me the SSL certificate status for mysite",
        "tags": ["edge-case"],
        "rubric": [
            "If the ssl_certificates endpoint returns 404, the response explains that SSL certificate listing is not available for this install's network type.",
            "The response does not treat a 404 as a generic error without explanation.",
        ],
    },
    {
        "id": "bulk-domain-add",
        "prompt": "add these domains to mysite: shop.example.com, blog.example.com, and redirect old.example.com to www.example.com",
        "tags": ["happy-path"],
        "rubric": [
            "The response uses POST /domains/bulk rather than three separate POST /domains calls.",
            "The response includes all three domains in the bulk request.",
            "The redirect for old.example.com points to www.example.com.",
        ],
    },
]
