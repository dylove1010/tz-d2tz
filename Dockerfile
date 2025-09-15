FROM python:3.11-slim

ENV PYTHONUNBUFFERED=1

# 安装 chromium 和 chromedriver
RUN apt-get update && apt-get install -y \
    chromium chromium-driver \
    fonts-liberation \
    && rm -rf /var/lib/apt/lists/*

WORKDIR /app

COPY requirements.txt .
RUN pip install -r requirements.txt

COPY . .

CMD ["python", "app.py"]
