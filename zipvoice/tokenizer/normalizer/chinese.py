import cn2an

from zipvoice.tokenizer.normalizer.base import TextNormalizer


class ChineseTextNormalizer(TextNormalizer):
    """A class to handle preprocessing of Chinese text including normalization."""

    def normalize(self, text: str) -> str:
        """Normalize text."""
        text = cn2an.transform(text, "an2cn")
        return text
