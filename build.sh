#!/usr/bin/env bash
set -e
echo "Installing Playwright browsers..."
# 用微软官方脚本，指定 chromium 仅安装一次
PLAYWRIGHT_BROWSERS_PATH=$HOME/.cache/ms-playwright playwright install chromium
# 把可执行文件路径写进环境变量，供 app.py 读取
echo "PLAYWRIGHT_CHROMIUM_PATH=$HOME/.cache/ms-playwright/chromium-*/chrome-linux/chromium" >> $HOME/.env
pip install -r requirements.txt
