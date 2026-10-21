"""Deployment settings shared by the model and HTTP boundary."""

import os
from urllib.parse import urlsplit


def air_gap_enabled() -> bool:
    return os.getenv("AIR_GAP_MODE", "false").lower() in {"1", "true"}


def vllm_settings() -> tuple[str, str]:
    model = os.getenv("LLM_MODEL", "").strip()
    base_url = os.getenv("OPENAI_BASE_URL", "").strip().rstrip("/")
    url = urlsplit(base_url)
    if not model:
        raise ValueError("LLM_MODEL must match the vLLM served model name.")
    if (url.scheme not in {"http", "https"} or not url.hostname
            or url.username or url.password or url.query or url.fragment
            or not url.path.endswith("/v1")):
        raise ValueError("OPENAI_BASE_URL must be an explicit http(s) vLLM URL ending in /v1.")
    return model, base_url
