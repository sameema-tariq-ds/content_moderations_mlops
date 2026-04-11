import os

bind = os.getenv("BIND", "0.0.0.0:8000")
workers = int(os.getenv("WEB_CONCURRENCY", "2"))
worker_class = "uvicorn.workers.UvicornWorker"
timeout = int(os.getenv("TIMEOUT", "60"))
graceful_timeout = int(os.getenv("GRACEFUL_TIMEOUT", "30"))
keepalive = int(os.getenv("KEEPALIVE", "5"))

accesslog = "-"
errorlog = "-"
loglevel = os.getenv("LOG_LEVEL", "info")
