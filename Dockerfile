# 使用官方 Python 镜像
FROM python:3.11-slim

ENV PYTHONUNBUFFERED=1

# 安装系统依赖 & Google Chrome
RUN apt-get update && apt-get install -y wget gnupg2 unzip curl ca-certificates \
    && mkdir -p /etc/apt/keyrings \
    && wget -q -O- https://dl.google.com/linux/linux_signing_key.pub | gpg --dearmor > /etc/apt/keyrings/google.gpg \
    && echo "deb [arch=amd64 signed-by=/etc/apt/keyrings/google.gpg] http://dl.google.com/linux/chrome/deb/ stable main" > /etc/apt/sources.list.d/google-chrome.list \
    && apt-get update && apt-get install -y google-chrome-stable chromium-driver \
    && rm -rf /var/lib/apt/lists/*

# 设置 DNS，避免 net::ERR_NAME_NOT_RESOLVED
RUN echo "nameserver 8.8.8.8" > /etc/resolv.conf && \
    echo "nameserver 8.8.4.4" >> /etc/resolv.conf

WORKDIR /app

# 安装 Python 依赖
COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt

# 拷贝代码
COPY . /app

# 启动 Flask
CMD ["python", "app.py"]
