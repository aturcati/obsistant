"""LLM configuration factory for CrewAI agents with rate limit retry handling."""

import os
from typing import Any, cast

from crewai import LLM


def _requires_max_completion_tokens(model: str) -> bool:
    """Check if model requires max_completion_tokens instead of max_tokens.

    Newer OpenAI models (o1, o3, gpt-5 series) require max_completion_tokens.
    Older models (gpt-4, gpt-4o, etc.) use max_tokens.

    Args:
        model: Model name (with or without provider prefix)

    Returns:
        True if model requires max_completion_tokens, False otherwise
    """
    # Remove provider prefix if present
    model_name = model.replace("openai/", "").lower()

    # Models that require max_completion_tokens
    completion_token_models = ["o1", "o3", "gpt-5"]

    return any(model_name.startswith(prefix) for prefix in completion_token_models)


def create_llm_with_retries(model: str | None = None, **kwargs: Any) -> LLM:
    """Create LLM with rate limit retry configuration.

    Automatically handles both max_tokens and max_completion_tokens parameters
    based on the model type. Ensures only the correct parameter is passed to prevent
    runtime API errors.

    Args:
        model: Model name (e.g., "gpt-4o-mini", "o1-preview", "gpt-5-mini").
               If None, uses MODEL env var.
        **kwargs: Additional LLM parameters. Can include:
            - max_tokens: Will be converted to max_completion_tokens if needed
            - max_completion_tokens: Will be converted to max_tokens if needed
            - If neither is provided, defaults to 4000 with appropriate parameter name

    Returns:
        Configured LLM instance with retry handling for rate limits.
    """
    model = model or os.getenv("MODEL", "gpt-4o-mini")

    # Ensure model has provider prefix
    if not model.startswith("openai/"):
        model = f"openai/{model}"

    # Extract token limit parameters (user may provide either)
    max_tokens = kwargs.pop("max_tokens", None)
    max_completion_tokens = kwargs.pop("max_completion_tokens", None)
    default_token_limit = 4000

    # Determine which parameter the model requires
    requires_completion_tokens = _requires_max_completion_tokens(model)

    # Get token limit value (accept either parameter name)
    token_limit = max_completion_tokens or max_tokens or default_token_limit

    # Prepare LLM arguments with ONLY the correct parameter
    llm_kwargs = {
        "model": model,
        "max_retries": 5,  # Higher than default 3 for better resilience
        "timeout": 120,  # Longer timeout to accommodate retries
        **kwargs,
    }

    # Use ONLY the correct parameter based on model requirements
    # Never pass both parameters simultaneously
    if requires_completion_tokens:
        llm_kwargs["max_completion_tokens"] = token_limit
    else:
        llm_kwargs["max_tokens"] = token_limit

    # Type cast to satisfy type checker - we know the types are correct
    return LLM(**cast(dict[str, Any], llm_kwargs))
