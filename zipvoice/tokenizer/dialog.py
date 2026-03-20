import re
from typing import Optional

from zipvoice.tokenizer.emilia import EmiliaTokenizer


class DialogTokenizer(EmiliaTokenizer):
    """Extends EmiliaTokenizer with speaker turn tokens ([S1], [S2])."""

    def __init__(self, token_file: Optional[str] = None, token_type="phone"):
        super().__init__(token_file=token_file, token_type=token_type)
        if token_file:
            self.spk_a_id = self.token2id["[S1]"]
            self.spk_b_id = self.token2id["[S2]"]

    def preprocess_text(self, text: str) -> str:
        text = re.sub(r"\s*(\[S[12]\])\s*", r"\1", text)
        text = self.map_punctuations(text)
        return text
