import asyncio
import sys
from unittest.mock import patch, MagicMock
from openai import RateLimitError, AuthenticationError
from tenacity import RetryError

import httpx
from app.core.llm.client import call_llm
from app.core.llm.exceptions import LLMRateLimitError, LLMAPIError

async def test_retry_success():
    print("=== Testing Retry on Transient Error (RateLimitError) ===")
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
            print(f"  Attempt {attempts}: simulating RateLimitError")
            # RateLimitError requires a response and a body according to openai's signature
            mock_httpx_response = httpx.Response(429, request=httpx.Request("POST", "https://api.openai.com/v1/chat/completions"))
            raise RateLimitError("Mocked RateLimit", response=mock_httpx_response, body=None)
        print(f"  Attempt {attempts}: success")
        return mock_response

    with patch("app.core.llm.client.client.chat.completions.create", side_effect=mock_create):
        response = await call_llm(role="default", prompt="Hello", max_tokens=10, timeout=1.0)
        print(f"Final response: {response.text}")
        print(f"Latency: {response.latency_ms:.2f}ms")
        assert attempts == 3

async def test_non_transient_failure():
    print("\n=== Testing Fail Fast on Non-Transient Error (AuthenticationError) ===")
    attempts = 0
    async def mock_create(*args, **kwargs):
        nonlocal attempts
        attempts += 1
        print(f"  Attempt {attempts}: simulating AuthenticationError")
        mock_httpx_response = httpx.Response(401, request=httpx.Request("POST", "https://api.openai.com/v1/chat/completions"))
        raise AuthenticationError("Mocked Auth Error", response=mock_httpx_response, body=None)

    with patch("app.core.llm.client.client.chat.completions.create", side_effect=mock_create):
        try:
            await call_llm(role="default", prompt="Hello", max_tokens=10, timeout=1.0)
            print("ERROR: Should have raised LLMAPIError")
        except LLMAPIError as e:
            print(f"Caught expected LLMAPIError: {e}")
            assert attempts == 1 # Should fail fast on first attempt

async def main():
    await test_retry_success()
    await test_non_transient_failure()

if __name__ == "__main__":
    asyncio.run(main())
