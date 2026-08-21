import pytest

from app.ai.openrouter import call_openrouter
from app.config import settings


@pytest.mark.integration
def test_call_openrouter_answers_simple_math():
    if not settings.openrouter_api_key:
        pytest.skip("OPENROUTER_API_KEY not set")

    reply = call_openrouter(
        [{"role": "user", "content": "What is 2+2? Answer with just the number."}]
    )

    assert "4" in reply
