"""FastAPI app â€” serves the spam classification model via REST endpoints."""

from contextlib import asynccontextmanager

from fastapi import FastAPI, HTTPException, Request
from fastapi.exceptions import RequestValidationError
from fastapi.responses import JSONResponse
from slowapi import Limiter, _rate_limit_exceeded_handler
from slowapi.errors import RateLimitExceeded
from slowapi.util import get_remote_address

from app.logger import get_logger
from app.predictor import Predictor
from app.schemas import (
    BatchPredictionRequest,
    BatchPredictionResponse,
    ErrorResponse,
    PredictionRequest,
    PredictionResponse,
)

logger = get_logger(__name__)


def _json_error(code: str, message: str, details=None) -> dict:
    return ErrorResponse(error={"code": code, "message": message, "details": details}).model_dump()


@asynccontextmanager
async def lifespan(app: FastAPI):
    """Load the model on startup and release resources on shutdown."""
    try:
        app.state.predictor = Predictor()
    except FileNotFoundError as exc:
        app.state.predictor = None
        logger.warning(f"Model not loaded on startup: {exc}")
    yield


app = FastAPI(title="Content Moderation API", lifespan=lifespan)

limiter = Limiter(key_func=get_remote_address)
app.state.limiter = limiter
app.add_exception_handler(RateLimitExceeded, _rate_limit_exceeded_handler)


@app.exception_handler(HTTPException)
def http_exception_handler(request: Request, exc: HTTPException):
    return JSONResponse(
        status_code=exc.status_code,
        content=_json_error("http_error", str(exc.detail)),
    )


@app.exception_handler(RequestValidationError)
def validation_exception_handler(request: Request, exc: RequestValidationError):
    return JSONResponse(
        status_code=422,
        content=_json_error("validation_error", "Validation error", details=exc.errors()),
    )


@app.exception_handler(RateLimitExceeded)
def rate_limit_exception_handler(request: Request, exc: RateLimitExceeded):
    return JSONResponse(status_code=429, content=_json_error("rate_limited", "Rate limit exceeded"))


@app.get("/health")
def health(request: Request):
    """Liveness probe: API process is up."""
    predictor = request.app.state.predictor
    return {
        "status": "ok",
        "model_loaded": predictor is not None,
        "model_version": getattr(predictor, "version", None),
    }


@app.get("/ready")
def ready(request: Request):
    """Readiness probe: model is loaded and /predict can serve traffic."""
    if request.app.state.predictor is None:
        raise HTTPException(
            status_code=503, detail="Model not loaded. Train and save the model first."
        )
    return {"status": "ready"}


@app.post("/predict", response_model=PredictionResponse)
@limiter.limit("10/minute")
def predict(request: Request, body: PredictionRequest) -> PredictionResponse:
    """Classify input text as spam or ham and return a confidence score."""
    predictor = request.app.state.predictor
    if predictor is None:
        raise HTTPException(
            status_code=503, detail="Model not loaded. Train and save the model first."
        )

    result = predictor.predict(body.text)
    return PredictionResponse(**result)


@app.post("/predict/batch", response_model=BatchPredictionResponse)
@limiter.limit("10/minute")
def predict_batch(request: Request, body: BatchPredictionRequest) -> BatchPredictionResponse:
    """Classify multiple inputs in one request. Returns predictions in input order."""
    predictor = request.app.state.predictor
    if predictor is None:
        raise HTTPException(
            status_code=503, detail="Model not loaded. Train and save the model first."
        )

    predictions: list[PredictionResponse] = []
    for text in body.texts:
        result = predictor.predict(text)
        predictions.append(PredictionResponse(**result))

    return BatchPredictionResponse(count=len(predictions), predictions=predictions)
