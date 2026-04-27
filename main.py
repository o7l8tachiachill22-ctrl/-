#!/usr/bin/env python3
"""Interactive CLI for Google Gemini API with Money Forward ME integration."""

import argparse
import sys

import gemini_client


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(description="Google Gemini API CLI")
    parser.add_argument("prompt", nargs="?", help="Prompt to send to Gemini")
    parser.add_argument(
        "--model", default="gemini-1.5-flash", help="Gemini model to use"
    )
    parser.add_argument("--system", help="System instruction")
    parser.add_argument("--stream", action="store_true", help="Stream the response")
    parser.add_argument(
        "--list-models", action="store_true", help="List available models"
    )
    parser.add_argument(
        "--interactive", "-i", action="store_true", help="Interactive chat mode"
    )

    mf_group = parser.add_argument_group("Money Forward ME")
    mf_group.add_argument(
        "--mf-assets",
        action="store_true",
        help="Show asset summary from Money Forward ME",
    )
    mf_group.add_argument(
        "--mf-transactions",
        action="store_true",
        help="Show recent transactions from Money Forward ME",
    )
    mf_group.add_argument(
        "--mf-analyze",
        action="store_true",
        help="Fetch Money Forward ME data and analyze with Gemini",
    )

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


def handle_mf_commands(args: argparse.Namespace) -> bool:
    """Handle Money Forward ME commands. Returns True if a MF command was executed."""
    import moneyforward_client

    if not (args.mf_assets or args.mf_transactions or args.mf_analyze):
        return False

    client = moneyforward_client.MoneyForwardClient()

    if args.mf_assets:
        assets = client.get_assets()
        if assets["total_assets"] is not None:
            print(f"総資産: {assets['total_assets']:,} 円\n")
        if assets["accounts"]:
            print("【口座残高】")
            for acct in assets["accounts"]:
                balance = (
                    f"{acct['balance']:,} 円"
                    if acct["balance"] is not None
                    else "取得不可"
                )
                print(f"  {acct['name']}: {balance}")
        return True

    if args.mf_transactions:
        transactions = client.get_transactions()
        if not transactions:
            print("取引データが見つかりませんでした。")
        else:
            print("【最近の取引】")
            for tx in transactions[:20]:
                line = f"  {tx['date']}  {tx['content']}  {tx['amount']}"
                if tx["category"]:
                    line += f"  [{tx['category']}]"
                print(line)
        return True

    if args.mf_analyze:
        gemini_client.configure()
        summary = client.get_summary_text()
        print(summary)
        print("\n--- Gemini による分析 ---\n")
        analysis_prompt = (
            "以下はマネーフォワードMEの家計データです。\n"
            "資産状況と収支の傾向を分析し、節約・資産運用に関するアドバイスを日本語で教えてください。\n\n"
            + summary
        )
        if args.stream:
            for chunk in gemini_client.stream_chat(
                analysis_prompt, model=args.model, system_instruction=args.system
            ):
                print(chunk, end="", flush=True)
            print()
        else:
            result = gemini_client.chat(
                analysis_prompt, model=args.model, system_instruction=args.system
            )
            print(result)
        return True

    return False


def main() -> None:
    args = parse_args()

    if handle_mf_commands(args):
        return

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
        for chunk in gemini_client.stream_chat(
            args.prompt, model=args.model, system_instruction=args.system
        ):
            print(chunk, end="", flush=True)
        print()
    else:
        result = gemini_client.chat(
            args.prompt, model=args.model, system_instruction=args.system
        )
        print(result)


if __name__ == "__main__":
    main()
