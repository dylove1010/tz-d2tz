FROM python:3.11-slim
ENV PYTHONUNBUFFERED=1

# 安装 lxml 依赖
RUN apt-get update && apt-get install -y --no-install-recommends \
    libxml2 libxslt1.1 libxslt1-dev && \
    rm -rf /var/lib/apt/lists/*

COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt

COPY . /app
WORKDIR /app
ENV PORT=10000
CMD ["python", "app.py"]
