# 使用官方 selenium 基础镜像，已经自带 Chrome 和 ChromeDriver
FROM selenium/standalone-chrome:120.0

# 设置 Python 环境
RUN apt-get update && apt-get install -y python3 python3-pip

# 设置工作目录
WORKDIR /app

# 复制依赖文件
COPY requirements.txt .

# 安装依赖
RUN pip3 install --no-cache-dir -r requirements.txt

# 复制代码
COPY . .

# 运行 Flask
CMD ["python3", "app.py"]
