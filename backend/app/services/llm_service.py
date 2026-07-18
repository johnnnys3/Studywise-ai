from __future__ import annotations

import json
from typing import Any, Iterator

import httpx

from app.core.config import get_settings


RESPONSES_URL = "https://api.openai.com/v1/responses"
GEMINI_URL = "https://generativelanguage.googleapis.com/v1beta/models/{model}:generateContent"


def is_ai_configured() -> bool:
    settings = get_settings()
    if settings.ai_provider == "gemini":
        return bool(settings.gemini_api_key)
    if settings.ai_provider == "openai":
        return bool(settings.openai_api_key)
    return False


def _openai_headers() -> dict[str, str]:
    settings = get_settings()
    if not settings.openai_api_key:
        raise RuntimeError("OPENAI_API_KEY is not configured.")
    return {
        "Authorization": f"Bearer {settings.openai_api_key}",
        "Content-Type": "application/json",
    }


def _extract_output_text(response_json: dict[str, Any]) -> str:
    if isinstance(response_json.get("output_text"), str):
        return response_json["output_text"]

    texts: list[str] = []
    for output in response_json.get("output", []):
        if output.get("type") != "message":
            continue
        for content in output.get("content", []):
            if content.get("type") == "output_text" and isinstance(content.get("text"), str):
                texts.append(content["text"])
    return "\n".join(texts).strip()


def create_text_response(system_instructions: str, user_input: str) -> str:
    settings = get_settings()
    if settings.ai_provider == "gemini":
        return _create_gemini_text_response(system_instructions, user_input)
    if settings.ai_provider != "openai":
        raise RuntimeError(f"Unsupported AI_PROVIDER: {settings.ai_provider}")
    return _create_openai_text_response(system_instructions, user_input)


def stream_text_response(system_instructions: str, user_input: str) -> Iterator[str]:
    settings = get_settings()
    if settings.ai_provider == "gemini":
        yield _create_gemini_text_response(system_instructions, user_input)
        return
    if settings.ai_provider != "openai":
        raise RuntimeError(f"Unsupported AI_PROVIDER: {settings.ai_provider}")
    yield from _stream_openai_text_response(system_instructions, user_input)


def _stream_openai_text_response(system_instructions: str, user_input: str) -> Iterator[str]:
    settings = get_settings()
    payload = {
        "model": settings.openai_model,
        "input": [
            {"role": "system", "content": system_instructions},
            {"role": "user", "content": user_input},
        ],
        "stream": True,
    }
    with httpx.Client(timeout=settings.ai_timeout_seconds) as client:
        with client.stream("POST", RESPONSES_URL, headers=_openai_headers(), json=payload) as response:
            response.raise_for_status()
            for line in response.iter_lines():
                if not line or not line.startswith("data: "):
                    continue
                data = line[len("data: "):].strip()
                if data == "[DONE]":
                    break
                try:
                    event = json.loads(data)
                except json.JSONDecodeError:
                    continue
                if event.get("type") == "response.output_text.delta":
                    delta = event.get("delta")
                    if isinstance(delta, str) and delta:
                        yield delta


def create_structured_response(system_instructions: str, user_input: str, schema_name: str, schema: dict[str, Any]) -> dict[str, Any]:
    settings = get_settings()
    if settings.ai_provider == "gemini":
        return _create_gemini_structured_response(system_instructions, user_input, schema)
    if settings.ai_provider != "openai":
        raise RuntimeError(f"Unsupported AI_PROVIDER: {settings.ai_provider}")
    return _create_openai_structured_response(system_instructions, user_input, schema_name, schema)


def _create_openai_text_response(system_instructions: str, user_input: str) -> str:
    settings = get_settings()
    payload = {
        "model": settings.openai_model,
        "input": [
            {"role": "system", "content": system_instructions},
            {"role": "user", "content": user_input},
        ],
    }
    with httpx.Client(timeout=settings.ai_timeout_seconds) as client:
        response = client.post(RESPONSES_URL, headers=_openai_headers(), json=payload)
        response.raise_for_status()
    return _extract_output_text(response.json())


def _create_openai_structured_response(system_instructions: str, user_input: str, schema_name: str, schema: dict[str, Any]) -> dict[str, Any]:
    settings = get_settings()
    payload = {
        "model": settings.openai_model,
        "input": [
            {"role": "system", "content": system_instructions},
            {"role": "user", "content": user_input},
        ],
        "text": {
            "format": {
                "type": "json_schema",
                "name": schema_name,
                "schema": schema,
                "strict": True,
            }
        },
    }
    with httpx.Client(timeout=settings.ai_timeout_seconds) as client:
        response = client.post(RESPONSES_URL, headers=_openai_headers(), json=payload)
        response.raise_for_status()
    output_text = _extract_output_text(response.json())
    return json.loads(output_text)


def _create_gemini_text_response(system_instructions: str, user_input: str) -> str:
    settings = get_settings()
    payload = {
        "system_instruction": {"parts": [{"text": system_instructions}]},
        "contents": [{"role": "user", "parts": [{"text": user_input}]}],
    }
    response_json = _post_gemini(payload)
    return _extract_gemini_text(response_json)


def _create_gemini_structured_response(system_instructions: str, user_input: str, schema: dict[str, Any]) -> dict[str, Any]:
    payload = {
        "system_instruction": {"parts": [{"text": system_instructions}]},
        "contents": [{"role": "user", "parts": [{"text": user_input}]}],
        "generationConfig": {
            "responseMimeType": "application/json",
            "responseSchema": _to_gemini_schema(schema),
        },
    }
    response_json = _post_gemini(payload)
    return json.loads(_extract_gemini_text(response_json))


def _post_gemini(payload: dict[str, Any]) -> dict[str, Any]:
    settings = get_settings()
    if not settings.gemini_api_key:
        raise RuntimeError("GEMINI_API_KEY is not configured.")
    url = GEMINI_URL.format(model=settings.gemini_model)
    with httpx.Client(timeout=settings.ai_timeout_seconds) as client:
        response = client.post(url, headers={"x-goog-api-key": settings.gemini_api_key}, json=payload)
        response.raise_for_status()
    return response.json()


def _extract_gemini_text(response_json: dict[str, Any]) -> str:
    texts: list[str] = []
    for candidate in response_json.get("candidates", []):
        content = candidate.get("content", {})
        for part in content.get("parts", []):
            text = part.get("text")
            if isinstance(text, str):
                texts.append(text)
    return "\n".join(texts).strip()


def _to_gemini_schema(schema: dict[str, Any]) -> dict[str, Any]:
    type_map = {
        "object": "OBJECT",
        "array": "ARRAY",
        "string": "STRING",
        "integer": "INTEGER",
        "number": "NUMBER",
        "boolean": "BOOLEAN",
    }
    converted: dict[str, Any] = {}
    for key, value in schema.items():
        if key == "additionalProperties":
            continue
        if key == "type" and isinstance(value, str):
            converted[key] = type_map.get(value, value)
        elif key in {"properties", "items"} and isinstance(value, dict):
            converted[key] = {name: _to_gemini_schema(child) for name, child in value.items()} if key == "properties" else _to_gemini_schema(value)
        elif isinstance(value, dict):
            converted[key] = _to_gemini_schema(value)
        elif isinstance(value, list):
            converted[key] = value
        else:
            converted[key] = value
    return converted
