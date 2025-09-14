FROM python:3.11-alpine

# 1. 装最小依赖 + chromium-driver（37 MB）
RUN apk add --no-cache \
    chromium-chromedriver \
    chromium \
    libstdc++

# 2. 装 Python 包
COPY requirements.txt .
RUN python -m pip install --upgrade pip && \
    pip config set global.index-url https://pypi.tuna.tsinghua.edu.cn/simple && \
    pip install --no-cache-dir -r requirements.txt

# 3. 拷代码
COPY . /app
WORKDIR /app

ENV PORT=10000
CMD ["gunicorn", "app:app", "-b", "0.0.0.0:10000"]
