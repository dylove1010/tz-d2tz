FROM python:3.11-slim

WORKDIR /app

# 仅安装必要系统依赖（证书用于HTTPS请求）
RUN apt-get update && apt-get install -y --no-install-recommends \
    ca-certificates \
    && apt-get clean \
    && rm -rf /var/lib/apt/lists/*

# 安装Python依赖
COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt

# 复制项目文件
COPY . .

# 启动应用
CMD ["python", "app.py"]
