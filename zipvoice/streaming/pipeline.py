import logging
from dataclasses import dataclass
from typing import Generator, List, Optional, Tuple

import torch

from zipvoice.streaming.buffer import CrossFadeBuffer
from zipvoice.streaming.events import (
    ChunkReady,
    ChunkStarted,
    EventBus,
    StreamComplete,
    StreamError,
)
from zipvoice.utils.infer import (
    add_punctuation,
    chunk_tokens_punctuation,
    load_prompt_wav,
    remove_silence,
    rms_norm,
)


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
    """Generator-based streaming TTS pipeline.

    Yields audio chunks as soon as each text segment is synthesized,
    enabling playback to start before the full utterance is complete.

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
        self.model = model
        self.vocoder = vocoder
        self.tokenizer = tokenizer
        self.feature_extractor = feature_extractor
        self.device = device
        self.config = config or StreamingConfig()
        self.events = EventBus()

    def _prepare_prompt(
        self, prompt_wav_path: str, prompt_text: str
    ) -> Tuple[torch.Tensor, torch.Tensor, List[List[int]], float]:
        """Load, normalize, and featurize the prompt audio."""
        cfg = self.config

        prompt_wav = load_prompt_wav(prompt_wav_path, sampling_rate=cfg.sampling_rate)
        prompt_wav = remove_silence(
            prompt_wav, cfg.sampling_rate, only_edge=False, trail_sil=200
        )
        prompt_wav, prompt_rms = rms_norm(prompt_wav, cfg.target_rms)

        prompt_duration = prompt_wav.shape[-1] / cfg.sampling_rate
        if prompt_duration > 20:
            logging.warning(
                f"Prompt wav is very long ({prompt_duration:.1f}s). "
                "1-3 seconds is recommended."
            )

        prompt_features = self.feature_extractor.extract(
            prompt_wav, sampling_rate=cfg.sampling_rate
        ).to(self.device)
        prompt_features = prompt_features.unsqueeze(0) * cfg.feat_scale

        prompt_text = add_punctuation(prompt_text)
        prompt_tokens_str = self.tokenizer.texts_to_tokens([prompt_text])[0]
        prompt_tokens = self.tokenizer.tokens_to_token_ids([prompt_tokens_str])

        return prompt_features, prompt_wav, prompt_tokens, prompt_rms

    def _chunk_text(
        self,
        text: str,
        prompt_tokens_str_len: int,
        prompt_duration: float,
    ) -> Tuple[List[List[int]], List[List[str]]]:
        """Tokenize and chunk text at punctuation boundaries."""
        cfg = self.config

        text = add_punctuation(text)
        tokens_str = self.tokenizer.texts_to_tokens([text])[0]

        token_duration = prompt_duration / (prompt_tokens_str_len * cfg.speed)
        max_tokens = int((25 - prompt_duration) / token_duration)

        chunked_tokens_str = chunk_tokens_punctuation(tokens_str, max_tokens=max_tokens)
        chunked_tokens = self.tokenizer.tokens_to_token_ids(chunked_tokens_str)

        return chunked_tokens, chunked_tokens_str

    def _generate_chunk_audio(
        self,
        tokens: List[int],
        prompt_tokens: List[List[int]],
        prompt_features: torch.Tensor,
        prompt_rms: float,
    ) -> torch.Tensor:
        """Run diffusion + vocoder for a single chunk. Returns (1, T) waveform."""
        cfg = self.config

        prompt_features_lens = torch.full(
            (1,), prompt_features.size(1), device=self.device
        )

        pred_features, pred_features_lens, _, _ = self.model.sample(
            tokens=[tokens],
            prompt_tokens=prompt_tokens,
            prompt_features=prompt_features,
            prompt_features_lens=prompt_features_lens,
            speed=cfg.speed,
            t_shift=cfg.t_shift,
            duration="predict",
            num_step=cfg.num_step,
            guidance_scale=cfg.guidance_scale,
        )

        pred_features = pred_features.permute(0, 2, 1) / cfg.feat_scale
        wav = (
            self.vocoder.decode(pred_features[:, :, : pred_features_lens[0]])
            .squeeze(1)
            .clamp(-1, 1)
        )

        if prompt_rms < cfg.target_rms:
            wav = wav * prompt_rms / cfg.target_rms

        return wav

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
        prompt_features, prompt_wav, prompt_tokens, prompt_rms = self._prepare_prompt(
            prompt_wav_path, prompt_text
        )
        prompt_text_added = add_punctuation(prompt_text)
        prompt_tokens_str = self.tokenizer.texts_to_tokens([prompt_text_added])[0]
        prompt_duration = prompt_wav.shape[-1] / cfg.sampling_rate

        # Chunk the input text
        chunked_tokens, _ = self._chunk_text(
            text, len(prompt_tokens_str), prompt_duration
        )
        total_chunks = len(chunked_tokens)

        total_samples = 0
        for i, tokens in enumerate(chunked_tokens):
            is_last = i == total_chunks - 1

            self.events.emit(
                ChunkStarted(chunk_index=i, total_chunks=total_chunks, num_tokens=len(tokens))
            )

            try:
                raw_audio = self._generate_chunk_audio(
                    tokens, prompt_tokens, prompt_features, prompt_rms
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
        all_audio = []
        for chunk in self.stream(text, prompt_text, prompt_wav_path):
            all_audio.append(chunk.audio)

        if not all_audio:
            return torch.tensor([])

        full_wav = torch.cat(all_audio, dim=-1)

        if self.config.remove_long_sil:
            full_wav = remove_silence(
                full_wav, self.config.sampling_rate, only_edge=False, trail_sil=0
            )
        else:
            full_wav = remove_silence(
                full_wav, self.config.sampling_rate, only_edge=True, trail_sil=0
            )

        return full_wav
