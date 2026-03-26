import os
from fastapi import FastAPI
import pyjokes

app = FastAPI()

# Kubernetes sets HOSTNAME to the pod name automatically.
# We also expose it explicitly via the Downward API in values.yaml
# so the name is unambiguous regardless of the base image.
POD_NAME = os.getenv("POD_NAME", "unknown-pod")


@app.get("/")
async def root():
    random_joke = pyjokes.get_joke("en", "neutral")
    return {"pod": POD_NAME, "random_joke": random_joke}
