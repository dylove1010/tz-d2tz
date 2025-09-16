# 使用 Python 3.11  slim 镜像（轻量且兼容）
FROM python:3.11-slim

# 设置工作目录
WORKDIR /app

# 安装系统依赖：Chromium 浏览器、驱动及必要库
RUN apt-get update && apt-get install -y \
    chromium \
    chromium-driver \
    libnss3 \
    libgconf-2-4 \
    libxi6 \
    libxrender1 \
    libxss1 \
    libxtst6 \
    && rm -rf /var/lib/apt/lists/*  # 清理缓存，减小镜像体积

# 复制依赖文件并安装
COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt

# 复制项目所有文件
COPY . .

# 启动命令（运行 Flask 应用）
CMD ["python", "app.py"]
