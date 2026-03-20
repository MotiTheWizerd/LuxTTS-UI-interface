from lhotse import CutSet


def add_tokens(cut_set: CutSet, tokenizer: str, lang: str):
    """Instantiate a tokenizer by name and attach tokens to each cut's supervision."""
    from zipvoice.tokenizer.dialog import DialogTokenizer
    from zipvoice.tokenizer.emilia import EmiliaTokenizer
    from zipvoice.tokenizer.espeak import EspeakTokenizer
    from zipvoice.tokenizer.libritts import LibriTTSTokenizer
    from zipvoice.tokenizer.simple import SimpleTokenizer

    registry = {
        "emilia": lambda: EmiliaTokenizer(),
        "espeak": lambda: EspeakTokenizer(lang=lang),
        "dialog": lambda: DialogTokenizer(),
        "libritts": lambda: LibriTTSTokenizer(),
        "simple": lambda: SimpleTokenizer(),
    }
    if tokenizer not in registry:
        raise ValueError(f"Unsupported tokenizer: {tokenizer}.")

    tok = registry[tokenizer]()

    def _prepare_cut(cut):
        assert len(cut.supervisions) == 1, (len(cut.supervisions), cut)
        text = cut.supervisions[0].text
        tokens = tok.texts_to_tokens([text])[0]
        cut.supervisions[0].tokens = tokens
        return cut

    return cut_set.map(_prepare_cut)
