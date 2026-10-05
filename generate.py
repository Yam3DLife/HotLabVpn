import json
import base64
import os
from datetime import datetime

# ===== ТАРИФЫ =====
TARIFFS = {
    "trial": {
        "display_name": "TRIAL 🔥",
        "default_days": 3,
        "default_traffic_gb": 5
    },
    "lite": {
        "display_name": "LITE ⚡",
        "default_days": 30,
        "default_traffic_gb": 50
    },
    "vip": {
        "display_name": "VIP 👑",
        "default_days": 30,
        "default_traffic_gb": 0
    }
}


def load_all_keys(tariff):
    """
    Загружает ВСЕ .json файлы из папки keys/{tariff}/
    Каждый файл = один ключ.
    Возвращает массив ключей.
    """
    folder = f"keys/{tariff}"
    print(f"  🔍 Ищу папку: {folder}")

    if not os.path.exists(folder):
        print(f"  ❌ Папка {folder} НЕ НАЙДЕНА")
        return []

    files = sorted(os.listdir(folder))
    print(f"  📂 Файлов в папке: {len(files)}")

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

    print(f"  🔑 Итого ключей: {len(all_keys)}")
    return all_keys


def build_subscription(keys, expire_timestamp, total_bytes, display_name):
    """
    Собирает подписку:
    - шапка (название, срок, лимит)
    - JSON-массив со всеми ключами
    - кодирует всё в base64
    """
    headers = f"""#profile-title: HotVPN {display_name}
#profile-update-interval: 5
#support-url: https://t.me/Wd_Life
#subscription-userinfo: upload=0; download=0; total={total_bytes}; expire={expire_timestamp}
#sub-expire: true

"""

    # JSON-массив со всеми ключами
    json_part = json.dumps(keys, indent=2, ensure_ascii=False)

    # Склеиваем: шапка + JSON
    combined = headers + json_part

    # Кодируем в base64
    encoded = base64.b64encode(combined.encode('utf-8')).decode('utf-8')
    return encoded


def main():
    print("=" * 50)
    print("=== СТАРТ ГЕНЕРАЦИИ ПОДПИСОК ===")
    print("=" * 50)

    # Создаём папку subs
    os.makedirs('subs', exist_ok=True)

    # Проверяем users.json
    if not os.path.exists('users.json'):
        print("❌ Файл users.json не найден!")
        return

    # Читаем базу клиентов
    with open('users.json', 'r', encoding='utf-8') as f:
        users = json.load(f)

    print(f"\n📦 Пользователей в базе: {len(users)}\n")

    for user_id, user_info in users.items():
        print(f"--- Обработка: {user_id} ---")

        # Если пользователь заблокирован — удаляем его файл
        if user_info.get('status') != 'active':
            if os.path.exists(f'subs/{user_id}.txt'):
                os.remove(f'subs/{user_id}.txt')
            print(f"❌ {user_id}: заблокирован, файл удалён\n")
            continue

        # Определяем тариф
        tariff = user_info.get('plan', 'lite')
        if tariff not in TARIFFS:
            print(f"⚠️ {user_id}: тариф '{tariff}' не найден, использую 'lite'")
            tariff = 'lite'

        tariff_config = TARIFFS[tariff]
        display_name = tariff_config["display_name"]

        # Дата истечения
        expire_date_str = user_info.get('expire_date')
        if expire_date_str:
            try:
                expire_timestamp = int(
                    datetime.strptime(expire_date_str, "%Y-%m-%d").timestamp()
                )
            except ValueError:
                print(f"⚠️ {user_id}: неверный формат даты '{expire_date_str}'")
                expire_timestamp = 0
        else:
            expire_timestamp = 0

        # Лимит трафика
        traffic_limit_gb = user_info.get(
            'traffic_limit_gb',
            tariff_config["default_traffic_gb"]
        )
        total_bytes = traffic_limit_gb * 1073741824

        # Загружаем ключи
        keys = load_all_keys(tariff)

        if not keys:
            print(f"❌ {user_id}: в папке keys/{tariff}/ нет ключей, пропущен\n")
            continue

        # Собираем подписку
        try:
            subscription = build_subscription(
                keys,
                expire_timestamp,
                total_bytes,
                display_name
            )

            output_path = f'subs/{user_id}.txt'
            with open(output_path, 'w', encoding='utf-8') as f:
                f.write(subscription)

            print(
                f"✅ {user_id}: {display_name} | "
                f"ключей: {len(keys)} | "
                f"истекает: {expire_date_str or 'никогда'} | "
                f"лимит: {traffic_limit_gb} GB\n"
            )

        except Exception as e:
            print(f"❌ {user_id}: ошибка сборки — {e}\n")

    print("=" * 50)
    print("=== ГОТОВО ===")
    print("=" * 50)


if __name__ == "__main__":
    main()
