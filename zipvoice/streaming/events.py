from dataclasses import dataclass, field
from typing import Any, Callable, Dict, List, Optional

import torch


@dataclass
class ChunkStarted:
    """Fired when a chunk begins processing."""

    chunk_index: int
    total_chunks: int
    num_tokens: int


@dataclass
class ChunkReady:
    """Fired when a chunk's audio is ready for playback."""

    chunk_index: int
    total_chunks: int
    audio: torch.Tensor  # (1, T) waveform at sample_rate
    sample_rate: int
    is_final: bool


@dataclass
class StreamComplete:
    """Fired when all chunks have been generated."""

    total_chunks: int
    total_samples: int
    sample_rate: int


@dataclass
class StreamError:
    """Fired when an error occurs during streaming."""

    chunk_index: int
    error: Exception


Event = ChunkStarted | ChunkReady | StreamComplete | StreamError


class EventBus:
    """Simple publish/subscribe event bus for streaming pipeline events."""

    def __init__(self):
        self._listeners: Dict[type, List[Callable]] = {}

    def on(self, event_type: type, callback: Callable) -> None:
        """Register a callback for a specific event type."""
        self._listeners.setdefault(event_type, []).append(callback)

    def emit(self, event: Any) -> None:
        """Emit an event to all registered listeners."""
        for cb in self._listeners.get(type(event), []):
            cb(event)
