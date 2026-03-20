"""zipvoice.streaming -- real-time streaming TTS pipeline."""

from zipvoice.streaming.buffer import CrossFadeBuffer
from zipvoice.streaming.events import (
    ChunkReady,
    ChunkStarted,
    EventBus,
    PromptReady,
    StreamComplete,
    StreamError,
    TextChunked,
)
from zipvoice.streaming.pipeline import AudioChunk, StreamingConfig, StreamingPipeline
from zipvoice.streaming.stages import AudioGenerator, PromptData, PromptProcessor, TextChunker

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
    "PromptReady",
    "TextChunked",
    "PromptProcessor",
    "PromptData",
    "TextChunker",
    "AudioGenerator",
]
