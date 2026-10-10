"""Speech-to-text via open-source Whisper (falls back gracefully)."""
try:
    import whisper  # type: ignore
    _model = None

    def transcribe(path: str) -> str:
        global _model
        if _model is None:
            _model = whisper.load_model("base")
        return _model.transcribe(path)["text"]

except ImportError:

    def transcribe(path: str) -> str:
        return f"[whisper not installed — placeholder transcript for {path}]"
