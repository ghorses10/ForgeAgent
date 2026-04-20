# ForgeAgent

Minimal Python Agent framework for research and learning. No heavy frameworks (LangChain, LlamaIndex, etc.).

## Setup

```bash
pip install -r requirements.txt
cp .env.example .env  # fill in your FORGE_AGENT_BASE_URL and FORGE_AGENT_API_KEY
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

## Step 1 — What exists

- Single-turn or interactive LLM dialog via OpenAI-compatible API
- No history, no tools, no agent loop (those come in later steps)

## Project Plan

See [PLAN.md](./PLAN.md) for the full development roadmap.
