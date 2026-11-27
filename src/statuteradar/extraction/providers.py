from __future__ import annotations

import json
import os
from typing import Protocol
from urllib.error import HTTPError, URLError
from urllib.request import Request, urlopen

from ..ingest.config import ROOT

try:
    from dotenv import load_dotenv

    load_dotenv(ROOT / ".env")
except ImportError:
    pass


class ExtractionProviderError(RuntimeError):
    pass


class JsonProvider(Protocol):
    name: str

    def generate_json(self, system_prompt: str, user_prompt: str,
                      schema: dict) -> str: ...


def _post_json(url: str, payload: dict, headers: dict[str, str], timeout: int) -> dict:
    body = json.dumps(payload, ensure_ascii=False).encode("utf-8")
    request = Request(url, data=body, headers={"Content-Type": "application/json", **headers})
    try:
        with urlopen(request, timeout=timeout) as response:
            return json.loads(response.read().decode("utf-8"))
    except HTTPError as exc:
        detail = exc.read().decode("utf-8", errors="replace")
        raise ExtractionProviderError(f"provider returned HTTP {exc.code}: {detail[:1000]}") from exc
    except (URLError, TimeoutError, OSError) as exc:
        raise ExtractionProviderError(f"could not reach extraction provider: {exc}") from exc
    except json.JSONDecodeError as exc:
        raise ExtractionProviderError("provider returned invalid JSON") from exc


class OllamaJsonProvider:
    """Local Ollama chat API with JSON-schema-constrained output."""

    def __init__(self, model: str | None = None, host: str | None = None, timeout: int = 300):
        self.model = model or os.environ.get("OLLAMA_EXTRACTION_MODEL", "qwen2.5:3b")
        self.host = (host or os.environ.get("OLLAMA_HOST", "http://localhost:11434")).rstrip("/")
        self.timeout = timeout
        self.name = f"ollama:{self.model}"

    def generate_json(self, system_prompt: str, user_prompt: str, schema: dict) -> str:
        response = _post_json(
            f"{self.host}/api/chat",
            {
                "model": self.model,
                "messages": [
                    {"role": "system", "content": system_prompt},
                    {"role": "user", "content": user_prompt},
                ],
                "stream": False,
                "format": schema,
                "options": {"temperature": 0},
            },
            {}, self.timeout,
        )
        try:
            return response["message"]["content"]
        except (KeyError, TypeError) as exc:
            raise ExtractionProviderError("Ollama response did not contain message.content") from exc


class AnthropicJsonProvider:
    """Anthropic Messages API provider. Sends only the selected public provision text."""

    def __init__(self, model: str | None = None, api_key: str | None = None, timeout: int = 300):
        self.model = model or os.environ.get("EXTRACTION_MODEL", "claude-haiku-4-5-20251001")
        self.api_key = api_key or os.environ.get("ANTHROPIC_API_KEY", "")
        if not self.api_key:
            raise ExtractionProviderError("set ANTHROPIC_API_KEY or choose LLM_PROVIDER=ollama")
        self.timeout = timeout
        self.name = f"anthropic:{self.model}"

    def generate_json(self, system_prompt: str, user_prompt: str, schema: dict) -> str:
        response = _post_json(
            "https://api.anthropic.com/v1/messages",
            {
                "model": self.model,
                "max_tokens": 4096,
                "temperature": 0,
                "system": f"{system_prompt}\n\nReturn JSON matching this schema:\n{json.dumps(schema)}",
                "messages": [{"role": "user", "content": user_prompt}],
            },
            {"x-api-key": self.api_key, "anthropic-version": "2023-06-01"},
            self.timeout,
        )
        try:
            text = "".join(block["text"] for block in response["content"]
                           if block.get("type") == "text")
        except (KeyError, TypeError) as exc:
            raise ExtractionProviderError("Anthropic response did not contain text content") from exc
        if not text:
            raise ExtractionProviderError("Anthropic returned no text content")
        return text


def make_provider(name: str | None = None) -> JsonProvider:
    selected = (name or os.environ.get("LLM_PROVIDER", "api")).strip().lower()
    if selected == "ollama":
        return OllamaJsonProvider()
    if selected == "api":
        return AnthropicJsonProvider()
    raise ExtractionProviderError("LLM_PROVIDER must be 'api' or 'ollama'")
