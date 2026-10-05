import json
import base64
import os
from datetime import datetime

# ===== ТАРИФЫ: НАСТРОЙКИ =====
TARIFFS = {
    "trial": {
        "display_name": "TRIAL 🔥",
        "description": "Пробный доступ на 3 дня",
        "default_days": 3,
        "default_traffic_gb": 5
    },
    "lite": {
        "display_name": "LITE ⚡",
        "description": "Доступные серверы, 50 ГБ/мес",
        "default_days": 30,
        "default_traffic_gb": 50
    },
    "vip": {
        "display_name": "VIP 👑",
        "description": "Все серверы, безлимит",
        "default_days": 30,
        "default_traffic_gb": 0
    }
}


def load_all_keys(tariff):
    """
    Собирает ВСЕ .json файлы из папки keys/{tariff}/ в один массив.
    Каждый файл = один ключ.
    """
    folder = f"keys/{tariff}"

    if not os.path.exists(folder):
        raise FileNotFoundError(f"❌ Папка {folder} не найдена!")

    all_keys = []

    # Читаем все .json файлы по порядку (01, 02, 03...)
    for filename in sorted(os.listdir(folder)):
        if filename.endswith('.json'):
            path = os.path.join(folder, filename)
            with open(path, 'r', encoding='utf-8') as f:
                try:
                    key = json.load(f)
                    all_keys.append(key)
                    print(f"  📄 Загружен: {filename}")
                except json.JSONDecodeError as e:
                    print(f"  ❌ Ошибка в {filename}: {e}")

    if not all_keys:
        raise ValueError(f"❌ В папке {folder} нет ни одного .json файла!")

    return all_keys


def build_subscription(keys, expire_timestamp, total_bytes, display_name, description):
    """
    Собирает подписку:
    - шапка (название, срок, лимит)
    - JSON-массив со всеми ключами
    - всё в base64
    """
    headers = f"""#profile-title: HotVPN {display_name}
#profile-update-interval: 5
#support-url: https://t.me/Wd_Life
#subscription-userinfo: upload=0; download=0; total={total_bytes}; expire={expire_timestamp}
#sub-expire: true
#announce: {description}

"""
    # JSON-массив со всеми ключами
    json_part = json.dumps(keys, indent=2, ensure_ascii=False)

    # Склеиваем: шапка + все ключи
    combined = headers + json_part

    # Кодируем в base64 (Happ понимает)
    return base64.b64encode(combined.encode()).decode()


def main():
    os.makedirs('subs', exist_ok=True)

    with open('users.json', 'r', encoding='utf-8') as f:
        users = json.load(f)

    print(f"📦 Обработка {len(users)} пользователей...\n")

    for user_id, user_info in users.items():
        # Пропускаем заблокированных
        if user_info.get('status') != 'active':
            if os.path.exists(f'subs/{user_id}.txt'):
                os.remove(f'subs/{user_id}.txt')
                print(f"❌ {user_id}: удалён (заблокирован)")
            continue

        tariff = user_info.get('plan', 'lite')

        if tariff not in TARIFFS:
            print(f"⚠️ {user_id}: тариф '{tariff}' не найден, использую 'lite'")
            tariff = 'lite'

        tariff_config = TARIFFS[tariff]
        display_name = tariff_config["display_name"]
        description = tariff_config["description"]

        # Дата истечения
        expire_date_str = user_info.get('expire_date')
        if expire_date_str:
            expire_timestamp = int(datetime.strptime(expire_date_str, "%Y-%m-%d").timestamp())
        else:
            expire_timestamp = 0

        # Лимит трафика
        traffic_limit_gb = user_info.get('traffic_limit_gb', tariff_config["default_traffic_gb"])
        total_bytes = traffic_limit_gb * 1073741824

        try:
            # Собираем все ключи из папки
            print(f"🔑 {user_id} ({tariff}):")
            keys = load_all_keys(tariff)

            # Собираем подписку
            subscription = build_subscription(keys, expire_timestamp, total_bytes, display_name, description)

            # Сохраняем
            with open(f'subs/{user_id}.txt', 'w', encoding='utf-8') as f:
                f.write(subscription)

            print(f"✅ {user_id}: {display_name}, ключей: {len(keys)}, истекает: {expire_date_str or 'никогда'}\n")
        except Exception as e:
            print(f"❌ {user_id}: {e}\n")


if __name__ == "__main__":
    main()