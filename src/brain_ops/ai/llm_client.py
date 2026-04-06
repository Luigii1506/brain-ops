"""Unified LLM client supporting Ollama (local) and OpenAI-compatible APIs (DeepSeek, Gemini, etc.)."""

from __future__ import annotations

import json
import os
from dataclasses import dataclass
from urllib import error, request

from brain_ops.errors import AIProviderError


@dataclass(slots=True, frozen=True)
class LLMProvider:
    name: str
    base_url: str
    model: str
    api_key: str | None = None
    timeout_seconds: int = 90

    def to_dict(self) -> dict[str, object]:
        return {
            "name": self.name,
            "base_url": self.base_url,
            "model": self.model,
            "has_api_key": self.api_key is not None,
        }


KNOWN_PROVIDERS: dict[str, dict[str, str]] = {
    "ollama": {
        "base_url": "http://127.0.0.1:11434",
        "default_model": "qwen3.5:9b",
    },
    "deepseek": {
        "base_url": "https://api.deepseek.com",
        "default_model": "deepseek-chat",
        "api_key_env": "DEEPSEEK_API_KEY",
    },
    "gemini": {
        "base_url": "https://generativelanguage.googleapis.com/v1beta/openai",
        "default_model": "gemini-2.0-flash",
        "api_key_env": "GEMINI_API_KEY",
    },
    "openai": {
        "base_url": "https://api.openai.com/v1",
        "default_model": "gpt-4o-mini",
        "api_key_env": "OPENAI_API_KEY",
    },
    "claude": {
        "base_url": "https://api.anthropic.com",
        "default_model": "claude-sonnet-4-6",
        "api_key_env": "ANTHROPIC_API_KEY",
    },
}


# Task routing: which provider to use for each task type
TASK_ROUTING: dict[str, str] = {
    "extract": "fast",         # parsing, bullet extraction, classification
    "classify": "fast",        # source type detection
    "summarize": "fast",       # quick summaries, TLDRs
    "write_wiki": "quality",   # final wiki page writing
    "enrich": "quality",       # enriching entities with synthesis
    "query": "quality",        # answering questions with depth
    "lint": "quality",         # detecting contradictions, gaps
    "generate": "quality",     # generating initial entity content
}


def resolve_provider(
    provider_name: str | None = None,
    *,
    model: str | None = None,
    base_url: str | None = None,
    api_key: str | None = None,
) -> LLMProvider:
    name = (provider_name or os.getenv("BRAIN_OPS_LLM_PROVIDER", "ollama")).strip().lower()
    known = KNOWN_PROVIDERS.get(name, {})

    resolved_url = base_url or os.getenv("BRAIN_OPS_LLM_BASE_URL") or known.get("base_url", "")
    resolved_model = model or os.getenv("BRAIN_OPS_LLM_MODEL") or known.get("default_model", "")
    resolved_key = api_key
    if resolved_key is None:
        key_env = known.get("api_key_env")
        if key_env:
            resolved_key = os.getenv(key_env)

    return LLMProvider(
        name=name,
        base_url=resolved_url,
        model=resolved_model,
        api_key=resolved_key,
    )


def llm_generate_text(provider: LLMProvider, prompt: str) -> str:
    if provider.name == "ollama":
        return _ollama_generate(provider, prompt)
    if provider.name == "claude":
        return _claude_generate(provider, prompt)
    return _openai_compatible_generate(provider, prompt)


def llm_generate_json(provider: LLMProvider, prompt: str) -> dict[str, object]:
    if provider.name == "ollama":
        return _ollama_generate_json(provider, prompt)
    if provider.name == "claude":
        return _claude_generate_json(provider, prompt)
    return _openai_compatible_generate_json(provider, prompt)


def _ollama_generate(provider: LLMProvider, prompt: str) -> str:
    url = provider.base_url.rstrip("/") + "/api/generate"
    payload = {
        "model": provider.model,
        "prompt": prompt,
        "stream": False,
        "options": {"temperature": 0.3, "num_predict": 4096},
    }
    raw = _http_post(url, payload, timeout=provider.timeout_seconds)
    outer = json.loads(raw)
    content = outer.get("response", "")
    if not isinstance(content, str) or not content.strip():
        raise AIProviderError("Ollama returned an empty response.")
    return content.strip()


def _ollama_generate_json(provider: LLMProvider, prompt: str) -> dict[str, object]:
    url = provider.base_url.rstrip("/") + "/api/generate"
    payload = {
        "model": provider.model,
        "prompt": prompt,
        "stream": False,
        "format": "json",
        "options": {"temperature": 0, "num_predict": 2048},
    }
    raw = _http_post(url, payload, timeout=provider.timeout_seconds)
    outer = json.loads(raw)
    content = outer.get("response", "")
    parsed = json.loads(content)
    if not isinstance(parsed, dict):
        raise AIProviderError("Ollama JSON response must be an object.")
    return parsed


def _openai_compatible_generate(provider: LLMProvider, prompt: str) -> str:
    url = provider.base_url.rstrip("/") + "/chat/completions"
    payload = {
        "model": provider.model,
        "messages": [{"role": "user", "content": prompt}],
        "temperature": 0.3,
        "max_tokens": 4096,
    }
    headers = {"Content-Type": "application/json"}
    if provider.api_key:
        headers["Authorization"] = f"Bearer {provider.api_key}"
    raw = _http_post(url, payload, timeout=provider.timeout_seconds, headers=headers)
    response = json.loads(raw)
    choices = response.get("choices", [])
    if not choices:
        raise AIProviderError(f"{provider.name} returned no choices.")
    content = choices[0].get("message", {}).get("content", "")
    if not isinstance(content, str) or not content.strip():
        raise AIProviderError(f"{provider.name} returned empty content.")
    return content.strip()


def _openai_compatible_generate_json(provider: LLMProvider, prompt: str) -> dict[str, object]:
    url = provider.base_url.rstrip("/") + "/chat/completions"
    payload = {
        "model": provider.model,
        "messages": [{"role": "user", "content": prompt}],
        "temperature": 0,
        "max_tokens": 2048,
        "response_format": {"type": "json_object"},
    }
    headers = {"Content-Type": "application/json"}
    if provider.api_key:
        headers["Authorization"] = f"Bearer {provider.api_key}"
    raw = _http_post(url, payload, timeout=provider.timeout_seconds, headers=headers)
    response = json.loads(raw)
    choices = response.get("choices", [])
    if not choices:
        raise AIProviderError(f"{provider.name} returned no choices.")
    content = choices[0].get("message", {}).get("content", "")
    parsed = json.loads(content)
    if not isinstance(parsed, dict):
        raise AIProviderError(f"{provider.name} JSON response must be an object.")
    return parsed


def _claude_generate(provider: LLMProvider, prompt: str) -> str:
    url = provider.base_url.rstrip("/") + "/v1/messages"
    payload = {
        "model": provider.model,
        "max_tokens": 4096,
        "messages": [{"role": "user", "content": prompt}],
    }
    headers = {
        "Content-Type": "application/json",
        "x-api-key": provider.api_key or "",
        "anthropic-version": "2023-06-01",
    }
    raw = _http_post(url, payload, timeout=provider.timeout_seconds, headers=headers)
    response = json.loads(raw)
    content_blocks = response.get("content", [])
    if not content_blocks:
        raise AIProviderError("Claude returned no content.")
    text = content_blocks[0].get("text", "")
    if not text.strip():
        raise AIProviderError("Claude returned empty text.")
    return text.strip()


def _claude_generate_json(provider: LLMProvider, prompt: str) -> dict[str, object]:
    text = _claude_generate(provider, prompt + "\n\nRespond ONLY with valid JSON.")
    start = text.find("{")
    end = text.rfind("}") + 1
    if start >= 0 and end > start:
        text = text[start:end]
    parsed = json.loads(text)
    if not isinstance(parsed, dict):
        raise AIProviderError("Claude JSON response must be an object.")
    return parsed


@dataclass(slots=True, frozen=True)
class SmartRouter:
    fast_provider: LLMProvider
    quality_provider: LLMProvider

    def provider_for_task(self, task: str) -> LLMProvider:
        tier = TASK_ROUTING.get(task, "fast")
        return self.quality_provider if tier == "quality" else self.fast_provider

    def generate_text(self, prompt: str, *, task: str = "extract") -> str:
        return llm_generate_text(self.provider_for_task(task), prompt)

    def generate_json(self, prompt: str, *, task: str = "extract") -> dict[str, object]:
        return llm_generate_json(self.provider_for_task(task), prompt)

    def to_dict(self) -> dict[str, object]:
        return {
            "fast": self.fast_provider.to_dict(),
            "quality": self.quality_provider.to_dict(),
            "routing": dict(TASK_ROUTING),
        }


def resolve_smart_router(
    *,
    fast_provider: str | None = None,
    quality_provider: str | None = None,
) -> SmartRouter:
    fast_name = fast_provider or os.getenv("BRAIN_OPS_LLM_FAST", "deepseek")
    quality_name = quality_provider or os.getenv("BRAIN_OPS_LLM_QUALITY", "deepseek")
    return SmartRouter(
        fast_provider=resolve_provider(fast_name),
        quality_provider=resolve_provider(quality_name),
    )


def _http_post(url: str, payload: dict, *, timeout: int = 60, headers: dict | None = None) -> str:
    data = json.dumps(payload).encode("utf-8")
    req_headers = {"Content-Type": "application/json"}
    if headers:
        req_headers.update(headers)
    req = request.Request(url, data=data, headers=req_headers, method="POST")
    try:
        with request.urlopen(req, timeout=timeout) as response:
            return response.read().decode("utf-8")
    except (error.URLError, TimeoutError, OSError) as exc:
        raise AIProviderError(f"LLM request failed: {exc}") from exc


__all__ = [
    "KNOWN_PROVIDERS",
    "LLMProvider",
    "SmartRouter",
    "TASK_ROUTING",
    "llm_generate_json",
    "llm_generate_text",
    "resolve_provider",
    "resolve_smart_router",
]
