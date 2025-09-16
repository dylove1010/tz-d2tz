FROM python:3.11-slim

# 安装 chromium 浏览器和驱动（适配 Render 环境）
RUN apt-get update && apt-get install -y \
    chromium \
    chromium-driver \
    && rm -rf /var/lib/apt/lists/*

WORKDIR /app
COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt
COPY app.py .
# 暴露 10000 端口（与代码一致）
EXPOSE 10000
CMD ["python", "app.py"]
