# tz-d2tz
免费 Selenium + Flask 整点推送服务（Render 版）

## 功能
- 每整点 + 20 秒自动抓取「恐怖地带」列表
- 纯区域格式推送（无 Now/Coming soon）
- 内存 &lt; 400 MB，Render 免费实例稳过

## 快速部署（Render 版）
1. Fork 本仓库
2. 申请 [Render 免费账户](https://render.com)
3. 新建 Web Service → 连接本仓库
4. 设置环境变量：
   - `PORT=10000`
   - `WEBHOOK_URL=你的企业微信机器人地址`
5. 新建 Cron Job：
   - Schedule: `1 * * * *`（每小时的 01 分 + 20 秒）
   - URL: `https://你的域名.onrender.com/`
6. 保存 → 部署完成！

## 内存优化
- 只装 `chromium-driver`，无完整 Chrome
- 只抓 2 行就关 driver
- 后台线程推，不阻塞检测

## 免费替代（&gt;512 MB 硬顶）
- [IBM LinuxONE 永久 8 GB](https://community.ibm.com/zsystems/form/l1cc-oss-vm-request/)
- 腾讯云/阿里云轻量 2 GB（1 个月试用）

## 许可证
MIT
