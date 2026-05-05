from .read_file import read_file, TOOL_SCHEMA as READ_FILE_SCHEMA
from .count_text_stats import count_text_stats, TOOL_SCHEMA as COUNT_TEXT_STATS_SCHEMA
from .list_files import list_files, TOOL_SCHEMA as LIST_FILES_SCHEMA

TOOLS = [READ_FILE_SCHEMA, COUNT_TEXT_STATS_SCHEMA, LIST_FILES_SCHEMA]
TOOL_MAP = {
    "read_file": read_file,
    "count_text_stats": count_text_stats,
    "list_files": list_files,
}

__all__ = ["read_file", "count_text_stats", "list_files", "TOOLS", "TOOL_MAP"]
