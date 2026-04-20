# CLAUDE.md

This file provides guidance to Claude Code (claude.ai/code) when working with code in this repository.

## Project Overview

ForgeAgent is a minimal Python Agent framework built from scratch for research and learning purposes. It deliberately avoids heavy frameworks (LangChain, LlamaIndex, etc.) to keep the architecture transparent and educational. The LLM backend uses any OpenAI-compatible API (custom `base_url` + `api_key`).

## Setup

```bash
pip install -r requirements.txt
cp .env.example .env  # then fill in your credentials
```

Required env vars (`.env` or shell environment):
```
FORGE_AGENT_BASE_URL=https://...   # OpenAI-compatible endpoint
FORGE_AGENT_API_KEY=sk-xxx
FORGE_AGENT_MODEL=gpt-4o-mini
```

## Running

```bash
# Interactive multi-turn chat
python -m forgeagent.cli.main --interactive

# Single-turn query
python -m forgeagent.cli.main "your question here"

# Override model/endpoint at runtime
python -m forgeagent.cli.main --base-url https://... --api-key sk-xxx --model gpt-4o -i
```

Config priority: CLI args > env vars > `.env` file.

## Architecture

The codebase is organized as four loosely-coupled layers:

```
CLI (cli/main.py)
    └── Agent loop (agent/agent.py)
            ├── LLMClient (client/llm_client.py)      — wraps openai SDK
            ├── ConversationHistory (history/)         — message store + truncation
            └── ToolCallExecutor (tools/tool_call.py)  — dispatches function calls
                    └── ToolRegistry (tools/tool_registry.py)  — global tool store
                            └── Tool (tools/tool.py)           — @tool decorator
```

### Key Design Decisions

- **`LLMClient.chat()`** returns a structured `ChatResponse(content, tool_calls, finish_reason)` — never expose raw SDK objects to upper layers.
- **`ConversationHistory`** stores messages as `dataclass Message` internally and exports `list[dict]` to the LLM. v0 uses fixed-turn truncation (`max_turns=20`), always preserving the system message.
- **`ToolRegistry`** is a global singleton (`registry = ToolRegistry()` in `tool_registry.py`). Register tools by importing them; the registry is queried at call time via `registry.get_openai_schema()`.
- **`@tool` decorator** wraps plain Python functions into `Tool` objects. `Tool.invoke()` catches all exceptions and returns an error string rather than raising — tool failures must never crash the agent loop.
- **Agent main loop** (`Agent.run()`) cycles until the LLM returns a plain-text response: `add_user → chat → [execute tools → chat]* → return`.

### Adding a New Tool

```python
from forgeagent.tools.tool import tool
from forgeagent.tools.tool_registry import registry

@tool(
    name="get_weather",
    description="Get current weather for a city",
    param_schema={
        "type": "object",
        "properties": {"city": {"type": "string"}},
        "required": ["city"],
    },
)
def get_weather(city: str) -> str:
    return f"Sunny in {city}"

registry.register(get_weather)
```

## v0 Scope

v0 is intentionally synchronous and simple. The following are **deferred to v1**:
- Streaming output
- Token-based history truncation (tiktoken)
- Parallel tool execution (asyncio)
- History persistence
- MCP protocol integration
