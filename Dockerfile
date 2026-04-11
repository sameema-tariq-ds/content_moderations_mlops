FROM python:3.11-slim

WORKDIR /app

ARG INSTALL_DEV=0
COPY pyproject.toml README.md LICENSE ./
COPY . .

RUN pip install --no-cache-dir --upgrade pip && \
    if [ "$INSTALL_DEV" = "1" ]; then pip install --no-cache-dir ".[dev]"; else pip install --no-cache-dir .; fi

EXPOSE 8000
CMD ["gunicorn", "-c", "gunicorn_conf.py", "app.main:app"]
