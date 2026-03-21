class ModelManager:
    """Lazy-loading singleton for the LuxTTS model."""

    def __init__(self, repo: str = "YatharthS/LuxTTS", device: str = "cpu", threads: int = 2):
        self._repo = repo
        self._device = device
        self._threads = threads
        self._model = None

    @property
    def is_loaded(self) -> bool:
        return self._model is not None

    def get_model(self):
        if self._model is None:
            from zipvoice.luxvoice import LuxTTS

            print("Loading LuxTTS model...")
            self._model = LuxTTS(self._repo, device=self._device, threads=self._threads)
            print("Model loaded.")
        return self._model

    def preload(self):
        """Eagerly load the model (e.g. at startup)."""
        self.get_model()


# Default instance — imported by routes
model_manager = ModelManager()
