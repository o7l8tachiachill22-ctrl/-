"""OpenAI ChatGPT client wrapper (チャッピー)."""

import os
from typing import Iterator, Optional

from openai import OpenAI

_client: Optional[OpenAI] = None


def configure(api_key: Optional[str] = None) -> None:
    global _client
    key = api_key or os.environ.get("OPENAI_API_KEY")
    if not key:
        raise ValueError("OPENAI_API_KEY is not set")
    _client = OpenAI(api_key=key)


def _get_client() -> OpenAI:
    if _client is None:
        configure()
    return _client


def chat(
    prompt: str,
    model: str = "gpt-4o-mini",
    system_instruction: Optional[str] = None,
) -> str:
    messages = []
    if system_instruction:
        messages.append({"role": "system", "content": system_instruction})
    messages.append({"role": "user", "content": prompt})

    response = _get_client().chat.completions.create(model=model, messages=messages)
    return response.choices[0].message.content


def stream_chat(
    prompt: str,
    model: str = "gpt-4o-mini",
    system_instruction: Optional[str] = None,
) -> Iterator[str]:
    messages = []
    if system_instruction:
        messages.append({"role": "system", "content": system_instruction})
    messages.append({"role": "user", "content": prompt})

    stream = _get_client().chat.completions.create(
        model=model, messages=messages, stream=True
    )
    for chunk in stream:
        delta = chunk.choices[0].delta.content
        if delta:
            yield delta


def interactive_chat(model: str, system_instruction: Optional[str] = None) -> None:
    print(f"チャッピー interactive chat ({model}). Type 'quit' or 'exit' to stop.\n")
    history = []
    if system_instruction:
        history.append({"role": "system", "content": system_instruction})

    client = _get_client()
    while True:
        try:
            user_input = input("You: ").strip()
        except (EOFError, KeyboardInterrupt):
            print("\nBye!")
            break

        if user_input.lower() in ("quit", "exit"):
            print("Bye!")
            break
        if not user_input:
            continue

        history.append({"role": "user", "content": user_input})
        response = client.chat.completions.create(model=model, messages=history)
        reply = response.choices[0].message.content
        history.append({"role": "assistant", "content": reply})
        print(f"チャッピー: {reply}\n")


def list_models() -> list[str]:
    return sorted(
        m.id for m in _get_client().models.list() if m.id.startswith("gpt")
    )
