FROM python:3.12-slim

WORKDIR /app

# Install worker requirements
COPY apps/worker/requirements.txt ./worker-requirements.txt
RUN pip install --no-cache-dir -r worker-requirements.txt

# Also install API requirements since we share its code
COPY apps/api/requirements.txt ./api-requirements.txt
RUN pip install --no-cache-dir -r api-requirements.txt

COPY apps/worker/ ./apps/worker/
COPY apps/api/ ./apps/api/

ENV PYTHONPATH=/app/apps/api:/app/apps/worker

CMD ["uvicorn", "apps.worker.main:app", "--host", "0.0.0.0", "--port", "8001"]
