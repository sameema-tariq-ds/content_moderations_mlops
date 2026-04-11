"""Saves the trained sklearn pipeline as a pickle bundle with metadata."""

import hashlib
import pickle

from app.logger import get_logger
from config.settings import MODEL_PATH

logger = get_logger(__name__)


def model_save(pipeline, metrics: dict, version: str, run_id: str) -> None:
    """Save pipeline and metadata as a pickle bundle to MODEL_PATH."""
    MODEL_PATH.parent.mkdir(parents=True, exist_ok=True)

    bundle = {
        "pipeline": pipeline,
        "version": version,
        "metrics": metrics,
        "run_id": run_id,
    }

    with open(MODEL_PATH, "wb") as f:
        pickle.dump(bundle, f)

    logger.info(f"Model bundle saved → {MODEL_PATH}")

    digest = hashlib.sha256(MODEL_PATH.read_bytes()).hexdigest()
    sha_path = MODEL_PATH.with_suffix(MODEL_PATH.suffix + ".sha256")
    sha_path.write_text(digest + "\n", encoding="utf-8")
    logger.info(f"Model SHA256 saved → {sha_path}")
