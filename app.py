import os, requests, logging
from flask import Flask
from selenium import webdriver
from selenium.webdriver.chrome.options import Options
from selenium.webdriver.common.by import By
from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.support import expected_conditions as EC
from threading import Thread

# 从环境变量读取Webhook地址（优先使用环境变量，避免硬编码）
WEBHOOK_URL = os.environ.get(
    "WEBHOOK_URL", 
    "https://qyapi.weixin.qq.com/cgi-bin/webhook/send?key=b0bcfe46-3aa1-4071-afd5-da63be5a8644"  # 备用默认值
)
TARGET_URL  = "https://www.d2tz.info/?l=zh-cn"

logging.basicConfig(level=logging.INFO, format="%(asctime)s %(levelname)s %(message)s")
logger = logging.getLogger(__name__)

app = Flask(__name__)

def fetch_terror_info():
    options = Options()
    # 关键修复：匹配render-build.sh中安装的Chromium路径
    options.binary_location = "/usr/bin/chromium-browser"  # 修正为正确的浏览器可执行文件路径
    
    # 完整的浏览器启动参数（解决权限、内存和会话冲突）
    options.add_argument("--headless=new")  # 新版无头模式，兼容性更好
    options.add_argument("--no-sandbox")  # 解决Render环境下的权限限制
    options.add_argument("--disable-dev-shm-usage")  # 避免共享内存不足
    options.add_argument("--disable-gpu")  # 无头模式无需GPU加速
    options.add_argument("--disable-images")  # 禁用图片加载，节省资源
    options.add_argument("--window-size=1280,720")  # 固定窗口尺寸，避免元素定位问题
    options.add_argument("--single-process")  # 单进程模式，减少资源占用
    # 唯一用户数据目录，彻底解决目录占用问题
    options.add_argument(f"--user-data-dir=/tmp/chromium-{os.getpid()}")
    options.add_argument("--disable-extensions")  # 禁用扩展，加快启动
    options.add_argument("--disable-plugins")  # 禁用插件，减少干扰

    # 初始化驱动时指定匹配的chromedriver（Render环境已通过render-build.sh安装）
    driver = webdriver.Chrome(options=options)
    
    try:
        # 设置页面加载超时
        driver.set_page_load_timeout(15)
        driver.get(TARGET_URL)
        
        # 等待关键元素加载（增加超时时间，确保页面加载完成）
        WebDriverWait(driver, 15).until(
            EC.presence_of_element_located((By.CSS_SELECTOR, "tbody[role='rowgroup'] tr"))
        )
        
        # 提取数据
        rows = driver.find_elements(By.CSS_SELECTOR, "tbody[role='rowgroup'] tr")[:2]
        out = []
        for row in rows:
            cells = row.find_elements(By.TAG_NAME, "td")
            if len(cells) >= 2:
                area_raw = cells[1].text.strip()
                area_only = area_raw.split("▶")[-1].strip()
                out.append((cells[0].text.strip(), area_only))
        
        if len(out) < 2:
            return None, None, None, None
        next_time, next_area = out[0]
        current_time, current_area = out[1]
        return current_area, current_time, next_area, next_time
    
    except Exception as e:
        logger.error(f"数据抓取失败: {str(e)}")
        return None, None, None, None
    
    finally:
        # 确保浏览器正确关闭，释放资源
        driver.quit()

def send_wecom_message(c, ct, n, nt):
    now  = c or "暂无"
    soon = n or "暂无"
    content = f"{now}▶{soon}"
    try:
        rsp = requests.post(
            WEBHOOK_URL,
            json={"msgtype": "text", "text": {"content": content}},
            timeout=10
        )
        rsp.raise_for_status()  # 捕获HTTP错误状态码
        logger.info("企业微信推送成功: %s", content)
    except Exception as e:
        logger.error(f"企业微信推送失败: {str(e)}")

@app.route("/")
def index():
    # 启动异步任务，避免阻塞HTTP响应
    Thread(target=_push_real_data, daemon=True).start()
    return "tz-d2tz is running!", 200

def _push_real_data():
    try:
        c, ct, n, nt = fetch_terror_info()
        if c or n:
            send_wecom_message(c, ct, n, nt)
        else:
            logger.warning("未获取到有效数据，不推送空消息")
    except Exception as e:
        logger.exception("后台推送任务失败")
        # 仅在异常时推送错误提示
        try:
            requests.post(
                WEBHOOK_URL,
                json={"msgtype": "text", "text": {"content": "数据抓取异常▶数据抓取异常"}},
                timeout=5
            )
        except:
            pass

if __name__ == "__main__":
    port = int(os.environ.get("PORT", 5000))
    app.run(host="0.0.0.0", port=port)
