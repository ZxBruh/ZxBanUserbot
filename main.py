import time, json, os, sys, subprocess, importlib, random, string
try:
    import requests
except ImportError:
    subprocess.check_call([sys.executable, "-m", "pip", "install", "requests"])
    import requests

from telethon import TelegramClient, events, Button
from telethon.tl.types import MessageEntityCustomEmoji

# Данные API
API_ID = 2040
API_HASH = 'b18441a1ff607e10a989891a5462e627'
CONFIG_FILE = 'config.json'
MODULES_DIR = 'modules'

if not os.path.exists(MODULES_DIR): os.makedirs(MODULES_DIR)

def load_config():
    if not os.path.exists(CONFIG_FILE):
        # Генерируем случайный юзернейм для подсказки
        rand_suffix = ''.join(random.choices(string.ascii_lowercase + string.digits, k=8))
        default = {
            "prefix": "!",
            "bot_token": "", # Сюда нужно будет вставить токен
            "bot_username": f"zxban_{rand_suffix}",
            "info_template": "🛡️ **Zxban Status**",
            "ping_template": "⚡ **Pong!** `{time}` ms"
        }
        with open(CONFIG_FILE, "w", encoding="utf-8") as f:
            json.dump(default, f, ensure_ascii=False, indent=4)
    with open(CONFIG_FILE, "r", encoding="utf-8") as f:
        return json.load(f)

cfg = load_config()

# Клиент юзербота
client = TelegramClient('zxban_session', API_ID, API_HASH)
# Клиент вспомогательного бота (запустится только если есть токен)
bot_client = None

if cfg.get("bot_token"):
    bot_client = TelegramClient('zxban_bot', API_ID, API_HASH).start(bot_token=cfg["bot_token"])

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

    if cmd == "кфг":
        if not cfg.get("bot_token"):
            await event.edit(f"⚠️ **Кнопки не работают!**\nДля работы меню мне нужен Inline-бот.\n\n1. Напиши @BotFather\n2. Создай бота: `/{cfg['bot_username']}`\n3. Получи токен и напиши:\n`!set_token ТВОЙ_ТОКЕН`")
            return
        
        # Если токен есть, используем Inline Query или отправку через бота
        # В режиме юзербота кнопки отправляются через «switch_inline»
        await event.edit(f"⚙️ **Настройки Zxban**\nИспользуйте кнопки ниже:", 
            buttons=[
                [Button.inline("📦 Встроенные", data="mods_int")],
                [Button.inline("🌐 Внешние", data="mods_ext")]
            ])

    elif cmd == "set_token":
        if len(args) > 1:
            cfg['bot_token'] = args[1]
            with open(CONFIG_FILE, "w") as f: json.dump(cfg, f)
            await event.edit("✅ **Токен сохранен! Перезагружаюсь для активации кнопок...**")
            os.execl(sys.executable, sys.executable, *sys.argv)

    elif cmd == "пинг":
        start = time.time()
        await event.edit("🚀")
        ms = round((time.time() - start) * 1000)
        await event.edit(f"⚡ {cfg['ping_template'].replace('{time}', str(ms))}", 
                         formatting_entities=[MessageEntityCustomEmoji(offset=0, length=2, document_id=5447103212130101411)])

    elif cmd == "апдейт":
        await event.edit("🔄 **Обновление...**")
        subprocess.Popen(["git", "pull"], stdout=subprocess.PIPE).communicate()
        os.execl(sys.executable, sys.executable, *sys.argv)

# Обработка нажатий на кнопки (через бот-аккаунт)
if bot_client:
    @bot_client.on(events.CallbackQuery)
    async def callback_handler(event):
        data = event.data.decode()
        if data == "mods_int":
            await event.edit("🛠 **Встроенные модули:**\n• Core\n• Loader\n• Config", buttons=[Button.inline("⬅️ Назад", data="back")])
        elif data == "mods_ext":
            mods = "\n".join([f"• {m}" for m in loaded_modules.keys()]) or "Нет"
            await event.edit(f"📂 **Внешние модули:**\n{mods}", buttons=[Button.inline("⬅️ Назад", data="back")])
        elif data == "back":
            await event.edit("⚙️ **Настройки Zxban**", buttons=[
                [Button.inline("📦 Встроенные", data="mods_int")],
                [Button.inline("🌐 Внешние", data="mods_ext")]
            ])

async def main():
    for file in os.listdir(MODULES_DIR):
        if file.endswith(".py"): load_module(os.path.join(MODULES_DIR, file))
    await client.start()
    print("Zxban запущен!")
    await client.run_until_disconnected()

if __name__ == '__main__':
    client.loop.run_until_complete(main())
