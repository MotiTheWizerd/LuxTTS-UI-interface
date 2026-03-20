from typing import List, Tuple

from zipvoice.streaming.events import EventBus, TextChunked
from zipvoice.utils.infer import add_punctuation, chunk_tokens_punctuation


class TextChunker:
    """Tokenizes text and splits it into chunks at punctuation boundaries."""

    def __init__(self, tokenizer):
        self.tokenizer = tokenizer

    def chunk(
        self,
        text: str,
        prompt_tokens_str_len: int,
        prompt_duration: float,
        *,
        speed: float = 1.0,
        events: EventBus | None = None,
    ) -> Tuple[List[List[int]], List[List[str]]]:
        """Tokenize and chunk text, returning (token_id_chunks, token_str_chunks)."""
        text = add_punctuation(text)
        tokens_str = self.tokenizer.texts_to_tokens([text])[0]

        token_duration = prompt_duration / (prompt_tokens_str_len * speed)
        max_tokens = int((25 - prompt_duration) / token_duration)

        chunked_tokens_str = chunk_tokens_punctuation(tokens_str, max_tokens=max_tokens)
        chunked_tokens = self.tokenizer.tokens_to_token_ids(chunked_tokens_str)

        if events:
            total_tokens = sum(len(t) for t in chunked_tokens)
            events.emit(
                TextChunked(total_chunks=len(chunked_tokens), total_tokens=total_tokens)
            )

        return chunked_tokens, chunked_tokens_str
