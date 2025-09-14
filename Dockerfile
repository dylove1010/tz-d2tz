FROM python:3.11-slim

# 1. 换国内源 + 装精简 chromium + 清缓存
RUN sed -i 's@http://deb.debian.org@http://mirrors.ustc.edu.cn@g' /etc/apt/sources.list && \
    apt-get update && \
    apt-get install -y --no-install-recommends \
        chromium chromium-driver && \
    rm -rf /var/lib/apt/lists/* /tmp/* /var/tmp/*

# 2. 装 Python 依赖
COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt

# 3. 拷代码
COPY . /app
WORKDIR /app

ENV PORT=10000
CMD ["gunicorn", "app:app", "-b", "0.0.0.0:10000"]
