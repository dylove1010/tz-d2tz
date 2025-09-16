FROM python:3.11-alpine

# 安装最小化依赖（仅 chromium 和必要库）
RUN apk add --no-cache \
    chromium \
    chromium-chromedriver \
    && rm -rf /var/cache/apk/*  # 清理缓存

WORKDIR /app

COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt

COPY app.py .

EXPOSE 10000
CMD ["python", "app.py"]
