"""Pydantic schemas for API request and response validation."""

from __future__ import annotations

from typing import Annotated, Any, Literal

from pydantic import BaseModel, Field

TextInput = Annotated[str, Field(min_length=1, max_length=2000, description="Text to classify")]


class PredictionRequest(BaseModel):
    """Input schema — raw text to be classified."""

    text: TextInput


class PredictionResponse(BaseModel):
    """Output schema — predicted label and model confidence."""

    label: Literal["spam", "ham"] = Field(..., description="Predicted label: spam or ham")
    confidence: float = Field(..., description="Model confidence score (0-1)")


class BatchPredictionRequest(BaseModel):
    """Batch input schema — a list of texts to be classified."""

    texts: list[TextInput] = Field(..., min_length=1, max_length=128)


class BatchPredictionResponse(BaseModel):
    """Batch output schema — predictions in the same order as inputs."""

    count: int = Field(..., ge=0)
    predictions: list[PredictionResponse]


class ErrorDetail(BaseModel):
    code: str
    message: str
    details: Any | None = None


class ErrorResponse(BaseModel):
    error: ErrorDetail
