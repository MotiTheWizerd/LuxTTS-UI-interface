import logging
from abc import ABC, abstractmethod
from typing import Dict, List, Optional

from zipvoice.tokenizer.hooks import TokenizerHooks


class Tokenizer(ABC, TokenizerHooks):
    """Abstract base class for tokenizers.

    Provides shared token file loading and token-id conversion so that
    subclasses only need to implement ``texts_to_tokens``.
    """

    def __init__(self, token_file: Optional[str] = None):
        self.__init_hooks__()
        self.has_tokens = False
        self.token2id: Dict[str, int] = {}
        self.pad_id: int = -1
        self.vocab_size: int = 0

        if token_file is not None:
            self._load_token_file(token_file)

    def _load_token_file(self, token_file: str) -> None:
        """Parse a TSV token file (``token\\tid`` per line)."""
        with open(token_file, "r", encoding="utf-8") as f:
            for line in f.readlines():
                info = line.rstrip().split("\t")
                token, id_ = info[0], int(info[1])
                assert token not in self.token2id, token
                self.token2id[token] = id_
        self.pad_id = self.token2id["_"]
        self.vocab_size = len(self.token2id)
        self.has_tokens = True
        self._fire("on_tokens_loaded", token2id=self.token2id)

    def texts_to_token_ids(self, texts: List[str]) -> List[List[int]]:
        """Convert texts to token ids (compose texts_to_tokens + tokens_to_token_ids)."""
        return self.tokens_to_token_ids(self.texts_to_tokens(texts))

    def tokens_to_token_ids(
        self, tokens_list: List[List[str]]
    ) -> List[List[int]]:
        """Map token strings to integer ids using the loaded vocabulary."""
        assert self.has_tokens, "Please initialize Tokenizer with a tokens file."

        token_ids_list = []
        for tokens in tokens_list:
            token_ids = []
            for t in tokens:
                if t not in self.token2id:
                    logging.debug(f"Skip OOV {t}")
                    continue
                token_ids.append(self.token2id[t])
            token_ids_list.append(token_ids)

        return token_ids_list

    @abstractmethod
    def texts_to_tokens(self, texts: List[str]) -> List[List[str]]:
        """Convert list of texts to list of token sequences."""
        raise NotImplementedError
