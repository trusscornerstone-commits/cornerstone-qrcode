#!/bin/sh
uvicorn apps.fastapi_app.main:app --host 0.0.0.0 --port 8001 --reload
