"""ForgeAgent CLI — multi-turn dialog with history, supports OpenAI & Anthropic."""

import argparse
import json
import sys
import os
from dataclasses import dataclass, field
from typing import Any, Literal

from dotenv import load_dotenv
from tools import TOOLS, TOOL_MAP

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
    role: Literal["user", "assistant", "tool"]
    content: Any  # str for user/tool, str | list[dict] for assistant
    tool_calls: list[dict] = field(default_factory=list)  # only assistant role
    tool_call_id: str = ""  # only tool role


@dataclass
class State:
    messages: list[Message] = field(default_factory=list)
    system_prompt: str = ""

    def add_user(self, content: str):
        self.messages.append(Message(role="user", content=content))

    def add_assistant(self, content, tool_calls=None):
        self.messages.append(Message(
            role="assistant", content=content, tool_calls=tool_calls or []
        ))

    def add_tool(self, tool_call_id: str, content: str):
        self.messages.append(Message(role="tool", content=content, tool_call_id=tool_call_id))

    def to_openai(self) -> list[dict]:
        msgs = []
        if self.system_prompt:
            msgs.append({"role": "system", "content": self.system_prompt})
        for m in self.messages:
            if m.role == "assistant" and m.tool_calls:
                msgs.append({"role": "assistant", "content": m.content, "tool_calls": m.tool_calls})
            elif m.role == "tool":
                msgs.append({"role": "tool", "tool_call_id": m.tool_call_id, "content": m.content})
            else:
                msgs.append({"role": m.role, "content": m.content})
        return msgs

    def to_anthropic(self) -> tuple[str, list[dict]]:
        msgs = []
        pending_tool_results = []
        for m in self.messages:
            if m.role == "tool":
                pending_tool_results.append({
                    "type": "tool_result",
                    "tool_use_id": m.tool_call_id,
                    "content": m.content,
                })
            else:
                if pending_tool_results:
                    msgs.append({"role": "user", "content": pending_tool_results})
                    pending_tool_results = []
                msgs.append({"role": m.role, "content": m.content})
        if pending_tool_results:
            msgs.append({"role": "user", "content": pending_tool_results})
        return self.system_prompt, msgs


def call_openai(client, model, state, tools=None):
    kwargs = {"model": model, "messages": state.to_openai()}
    if tools:
        kwargs["tools"] = tools
    response = client.chat.completions.create(**kwargs)
    return response.choices[0].message


def openai_to_anthropic_tools(tools):
    """Convert OpenAI tool schema to Anthropic format."""
    result = []
    for t in tools:
        func = t["function"]
        result.append({
            "name": func["name"],
            "description": func["description"],
            "input_schema": func["parameters"],
        })
    return result


def call_anthropic(client, model, state, tools=None):
    system, messages = state.to_anthropic()
    kwargs = {"model": model, "messages": messages, "max_tokens": 4096}
    if system:
        kwargs["system"] = system
    if tools:
        kwargs["tools"] = openai_to_anthropic_tools(tools)
    response = client.messages.create(**kwargs)
    return response


def dispatch_tool(name, arguments):
    """Execute a tool by name with given arguments."""
    func = TOOL_MAP.get(name)
    if not func:
        return f"Error: unknown tool '{name}'"
    return func(**arguments)


def process_response(provider, response):
    """Extract tool_calls and text from an LLM response.

    Returns (tool_calls, text) where tool_calls is a list of (id, name, args_dict),
    or ([], text) if the model returned a plain text response.
    """
    if provider == "openai":
        if response.tool_calls:
            results = []
            for tc in response.tool_calls:
                args = json.loads(tc.function.arguments) if isinstance(tc.function.arguments, str) else tc.function.arguments
                results.append((tc.id, tc.function.name, args))
            return results, response.content or ""
        return [], response.content or ""
    else:
        if response.stop_reason == "tool_use":
            results = []
            for block in response.content:
                if block.type == "tool_use":
                    results.append((block.id, block.name, block.input))
            return results, ""
        # Extract text from content blocks
        text = ""
        for block in response.content:
            if block.type == "text":
                text += block.text
        return [], text


def run_agent_loop(call_fn, client, model, provider, state):
    """Run the tool-call loop until the model produces a text-only response."""
    while True:
        response = call_fn(client, model, state, tools=TOOLS)
        tool_calls, text = process_response(provider, response)

        if not tool_calls:
            # No tool calls — store the final assistant reply and return it
            state.add_assistant(text)
            return text

        # Store the assistant message that requested tool calls
        if provider == "openai":
            assistant_tool_calls = response.tool_calls
            state.add_assistant(text, tool_calls=assistant_tool_calls)
        else:
            # For Anthropic, store the full content list
            state.add_assistant(response.content)

        # Execute each tool call and add results to state
        for tc_id, name, args in tool_calls:
            print(f"  [tool] {name}({args})")
            result = dispatch_tool(name, args)
            result_str = result if isinstance(result, str) else json.dumps(result)
            state.add_tool(tc_id, result_str)


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
                reply = run_agent_loop(call_fn, client, MODEL, PROVIDER, state)
                print(f"Agent: {reply}")
            except (EOFError, KeyboardInterrupt):
                print("\nExiting.")
                break
    elif args.message:
        state.add_user(args.message)
        reply = run_agent_loop(call_fn, client, MODEL, PROVIDER, state)
        print(reply)
    else:
        parser.print_help()
        sys.exit(1)


if __name__ == "__main__":
    main()
