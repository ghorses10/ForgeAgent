"""Count characters, words, and lines in a given text."""

TOOL_SCHEMA = {
    "type": "function",
    "function": {
        "name": "count_text_stats",
        "description": "Count the number of characters, words, and lines in a given text.",
        "parameters": {
            "type": "object",
            "properties": {
                "text": {
                    "type": "string",
                    "description": "The text to analyze",
                }
            },
            "required": ["text"],
        },
    },
}


def count_text_stats(text: str) -> dict:
    """Count characters, words, and lines in the given text."""
    return {
        "characters": len(text),
        "words": len(text.split()),
        "lines": text.count("\n") + 1 if text else 0,
    }
