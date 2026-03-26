import os
from fastapi import FastAPI
import pyjokes
from prometheus_fastapi_instrumentator import Instrumentator

app = FastAPI()

POD_NAME = os.getenv("POD_NAME", "unknown-pod")

# Exposes /metrics with standard HTTP metrics automatically.
# Metrics: http_requests_total, http_request_duration_seconds,
#          http_request_size_bytes, http_response_size_bytes
Instrumentator().instrument(app).expose(app)


@app.get("/")
async def root():
    random_joke = pyjokes.get_joke("en", "neutral")
    return {
        "pod": POD_NAME,
        "random_joke": random_joke,
    }
