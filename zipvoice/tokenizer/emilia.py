import logging
import re
from functools import reduce
from typing import List, Optional

import jieba
from pypinyin import Style, lazy_pinyin
from pypinyin.contrib.tone_convert import to_finals_tone3, to_initials

from zipvoice.tokenizer.base import Tokenizer
from zipvoice.tokenizer.normalizer.chinese import ChineseTextNormalizer
from zipvoice.tokenizer.normalizer.english import EnglishTextNormalizer

try:
    from piper_phonemize import phonemize_espeak
except Exception as ex:
    raise RuntimeError(
        f"{ex}\nPlease run\n"
        "pip install piper_phonemize -f "
        "https://k2-fsa.github.io/icefall/piper_phonemize.html"
    )

jieba.default_logger.setLevel(logging.INFO)


class EmiliaTokenizer(Tokenizer):
    """Bilingual Chinese/English tokenizer with pinyin and tag support."""

    def __init__(self, token_file: Optional[str] = None, token_type="phone"):
        assert (
            token_type == "phone"
        ), f"Only support phone tokenizer for Emilia, but get {token_type}."

        self.english_normalizer = EnglishTextNormalizer()
        self.chinese_normalizer = ChineseTextNormalizer()
        super().__init__(token_file)

    def preprocess_text(self, text: str) -> str:
        return self.map_punctuations(text)

    def texts_to_tokens(self, texts: List[str]) -> List[List[str]]:
        for i in range(len(texts)):
            texts[i] = self.preprocess_text(texts[i])

        phoneme_list = []
        for text in texts:
            segments = self.get_segment(text)
            all_phoneme = []
            for seg in segments:
                if seg[1] == "zh":
                    phoneme = self.tokenize_ZH(seg[0])
                elif seg[1] == "en":
                    phoneme = self.tokenize_EN(seg[0])
                elif seg[1] == "pinyin":
                    phoneme = self.tokenize_pinyin(seg[0])
                elif seg[1] == "tag":
                    phoneme = [seg[0]]
                else:
                    logging.warning(
                        f"No English or Chinese characters found, "
                        f"skipping segment of unknown language: {seg}"
                    )
                    continue
                all_phoneme += phoneme
            phoneme_list.append(all_phoneme)
        return phoneme_list

    def tokenize_ZH(self, text: str) -> List[str]:
        try:
            text = self.chinese_normalizer.normalize(text)
            segs = list(jieba.cut(text))
            full = lazy_pinyin(
                segs,
                style=Style.TONE3,
                tone_sandhi=True,
                neutral_tone_with_five=True,
            )
            phones = []
            for x in full:
                if not (x[0:-1].isalpha() and x[-1] in ("1", "2", "3", "4", "5")):
                    phones.append(x)
                else:
                    phones.extend(self.seperate_pinyin(x))
            return phones
        except Exception as ex:
            logging.warning(f"Tokenization of Chinese texts failed: {ex}")
            return []

    def tokenize_EN(self, text: str) -> List[str]:
        try:
            text = self.english_normalizer.normalize(text)
            tokens = phonemize_espeak(text, "en-us")
            tokens = reduce(lambda x, y: x + y, tokens)
            return tokens
        except Exception as ex:
            logging.warning(f"Tokenization of English texts failed: {ex}")
            return []

    def tokenize_pinyin(self, text: str) -> List[str]:
        try:
            assert text.startswith("<") and text.endswith(">")
            text = text.lstrip("<").rstrip(">")
            if not (text[0:-1].isalpha() and text[-1] in ("1", "2", "3", "4", "5")):
                logging.warning(
                    f"Strings enclosed with <> should be pinyin, "
                    f"but got: {text}. Skipped it. "
                )
                return []
            else:
                return self.seperate_pinyin(text)
        except Exception as ex:
            logging.warning(f"Tokenize pinyin failed: {ex}")
            return []

    def seperate_pinyin(self, text: str) -> List[str]:
        """Separate pinyin into initial and final."""
        pinyins = []
        initial = to_initials(text, strict=False)
        final = to_finals_tone3(
            text,
            strict=False,
            neutral_tone_with_five=True,
        )
        if initial != "":
            pinyins.append(initial + "0")
        if final != "":
            pinyins.append(final)
        return pinyins

    def map_punctuations(self, text):
        text = text.replace("，", ",")
        text = text.replace("。", ".")
        text = text.replace("！", "!")
        text = text.replace("？", "?")
        text = text.replace("；", ";")
        text = text.replace("：", ":")
        text = text.replace("、", ",")
        text = text.replace("\u2018", "'")
        text = text.replace("\u201c", '"')
        text = text.replace("\u201d", '"')
        text = text.replace("\u2019", "'")
        text = text.replace("\u22ef", "\u2026")
        text = text.replace("\u00b7\u00b7\u00b7", "\u2026")
        text = text.replace("\u30fb\u30fb\u30fb", "\u2026")
        text = text.replace("...", "\u2026")
        return text

    def get_segment(self, text: str) -> List[str]:
        """Split text into segments based on language type (Chinese, English, Pinyin, tags)."""
        segments = []
        types = []
        temp_seg = ""
        temp_lang = ""

        _part_pattern = re.compile(r"[<[].*?[>\]]|.")
        text = _part_pattern.findall(text)

        for part in text:
            if self.is_chinese(part) or self.is_pinyin(part):
                types.append("zh")
            elif self.is_alphabet(part):
                types.append("en")
            else:
                types.append("other")

        assert len(types) == len(text)

        for i in range(len(types)):
            if i == 0:
                temp_seg += text[i]
                temp_lang = types[i]
            else:
                if temp_lang == "other":
                    temp_seg += text[i]
                    temp_lang = types[i]
                else:
                    if types[i] in [temp_lang, "other"]:
                        temp_seg += text[i]
                    else:
                        segments.append((temp_seg, temp_lang))
                        temp_seg = text[i]
                        temp_lang = types[i]

        segments.append((temp_seg, temp_lang))
        segments = self.split_segments(segments)
        return segments

    def split_segments(self, segments):
        """Split segments into smaller parts if special strings enclosed by [] or <> are found."""
        result = []
        for temp_seg, temp_lang in segments:
            parts = re.split(r"([<[].*?[>\]])", temp_seg)
            for part in parts:
                if not part:
                    continue
                if self.is_pinyin(part):
                    result.append((part, "pinyin"))
                elif self.is_tag(part):
                    result.append((part, "tag"))
                else:
                    result.append((part, temp_lang))
        return result

    def is_chinese(self, char: str) -> bool:
        return "\u4e00" <= char <= "\u9fa5"

    def is_alphabet(self, char: str) -> bool:
        return ("\u0041" <= char <= "\u005a") or ("\u0061" <= char <= "\u007a")

    def is_pinyin(self, part: str) -> bool:
        return part.startswith("<") and part.endswith(">")

    def is_tag(self, part: str) -> bool:
        return part.startswith("[") and part.endswith("]")
