import torch
import torch.nn as nn


class EnergyLoss(nn.Module):
    """Penalizes frames where both speakers are active simultaneously."""

    def __init__(self, feat_dim: int):
        super().__init__()
        self.feat_dim = feat_dim

    def forward(
        self,
        fbank1: torch.Tensor,
        fbank2: torch.Tensor,
        gt_fbank: torch.Tensor,
    ) -> torch.Tensor:
        """Compute per-frame energy overlap penalty.

        Args:
            fbank1: Speaker A features (B, T, feat_dim).
            fbank2: Speaker B features (B, T, feat_dim).
            gt_fbank: Ground-truth concatenated features (B, T, feat_dim*2).

        Returns:
            Per-frame penalty tensor (B, T).
        """
        energy1 = fbank1.mean(dim=-1)
        energy2 = fbank2.mean(dim=-1)

        gt_cat = torch.cat(
            [gt_fbank[:, :, : self.feat_dim], gt_fbank[:, :, self.feat_dim :]],
            dim=1,
        )
        thresholds = torch.quantile(
            gt_cat.mean(dim=-1), q=0.5, dim=1
        ).unsqueeze(1)

        both_speaking = ((energy1 > thresholds) & (energy2 > thresholds)).float()
        return both_speaking * (energy1 - thresholds) * (energy2 - thresholds)
