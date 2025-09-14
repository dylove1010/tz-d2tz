# 官方 Python 3.11  slim 镜像，已带 apt
FROM python:3.11-slim

# 安装系统依赖 + chromium 一次过
RUN apt-get update && apt-get install -y \
    wget gnupg \
    && wget -q -O - https://dl.google.com/linux/linux_signing_key.pub | apt-key add - \
    && echo "deb [arch=amd64] http://dl.google.com/linux/chrome/deb/ stable main" >> /etc/apt/sources.list.d/google.list \
    && apt-get update && apt-get install -y chromium \
    && rm -rf /var/lib/apt/lists/*

# 装 Python 依赖
COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt

# 把代码拷进去
COPY . /app
WORKDIR /app

# 暴露端口（Render 自动注入 PORT）
ENV PORT=10000
CMD ["gunicorn", "app:app", "-b", "0.0.0.0:10000"]
