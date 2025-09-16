#!/usr/bin/env bash
# 安装Chromium浏览器及依赖
sudo apt-get update
sudo apt-get install -y chromium-browser
# 验证安装
if [ -f "/usr/bin/chromium-browser" ]; then
    echo "Chromium安装成功"
else
    echo "Chromium安装失败"
    exit 1
fi
