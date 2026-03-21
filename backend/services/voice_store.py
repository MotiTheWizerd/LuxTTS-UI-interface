import os
import uuid
from pathlib import Path

import torch


class VoiceStore:
    """Persists encoded voice prompts as .pt files in a voices/ directory."""

    def __init__(self, voices_dir: str = None):
        if voices_dir is None:
            voices_dir = os.path.join(
                os.path.dirname(__file__), "..", "..", "voices"
            )
        self._dir = Path(voices_dir)
        self._dir.mkdir(parents=True, exist_ok=True)

    def save(self, name: str, encode_dict: dict) -> str:
        """Save an encoded prompt under the given name. Returns the voice_id."""
        voice_id = name or str(uuid.uuid4())[:8]
        # Sanitize filename
        safe_name = "".join(c for c in voice_id if c.isalnum() or c in "-_ ").strip()
        if not safe_name:
            safe_name = str(uuid.uuid4())[:8]

        path = self._dir / f"{safe_name}.pt"
        torch.save(encode_dict, str(path))
        return safe_name

    def load(self, voice_id: str) -> dict:
        """Load an encoded prompt by voice_id. Raises FileNotFoundError if missing."""
        path = self._dir / f"{voice_id}.pt"
        if not path.exists():
            raise FileNotFoundError(f"Voice '{voice_id}' not found")
        return torch.load(str(path), weights_only=False)

    def list(self) -> list:
        """Return a list of available voice IDs."""
        return [p.stem for p in sorted(self._dir.glob("*.pt"))]

    def delete(self, voice_id: str) -> bool:
        """Delete a saved voice. Returns True if deleted, False if not found."""
        path = self._dir / f"{voice_id}.pt"
        if path.exists():
            path.unlink()
            return True
        return False


# Default instance
voice_store = VoiceStore()
