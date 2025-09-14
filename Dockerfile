FROM python:3.11-alpine
RUN apk add --no-cache libstdc++
COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt
COPY . /app
WORKDIR /app
ENV PORT=10000
CMD ["python", "app.py"]
