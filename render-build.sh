#!/usr/bin/env bash
# 安装Chromium浏览器及配套驱动（必须，否则Selenium无法运行）
sudo apt-get update
sudo apt-get install -y chromium-browser chromium-chromedriver
# 验证安装完整性
if [ -f "/usr/bin/chromium-browser" ] && [ -f "/usr/bin/chromedriver" ]; then
    echo "Chromium及驱动安装成功"
else
    echo "Chromium或驱动安装失败"
    exit 1
fi
