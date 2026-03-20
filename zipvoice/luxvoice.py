import io

import numpy as np
import soundfile as sf
import torch

from zipvoice.modeling_utils import process_audio, generate, load_models_gpu, load_models_cpu
from zipvoice.onnx_modeling import generate_cpu

class LuxTTS:
    """
    LuxTTS class for encoding prompt and generating speech on cpu/cuda/mps.
    """

    def __init__(self, model_path='YatharthS/LuxTTS', device='cuda', threads=4):
        if model_path == 'YatharthS/LuxTTS':
            model_path = None

        # Auto-detect better device if cuda is requested but not available
        if device == 'cuda' and not torch.cuda.is_available():
            if torch.backends.mps.is_available():
                print("CUDA not available, switching to MPS")
                device = 'mps'
            else:
                print("CUDA not available, switching to CPU")
                device = 'cpu'

        if device == 'cpu':
            model, feature_extractor, vocos, tokenizer, transcriber = load_models_cpu(model_path, threads)
            print("Loading model on CPU")
        else:
            model, feature_extractor, vocos, tokenizer, transcriber = load_models_gpu(model_path, device=device)
            print("Loading model on GPU")

        self.model = model
        self.feature_extractor = feature_extractor
        self.vocos = vocos
        self.tokenizer = tokenizer
        self.transcriber = transcriber
        self.device = device
        self.vocos.freq_range = 12000



    def encode_prompt(self, prompt_audio, duration=5, rms=0.001):
        """encodes audio prompt according to duration and rms(volume control)"""
        prompt_tokens, prompt_features_lens, prompt_features, prompt_rms = process_audio(prompt_audio, self.transcriber, self.tokenizer, self.feature_extractor, self.device, target_rms=rms, duration=duration)
        encode_dict = {"prompt_tokens": prompt_tokens, 'prompt_features_lens': prompt_features_lens, 'prompt_features': prompt_features, 'prompt_rms': prompt_rms}

        return encode_dict

    def generate_speech(self, text, encode_dict, num_steps=4, guidance_scale=3.0, t_shift=0.5, speed=1.0, return_smooth=False):
        """encodes text and generates speech using flow matching model according to steps, guidance scale, and t_shift(like temp)"""

        prompt_tokens, prompt_features_lens, prompt_features, prompt_rms = encode_dict.values()

        if return_smooth == True:
            self.vocos.return_48k = False
        else:
            self.vocos.return_48k = True

        if self.device == 'cpu':
            final_wav = generate_cpu(prompt_tokens, prompt_features_lens, prompt_features, prompt_rms, text, self.model, self.vocos, self.tokenizer, num_step=num_steps, guidance_scale=guidance_scale, t_shift=t_shift, speed=speed)
        else:
            final_wav = generate(prompt_tokens, prompt_features_lens, prompt_features, prompt_rms, text, self.model, self.vocos, self.tokenizer, num_step=num_steps, guidance_scale=guidance_scale, t_shift=t_shift, speed=speed)

        return final_wav.cpu()

    @staticmethod
    def _split_text_for_streaming(text, max_chars=80, min_chars=3):
        """Split text into small chunks for low-latency streaming.

        Splits at commas, semicolons, colons, and sentence-ending punctuation.
        Falls back to word boundaries when a segment exceeds *max_chars*.
        Merges fragments shorter than *min_chars* into the previous chunk
        to avoid producing empty-token segments that crash the model.
        """
        import re

        # Split at any punctuation that is a natural pause
        raw = re.split(
            r'(?<=[.!?;:,，。！？；：、])\s*',
            text.strip(),
        )
        raw = [c for c in raw if c.strip()]

        # Second pass: break oversized segments at word boundaries
        split = []
        for seg in raw:
            while len(seg) > max_chars:
                cut = seg.rfind(' ', 0, max_chars)
                if cut <= 0:
                    cut = max_chars
                split.append(seg[:cut].strip())
                seg = seg[cut:].strip()
            if seg:
                split.append(seg)

        if not split:
            return [text]

        # Third pass: merge tiny fragments into the previous chunk
        # so we never send a chunk that tokenizes to zero tokens
        chunks = [split[0]]
        for seg in split[1:]:
            if len(seg) < min_chars:
                chunks[-1] += ' ' + seg
            else:
                chunks.append(seg)

        return chunks

    def generate_speech_streaming(self, text, encode_dict, num_steps=4, guidance_scale=3.0, t_shift=0.5, speed=1.0, return_smooth=False):
        """Generator that yields WAV bytes per text chunk for streaming playback.

        Yields small chunks as soon as each is generated so playback can
        begin with minimal latency.

        Yields:
            dict with keys: type, chunk_index, total_chunks, audio_bytes, sample_rate, is_final
        """
        prompt_tokens, prompt_features_lens, prompt_features, prompt_rms = encode_dict.values()

        if return_smooth:
            self.vocos.return_48k = False
            sample_rate = 24000
        else:
            self.vocos.return_48k = True
            sample_rate = 48000

        chunks = self._split_text_for_streaming(text)
        total = len(chunks)
        gen_fn = generate_cpu if self.device == 'cpu' else generate

        for i, chunk_text in enumerate(chunks):
            # Guard: skip chunks that would tokenize to nothing
            test_tokens = self.tokenizer.texts_to_token_ids([chunk_text])
            if not test_tokens or not test_tokens[0]:
                continue

            wav = gen_fn(
                prompt_tokens, prompt_features_lens, prompt_features, prompt_rms,
                chunk_text, self.model, self.vocos, self.tokenizer,
                num_step=num_steps, guidance_scale=guidance_scale,
                t_shift=t_shift, speed=speed,
            )

            wav_np = wav.cpu().numpy().squeeze()
            buf = io.BytesIO()
            sf.write(buf, wav_np, sample_rate, format='WAV')
            buf.seek(0)

            yield {
                "type": "audio",
                "chunk_index": i,
                "total_chunks": total,
                "audio_bytes": buf.read(),
                "sample_rate": sample_rate,
                "is_final": i == total - 1,
            }
