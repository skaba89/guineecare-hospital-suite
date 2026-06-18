#!/bin/bash
cd /home/z/my-project/guineecare-hospital-suite/backend
export DATABASE_URL="sqlite:///./test_guineecare.db"
export AUTH_SECRET="test-secret-key-for-e2e-testing"
export ENVIRONMENT="local"
exec /home/z/my-project/guineecare-hospital-suite/.venv/bin/python -m uvicorn app.main:app --host 0.0.0.0 --port 8000
