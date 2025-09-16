# tz-d2tz
免费 Selenium + Flask 整点推送服务（Render 版）

## 功能
- 每整点 + 20 秒自动抓取「恐怖地带」列表
- 纯区域格式推送（无 Now/Coming soon）
- 内存优化至 400MB 以内，适配 Render 免费实例

## 快速部署（Render 版）
1. Fork 本仓库
2. 申请 [Render 免费账户](https://render.com)
3. 新建 Web Service → 连接本仓库
4. 设置环境变量：
   - `PORT=10000`
   - `WEBHOOK_URL=你的企业微信机器人地址`（必填）
5. 新建 Cron Job（可选，也可使用GitHub Actions定时任务）：
   - Schedule: `1 * * * *`
   - URL: `https://你的域名.onrender.com/`
6. 保存 → 部署完成！

## 优化说明
- 自动安装 Chromium 浏览器（解决启动失败问题）
- 精简浏览器参数（禁用图片、GPU，单进程模式）
- 即用即走模式（抓取后立即关闭浏览器释放内存）
- 从环境变量读取配置（避免硬编码敏感信息）

## 许可证
MIT
