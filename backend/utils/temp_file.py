import os
import tempfile
from contextlib import contextmanager

from werkzeug.datastructures import FileStorage


@contextmanager
def temp_audio_file(audio_file: FileStorage):
    """Save an uploaded audio file to a temp path, clean up on exit."""
    ext = os.path.splitext(audio_file.filename)[1] or ".wav"
    tmp = tempfile.NamedTemporaryFile(suffix=ext, delete=False)
    tmp.close()
    try:
        audio_file.save(tmp.name)
        yield tmp.name
    finally:
        try:
            os.unlink(tmp.name)
        except OSError:
            pass
