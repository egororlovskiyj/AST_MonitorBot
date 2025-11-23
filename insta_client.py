from instagrapi import Client

# === Instagram credentials ===
IG_USERNAME = "error_dixon"
IG_PASSWORD = "1226Egor!"  # <-- 

# === Socks5 proxy ===
PROXY_URL = "socks5://originalharmony271109:eWvTse@5y7uqt2ob5.cn.fxdx.in:15469"


def get_insta_client():
    cl = Client()

    # подключаем proxy
    cl.set_proxy(PROXY_URL)

    # пробуем загрузить сессию
    try:
        cl.load_settings("ig_session.json")
        cl.login(IG_USERNAME, IG_PASSWORD)
    except Exception:
        # если не получилось — создаём новую
        cl.login(IG_USERNAME, IG_PASSWORD)
        cl.dump_settings("ig_session.json")

    return cl


# ==== ТЕСТ ====
if __name__ == "__main__":
    cli = get_insta_client()
    me = cli.user_info_by_username(IG_USERNAME)
    print(me)
