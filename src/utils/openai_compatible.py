from __future__ import annotations

from json import JSONDecodeError
from typing import Any
from urllib.parse import urlparse

import requests


def chat_completions_url(configured_url: str) -> str:
    """Return a chat completions endpoint from either a base URL or full URL."""
    url = configured_url.strip().rstrip("/")
    if not url:
        raise ValueError("OpenAI-compatible gateway URL must be set")

    parsed = urlparse(url)
    if parsed.scheme not in {"http", "https"} or not parsed.netloc:
        raise ValueError(
            "OpenAI-compatible gateway URL must start with http:// or https://"
        )

    if parsed.path.rstrip("/").endswith("/chat/completions"):
        return url

    return f"{url}/chat/completions"


def post_chat_completion(
    session: requests.Session,
    configured_url: str,
    api_key: str,
    body: dict[str, Any],
) -> dict[str, Any]:
    headers = {
        "Authorization": f"Bearer {api_key}",
        "Content-Type": "application/json",
    }
    response = session.post(
        chat_completions_url(configured_url),
        json=body,
        headers=headers,
        timeout=60,
    )
    return _response_json(response)


def chat_message_content(data: dict[str, Any]) -> str:
    choices = data.get("choices")
    if not isinstance(choices, list) or not choices:
        raise RuntimeError("OpenAI-compatible response missing choices")

    first_choice = choices[0]
    if not isinstance(first_choice, dict):
        raise RuntimeError("OpenAI-compatible response has invalid choice data")

    message = first_choice.get("message")
    if not isinstance(message, dict):
        raise RuntimeError("OpenAI-compatible response missing message")

    content = message.get("content")
    if isinstance(content, str):
        return content.strip()

    if isinstance(content, list):
        text_parts: list[str] = []
        for item in content:
            if not isinstance(item, dict):
                continue
            text = item.get("text")
            if isinstance(text, str):
                text_parts.append(text)

        return "".join(text_parts).strip()

    raise RuntimeError("OpenAI-compatible response message content is not text")


def _response_json(response: requests.Response) -> dict[str, Any]:
    if response.status_code < 200 or response.status_code >= 300:
        raise RuntimeError(_http_error_message(response))

    try:
        data = response.json()
    except JSONDecodeError as error:
        raise RuntimeError(_non_json_error_message(response)) from error

    if not isinstance(data, dict):
        raise RuntimeError("OpenAI-compatible response JSON must be an object")

    error_data = data.get("error")
    if isinstance(error_data, dict):
        message = error_data.get("message")
        if isinstance(message, str) and message:
            raise RuntimeError(f"OpenAI-compatible API error: {message}")

    return data


def _http_error_message(response: requests.Response) -> str:
    details = _response_excerpt(response)
    if details:
        return f"OpenAI-compatible API HTTP {response.status_code}: {details}"

    return f"OpenAI-compatible API HTTP {response.status_code} with empty response body"


def _non_json_error_message(response: requests.Response) -> str:
    content_type = response.headers.get("Content-Type") or "unknown content type"
    details = _response_excerpt(response)
    if details:
        return (
            "OpenAI-compatible API returned non-JSON response "
            f"({content_type}): {details}"
        )

    return (
        "OpenAI-compatible API returned an empty non-JSON response "
        f"({content_type}). Check that Gateway URL points to /chat/completions."
    )


def _response_excerpt(response: requests.Response) -> str:
    text = response.text.strip()
    if len(text) <= 500:
        return text

    return f"{text[:500]}..."
