# ForgeAgent

Minimal Python Agent framework for research and learning. No heavy frameworks (LangChain, LlamaIndex, etc.).

## Setup

```bash
pip install -r requirements.txt
cp .env.example .env  # fill in your API key and endpoint
```

## Run

```bash
python main.py "Hello"           # single turn
python main.py --interactive     # interactive chat (default when no args)
```

Or use the launcher scripts:

```bash
./run.sh "Hello"      # Linux/Mac
run.bat "Hello"       # Windows
```

## Current Features

- Multi-turn dialog with conversation history
- Dual provider support: OpenAI-compatible API and Anthropic native API
- System prompt support
- Interactive mode (default) and single-turn mode

## Project Plan

See [PLAN.md](./PLAN.md) for the full development roadmap.
