FROM python:3.12-slim

WORKDIR /app

COPY apps/api/requirements.txt ./api-requirements.txt
RUN pip install --no-cache-dir -r api-requirements.txt

COPY apps/api/ ./apps/api/

ENV PYTHONPATH=/app/apps/api

CMD ["uvicorn", "apps.api.main:app", "--host", "0.0.0.0", "--port", "8000"]
