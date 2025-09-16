#!/usr/bin/env bash
# 安装Chromium及匹配的驱动
sudo apt-get update
sudo apt-get install -y chromium-browser chromium-chromedriver
# 验证安装
if [ -f "/usr/bin/chromium-browser" ] && [ -f "/usr/bin/chromedriver" ]; then
    echo "Chromium及驱动安装成功"
    # 验证版本匹配
    chromium_version=$(chromium-browser --version | grep -oP '\d+\.\d+\.\d+\.\d+')
    driver_version=$(chromedriver --version | grep -oP '\d+\.\d+\.\d+\.\d+')
    if [ "$chromium_version" = "$driver_version" ]; then
        echo "浏览器与驱动版本匹配: $chromium_version"
    else
        echo "警告: 浏览器版本($chromium_version)与驱动版本($driver_version)不匹配"
    fi
else
    echo "Chromium或驱动安装失败"
    exit 1
fi
