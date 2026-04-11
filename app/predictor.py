"""Loads the trained model bundle and exposes a predict method."""

import pickle
from pathlib import Path

from app.artifacts import ensure_model_present, verify_model_sha256
from app.logger import get_logger
from config.settings import MODEL_DOWNLOAD_TIMEOUT_S, MODEL_PATH, MODEL_SHA256, MODEL_URL

logger = get_logger(__name__)


class Predictor:
    """Loads the model bundle once at startup and serves predictions."""

    def __init__(self):
        model_path = Path(MODEL_PATH)
        ensure_model_present(model_path, model_url=MODEL_URL, timeout_s=MODEL_DOWNLOAD_TIMEOUT_S)
        if not model_path.exists():
            raise FileNotFoundError(
                f"Model not found at {MODEL_PATH}. "
                "Run the training pipeline first or set MODEL_URL."
            )
        verify_model_sha256(model_path, expected_sha256=MODEL_SHA256)

        with open(model_path, "rb") as f:
            bundle = pickle.load(f)

        self.pipeline = bundle["pipeline"]
        self.version = bundle["version"]
        self.run_id = bundle["run_id"]
        logger.info(f"Model loaded | version: {self.version} | run_id: {self.run_id}")

    def predict(self, text: str) -> dict:
        """Run prediction on a single text. Returns label and confidence."""
        label_idx = self.pipeline.predict([text])[0]
        proba = self.pipeline.predict_proba([text])[0]
        confidence = round(float(proba[label_idx]), 4)
        label = "spam" if label_idx == 1 else "ham"
        return {"label": label, "confidence": confidence}
