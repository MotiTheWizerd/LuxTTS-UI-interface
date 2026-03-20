from typing import Optional

import torch


class CrossFadeBuffer:
    """Incrementally cross-fades audio chunks as they arrive.

    Instead of collecting all chunks and merging at the end,
    this buffer yields playable audio as soon as each chunk is ready,
    holding back only the fade-overlap tail.
    """

    def __init__(self, fade_duration: float = 0.1, sample_rate: int = 24000):
        self.fade_samples = int(fade_duration * sample_rate)
        self._tail: Optional[torch.Tensor] = None

    def push(self, chunk: torch.Tensor, is_final: bool = False) -> torch.Tensor:
        """Accept a new chunk and return the audio safe to play now.

        Args:
            chunk: Audio tensor of shape (1, T).
            is_final: If True, flushes the held-back tail as well.

        Returns:
            Audio tensor ready for immediate playback.
        """
        if self._tail is None:
            # First chunk — hold back the fade tail
            if is_final or self.fade_samples <= 0:
                self._tail = None
                return chunk
            self._tail = chunk[..., -self.fade_samples :]
            return chunk[..., : -self.fade_samples]

        # Cross-fade the held tail with the start of the new chunk
        k = min(self.fade_samples, self._tail.shape[-1], chunk.shape[-1])
        if k <= 0:
            merged = torch.cat([self._tail, chunk], dim=-1)
        else:
            fade = torch.linspace(1, 0, k, device=chunk.device)[None]
            merged = torch.cat(
                [
                    self._tail[..., :-k] if self._tail.shape[-1] > k else torch.tensor([], device=chunk.device).unsqueeze(0),
                    self._tail[..., -k:] * fade + chunk[..., :k] * (1 - fade),
                    chunk[..., k:],
                ],
                dim=-1,
            )

        if is_final or self.fade_samples <= 0:
            self._tail = None
            return merged

        # Hold back the new tail for cross-fade with next chunk
        self._tail = merged[..., -self.fade_samples :]
        return merged[..., : -self.fade_samples]

    def flush(self) -> Optional[torch.Tensor]:
        """Return any remaining audio held in the buffer."""
        tail = self._tail
        self._tail = None
        return tail

    def reset(self) -> None:
        """Clear the buffer state."""
        self._tail = None
