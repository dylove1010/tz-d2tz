FROM python:3.11-slim

# ① 最小化安装（仅 driver + 字体）
RUN apt-get update && apt-get install -y --no-install-recommends \
    chromium-driver fonts-liberation && \
    rm -rf /var/lib/apt/lists/*

# ② Python 依赖
COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt

# ③ 拷代码
COPY . /app
WORKDIR /app

ENV PORT=10000
CMD ["gunicorn", "app:app", "-b", "0.0.0.0:10000"]
