#!/usr/bin/env bash
# 安装Chromium及驱动
sudo apt-get update
sudo apt-get install -y chromium-browser chromium-chromedriver
# 验证安装
if [ -f "/usr/bin/chromium-browser" ] && [ -f "/usr/bin/chromedriver" ]; then
    echo "Chromium及驱动安装成功"
else
    echo "Chromium或驱动安装失败"
    exit 1
fi
