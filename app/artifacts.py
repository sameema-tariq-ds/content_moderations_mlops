from __future__ import annotations

import hashlib
import os
import tempfile
import urllib.request
from pathlib import Path

from app.logger import get_logger

logger = get_logger(__name__)


def sha256_file(path: Path) -> str:
    digest = hashlib.sha256()
    with path.open("rb") as f:
        for chunk in iter(lambda: f.read(1024 * 1024), b""):
            digest.update(chunk)
    return digest.hexdigest()


def download_file(url: str, dest: Path, timeout_s: float) -> None:
    dest.parent.mkdir(parents=True, exist_ok=True)

    req = urllib.request.Request(
        url,
        headers={
            "User-Agent": "content-moderation-mlops/1.0",
        },
    )

    with urllib.request.urlopen(req, timeout=timeout_s) as r:  # nosec B310 (timeout set)
        with tempfile.NamedTemporaryFile(delete=False, dir=str(dest.parent), suffix=".tmp") as tmp:
            tmp_path = Path(tmp.name)
            while True:
                chunk = r.read(1024 * 1024)
                if not chunk:
                    break
                tmp.write(chunk)

    os.replace(str(tmp_path), str(dest))


def ensure_model_present(model_path: Path, model_url: str | None, timeout_s: float) -> None:
    if model_path.exists():
        return
    if not model_url:
        return

    logger.info(f"Model missing; downloading from MODEL_URL -> {model_path}")
    download_file(model_url, model_path, timeout_s=timeout_s)


def verify_model_sha256(model_path: Path, expected_sha256: str | None) -> None:
    if not expected_sha256:
        return

    actual = sha256_file(model_path)
    expected = expected_sha256.strip().lower()
    if actual != expected:
        raise ValueError(
            f"MODEL_SHA256 mismatch for {model_path}. Expected {expected}, got {actual}."
        )
