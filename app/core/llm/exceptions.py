class LLMError(Exception):
    """Base exception for LLM-related errors."""
    pass

class LLMConfigurationError(LLMError):
    """Raised when there's an issue with LLM configuration or mapping."""
    pass

class LLMAPIError(LLMError):
    """Raised when the LLM API returns a non-transient error (e.g., 400, 401)."""
    def __init__(self, message: str, role: str, model: str, attempt: int, original_error: Exception):
        super().__init__(f"LLM API Error for role '{role}' using model '{model}' at attempt {attempt}: {message} - {original_error}")
        self.role = role
        self.model = model
        self.attempt = attempt
        self.original_error = original_error

class LLMTimeoutError(LLMError):
    """Raised when the LLM API call times out after all retries."""
    def __init__(self, message: str, role: str, model: str, attempt: int):
        super().__init__(f"LLM Timeout Error for role '{role}' using model '{model}' after {attempt} attempts: {message}")
        self.role = role
        self.model = model
        self.attempt = attempt

class LLMRateLimitError(LLMError):
    """Raised when the LLM API rate limit is exceeded after all retries."""
    def __init__(self, message: str, role: str, model: str, attempt: int):
        super().__init__(f"LLM Rate Limit Error for role '{role}' using model '{model}' after {attempt} attempts: {message}")
        self.role = role
        self.model = model
        self.attempt = attempt
