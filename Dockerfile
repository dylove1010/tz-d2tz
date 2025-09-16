# 使用 Python 官方镜像
FROM python:3.11-slim

# 设置工作目录
WORKDIR /app

# 安装系统依赖（Chromium 浏览器及驱动）
RUN apt-get update && apt-get install -y \
    chromium-browser \
    chromium-driver \
    && rm -rf /var/lib/apt/lists/*

# 复制项目文件
COPY . .

# 安装 Python 依赖
RUN pip install --no-cache-dir -r requirements.txt

# 暴露端口（与代码中 PORT 保持一致）
EXPOSE 10000

# 启动命令（通过环境变量注入配置）
CMD ["python", "app.py"]
