from __future__ import annotations

import json
from urllib import error, request

from brain_ops.errors import AIProviderError


def generate_json(
    *,
    host: str,
    model: str,
    prompt: str,
    json_schema: dict[str, object] | None = None,
    timeout_seconds: int = 20,
) -> dict[str, object]:
    url = host.rstrip("/") + "/api/generate"
    payload = {
        "model": model,
        "prompt": prompt,
        "stream": False,
        "format": json_schema if json_schema is not None else "json",
        "options": {
            "temperature": 0,
            "num_predict": 96,
        },
    }
    data = json.dumps(payload).encode("utf-8")
    req = request.Request(
        url,
        data=data,
        headers={"Content-Type": "application/json"},
        method="POST",
    )
    try:
        with request.urlopen(req, timeout=timeout_seconds) as response:
            raw = response.read().decode("utf-8")
    except (error.URLError, TimeoutError, OSError) as exc:
        raise AIProviderError(f"Ollama request failed: {exc}") from exc

    try:
        outer = json.loads(raw)
        content = outer.get("response", "")
        if not isinstance(content, str) or not content.strip():
            raise AIProviderError("Ollama returned an empty response.")
        parsed = json.loads(content)
    except (json.JSONDecodeError, TypeError) as exc:
        raise AIProviderError("Ollama did not return valid JSON content.") from exc

    if not isinstance(parsed, dict):
        raise AIProviderError("Ollama JSON response must be an object.")
    return parsed


def generate_text(
    *,
    host: str,
    model: str,
    prompt: str,
    timeout_seconds: int = 60,
) -> str:
    url = host.rstrip("/") + "/api/generate"
    payload = {
        "model": model,
        "prompt": prompt,
        "stream": False,
        "options": {
            "temperature": 0.3,
            "num_predict": 2048,
        },
    }
    data = json.dumps(payload).encode("utf-8")
    req = request.Request(
        url,
        data=data,
        headers={"Content-Type": "application/json"},
        method="POST",
    )
    try:
        with request.urlopen(req, timeout=timeout_seconds) as response:
            raw = response.read().decode("utf-8")
    except (error.URLError, TimeoutError, OSError) as exc:
        raise AIProviderError(f"Ollama request failed: {exc}") from exc

    try:
        outer = json.loads(raw)
        content = outer.get("response", "")
        if not isinstance(content, str) or not content.strip():
            raise AIProviderError("Ollama returned an empty response.")
        return content.strip()
    except (json.JSONDecodeError, TypeError) as exc:
        raise AIProviderError("Ollama did not return valid text content.") from exc
