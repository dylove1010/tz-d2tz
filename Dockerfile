FROM python:3.11-slim
RUN apt-get update && apt-get install -y --no-install-recommends \
    chromium-driver fonts-liberation && \
    rm -rf /var/lib/apt/lists/*
COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt
COPY . /app
WORKDIR /app
ENV PORT=10000
CMD ["python", "app.py"]
