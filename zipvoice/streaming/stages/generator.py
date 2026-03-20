from typing import List

import torch


class AudioGenerator:
    """Runs diffusion sampling + vocoder decoding for a single chunk."""

    def __init__(self, model: torch.nn.Module, vocoder: torch.nn.Module, device: torch.device):
        self.model = model
        self.vocoder = vocoder
        self.device = device

    def generate(
        self,
        tokens: List[int],
        prompt_tokens: List[List[int]],
        prompt_features: torch.Tensor,
        prompt_rms: float,
        *,
        speed: float,
        t_shift: float,
        num_step: int,
        guidance_scale: float,
        feat_scale: float,
        target_rms: float,
    ) -> torch.Tensor:
        """Generate a (1, T) waveform from tokens and prompt context."""
        prompt_features_lens = torch.full(
            (1,), prompt_features.size(1), device=self.device
        )

        pred_features, pred_features_lens, _, _ = self.model.sample(
            tokens=[tokens],
            prompt_tokens=prompt_tokens,
            prompt_features=prompt_features,
            prompt_features_lens=prompt_features_lens,
            speed=speed,
            t_shift=t_shift,
            duration="predict",
            num_step=num_step,
            guidance_scale=guidance_scale,
        )

        pred_features = pred_features.permute(0, 2, 1) / feat_scale
        wav = (
            self.vocoder.decode(pred_features[:, :, : pred_features_lens[0]])
            .squeeze(1)
            .clamp(-1, 1)
        )

        if prompt_rms < target_rms:
            wav = wav * prompt_rms / target_rms

        return wav
