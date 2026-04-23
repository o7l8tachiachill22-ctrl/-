"""Google Gemini API client wrapper."""

import os
import google.generativeai as genai
from typing import Optional


def configure(api_key: Optional[str] = None) -> None:
    key = api_key or os.environ.get("GEMINI_API_KEY")
    if not key:
        raise ValueError("GEMINI_API_KEY is not set")
    genai.configure(api_key=key)


def chat(
    prompt: str,
    model: str = "gemini-1.5-flash",
    system_instruction: Optional[str] = None,
) -> str:
    kwargs = {}
    if system_instruction:
        kwargs["system_instruction"] = system_instruction

    model_instance = genai.GenerativeModel(model, **kwargs)
    response = model_instance.generate_content(prompt)
    return response.text


def stream_chat(
    prompt: str,
    model: str = "gemini-1.5-flash",
    system_instruction: Optional[str] = None,
):
    kwargs = {}
    if system_instruction:
        kwargs["system_instruction"] = system_instruction

    model_instance = genai.GenerativeModel(model, **kwargs)
    for chunk in model_instance.generate_content(prompt, stream=True):
        if chunk.text:
            yield chunk.text


def list_models() -> list[str]:
    return [
        m.name
        for m in genai.list_models()
        if "generateContent" in m.supported_generation_methods
    ]
