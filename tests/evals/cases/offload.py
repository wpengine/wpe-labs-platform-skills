"""
Eval test cases for wpe-labs:offload.
"""

CASES = [
    {
        "id": "get-config",
        "prompt": "show me the offload configuration for {WPE_INSTALL_NAME}",
        "tags": ["happy-path"],
        "rubric": [
            "The response identifies the install by name or uses the known install ID from context.",
            "The response calls GET /installs/{id}/offload_settings/files.",
            "The response shows or describes the current offload configuration.",
        ],
    },
    {
        "id": "get-validation-file",
        "prompt": "get the LargeFS validation file for {WPE_INSTALL_NAME}",
        "tags": ["happy-path"],
        "rubric": [
            "The response calls GET /installs/{id}/offload_settings/largefs_validation_file.",
            "The response explains that the file must be uploaded to the root of the S3 bucket before configuration.",
        ],
    },
    {
        "id": "setup-order",
        "prompt": "help me set up media offload for {WPE_INSTALL_NAME}",
        "tags": ["workflow"],
        "rubric": [
            "The response describes getting the validation file first before configuring offload.",
            "The response uses POST /offload_settings/files for initial setup.",
            "The response notes that configuration is applied asynchronously (202 response).",
        ],
    },
    {
        "id": "update-vs-create",
        "prompt": "update the offload configuration for {WPE_INSTALL_NAME}",
        "tags": ["edge-case"],
        "rubric": [
            "The response reads the existing config via GET before making any changes.",
            "The response uses PATCH /offload_settings/files (not POST) for updates.",
            "The response sends the full config object, not just the changed fields.",
        ],
    },
]
