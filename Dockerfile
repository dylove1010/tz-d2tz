# ---------- 基础镜像 ----------
FROM python:3.11-slim

ENV PYTHONUNBUFFERED=1 \
    PORT=10000

# ---------- 安装依赖 ----------
RUN apt-get update && apt-get install -y --no-install-recommends \
    ca-certificates \
    && rm -rf /var/lib/apt/lists/*

# ---------- 拷贝文件 ----------
COPY requirements.txt /app/requirements.txt
COPY . /app
WORKDIR /app

# ---------- 安装 Python 库 ----------
RUN pip install --no-cache-dir -r requirements.txt

# ---------- 暴露端口 ----------
EXPOSE 10000

# ---------- 启动 Flask ----------
CMD ["python", "app.py"]
