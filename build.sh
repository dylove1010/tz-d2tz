#!/usr/bin/env bash
set -e
echo "Installing Playwright browsers..."
PLAYWRIGHT_BROWSERS_PATH=$HOME/.cache/ms-playwright playwright install chromium
echo "PLAYWRIGHT_CHROMIUM_PATH=$HOME/.cache/ms-playwright/chromium-*/chrome-linux/chromium" >> $HOME/.env
pip install -r requirements.txt
