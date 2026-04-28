"""
Eval test cases for wpe-labs:users.
"""

CASES = [
    {
        "id": "list-users",
        "prompt": "who has access to my account?",
        "tags": ["happy-path"],
        "rubric": [
            "The response lists users with their email addresses and roles.",
            "The response uses GET /accounts/{id}/account_users.",
        ],
    },
    {
        "id": "invite-user",
        "prompt": "invite jane@example.com as a full user on my account",
        "tags": ["happy-path"],
        "rubric": [
            "The response uses POST /account_users with the correct email and role.",
            "The role is set to 'full', not 'owner' or 'partial'.",
            "The response notes that the user will receive an invitation email to accept.",
        ],
    },
    {
        "id": "cross-account-audit",
        "prompt": "audit all users across all my accounts",
        "tags": ["workflow"],
        "rubric": [
            "The response either calls GET /accounts to discover all accounts, or uses account IDs from context — it does not invent account IDs.",
            "The response fetches users for each account separately via GET /account_users.",
            "The response presents a clear per-account breakdown of who has access and with what role.",
        ],
    },
    {
        "id": "remove-user-confirmation",
        "prompt": "remove jane@example.com from my account",
        "tags": ["destructive"],
        "rubric": [
            "The response looks up the user ID by email before attempting deletion.",
            "The response confirms the action with the user or clearly states what will happen before calling DELETE.",
            "The response uses DELETE /account_users/{user_id}, not a different method.",
        ],
    },
    {
        "id": "role-update",
        "prompt": "change jane@example.com from full to billing only",
        "tags": ["happy-path"],
        "rubric": [
            "The response looks up the user ID by email first.",
            "The response uses PATCH /account_users/{user_id} with roles set to ['billing'].",
            "The response does not delete and re-invite the user to change the role.",
        ],
    },
]
