from .read_file import read_file, TOOL_SCHEMA as READ_FILE_SCHEMA
from .count_text_stats import count_text_stats, TOOL_SCHEMA as COUNT_TEXT_STATS_SCHEMA

TOOLS = [READ_FILE_SCHEMA, COUNT_TEXT_STATS_SCHEMA]
TOOL_MAP = {
    "read_file": read_file,
    "count_text_stats": count_text_stats,
}

__all__ = ["read_file", "count_text_stats", "TOOLS", "TOOL_MAP"]
