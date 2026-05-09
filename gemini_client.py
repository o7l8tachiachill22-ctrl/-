"""Google Gemini API client wrapper."""

import os
import google.generativeai as genai
import google.api_core.exceptions
from typing import Optional


class TokenLimitError(Exception):
    """Raised when the prompt exceeds the model's token limit."""

    pass


class RateLimitError(Exception):
    """Raised when the API rate/quota limit is exceeded."""

    pass


def configure(api_key: Optional[str] = None) -> None:
    key = api_key or os.environ.get("GEMINI_API_KEY")
    if not key:
        raise ValueError("GEMINI_API_KEY is not set")
    genai.configure(api_key=key)


def count_tokens(prompt: str, model: str = "gemini-1.5-flash") -> int:
    model_instance = genai.GenerativeModel(model)
    result = model_instance.count_tokens(prompt)
    return result.total_tokens


def chat(
    prompt: str,
    model: str = "gemini-1.5-flash",
    system_instruction: Optional[str] = None,
) -> str:
    kwargs = {}
    if system_instruction:
        kwargs["system_instruction"] = system_instruction

    model_instance = genai.GenerativeModel(model, **kwargs)
    try:
        response = model_instance.generate_content(prompt)
        return response.text
    except google.api_core.exceptions.InvalidArgument as e:
        if "token" in str(e).lower():
            raise TokenLimitError(str(e)) from e
        raise
    except google.api_core.exceptions.ResourceExhausted as e:
        raise RateLimitError(str(e)) from e


def stream_chat(
    prompt: str,
    model: str = "gemini-1.5-flash",
    system_instruction: Optional[str] = None,
):
    kwargs = {}
    if system_instruction:
        kwargs["system_instruction"] = system_instruction

    model_instance = genai.GenerativeModel(model, **kwargs)
    try:
        for chunk in model_instance.generate_content(prompt, stream=True):
            if chunk.text:
                yield chunk.text
    except google.api_core.exceptions.InvalidArgument as e:
        if "token" in str(e).lower():
            raise TokenLimitError(str(e)) from e
        raise
    except google.api_core.exceptions.ResourceExhausted as e:
        raise RateLimitError(str(e)) from e


def list_models() -> list[str]:
    return [
        m.name
        for m in genai.list_models()
        if "generateContent" in m.supported_generation_methods
    ]
