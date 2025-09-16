FROM python:3.11-slim

# 安装浏览器和驱动
RUN apt-get update && apt-get install -y \
    chromium \
    chromium-driver \
    && rm -rf /var/lib/apt/lists/*

WORKDIR /app

# 先复制依赖文件并安装，利用 Docker 缓存加速后续构建
COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt --upgrade pip  # 增加 --upgrade pip 确保工具正常

# 再复制应用代码
COPY app.py .

EXPOSE 10000
CMD ["python", "app.py"]
