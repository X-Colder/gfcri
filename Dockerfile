FROM python:3.11-slim

RUN apt-get update && \
    apt-get install -y --no-install-recommends libpq5 gcc python3-dev libpq-dev \
    fonts-noto-cjk fontconfig && \
    fc-cache -fv && \
    apt-get clean && rm -rf /var/lib/apt/lists/*

WORKDIR /app

COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt \
    -i https://pypi.tuna.tsinghua.edu.cn/simple \
    --trusted-host pypi.tuna.tsinghua.edu.cn \
    --timeout 120 && \
    python -c "import matplotlib.font_manager"  && \
    rm -rf /root/.cache/matplotlib

COPY src/ ./src/
COPY dashboard/ ./dashboard/
COPY scripts/ ./scripts/

ENV PYTHONPATH=/app
ENV PYTHONUNBUFFERED=1
