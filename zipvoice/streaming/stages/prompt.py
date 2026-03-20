import logging
from dataclasses import dataclass
from typing import List, Tuple

import torch

from zipvoice.streaming.events import EventBus, PromptReady
from zipvoice.utils.infer import add_punctuation, load_prompt_wav, remove_silence, rms_norm


@dataclass
class PromptData:
    """All pre-computed prompt artifacts needed by downstream stages."""

    features: torch.Tensor  # (1, F, T)
    wav: torch.Tensor
    tokens: List[List[int]]
    rms: float
    tokens_str_len: int
    duration: float


class PromptProcessor:
    """Loads, normalizes, featurizes, and tokenizes a prompt audio clip."""

    def __init__(self, tokenizer, feature_extractor, device: torch.device):
        self.tokenizer = tokenizer
        self.feature_extractor = feature_extractor
        self.device = device

    def prepare(
        self,
        prompt_wav_path: str,
        prompt_text: str,
        *,
        sampling_rate: int,
        target_rms: float,
        feat_scale: float,
        events: EventBus | None = None,
    ) -> PromptData:
        """Load and prepare all prompt artifacts in one pass."""
        prompt_wav = load_prompt_wav(prompt_wav_path, sampling_rate=sampling_rate)
        prompt_wav = remove_silence(prompt_wav, sampling_rate, only_edge=False, trail_sil=200)
        prompt_wav, prompt_rms = rms_norm(prompt_wav, target_rms)

        duration = prompt_wav.shape[-1] / sampling_rate
        if duration > 20:
            logging.warning(
                f"Prompt wav is very long ({duration:.1f}s). 1-3 seconds is recommended."
            )

        features = self.feature_extractor.extract(
            prompt_wav, sampling_rate=sampling_rate
        ).to(self.device)
        features = features.unsqueeze(0) * feat_scale

        prompt_text = add_punctuation(prompt_text)
        tokens_str = self.tokenizer.texts_to_tokens([prompt_text])[0]
        tokens = self.tokenizer.tokens_to_token_ids([tokens_str])

        data = PromptData(
            features=features,
            wav=prompt_wav,
            tokens=tokens,
            rms=prompt_rms,
            tokens_str_len=len(tokens_str),
            duration=duration,
        )

        if events:
            events.emit(PromptReady(duration=duration, tokens_len=len(tokens_str)))

        return data
