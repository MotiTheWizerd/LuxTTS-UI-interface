from abc import ABC, abstractmethod


class TextNormalizer(ABC):
    """Abstract base class for text normalization, defining common interface."""

    @abstractmethod
    def normalize(self, text: str) -> str:
        """Normalize text."""
        raise NotImplementedError
