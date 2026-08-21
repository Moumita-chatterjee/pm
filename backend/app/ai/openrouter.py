import httpx

from app.config import settings

OPENROUTER_URL = "https://openrouter.ai/api/v1/chat/completions"
MODEL = "openai/gpt-oss-120b"


def call_openrouter(
    messages: list[dict], response_format: dict | None = None
) -> str:
    payload: dict = {"model": MODEL, "messages": messages}
    if response_format is not None:
        payload["response_format"] = response_format

    response = httpx.post(
        OPENROUTER_URL,
        headers={"Authorization": f"Bearer {settings.openrouter_api_key}"},
        json=payload,
        timeout=30,
    )
    response.raise_for_status()
    return response.json()["choices"][0]["message"]["content"]
