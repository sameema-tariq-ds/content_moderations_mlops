from __future__ import annotations

import app.main as main


class _FakePredictor:
    version = "test"

    def predict(self, text: str) -> dict:
        lowered = text.lower()
        is_spam = any(
            token in lowered for token in ("free", "won", "prize", "urgent", "cash", "offer")
        )
        return {"label": "spam" if is_spam else "ham", "confidence": 0.99 if is_spam else 0.9}


# Ensure the app can start in CI without a trained model artifact.
main.Predictor = _FakePredictor
