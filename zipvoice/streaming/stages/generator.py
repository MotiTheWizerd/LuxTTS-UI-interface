from typing import List

import torch


class AudioGenerator:
    """Runs diffusion sampling + vocoder decoding for a single chunk.

    Supports both GPU (PyTorch model with .sample()) and CPU (ONNX model
    with standalone sample() function) paths.
    """

    def __init__(self, model, vocoder, device):
        self.model = model
        self.vocoder = vocoder
        self.device = device
        self._is_onnx = not hasattr(model, 'sample')

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
        if not tokens:
            return None

        if self._is_onnx:
            return self._generate_onnx(
                tokens, prompt_tokens, prompt_features, prompt_rms,
                speed=speed, t_shift=t_shift, num_step=num_step,
                guidance_scale=guidance_scale, feat_scale=feat_scale,
                target_rms=target_rms,
            )

        return self._generate_gpu(
            tokens, prompt_tokens, prompt_features, prompt_rms,
            speed=speed, t_shift=t_shift, num_step=num_step,
            guidance_scale=guidance_scale, feat_scale=feat_scale,
            target_rms=target_rms,
        )

    def _generate_gpu(
        self, tokens, prompt_tokens, prompt_features, prompt_rms,
        *, speed, t_shift, num_step, guidance_scale, feat_scale, target_rms,
    ) -> torch.Tensor:
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

    def _generate_onnx(
        self, tokens, prompt_tokens, prompt_features, prompt_rms,
        *, speed, t_shift, num_step, guidance_scale, feat_scale, target_rms,
    ) -> torch.Tensor:
        from zipvoice.onnx_modeling import sample

        pred_features = sample(
            model=self.model,
            tokens=[tokens],
            prompt_tokens=prompt_tokens,
            prompt_features=prompt_features,
            speed=speed * 1.3,  # CPU default is too slow
            t_shift=t_shift,
            guidance_scale=guidance_scale,
            num_step=num_step,
        )

        pred_features = pred_features.permute(0, 2, 1) / feat_scale
        wav = self.vocoder.decode(pred_features).squeeze(1).clamp(-1, 1)

        if prompt_rms < target_rms:
            wav = wav * prompt_rms / target_rms

        return wav
