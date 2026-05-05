# ForgeAgent

Minimal Python Agent framework for research and learning. No heavy frameworks (LangChain, LlamaIndex, etc.). The LLM backend uses any OpenAI-compatible API or Anthropic native API.

## Setup

```bash
pip install -r requirements.txt
cp .env.example .env  # fill in your API key and endpoint
```

Required env vars:

```
FORGE_AGENT_PROVIDER=openai        # "openai" or "anthropic"
FORGE_AGENT_BASE_URL=https://...   # OpenAI-compatible endpoint (required for openai)
FORGE_AGENT_API_KEY=sk-xxx
FORGE_AGENT_MODEL=gpt-4o-mini
```

## Run

```bash
python main.py "Hello"           # single turn
python main.py --interactive     # interactive chat (default when no args)
```

## Architecture

```
main.py            — entry point, CLI, State, agent loop
tools/
  __init__.py      — TOOLS (schema list) and TOOL_MAP (name → function)
  read_file.py     — read_file tool
  count_text_stats.py — count_text_stats tool
```

### Key Components (all in main.py)

- **State** — conversation history as a list of `Message` objects, with `to_openai()` and `to_anthropic()` serializers
- **run_agent_loop()** — the core loop: call LLM → if tool_calls, execute tools and feed results back → repeat until model returns text
- **dispatch_tool()** — looks up tool by name in `TOOL_MAP` and calls it
- **process_response()** — extracts `(tool_calls, text)` from LLM response, supports both OpenAI and Anthropic formats

### Tool Calling Flow

```
User message → LLM → tool_calls? ──no──→ return text
                          │
                         yes
                          │
                   execute tools
                          │
                   add results to state
                          │
                   loop back to LLM
```

## Current Features

- Multi-turn dialog with conversation history
- Tool calling with agent loop (tool results fed back to model)
- Dual provider support: OpenAI-compatible API and Anthropic native API
- System prompt support
- Interactive mode (default) and single-turn mode
- Built-in tools: `read_file`, `count_text_stats`

## Project Plan

See [PLAN.md](./PLAN.md) for the full development roadmap.
