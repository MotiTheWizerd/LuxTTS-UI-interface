from typing import Any, Callable, Dict, List


class TokenizerHooks:
    """Mixin that provides lightweight event hooks for tokenizer lifecycle.

    Supported events:
      - "on_tokens_loaded"         -- after token file is parsed
      - "on_text_preprocessed"     -- after text normalization/preprocessing
      - "on_tokenization_complete" -- after texts_to_tokens finishes
    """

    def __init_hooks__(self):
        self._hooks: Dict[str, List[Callable]] = {}

    def register_hook(self, event: str, callback: Callable) -> None:
        self._hooks.setdefault(event, []).append(callback)

    def _fire(self, event: str, **kwargs: Any) -> None:
        for cb in self._hooks.get(event, []):
            cb(**kwargs)
