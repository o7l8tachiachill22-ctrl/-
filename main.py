#!/usr/bin/env python3
"""Interactive CLI for Google Gemini API."""

import argparse
import sys

import gemini_client


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(description="Google Gemini API CLI")
    parser.add_argument("prompt", nargs="?", help="Prompt to send to Gemini")
    parser.add_argument("--model", default="gemini-1.5-flash", help="Gemini model to use")
    parser.add_argument("--system", help="System instruction")
    parser.add_argument("--stream", action="store_true", help="Stream the response")
    parser.add_argument("--list-models", action="store_true", help="List available models")
    parser.add_argument("--interactive", "-i", action="store_true", help="Interactive chat mode")
    return parser.parse_args()


def interactive_mode(model: str, system: str | None) -> None:
    print(f"Gemini interactive chat ({model}). Type 'quit' or 'exit' to stop.\n")

    import google.generativeai as genai
    kwargs = {}
    if system:
        kwargs["system_instruction"] = system
    m = genai.GenerativeModel(model, **kwargs)
    session = m.start_chat(history=[])

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

        response = session.send_message(user_input)
        print(f"Gemini: {response.text}\n")


def main() -> None:
    args = parse_args()
    gemini_client.configure()

    if args.list_models:
        for name in gemini_client.list_models():
            print(name)
        return

    if args.interactive:
        interactive_mode(args.model, args.system)
        return

    if not args.prompt:
        print("Error: provide a prompt or use --interactive mode.", file=sys.stderr)
        sys.exit(1)

    if args.stream:
        for chunk in gemini_client.stream_chat(args.prompt, model=args.model, system_instruction=args.system):
            print(chunk, end="", flush=True)
        print()
    else:
        result = gemini_client.chat(args.prompt, model=args.model, system_instruction=args.system)
        print(result)


if __name__ == "__main__":
    main()
