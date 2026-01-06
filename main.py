import time, json, os, sys, subprocess, importlib, random, string
try:
    import requests
except ImportError:
    subprocess.check_call([sys.executable, "-m", "pip", "install", "requests"])
    import requests

from telethon import TelegramClient, events, Button
from telethon.tl.types import MessageEntityCustomEmoji

# --- КОНФИГУРАЦИЯ ---
API_ID = 2040
API_HASH = 'b18441a1ff607e10a989891a5462e627'
CONFIG_FILE = 'config.json'
MODULES_DIR = 'modules'

if not os.path.exists(MODULES_DIR): os.makedirs(MODULES_DIR)

def load_config():
    rand_suffix = ''.join(random.choices(string.ascii_lowercase + string.digits, k=8))
    default = {
        "prefix": "!",
        "bot_token": "",
        "bot_username": f"zxban_{rand_suffix}_bot",
        "info_template": "🛡️ **Zxban Status: Online**",
        "ping_template": "⚡ **Pong!** `{time}` ms"
    }
    if not os.path.exists(CONFIG_FILE):
        with open(CONFIG_FILE, "w", encoding="utf-8") as f:
            json.dump(default, f, ensure_ascii=False, indent=4)
        return default
    with open(CONFIG_FILE, "r", encoding="utf-8") as f:
        current = json.load(f)
    # Авто-добавление недостающих ключей
    updated = False
    for key, value in default.items():
        if key not in current:
            current[key] = value
            updated = True
    if updated:
        with open(CONFIG_FILE, "w", encoding="utf-8") as f:
            json.dump(current, f, ensure_ascii=False, indent=4)
    return current

cfg = load_config()
client = TelegramClient('zxban_session', API_ID, API_HASH)
bot_client = None

# Запуск бота-помощника для кнопок
if cfg.get("bot_token"):
    try:
        bot_client = TelegramClient('zxban_bot', API_ID, API_HASH).start(bot_token=cfg["bot_token"])
    except Exception as e:
        print(f"Ошибка запуска бота: {e}")

loaded_modules = {}

def load_module(file_path):
    module_name = os.path.basename(file_path)[:-3]
    try:
        spec = importlib.util.spec_from_file_location(module_name, file_path)
        mod = importlib.util.module_from_spec(spec)
        spec.loader.exec_module(mod)
        loaded_modules[module_name] = mod
        if hasattr(mod, "init"): mod.init(client)
        return True
    except Exception: return False

@client.on(events.NewMessage(outgoing=True))
async def main_handler(event):
    global cfg
    prefix = cfg.get("prefix", "!")
    text = event.raw_text
    if not text.startswith(prefix): return
    args = text[len(prefix):].split()
    if not args: return
    cmd = args[0].lower()

    # --- КОМАНДА ХЕЛП ---
    if cmd == "хелп" or cmd == "help":
        help_text = (
            "📖 **Меню команд Zxban:**\n\n"
            f"• `{prefix}инфо` — Статус бота\n"
            f"• `{prefix}пинг` — Проверка скорости\n"
            f"• `{prefix}кфг` — Настройки (кнопки)\n"
            f"• `{prefix}загрузить` — Установка модуля (.py)\n"
            f"• `{prefix}апдейт` — Обновление из GitHub"
        )
        await event.edit(help_text)

    # --- КОМАНДА ИНФО ---
    elif cmd == "инфо":
        await event.edit(f"{cfg['info_template']}\n**Modules:** {len(loaded_modules)}")

    # --- КОМАНДА ПИНГ ---
    elif cmd == "пинг":
        start = time.time()
        await event.edit("🚀")
        ms = round((time.time() - start) * 1000)
        await event.edit(f"⚡ {cfg['ping_template'].replace('{time}', str(ms))}", 
                         formatting_entities=[MessageEntityCustomEmoji(offset=0, length=2, document_id=5447103212130101411)])

    # --- КОМАНДА КФГ (КНОПКИ ЧЕРЕЗ БОТА) ---
    elif cmd == "кфг":
        if not bot_client:
            await event.edit(f"⚠️ **Кнопки не работают!**\n1. Напиши @BotFather\n2. Создай бота: `@{cfg['bot_username']}`\n3. Введи: `!set_token ТОКЕН`")
        else:
            await event.delete() # Удаляем сообщение юзера
            # Отправляем сообщение с кнопками ОТ ИМЕНИ БОТА
            await bot_client.send_message(event.chat_id, "⚙️ **Настройки Zxban**\nВыберите категорию:", buttons=[
                [Button.inline("📦 Встроенные", data="mods_int")],
                [Button.inline("🌐 Внешние", data="mods_ext")]
            ])

    # --- УСТАНОВКА ТОКЕНА ---
    elif cmd == "set_token":
        if len(args) > 1:
            cfg['bot_token'] = args[1]
            with open(CONFIG_FILE, "w", encoding="utf-8") as f:
                json.dump(cfg, f, ensure_ascii=False, indent=4)
            await event.edit("✅ Токен привязан! Рестарт...")
            os.execl(sys.executable, sys.executable, *sys.argv)

    # --- АПДЕЙТ ---
    elif cmd == "апдейт":
        await event.edit("🔄 **Обновление...**")
        subprocess.Popen(["git", "pull"], stdout=subprocess.PIPE).communicate()
        os.execl(sys.executable, sys.executable, *sys.argv)

# --- ОБРАБОТКА НАЖАТИЙ (ЧЕРЕЗ БОТА) ---
if bot_client:
    @bot_client.on(events.CallbackQuery)
    async def callback_handler(event):
        data = event.data
        if data == b"mods_int":
            await event.edit("🛠 **Встроенные модули:**\n• Core\n• Loader\n• Update", buttons=[Button.inline("⬅️ Назад", data="back")])
        elif data == b"mods_ext":
            mods = "\n".join([f"• {m}" for m in loaded_modules.keys()]) or "Пусто"
            await event.edit(f"📂 **Внешние модули:**\n{mods}", buttons=[Button.inline("⬅️ Назад", data="back")])
        elif data == b"back":
            await event.edit("⚙️ **Настройки Zxban**", buttons=[
                [Button.inline("📦 Встроенные", data="mods_int")],
                [Button.inline("🌐 Внешние", data="mods_ext")]
            ])

async def main():
    if os.path.exists(MODULES_DIR):
        for file in os.listdir(MODULES_DIR):
            if file.endswith(".py"): load_module(os.path.join(MODULES_DIR, file))
    await client.start()
    print("Zxban запущен!")
    await client.run_until_disconnected()

if __name__ == '__main__':
    client.loop.run_until_complete(main())
