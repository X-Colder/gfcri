FROM python:3.11-slim

RUN apt-get update && apt-get install -y --no-install-recommends \
    libpq5 gcc python3-dev libpq-dev && \
    apt-get clean && rm -rf /var/lib/apt/lists/*

WORKDIR /app

COPY requirements.txt requirements-api.txt ./
RUN pip install --no-cache-dir \
    -r requirements.txt \
    -r requirements-api.txt \
    -i https://pypi.tuna.tsinghua.edu.cn/simple

COPY src/ ./src/
COPY api/ ./api/
COPY scripts/ ./scripts/
COPY dashboard/style.py ./dashboard/style.py

ENV PYTHONPATH=/app
ENV PYTHONUNBUFFERED=1

EXPOSE 8000

CMD ["uvicorn", "api.main:app", "--host", "0.0.0.0", "--port", "8000"]
