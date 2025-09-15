# 使用与 Playwright 版本匹配的官方镜像
FROM mcr.microsoft.com/playwright/python:1.55.0-jammy

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
