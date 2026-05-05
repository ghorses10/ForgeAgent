"""ForgeAgent CLI — multi-turn dialog with history, supports OpenAI & Anthropic, no tools yet. """

import argparse
import sys
import os
from dataclasses import dataclass, field
from typing import Literal

from dotenv import load_dotenv

load_dotenv()

PROVIDER = os.getenv("FORGE_AGENT_PROVIDER", "openai")  # "openai" or "anthropic"
BASE_URL = os.getenv("FORGE_AGENT_BASE_URL")
API_KEY = os.getenv("FORGE_AGENT_API_KEY")
MODEL = os.getenv("FORGE_AGENT_MODEL")
SYSTEM_PROMPT = os.getenv("FORGE_AGENT_SYSTEM_PROMPT", "")

if PROVIDER not in ("openai", "anthropic"):
    print(f"Error: FORGE_AGENT_PROVIDER must be 'openai' or 'anthropic', got '{PROVIDER}'", file=sys.stderr)
    sys.exit(1)

for var, val in [("FORGE_AGENT_API_KEY", API_KEY), ("FORGE_AGENT_MODEL", MODEL)]:
    if not val:
        print(f"Error: {var} is not set in .env", file=sys.stderr)
        sys.exit(1)

if PROVIDER == "openai" and not BASE_URL:
    print("Error: FORGE_AGENT_BASE_URL is required for openai provider", file=sys.stderr)
    sys.exit(1)


@dataclass
class Message:
    role: Literal["user", "assistant"]
    content: str


@dataclass
class State:
    messages: list[Message] = field(default_factory=list)
    system_prompt: str = ""

    def add_user(self, content: str):
        self.messages.append(Message(role="user", content=content))

    def add_assistant(self, content: str):
        self.messages.append(Message(role="assistant", content=content))

    def to_openai(self) -> list[dict]:
        msgs = []
        if self.system_prompt:
            msgs.append({"role": "system", "content": self.system_prompt})
        msgs.extend({"role": m.role, "content": m.content} for m in self.messages)
        return msgs

    def to_anthropic(self) -> tuple[str, list[dict]]:
        msgs = [{"role": m.role, "content": m.content} for m in self.messages]
        return self.system_prompt, msgs


def call_openai(client, model, state):
    response = client.chat.completions.create(
        model=model,
        messages=state.to_openai(),
    )
    return response.choices[0].message.content


def call_anthropic(client, model, state):
    system, messages = state.to_anthropic()
    kwargs = {"model": model, "messages": messages, "max_tokens": 4096}
    if system:
        kwargs["system"] = system
    response = client.messages.create(**kwargs)
    return response.content[0].text


def main():
    parser = argparse.ArgumentParser(description="ForgeAgent CLI")
    parser.add_argument("message", nargs="?", help="Message to send to the LLM")
    parser.add_argument("--interactive", "-i", action="store_true", help="Interactive chat mode")
    args = parser.parse_args()

    if PROVIDER == "anthropic":
        import anthropic
        client = anthropic.Anthropic(api_key=API_KEY)
        call_fn = call_anthropic
    else:
        from openai import OpenAI
        client = OpenAI(base_url=BASE_URL, api_key=API_KEY)
        call_fn = call_openai

    state = State(system_prompt=SYSTEM_PROMPT)

    if args.interactive or not args.message:
        print(f"ForgeAgent CLI [{PROVIDER}] (type 'quit' or 'exit' to exit)")
        while True:
            try:
                user_input = input("You: ")
                if user_input.lower() in ("quit", "exit"):
                    break
                state.add_user(user_input)
                reply = call_fn(client, MODEL, state)
                state.add_assistant(reply)
                print(f"Agent: {reply}")
            except (EOFError, KeyboardInterrupt):
                print("\nExiting.")
                break
    elif args.message:
        state.add_user(args.message)
        reply = call_fn(client, MODEL, state)
        print(reply)
    else:
        parser.print_help()
        sys.exit(1)


if __name__ == "__main__":
    main()
