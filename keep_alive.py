import requests
import random
import threading
import time
from flask import Flask

app = Flask(__name__)

@app.route('/')
def index():
    return """
    <html>
    <head>
        <title>Replit Uptime</title>
    </head>
    <body style='text-align:center; font-family:Arial;'>
        <h1 style="color:green;">🟢 Server Đang Hoạt Động</h1>
        <p>Hệ thống auto-ping đa luồng đang chạy...</p>
    </body>
    </html>
    """

def run_flask():
    app.run(host='0.0.0.0', port=8080)

def random_ua():
    uas = [
        "Mozilla/5.0 (Windows NT 10.0; Win64; x64)",
        "Mozilla/5.0 (Linux; Android 10)",
        "Mozilla/5.0 (iPhone; CPU iPhone OS 14)",
        "Mozilla/5.0 (Macintosh; Intel Mac OS X)",
    ]
    return random.choice(uas)

def auto_ping(url, proxy=None):
    while True:
        try:
            headers = {"User-Agent": random_ua()}
            if proxy:
                requests.get(url, headers=headers, proxies={"http": proxy, "https": proxy}, timeout=10)
            else:
                requests.get(url, headers=headers, timeout=10)

            print(f"[PING] {url} ✔")
        except Exception as e:
            print("[PING ERROR]", e)

        time.sleep(random.randint(20, 40))

def keep_alive(proxy_list=None, threads=5):
    flask_thread = threading.Thread(target=run_flask, daemon=True)
    flask_thread.start()

    my_url = "http://0.0.0.0:8080"

    for _ in range(threads):
        proxy = random.choice(proxy_list) if proxy_list else None
        t = threading.Thread(target=auto_ping, args=(my_url, proxy), daemon=True)
        t.start()

    print(f"🚀 Đã bật keep_alive với {threads} luồng ping!")

# KHỞI CHẠY
keep_alive(
    proxy_list=None,  # thay bằng list proxy nếu muốn
    threads=8
)
