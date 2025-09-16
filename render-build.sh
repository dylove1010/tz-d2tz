#!/usr/bin/env bash
# 安装Chromium及所有依赖
sudo apt-get update
sudo apt-get install -y chromium-browser chromium-chromedriver
# 验证安装结果
if [ ! -f "/usr/bin/chromium-browser" ]; then
    echo "Chromium浏览器安装失败"
    exit 1
fi
if [ ! -f "/usr/bin/chromedriver" ]; then
    echo "ChromeDriver安装失败"
    exit 1
fi
# 建立软链接（解决路径问题）
sudo ln -s /usr/bin/chromedriver /usr/local/bin/chromedriver
