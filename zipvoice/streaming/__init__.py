"""zipvoice.streaming -- real-time streaming TTS pipeline."""

from zipvoice.streaming.buffer import CrossFadeBuffer
from zipvoice.streaming.events import (
    ChunkReady,
    ChunkStarted,
    EventBus,
    StreamComplete,
    StreamError,
)
from zipvoice.streaming.pipeline import AudioChunk, StreamingConfig, StreamingPipeline

__all__ = [
    "StreamingPipeline",
    "StreamingConfig",
    "AudioChunk",
    "CrossFadeBuffer",
    "EventBus",
    "ChunkStarted",
    "ChunkReady",
    "StreamComplete",
    "StreamError",
]
