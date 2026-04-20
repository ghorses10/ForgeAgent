# ForgeAgent v0 — 从零构建通用对话 Agent

## Context

在空目录 `ForgeAgent` 中，从零构建一个用于研究/学习的 v0 基础通用对话 Agent。
目标是理解 Agent 架构原理，代码结构清晰、依赖极简，不依赖 LangChain 等重框架。
LLM 接入层使用 OpenAI Python SDK，支持自定义 `base_url` + `api_key`（OpenAI 兼容接口）。

---

## 项目结构

```
ForgeAgent/
├── forgeagent/
│   ├── __init__.py                  # 导出公开接口
│   ├── version.py                   # __version__ = "0.1.0"
│   ├── client/
│   │   ├── __init__.py
│   │   └── llm_client.py            # LLM 客户端封装（OpenAI SDK）
│   ├── history/
│   │   ├── __init__.py
│   │   └── conversation_history.py  # 消息存储与轮数截断
│   ├── tools/
│   │   ├── __init__.py
│   │   ├── tool.py                  # @tool 装饰器 + Tool 类
│   │   ├── tool_registry.py         # 工具注册表（全局单例）
│   │   └── tool_call.py             # 工具调用执行器
│   ├── agent/
│   │   ├── __init__.py
│   │   ├── agent.py                 # Agent 主循环
│   │   └── prompts.py               # system prompt 模板
│   └── cli/
│       ├── __init__.py
│       └── main.py                  # CLI 入口（argparse）
├── .env.example                     # 环境变量示例
├── requirements.txt
├── PLAN.md                          # 本文件
└── README.md
```

---

## 核心模块设计

### 1. `llm_client.py` — LLM 客户端

```python
class LLMClient:
    def __init__(self, base_url: str, api_key: str, model: str, timeout: float = 120.0)
    def chat(self, messages: list[dict], tools: list[dict] | None = None) -> ChatResponse
```

- 组合 `openai.OpenAI(base_url=..., api_key=...)` 客户端
- 返回结构化 `ChatResponse(content, tool_calls, finish_reason)`，屏蔽 SDK 细节

### 2. `conversation_history.py` — 对话历史

```python
class ConversationHistory:
    def __init__(self, max_turns: int = 20)
    def add_user(self, content: str)
    def add_assistant(self, content: str, tool_calls=None)
    def add_tool_result(self, tool_call_id: str, content: str)
    def add_system(self, content: str)
    def to_list(self) -> list[dict]   # 导出给 LLM client
    def truncate(self)                # 截断到 max_turns，保留 system 消息
    def clear(self)
```

- 用 `dataclass Message` 存储，类型安全
- v0 使用**固定轮数截断**策略（简单有效）

### 3. `tool.py` — 工具装饰器

```python
@tool(name="calculator", description="...", param_schema={...})
def calculator(expression: str) -> str: ...
```

- `@tool` 装饰器将普通函数包装为 `Tool` 对象
- `Tool.invoke(**kwargs) -> str`，内部捕获异常避免崩溃

### 4. `tool_registry.py` — 工具注册表

```python
class ToolRegistry:
    def register(self, tool: Tool)
    def get(self, name: str) -> Tool | None
    def get_openai_schema(self) -> list[dict]  # 导出 OpenAI function calling 格式

registry = ToolRegistry()  # 全局单例
```

### 5. `tool_call.py` — 工具执行器

```python
class ToolCallExecutor:
    def execute_tool_calls(self, tool_calls: list) -> list[ToolCallResult]
```

- 解析 LLM 返回的 `tool_calls`，查询 `registry` 执行，返回 `ToolCallResult(id, name, content)`

### 6. `agent.py` — Agent 主循环（核心）

```python
class Agent:
    def __init__(self, llm_client, history, tool_executor, system_prompt=DEFAULT_SYSTEM_PROMPT)
    def run(self, user_message: str) -> str
```

主循环逻辑（ReAct 风格）：
```
add_user(message)
while True:
    response = llm.chat(history.to_list(), tools=registry.get_openai_schema())
    if response.tool_calls:
        add_assistant(tool_calls=...)
        results = executor.execute_tool_calls(response.tool_calls)
        for r in results: add_tool_result(r.id, r.content)
    else:
        add_assistant(response.content)
        return response.content
```

### 7. `cli/main.py` — CLI 入口

```bash
# 交互模式
python -m forgeagent.cli.main --interactive

# 单轮问答
python -m forgeagent.cli.main "你好"

# 指定模型和接口
python -m forgeagent.cli.main --base-url https://... --api-key sk-xxx --model gpt-4o -i
```

配置优先级：**命令行参数 > 环境变量 > `.env` 文件**

---

## 依赖清单

```
openai>=1.50.0
python-dotenv>=1.0.0
```

仅两个依赖，无框架锁定。

---

## 配置方式 (`.env.example`)

```env
FORGE_AGENT_BASE_URL=https://api.openai.com/v1
FORGE_AGENT_API_KEY=sk-xxxxx
FORGE_AGENT_MODEL=gpt-4o-mini
```

---

## v0 边界

**包含：**
- OpenAI 兼容接口调用（自定义 base_url + api_key）
- 多轮对话历史管理（固定轮数截断）
- Function Calling 完整流程（注册 → 执行 → 返回结果 → 继续对话）
- CLI 交互模式 + 单轮问答模式
- .env 配置支持
- 工具异常隔离

**v1 留待实现：**
- 流式输出（streaming）
- 按 token 数截断历史（tiktoken）
- 工具并行执行（asyncio）
- 历史持久化
- MCP 协议接入

---

## 文件创建顺序

1. `requirements.txt` + `.env.example`
2. `forgeagent/version.py`
3. `forgeagent/client/llm_client.py`
4. `forgeagent/history/conversation_history.py`
5. `forgeagent/tools/tool.py`
6. `forgeagent/tools/tool_registry.py`
7. `forgeagent/tools/tool_call.py`
8. `forgeagent/agent/prompts.py`
9. `forgeagent/agent/agent.py`
10. 所有 `__init__.py`（各包 + 顶层导出）
11. `forgeagent/cli/main.py`
12. `README.md`

---

## 验证方式

1. 安装依赖：`pip install -r requirements.txt`
2. 复制 `.env.example` 为 `.env`，填入真实的 base_url 和 api_key
3. 运行交互模式：`python -m forgeagent.cli.main --interactive`
4. 测试纯文本对话：输入 "你好，介绍一下自己"，验证返回正常
5. 注册一个测试工具（如计算器），测试 function calling 流程：输入 "帮我计算 123 * 456"
6. 验证多轮对话上下文保持：连续提问后询问 "我刚才问了什么"，验证历史正常
