# 官方 Playwright 镜像（使用 latest，带浏览器和依赖）
FROM mcr.microsoft.com/playwright/python:latest

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
