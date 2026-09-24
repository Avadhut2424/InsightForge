# ONLY PLACE IN CODEBASE TO CALL LLM SDK DIRECTLY
# Do NOT import or use openai or other LLM SDKs anywhere else.

import time
from typing import Optional
from dataclasses import dataclass
from openai import AsyncOpenAI
import openai
from tenacity import retry, wait_exponential, stop_after_attempt, retry_if_exception_type, RetryError

from app.core.config import settings
from app.core.llm.config import get_model_for_role, DEFAULT_TIMEOUT_SECONDS, DEFAULT_MAX_TOKENS, MAX_RETRIES
from app.core.llm.exceptions import LLMAPIError, LLMTimeoutError, LLMRateLimitError, LLMError

@dataclass
class LLMResponse:
    text: str
    model_used: str
    input_tokens: int
    output_tokens: int
    latency_ms: float

# Initialize a single AsyncOpenAI client reusing the connection
client = AsyncOpenAI(api_key=settings.openai_api_key)

def is_transient_error(e: BaseException) -> bool:
    """Return True if the error is transient and should be retried."""
    return isinstance(e, (openai.APITimeoutError, openai.RateLimitError, openai.InternalServerError))

@retry(
    wait=wait_exponential(multiplier=1, min=1, max=10),
    stop=stop_after_attempt(MAX_RETRIES),
    retry=retry_if_exception_type((openai.APITimeoutError, openai.RateLimitError, openai.InternalServerError)),
    reraise=True
)
async def _execute_llm_call_with_retry(
    model: str,
    prompt: str,
    max_tokens: int,
    timeout: float
):
    """Inner function to handle retries using tenacity."""
    return await client.chat.completions.create(
        model=model,
        messages=[{"role": "user", "content": prompt}],
        max_tokens=max_tokens,
        timeout=timeout,
        temperature=0.0
    )


async def call_llm(
    role: str,
    prompt: str,
    max_tokens: Optional[int] = None,
    timeout: Optional[float] = None,
    **kwargs
) -> LLMResponse:
    """
    Call the LLM for a given role and prompt.
    This is the sole point of integration with the LLM provider.
    """
    model = get_model_for_role(role)
    actual_max_tokens = max_tokens if max_tokens is not None else DEFAULT_MAX_TOKENS
    actual_timeout = timeout if timeout is not None else DEFAULT_TIMEOUT_SECONDS

    start_time = time.monotonic()
    
    try:
        response = await _execute_llm_call_with_retry(
            model=model,
            prompt=prompt,
            max_tokens=actual_max_tokens,
            timeout=actual_timeout
        )
    except RetryError as e:
        # Tenacity raised a RetryError after exhausting attempts
        original_error = e.last_attempt.exception() if e.last_attempt else e
        if isinstance(original_error, openai.APITimeoutError):
            raise LLMTimeoutError("Request timed out", role, model, MAX_RETRIES) from original_error
        elif isinstance(original_error, openai.RateLimitError):
            raise LLMRateLimitError("Rate limit exceeded", role, model, MAX_RETRIES) from original_error
        else:
            raise LLMAPIError("API Error after retries", role, model, MAX_RETRIES, original_error) from original_error
    except (openai.APITimeoutError, openai.RateLimitError, openai.InternalServerError) as e:
        # If reraise=True in @retry, these exceptions might be raised directly when out of retries
        if isinstance(e, openai.APITimeoutError):
            raise LLMTimeoutError("Request timed out", role, model, MAX_RETRIES) from e
        elif isinstance(e, openai.RateLimitError):
            raise LLMRateLimitError("Rate limit exceeded", role, model, MAX_RETRIES) from e
        else:
            raise LLMAPIError("Internal Server Error after retries", role, model, MAX_RETRIES, e) from e
    except openai.AuthenticationError as e:
        # Non-transient errors (401 invalid key, etc.)
        raise LLMAPIError("Authentication failed (invalid API key or unauthorized)", role, model, 1, e) from e
    except openai.BadRequestError as e:
        # Non-transient error (400 bad request)
        raise LLMAPIError("Bad request", role, model, 1, e) from e
    except openai.OpenAIError as e:
        # Any other OpenAI specific error
        raise LLMAPIError("Unexpected OpenAI API Error", role, model, 1, e) from e
    except Exception as e:
        raise LLMError(f"Unexpected error calling LLM: {str(e)}") from e

    end_time = time.monotonic()
    latency_ms = (end_time - start_time) * 1000.0

    return LLMResponse(
        text=response.choices[0].message.content or "",
        model_used=response.model,
        input_tokens=response.usage.prompt_tokens if response.usage else 0,
        output_tokens=response.usage.completion_tokens if response.usage else 0,
        latency_ms=latency_ms
    )
