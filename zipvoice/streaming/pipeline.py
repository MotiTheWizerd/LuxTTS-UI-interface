import logging
from dataclasses import dataclass
from typing import Generator, Optional

import torch

from zipvoice.streaming.buffer import CrossFadeBuffer
from zipvoice.streaming.events import (
    ChunkReady,
    ChunkStarted,
    EventBus,
    StreamComplete,
    StreamError,
)
from zipvoice.streaming.stages import AudioGenerator, PromptProcessor, TextChunker
from zipvoice.utils.infer import remove_silence


@dataclass
class StreamingConfig:
    """Configuration for streaming TTS generation."""

    num_step: int = 16
    guidance_scale: float = 1.0
    speed: float = 1.0
    t_shift: float = 0.5
    target_rms: float = 0.1
    feat_scale: float = 0.1
    sampling_rate: int = 24000
    fade_duration: float = 0.1
    remove_long_sil: bool = False


@dataclass
class AudioChunk:
    """A single chunk of generated audio."""

    audio: torch.Tensor  # (1, T)
    chunk_index: int
    total_chunks: int
    is_final: bool
    sample_rate: int


class StreamingPipeline:
    """Orchestrator for streaming TTS generation.

    Composes PromptProcessor, TextChunker, AudioGenerator, and CrossFadeBuffer
    to yield audio chunks as soon as each text segment is synthesized.

    Usage:
        pipeline = StreamingPipeline(model, vocoder, tokenizer, feature_extractor, device)

        # Generator mode — pull chunks as they're ready
        for chunk in pipeline.stream(text, prompt_text, prompt_wav_path):
            play_audio(chunk.audio, chunk.sample_rate)

        # Callback mode — push chunks to listeners
        pipeline.events.on(ChunkReady, lambda e: play_audio(e.audio, e.sample_rate))
        pipeline.run(text, prompt_text, prompt_wav_path)
    """

    def __init__(
        self,
        model: torch.nn.Module,
        vocoder: torch.nn.Module,
        tokenizer,
        feature_extractor,
        device: torch.device,
        config: Optional[StreamingConfig] = None,
    ):
        self.config = config or StreamingConfig()
        self.events = EventBus()

        self._prompt_processor = PromptProcessor(tokenizer, feature_extractor, device)
        self._chunker = TextChunker(tokenizer)
        self._generator = AudioGenerator(model, vocoder, device)

    def stream(
        self,
        text: str,
        prompt_text: str,
        prompt_wav_path: str,
    ) -> Generator[AudioChunk, None, None]:
        """Generate audio chunks as a Python generator.

        Yields AudioChunk objects as each text segment is synthesized.
        Cross-fade is applied incrementally between chunks.
        """
        cfg = self.config
        buffer = CrossFadeBuffer(
            fade_duration=cfg.fade_duration, sample_rate=cfg.sampling_rate
        )

        # Prepare prompt (one-time cost)
        prompt = self._prompt_processor.prepare(
            prompt_wav_path,
            prompt_text,
            sampling_rate=cfg.sampling_rate,
            target_rms=cfg.target_rms,
            feat_scale=cfg.feat_scale,
            events=self.events,
        )

        # Chunk the input text
        chunked_tokens, _ = self._chunker.chunk(
            text,
            prompt.tokens_str_len,
            prompt.duration,
            speed=cfg.speed,
            events=self.events,
        )
        total_chunks = len(chunked_tokens)

        total_samples = 0
        for i, tokens in enumerate(chunked_tokens):
            is_last = i == total_chunks - 1

            self.events.emit(
                ChunkStarted(chunk_index=i, total_chunks=total_chunks, num_tokens=len(tokens))
            )

            try:
                raw_audio = self._generator.generate(
                    tokens,
                    prompt.tokens,
                    prompt.features,
                    prompt.rms,
                    speed=cfg.speed,
                    t_shift=cfg.t_shift,
                    num_step=cfg.num_step,
                    guidance_scale=cfg.guidance_scale,
                    feat_scale=cfg.feat_scale,
                    target_rms=cfg.target_rms,
                )
            except Exception as ex:
                self.events.emit(StreamError(chunk_index=i, error=ex))
                logging.error(f"Chunk {i} failed: {ex}")
                continue

            playable = buffer.push(raw_audio, is_final=is_last)
            total_samples += playable.shape[-1]

            chunk = AudioChunk(
                audio=playable,
                chunk_index=i,
                total_chunks=total_chunks,
                is_final=is_last,
                sample_rate=cfg.sampling_rate,
            )

            self.events.emit(
                ChunkReady(
                    chunk_index=i,
                    total_chunks=total_chunks,
                    audio=playable,
                    sample_rate=cfg.sampling_rate,
                    is_final=is_last,
                )
            )

            yield chunk

        # Flush any remaining audio in the buffer
        remaining = buffer.flush()
        if remaining is not None and remaining.shape[-1] > 0:
            total_samples += remaining.shape[-1]
            yield AudioChunk(
                audio=remaining,
                chunk_index=total_chunks - 1,
                total_chunks=total_chunks,
                is_final=True,
                sample_rate=cfg.sampling_rate,
            )

        self.events.emit(
            StreamComplete(
                total_chunks=total_chunks,
                total_samples=total_samples,
                sample_rate=cfg.sampling_rate,
            )
        )

    def run(
        self,
        text: str,
        prompt_text: str,
        prompt_wav_path: str,
    ) -> torch.Tensor:
        """Event-driven mode: process all chunks, emitting events.

        Returns the full concatenated waveform (for convenience / saving).
        """
        all_audio = [chunk.audio for chunk in self.stream(text, prompt_text, prompt_wav_path)]

        if not all_audio:
            return torch.tensor([])

        full_wav = torch.cat(all_audio, dim=-1)
        full_wav = remove_silence(
            full_wav,
            self.config.sampling_rate,
            only_edge=not self.config.remove_long_sil,
            trail_sil=0,
        )

        return full_wav
