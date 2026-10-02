import asyncio
import sys
from unittest.mock import patch, MagicMock
import pytest
from openai import RateLimitError, AuthenticationError
from tenacity import RetryError

import httpx
from app.core.llm.client import call_llm
from app.core.llm.exceptions import LLMRateLimitError, LLMAPIError

@pytest.mark.asyncio
async def test_retry_success():
    mock_response = MagicMock()
    mock_response.choices = [MagicMock(message=MagicMock(content="Mocked success!"))]
    mock_response.model = "gpt-4o-mini-mock"
    mock_response.usage = MagicMock(prompt_tokens=10, completion_tokens=20)
    
    # We will simulate 2 failures, then 1 success
    attempts = 0
    async def mock_create(*args, **kwargs):
        nonlocal attempts
        attempts += 1
        if attempts <= 2:
            mock_httpx_response = httpx.Response(429, request=httpx.Request("POST", "https://api.openai.com/v1/chat/completions"))
            raise RateLimitError("Mocked RateLimit", response=mock_httpx_response, body=None)
        return mock_response

    with patch("app.core.llm.client.client.chat.completions.create", side_effect=mock_create):
        response = await call_llm(role="default", prompt="Hello", max_tokens=10, timeout=1.0)
        assert response.text == "Mocked success!"
        assert attempts == 3

@pytest.mark.asyncio
async def test_non_transient_failure():
    attempts = 0
    async def mock_create(*args, **kwargs):
        nonlocal attempts
        attempts += 1
        mock_httpx_response = httpx.Response(401, request=httpx.Request("POST", "https://api.openai.com/v1/chat/completions"))
        raise AuthenticationError("Mocked Auth Error", response=mock_httpx_response, body=None)

    with patch("app.core.llm.client.client.chat.completions.create", side_effect=mock_create):
        with pytest.raises(LLMAPIError):
            await call_llm(role="default", prompt="Hello", max_tokens=10, timeout=1.0)
        assert attempts == 1 # Should fail fast on first attempt

