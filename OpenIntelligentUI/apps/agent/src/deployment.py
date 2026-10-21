"""Server-side model configuration; environment values override .env files."""

import os
from urllib.parse import urlsplit


def air_gap_enabled() -> bool:
    return os.getenv("AIR_GAP_MODE", "false").lower() in {"1", "true"}


def server_model_enabled() -> bool:
    return os.getenv("LLM_PROVIDER", "auto").strip().lower() in {"openai", "vllm", "ollama"}


def configured_model_settings() -> tuple[str, str, str]:
    provider = os.getenv("LLM_PROVIDER", "auto").strip().lower()
    if provider not in {"openai", "vllm", "ollama"}:
        raise ValueError("Configured models require LLM_PROVIDER=openai, vllm or ollama.")
    if air_gap_enabled() and provider not in {"vllm", "ollama"}:
        raise ValueError("AIR_GAP_MODE requires LLM_PROVIDER=vllm or ollama.")
    model = os.getenv("LLM_MODEL", "chat-latest" if provider == "openai" else "").strip()
    # A deliberately empty new setting never falls back to a stale legacy value.
    base_url = os.getenv("LLM_BASE_URL", os.getenv(
        "OPENAI_BASE_URL", "https://api.openai.com/v1" if provider == "openai" else ""
    )).strip().rstrip("/")
    url = urlsplit(base_url)
    if not model:
        raise ValueError("LLM_MODEL must name the served model.")
    if (url.scheme not in {"http", "https"} or not url.hostname
            or url.username or url.password or url.query or url.fragment
            or not url.path.endswith("/v1")):
        raise ValueError("LLM_BASE_URL (legacy OPENAI_BASE_URL) must be an explicit http(s) URL ending in /v1.")
    legacy_key = {"openai": "OPENAI_API_KEY", "vllm": "VLLM_API_KEY", "ollama": "OLLAMA_API_KEY"}[provider]
    key = os.getenv("LLM_API_KEY", os.getenv(legacy_key, "")).strip()
    if provider == "openai" and not key:
        raise ValueError("LLM_API_KEY is required. Set it in apps/agent/.env and restart the agent.")
    return model, base_url, key or "EMPTY"
