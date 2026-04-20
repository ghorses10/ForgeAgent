"""ForgeAgent CLI — single-turn LLM dialog, no history, no tools."""

import argparse
import sys
import os
from pathlib import Path

from dotenv import load_dotenv
from openai import OpenAI

load_dotenv()

BASE_URL = os.getenv("FORGE_AGENT_BASE_URL")
API_KEY = os.getenv("FORGE_AGENT_API_KEY")
MODEL = os.getenv("FORGE_AGENT_MODEL")

for var, val in [("FORGE_AGENT_BASE_URL", BASE_URL), ("FORGE_AGENT_API_KEY", API_KEY), ("FORGE_AGENT_MODEL", MODEL)]:
    if not val:
        print(f"Error: {var} is not set in .env", file=sys.stderr)
        sys.exit(1)


def main():
    parser = argparse.ArgumentParser(description="ForgeAgent CLI")
    parser.add_argument("message", nargs="?", help="Message to send to the LLM")
    parser.add_argument("--interactive", "-i", action="store_true", help="Interactive chat mode")
    args = parser.parse_args()

    client = OpenAI(base_url=BASE_URL, api_key=API_KEY)

    if args.interactive or not args.message:
        print("ForgeAgent CLI (type 'quit' or 'exit' to exit)")
        while True:
            try:
                user_input = input("You: ")
                if user_input.lower() in ("quit", "exit"):
                    break
                response = client.chat.completions.create(
                    model=MODEL,
                    messages=[{"role": "user", "content": user_input}],
                )
                print(f"Agent: {response.choices[0].message.content}")
            except (EOFError, KeyboardInterrupt):
                print("\nExiting.")
                break
    elif args.message:
        response = client.chat.completions.create(
            model=MODEL,
            messages=[{"role": "user", "content": args.message}],
        )
        print(response.choices[0].message.content)
    else:
        parser.print_help()
        sys.exit(1)


if __name__ == "__main__":
    main()
