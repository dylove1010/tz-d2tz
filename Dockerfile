# 使用官方 Playwright Python 镜像，带 Chromium 和依赖
FROM mcr.microsoft.com/playwright/python:1.58.0-focal

ENV PYTHONUNBUFFERED=1
WORKDIR /app

COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt

COPY . /app

ENV PORT=10000
EXPOSE 10000

CMD ["python", "app.py"]
