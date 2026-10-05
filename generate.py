import json
import base64
import os
from datetime import datetime

TARIFFS = {
    "trial": {"display_name": "TRIAL 🔥", "default_days": 3, "default_traffic_gb": 5},
    "lite":  {"display_name": "LITE ⚡",  "default_days": 30, "default_traffic_gb": 50},
    "vip":   {"display_name": "VIP 👑",  "default_days": 30, "default_traffic_gb": 0}
}


def load_all_keys(tariff):
    """Читает все .json из папки и собирает в массив"""
    folder = f"keys/{tariff}"
    print(f"  🔍 Папка: {folder}")

    if not os.path.exists(folder):
        print(f"  ❌ НЕ НАЙДЕНА")
        return []

    files = sorted(os.listdir(folder))
    print(f"  📂 Файлов: {len(files)}")

    all_keys = []
    for filename in files:
        if filename.endswith('.json'):
            path = os.path.join(folder, filename)
            with open(path, 'r', encoding='utf-8') as f:
                try:
                    key = json.load(f)
                    all_keys.append(key)
                    print(f"  ✅ Загружен: {filename}")
                except json.JSONDecodeError as e:
                    print(f"  ❌ Ошибка JSON в {filename}: {e}")

    print(f"  🔑 Итого: {len(all_keys)}")
    return all_keys


def build_subscription(keys, expire_timestamp, total_bytes, display_name):
    """Шапка + JSON-массив, всё в base64"""
    headers = f"""#profile-title: HotVPN {display_name}
#profile-update-interval: 5
#support-url: https://t.me/Wd_Life
#subscription-userinfo: upload=0; download=0; total={total_bytes}; expire={expire_timestamp}
#sub-expire: true

"""
    json_part = json.dumps(keys, indent=2, ensure_ascii=False)
    combined = headers + json_part
    return base64.b64encode(combined.encode('utf-8')).decode('utf-8')


def main():
    print("=" * 50)
    print("=== СТАРТ ===")
    print("=" * 50)

    os.makedirs('subs', exist_ok=True)

    if not os.path.exists('users.json'):
        print("❌ users.json не найден!")
        return

    with open('users.json', 'r', encoding='utf-8') as f:
        users = json.load(f)

    print(f"\n📦 Пользователей: {len(users)}\n")

    for user_id, user_info in users.items():
        print(f"--- {user_id} ---")

        if user_info.get('status') != 'active':
            if os.path.exists(f'subs/{user_id}.txt'):
                os.remove(f'subs/{user_id}.txt')
            print(f"❌ заблокирован\n")
            continue

        tariff = user_info.get('plan', 'lite')
        if tariff not in TARIFFS:
            print(f"⚠️ тариф '{tariff}' не найден, использую 'lite'")
            tariff = 'lite'

        cfg = TARIFFS[tariff]

        expire_date_str = user_info.get('expire_date')
        if expire_date_str:
            try:
                expire_timestamp = int(datetime.strptime(expire_date_str, "%Y-%m-%d").timestamp())
            except ValueError:
                expire_timestamp = 0
        else:
            expire_timestamp = 0

        traffic_limit_gb = user_info.get('traffic_limit_gb', cfg["default_traffic_gb"])
        total_bytes = traffic_limit_gb * 1073741824

        keys = load_all_keys(tariff)

        if not keys:
            print(f"❌ нет ключей в keys/{tariff}/\n")
            continue

        subscription = build_subscription(keys, expire_timestamp, total_bytes, cfg["display_name"])

        with open(f'subs/{user_id}.txt', 'w', encoding='utf-8') as f:
            f.write(subscription)

        print(f"✅ {cfg['display_name']} | ключей: {len(keys)} | до: {expire_date_str or '∞'}\n")

    print("=" * 50)
    print("=== ГОТОВО ===")
    print("=" * 50)


if __name__ == "__main__":
    main()
