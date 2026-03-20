import logging
from functools import reduce
from typing import List, Optional

from zipvoice.tokenizer.base import Tokenizer

try:
    from piper_phonemize import phonemize_espeak
except Exception as ex:
    raise RuntimeError(
        f"{ex}\nPlease run\n"
        "pip install piper_phonemize -f "
        "https://k2-fsa.github.io/icefall/piper_phonemize.html"
    )


class EspeakTokenizer(Tokenizer):
    """A tokenizer with Espeak g2p function."""

    def __init__(self, token_file: Optional[str] = None, lang: str = "en-us"):
        self.lang = lang
        super().__init__(token_file)

    def g2p(self, text: str) -> List[str]:
        try:
            tokens = phonemize_espeak(text, self.lang)
            return reduce(lambda x, y: x + y, tokens)
        except Exception as ex:
            logging.warning(f"Tokenization of {self.lang} texts failed: {ex}")
            return []

    def texts_to_tokens(self, texts: List[str]) -> List[List[str]]:
        return [self.g2p(text) for text in texts]
