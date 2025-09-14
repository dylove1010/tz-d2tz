FROM --platform=linux/amd64 python:3.11-slim

# 装系统依赖 + driver
RUN apt-get update && apt-get install -y --no-install-recommends \
    chromium-driver fonts-liberation && \
    rm -rf /var/lib/apt/lists/*

# 装 Python 包（官方 wheel 已存在）
COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt

COPY . /app
WORKDIR /app
ENV PORT=10000
CMD ["gunicorn", "app:app", "-b", "0.0.0.0:10000"]
