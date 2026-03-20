# Copyright    2025    Xiaomi Corp.        (authors:  Han Zhu)
#
# See ../../../../LICENSE for clarification regarding multiple authors
#
# Licensed under the Apache License, Version 2.0 (the "License");
# you may not use this file except in compliance with the License.
# You may obtain a copy of the License at
#
#     http://www.apache.org/licenses/LICENSE-2.0
#
# Unless required by applicable law or agreed to in writing, software
# distributed under the License is distributed on an "AS IS" BASIS,
# WITHOUT WARRANTIES OR CONDITIONS OF ANY KIND, either express or implied.
# See the License for the specific language governing permissions and
# limitations under the License.

from dataclasses import dataclass
from typing import List, Tuple

import torch
import torch.nn as nn
from torch.nn.parallel import DistributedDataParallel as DDP

from zipvoice.models.energy_loss import EnergyLoss
from zipvoice.models.modules.zipformer_two_stream import TTSZipformerTwoStream
from zipvoice.models.zipvoice import ZipVoice
from zipvoice.utils.common import condition_time_mask_suffix, make_pad_mask, pad_labels


@dataclass
class _FMLossResult:
    """Intermediate results from the shared flow-matching forward pass."""

    fm_loss: torch.Tensor
    vt: torch.Tensor
    xt: torch.Tensor
    t: torch.Tensor
    loss_mask: torch.Tensor


class ZipVoiceDialog(ZipVoice):
    """The ZipVoice-Dialog model."""

    def __init__(
        self,
        fm_decoder_downsampling_factor: List[int] = [1, 2, 4, 2, 1],
        fm_decoder_num_layers: List[int] = [2, 2, 4, 4, 4],
        fm_decoder_cnn_module_kernel: List[int] = [31, 15, 7, 15, 31],
        fm_decoder_feedforward_dim: int = 1536,
        fm_decoder_num_heads: int = 4,
        fm_decoder_dim: int = 512,
        text_encoder_num_layers: int = 4,
        text_encoder_feedforward_dim: int = 512,
        text_encoder_cnn_module_kernel: int = 9,
        text_encoder_num_heads: int = 4,
        text_encoder_dim: int = 192,
        time_embed_dim: int = 192,
        text_embed_dim: int = 192,
        query_head_dim: int = 32,
        value_head_dim: int = 12,
        pos_head_dim: int = 4,
        pos_dim: int = 48,
        feat_dim: int = 100,
        vocab_size: int = 26,
        pad_id: int = 0,
        spk_a_id: int = 360,
        spk_b_id: int = 361,
    ):
        super().__init__(
            fm_decoder_downsampling_factor=fm_decoder_downsampling_factor,
            fm_decoder_num_layers=fm_decoder_num_layers,
            fm_decoder_cnn_module_kernel=fm_decoder_cnn_module_kernel,
            fm_decoder_feedforward_dim=fm_decoder_feedforward_dim,
            fm_decoder_num_heads=fm_decoder_num_heads,
            fm_decoder_dim=fm_decoder_dim,
            text_encoder_num_layers=text_encoder_num_layers,
            text_encoder_feedforward_dim=text_encoder_feedforward_dim,
            text_encoder_cnn_module_kernel=text_encoder_cnn_module_kernel,
            text_encoder_num_heads=text_encoder_num_heads,
            text_encoder_dim=text_encoder_dim,
            time_embed_dim=time_embed_dim,
            text_embed_dim=text_embed_dim,
            query_head_dim=query_head_dim,
            value_head_dim=value_head_dim,
            pos_head_dim=pos_head_dim,
            pos_dim=pos_dim,
            feat_dim=feat_dim,
            vocab_size=vocab_size,
            pad_id=pad_id,
        )

        self.spk_a_id = spk_a_id
        self.spk_b_id = spk_b_id
        self.spk_embed = nn.Embedding(2, feat_dim)
        torch.nn.init.normal_(self.spk_embed.weight, mean=0, std=0.1)

        # Registered buffers — moved to device automatically, no per-call allocation
        self.register_buffer("_spk_a_idx", torch.tensor(0))
        self.register_buffer("_spk_b_idx", torch.tensor(1))

    def extract_spk_indices(self, tensor):
        turn_mask = ((tensor == self.spk_a_id) | (tensor == self.spk_b_id)).long()
        turn_counts = turn_mask.cumsum(dim=1)
        spk_mask = turn_counts % 2
        spk_mask = torch.where(tensor == self.pad_id, -1, spk_mask)
        spk_a_indices = torch.where(spk_mask == 0)
        spk_b_indices = torch.where(spk_mask == 1)
        return spk_a_indices, spk_b_indices

    def forward_text_embed(
        self,
        tokens: List[List[int]],
    ):
        """Get the text embeddings with speaker-specific offsets."""
        device = (
            self.device if isinstance(self, DDP) else next(self.parameters()).device
        )
        tokens_padded = pad_labels(tokens, pad_id=self.pad_id, device=device)  # (B, S)
        embed = self.embed(tokens_padded)  # (B, S, C)
        spk_a_indices, spk_b_indices = self.extract_spk_indices(tokens_padded)
        tokens_lens = torch.tensor(
            [len(token) for token in tokens], dtype=torch.int64, device=device
        )
        tokens_padding_mask = make_pad_mask(tokens_lens, embed.shape[1])  # (B, S)

        embed = self.text_encoder(
            x=embed, t=None, padding_mask=tokens_padding_mask
        )  # (B, S, C)
        embed[spk_a_indices] += self.spk_embed(self._spk_a_idx).to(embed.dtype)
        embed[spk_b_indices] += self.spk_embed(self._spk_b_idx).to(embed.dtype)
        return embed, tokens_lens

    def _compute_fm_loss(
        self,
        tokens: List[List[int]],
        features: torch.Tensor,
        features_lens: torch.Tensor,
        noise: torch.Tensor,
        t: torch.Tensor,
        condition_drop_ratio: float = 0.0,
    ) -> _FMLossResult:
        """Shared flow-matching forward pass used by Dialog and Stereo."""
        (text_condition, padding_mask,) = self.forward_text_train(
            tokens=tokens,
            features_lens=features_lens,
        )

        speech_condition_mask = condition_time_mask_suffix(
            features_lens=features_lens,
            mask_percent=(0.5, 1.0),
            max_len=features.size(1),
        )
        speech_condition = torch.where(speech_condition_mask.unsqueeze(-1), 0, features)

        if condition_drop_ratio > 0.0:
            drop_mask = (
                torch.rand(text_condition.size(0), 1, 1).to(text_condition.device)
                > condition_drop_ratio
            )
            text_condition = text_condition * drop_mask

        xt = features * t + noise * (1 - t)
        ut = features - noise  # (B, T, F)

        vt = self.forward_fm_decoder(
            t=t,
            xt=xt,
            text_condition=text_condition,
            speech_condition=speech_condition,
            padding_mask=padding_mask,
        )

        loss_mask = speech_condition_mask & (~padding_mask)
        fm_loss = torch.mean((vt[loss_mask] - ut[loss_mask]) ** 2)

        return _FMLossResult(
            fm_loss=fm_loss, vt=vt, xt=xt, t=t, loss_mask=loss_mask
        )

    def forward(
        self,
        tokens: List[List[int]],
        features: torch.Tensor,
        features_lens: torch.Tensor,
        noise: torch.Tensor,
        t: torch.Tensor,
        condition_drop_ratio: float = 0.0,
    ) -> torch.Tensor:
        """Forward pass of the model for training.
        Args:
            tokens: a list of list of token ids.
            features: the acoustic features, with the shape (batch, seq_len, feat_dim).
            features_lens: the length of each acoustic feature sequence, shape (batch,).
            noise: the intitial noise, with the shape (batch, seq_len, feat_dim).
            t: the time step, with the shape (batch, 1, 1).
            condition_drop_ratio: the ratio of dropped text condition.
        Returns:
            fm_loss: the flow-matching loss.
        """
        result = self._compute_fm_loss(
            tokens, features, features_lens, noise, t, condition_drop_ratio
        )
        return result.fm_loss


class ZipVoiceDialogStereo(ZipVoiceDialog):
    def __init__(
        self,
        fm_decoder_downsampling_factor: List[int] = [1, 2, 4, 2, 1],
        fm_decoder_num_layers: List[int] = [2, 2, 4, 4, 4],
        fm_decoder_cnn_module_kernel: List[int] = [31, 15, 7, 15, 31],
        fm_decoder_feedforward_dim: int = 1536,
        fm_decoder_num_heads: int = 4,
        fm_decoder_dim: int = 512,
        text_encoder_num_layers: int = 4,
        text_encoder_feedforward_dim: int = 512,
        text_encoder_cnn_module_kernel: int = 9,
        text_encoder_num_heads: int = 4,
        text_encoder_dim: int = 192,
        time_embed_dim: int = 192,
        text_embed_dim: int = 192,
        query_head_dim: int = 32,
        value_head_dim: int = 12,
        pos_head_dim: int = 4,
        pos_dim: int = 48,
        feat_dim: int = 100,
        vocab_size: int = 26,
        pad_id: int = 0,
        spk_a_id: int = 360,
        spk_b_id: int = 361,
    ):
        super().__init__(
            fm_decoder_downsampling_factor=fm_decoder_downsampling_factor,
            fm_decoder_num_layers=fm_decoder_num_layers,
            fm_decoder_cnn_module_kernel=fm_decoder_cnn_module_kernel,
            fm_decoder_feedforward_dim=fm_decoder_feedforward_dim,
            fm_decoder_num_heads=fm_decoder_num_heads,
            fm_decoder_dim=fm_decoder_dim,
            text_encoder_num_layers=text_encoder_num_layers,
            text_encoder_feedforward_dim=text_encoder_feedforward_dim,
            text_encoder_cnn_module_kernel=text_encoder_cnn_module_kernel,
            text_encoder_num_heads=text_encoder_num_heads,
            text_encoder_dim=text_encoder_dim,
            time_embed_dim=time_embed_dim,
            text_embed_dim=text_embed_dim,
            query_head_dim=query_head_dim,
            value_head_dim=value_head_dim,
            pos_head_dim=pos_head_dim,
            pos_dim=pos_dim,
            feat_dim=feat_dim,
            vocab_size=vocab_size,
            pad_id=pad_id,
            spk_a_id=spk_a_id,
            spk_b_id=spk_b_id,
        )

        self.fm_decoder = TTSZipformerTwoStream(
            in_dim=(feat_dim * 5, feat_dim * 3),
            out_dim=(feat_dim * 2, feat_dim),
            downsampling_factor=fm_decoder_downsampling_factor,
            num_encoder_layers=fm_decoder_num_layers,
            cnn_module_kernel=fm_decoder_cnn_module_kernel,
            encoder_dim=fm_decoder_dim,
            feedforward_dim=fm_decoder_feedforward_dim,
            num_heads=fm_decoder_num_heads,
            query_head_dim=query_head_dim,
            pos_head_dim=pos_head_dim,
            value_head_dim=value_head_dim,
            pos_dim=pos_dim,
            use_time_embed=True,
            time_embed_dim=time_embed_dim,
        )

        self.energy_loss = EnergyLoss(feat_dim)

    def forward(
        self,
        tokens: List[List[int]],
        features: torch.Tensor,
        features_lens: torch.Tensor,
        noise: torch.Tensor,
        t: torch.Tensor,
        condition_drop_ratio: float = 0.0,
        se_weight: float = 1.0,
    ) -> torch.Tensor:
        """Forward pass of the model for training.
        Args:
            tokens: a list of list of token ids.
            features: the acoustic features, with the shape (batch, seq_len, feat_dim).
            features_lens: the length of each acoustic feature sequence, shape (batch,).
            noise: the intitial noise, with the shape (batch, seq_len, feat_dim).
            t: the time step, with the shape (batch, 1, 1).
            condition_drop_ratio: the ratio of dropped text condition.
            se_weight: the weight of the speaker exclusive loss.
        Returns:
            fm_loss: the flow-matching loss.
        """
        result = self._compute_fm_loss(
            tokens, features, features_lens, noise, t, condition_drop_ratio
        )

        if se_weight > 0:
            target = result.xt + result.vt * (1 - result.t)
            fbank_1 = target[:, :, : self.feat_dim]
            fbank_2 = target[:, :, self.feat_dim :]
            energy = torch.mean(
                self.energy_loss(fbank_1, fbank_2, features)[result.loss_mask]
            )
            return result.fm_loss + energy * se_weight

        return result.fm_loss
