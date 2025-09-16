import os, requests, logging, time
from flask import Flask
from selenium import webdriver
from selenium.webdriver.chrome.options import Options
from selenium.webdriver.common.by import By
from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.support import expected_conditions as EC
from threading import Thread

# 从环境变量读取Webhook地址
WEBHOOK_URL = os.environ.get("WEBHOOK_URL")  # 移除硬编码默认值，强制用户配置
TARGET_URL  = "https://www.d2tz.info/?l=zh-cn"

# 日志配置
logging.basicConfig(level=logging.INFO, format="%(asctime)s %(levelname)s %(message)s")
logger = logging.getLogger(__name__)

app = Flask(__name__)

def fetch_terror_info(max_retries=2):
    """带重试机制的抓取函数"""
    for attempt in range(max_retries + 1):
        try:
            options = Options()
            # 浏览器路径（匹配Render安装路径）
            options.binary_location = "/usr/bin/chromium-browser"
            
            # 强化资源优化参数
            options.add_argument("--headless=new")  # 无头模式
            options.add_argument("--no-sandbox")  # 解决权限问题
            options.add_argument("--disable-dev-shm-usage")  # 避免共享内存不足
            options.add_argument("--disable-gpu")  # 禁用GPU
            options.add_argument("--disable-images")  # 禁用图片
            options.add_argument("--disable-audio")  # 禁用音频
            options.add_argument("--disable-popup-blocking")  # 禁用弹窗
            options.add_argument("--window-size=1024,768")  # 更小窗口尺寸
            options.add_argument("--single-process")  # 单进程模式
            options.add_argument("--blink-settings=imagesEnabled=false")  # 彻底禁用图片
            options.add_argument(f"--user-data-dir=/tmp/chromium-tmp-{os.urandom(8).hex()}")  # 随机临时目录
            options.add_argument("--disable-extensions")
            options.add_argument("--disable-plugins")
            options.add_argument("--disable-software-rasterizer")  # 禁用软件光栅化
            options.add_argument("--disable-translate")  # 禁用翻译
            options.add_argument("--no-first-run")  # 跳过首次运行配置
            
            # 初始化驱动
            driver = webdriver.Chrome(options=options)
            
            try:
                # 延长超时时间（资源受限环境需要更长时间）
                driver.set_page_load_timeout(30)  # 页面加载超时30秒
                driver.get(TARGET_URL)
                
                # 等待元素加载（最长25秒）
                WebDriverWait(driver, 25).until(
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
                    logger.warning(f"第{attempt+1}次尝试：数据不完整（{len(out)}条）")
                    if attempt < max_retries:
                        time.sleep(2)  # 重试前短暂等待
                        continue
                    return None, None, None, None
                
                next_time, next_area = out[0]
                current_time, current_area = out[1]
                logger.info(f"第{attempt+1}次尝试：抓取成功")
                return current_area, current_time, next_area, next_time
            
            except Exception as e:
                logger.error(f"第{attempt+1}次尝试失败: {str(e)}")
                if attempt < max_retries:
                    time.sleep(2)  # 重试间隔
                    continue
                return None, None, None, None
            
            finally:
                # 确保浏览器关闭
                driver.quit()
        
        except Exception as e:
            logger.error(f"浏览器启动失败（第{attempt+1}次）: {str(e)}")
            if attempt < max_retries:
                time.sleep(2)
                continue
            return None, None, None, None
    
    return None, None, None, None  # 所有重试失败

def send_wecom_message(c, ct, n, nt):
    if not WEBHOOK_URL:
        logger.error("未配置WEBHOOK_URL，无法推送")
        return
    
    now  = c or "暂无"
    soon = n or "暂无"
    content = f"当前: {now} ({ct or '未知时间'})\n即将: {soon} ({nt or '未知时间'})"
    try:
        rsp = requests.post(
            WEBHOOK_URL,
            json={"msgtype": "text", "text": {"content": content}},
            timeout=10
        )
        rsp.raise_for_status()
        logger.info("推送成功: %s", content)
    except Exception as e:
        logger.error(f"推送失败: {str(e)}")

@app.route("/")
def index():
    # 异步执行抓取任务，避免阻塞响应
    Thread(target=_push_real_data, daemon=True).start()
    return "tz-d2tz is running!", 200

def _push_real_data():
    try:
        c, ct, n, nt = fetch_terror_info()
        if c or n:
            send_wecom_message(c, ct, n, nt)
        else:
            logger.warning("未获取到有效数据，不推送")
            # 失败时推送提示（可选）
            # send_wecom_message("抓取失败", "", "抓取失败", "")
    except Exception as e:
        logger.exception("推送任务异常")
        try:
            if WEBHOOK_URL:
                requests.post(
                    WEBHOOK_URL,
                    json={"msgtype": "text", "text": {"content": "服务运行异常"}},
                    timeout=5
                )
        except:
            pass

if __name__ == "__main__":
    port = int(os.environ.get("PORT", 10000))
    app.run(host="0.0.0.0", port=port)
