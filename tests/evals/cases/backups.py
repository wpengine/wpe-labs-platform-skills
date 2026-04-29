"""
Eval test cases for wpe-labs:backups.
"""

CASES = [
    {
        "id": "backup-before-deploy",
        "prompt": "back up mysite production before deployment",
        "tags": ["happy-path"],
        "rubric": [
            "The response identifies the correct install — either by looking up by name via GET /installs, or by using a known install ID from context — and names which install it is backing up.",
            "The response creates a backup with a meaningful description (e.g. includes 'pre-deployment' or today's date).",
            "The response captures and reports the backup ID.",
            "The response indicates it will poll or notify when the backup completes.",
        ],
    },
    {
        "id": "poll-until-complete",
        "prompt": "check backup status until it's done",
        "tags": ["async"],
        "rubric": [
            "The response polls the backup status endpoint repeatedly.",
            "The response stops polling when status is 'completed' or 'aborted'.",
            "The response reports the final status clearly.",
        ],
    },
    {
        "id": "aborted-backup",
        "prompt": "the backup was aborted — what do I do?",
        "tags": ["error-handling"],
        "rubric": [
            "The response advises retrying the backup.",
            "The response does not treat 'aborted' as a permanent failure without suggesting a retry.",
        ],
    },
]
