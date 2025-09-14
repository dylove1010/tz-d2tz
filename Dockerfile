FROM python:3.11-alpine

# 1. 装最小依赖 + chromium-driver（37 MB）
RUN apk add --no-cache \
    chromium-chromedriver \
    chromium \
    libstdc++

# 2. 修索引 + 升级 pip + 装包（缓存层）
COPY requirements.txt .
RUN pip install --upgrade pip && \
    pip install -i https://pypi.org/simple --no-cache-dir -r requirements.txt

# 3. 拷代码
COPY . /app
WORKDIR /app

ENV PORT=10000
CMD ["gunicorn", "app:app", "-b", "0.0.0.0:10000"]
