import json
from typing import Any, Dict


def sse_event(data: Dict[str, Any]) -> str:
    """Format a dict as an SSE data line."""
    return f"data: {json.dumps(data)}\n\n"


def sse_done() -> str:
    """Format the SSE stream terminator."""
    return "data: [DONE]\n\n"
