# 官方 Playwright 镜像，已自带 Chromium 和依赖
FROM mcr.microsoft.com/playwright/python:1.40.0-focal

ENV PYTHONUNBUFFERED=1
WORKDIR /app

# 安装 Python 依赖
COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt

# 复制代码
COPY . /app

# Render 端口
ENV PORT=10000

# 启动 Flask
CMD ["python", "app.py"]
