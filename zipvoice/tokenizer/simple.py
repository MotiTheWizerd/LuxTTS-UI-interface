from typing import List, Optional

from zipvoice.tokenizer.base import Tokenizer


class SimpleTokenizer(Tokenizer):
    """The simplest tokenizer — treats every character as a token,
    without text normalization.
    """

    def __init__(self, token_file: Optional[str] = None):
        super().__init__(token_file)

    def texts_to_tokens(self, texts: List[str]) -> List[List[str]]:
        return [list(text) for text in texts]
