# insta_client.py
import os
from instagrapi import Client

# Instagram credentials (тянуть из Railway ENV)
IG_USERNAME = os.getenv("IG_USERNAME", "error_dixon")
IG_PASSWORD = os.getenv("IG_PASSWORD", "1226Egor!")

# Proxy settings (SOCKS5)
PROXY_HOST = os.getenv("PROXY_HOST", "5y7uqt2ob5.cn.fxdx.in")
PROXY_PORT = os.getenv("PROXY_PORT", "15469")
PROXY_USER = os.getenv("PROXY_USER", "originalharmony271109")
PROXY_PASS = os.getenv("PROXY_PASS", "eWvTse")

PROXY_URL = f"socks5://{PROXY_USER}:{PROXY_PASS}@{PROXY_HOST}:{PROXY_PORT}"


def get_insta_client():
    """
    Создаёт Instagram-клиент с сессией и мобильным SOCKS5-прокси.
    Работает стабильно на Railway.
    """

    cl = Client()
    cl.set_proxy(PROXY_URL)

    # Пытаемся загрузить старую сессию — это важно для стабильности
    try:
        cl.load_settings("ig_session.json")
        cl.login(IG_USERNAME, IG_PASSWORD)

    except Exception:
        # Если не удалось — логинимся заново
        cl.login(IG_USERNAME, IG_PASSWORD)
        cl.dump_settings("ig_session.json")

    return cl


# Тестовый запуск (локально)
if __name__ == "__main__":
    client = get_insta_client()
    print(client.user_info_by_username(IG_USERNAME))

