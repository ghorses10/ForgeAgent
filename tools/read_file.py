"""Read a file and return its content."""

from pathlib import Path

TOOL_SCHEMA = {
    "type": "function",
    "function": {
        "name": "read_file",
        "description": "Read a file and return its content as string.",
        "parameters": {
            "type": "object",
            "properties": {
                "path": {
                    "type": "string",
                    "description": "The file path to read",
                }
            },
            "required": ["path"],
        },
    },
}


def read_file(path: str) -> str:
    """Read a file and return its content as string."""
    p = Path(path)
    if not p.exists():
        return f"Error: file '{path}' does not exist"
    if not p.is_file():
        return f"Error: '{path}' is not a file"
    try:
        return p.read_text(encoding="utf-8")
    except Exception as e:
        return f"Error reading '{path}': {e}"
