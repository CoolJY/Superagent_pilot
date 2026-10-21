"""Server-side model configuration; environment values override .env files."""

import os
from urllib.parse import urlsplit


def air_gap_enabled() -> bool:
    return os.getenv("AIR_GAP_MODE", "false").lower() in {"1", "true"}


def server_model_enabled() -> bool:
    return os.getenv("LLM_PROVIDER", "auto").strip().lower() in {"openai", "gemini", "vllm", "ollama"}


def configured_model_settings() -> tuple[str, str, str]:
    provider = os.getenv("LLM_PROVIDER", "auto").strip().lower()
    if provider not in {"openai", "gemini", "vllm", "ollama"}:
        raise ValueError("Configured models require LLM_PROVIDER=openai, gemini, vllm or ollama.")
    if air_gap_enabled() and provider not in {"vllm", "ollama"}:
        raise ValueError("AIR_GAP_MODE requires LLM_PROVIDER=vllm or ollama.")
    default_model = {"openai": "chat-latest", "gemini": "gemini-3.5-flash-lite"}.get(provider, "")
    model = os.getenv("LLM_MODEL", default_model).strip()
    # A deliberately empty new setting never falls back to a stale legacy value.
    base_url = os.getenv("LLM_BASE_URL", os.getenv(
        "OPENAI_BASE_URL", "https://api.openai.com/v1" if provider == "openai" else ""
    )).strip().rstrip("/")
    if provider == "gemini" and "LLM_BASE_URL" not in os.environ:
        base_url = "https://generativelanguage.googleapis.com/v1beta/openai"
    url = urlsplit(base_url)
    if not model:
        raise ValueError("LLM_MODEL must name the served model.")
    if (url.scheme not in {"http", "https"} or not url.hostname
            or url.username or url.password or url.query or url.fragment):
        raise ValueError("LLM_BASE_URL must be an explicit http(s) URL without credentials or query strings.")
    if provider == "gemini":
        if (url.scheme != "https" or url.hostname != "generativelanguage.googleapis.com"
                or url.port is not None or url.path != "/v1beta/openai"):
            raise ValueError("Gemini LLM_BASE_URL must be https://generativelanguage.googleapis.com/v1beta/openai.")
        # Never reuse LLM_API_KEY: it may still hold an OpenAI secret.
        key = os.getenv("GEMINI_API_KEY", "").strip()
        if not key:
            raise ValueError("GEMINI_API_KEY is required. Set it in apps/agent/.env and restart the agent.")
    else:
        if not url.path.endswith("/v1"):
            raise ValueError("LLM_BASE_URL (legacy OPENAI_BASE_URL) must end in /v1.")
        legacy_key = {"openai": "OPENAI_API_KEY", "vllm": "VLLM_API_KEY", "ollama": "OLLAMA_API_KEY"}[provider]
        key = os.getenv("LLM_API_KEY", os.getenv(legacy_key, "")).strip()
        if provider == "openai" and not key:
            raise ValueError("LLM_API_KEY is required. Set it in apps/agent/.env and restart the agent.")
    return model, base_url, key or "EMPTY"
