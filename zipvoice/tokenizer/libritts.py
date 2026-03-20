import logging
from typing import List, Optional

from zipvoice.tokenizer.base import Tokenizer


class LibriTTSTokenizer(Tokenizer):
    """Tokenizer for LibriTTS dataset, supporting BPE, char, and phone modes."""

    def __init__(self, token_file: Optional[str] = None, token_type="char"):
        assert token_type in ["bpe", "char", "phone"]
        self.type = token_type

        try:
            import tacotron_cleaner.cleaners
        except Exception as ex:
            raise RuntimeError(f"{ex}\nPlease run\n" "pip install espnet_tts_frontend")

        self.normalize = tacotron_cleaner.cleaners.custom_english_cleaners

        if token_type == "bpe" and token_file is not None:
            # BPE uses sentencepiece — skip the TSV-based _load_token_file
            self.__init_hooks__()
            self.has_tokens = False
            self.token2id = {}
            self.pad_id = -1
            self.vocab_size = 0

            import sentencepiece as spm

            self.sp = spm.SentencePieceProcessor()
            self.sp.load(token_file)
            self.pad_id = self.sp.piece_to_id("<pad>")
            self.vocab_size = self.sp.get_piece_size()
            self.has_tokens = True
            self._fire("on_tokens_loaded", token2id=None)
        else:
            super().__init__(token_file)

    def texts_to_token_ids(self, texts: List[str]) -> List[List[int]]:
        if self.type == "bpe":
            texts = [self.normalize(t) for t in texts]
            return self.sp.encode(texts)
        return super().texts_to_token_ids(texts)

    def tokens_to_token_ids(
        self, tokens_list: List[List[str]]
    ) -> List[List[int]]:
        assert self.type != "bpe", "BPE tokenizer does not support this function."
        return super().tokens_to_token_ids(tokens_list)

    def texts_to_tokens(self, texts: List[str]) -> List[List[str]]:
        texts = [self.normalize(t) for t in texts]

        if self.type == "char":
            return [list(t) for t in texts]
        elif self.type == "phone":
            from piper_phonemize import phonemize_espeak

            return [phonemize_espeak(t.lower(), "en-us") for t in texts]
        elif self.type == "bpe":
            return self.sp.encode(texts, out_type=str)
