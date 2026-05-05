"""List files and directories in a specified directory."""

from pathlib import Path

TOOL_SCHEMA = {
    "type": "function",
    "function": {
        "name": "list_files",
        "description": "List files and directories in the specified directory.",
        "parameters": {
            "type": "object",
            "properties": {
                "directory": {
                    "type": "string",
                    "description": "The directory path to list",
                }
            },
            "required": ["directory"],
        },
    },
}


def list_files(directory: str) -> dict:
    """List files and directories in the given directory."""
    p = Path(directory)
    if not p.exists():
        return {"error": f"'{directory}' does not exist"}
    if not p.is_dir():
        return {"error": f"'{directory}' is not a directory"}
    entries = sorted(p.iterdir())
    return {
        "path": str(p.resolve()),
        "entries": [
            {"name": e.name, "type": "dir" if e.is_dir() else "file"}
            for e in entries
        ],
    }
