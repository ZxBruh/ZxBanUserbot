import time
import json
import os
import io
import sys
import subprocess
from contextlib import redirect_stdout
from telethon import TelegramClient, events

# --- НАСТРОЙКИ ---
# Получи их на my.telegram.org
API_ID = 2040
API_HASH = 'b18441a1ff607e10a989891a5462e627'
CONFIG_FILE = 'config.json'

# --- ФУНКЦИИ КОНФИГА ---
def load_config():
    if not os.path.exists(CONFIG_FILE):
        default = {
            "info_template": "**🛡️ Юзербот Zxban**\n---\n**Статус:** Работает\n**Платформа:** Termux",
            "ping_template": "**🏓 Понг!**\nЗадержка: `{time}` мс",
            "help_template": "**📜 Список команд:**\n`!инфо` — статус бота\n`!пинг` — задержка\n`!хелп` — это меню\n`!кфг` — настройка\n`!е` — python код\n`!терминал` — команды консоли\n`!апдейт` — обновить бота",
            "prefix": "!"
        }
        with open(CONFIG_FILE, "w", encoding="utf-8") as f:
            json.dump(default, f, ensure_ascii=False, indent=4)
    with open(CONFIG_FILE, "r", encoding="utf-8") as f:
        return json.load(f)

def save_config(config):
    with open(CONFIG_FILE, "w", encoding="utf-8") as f:
        json.dump(config, f, ensure_ascii=False, indent=4)

# Инициализация
config_data = load_config()
PREFIX = config_data.get("prefix", "!")
client = TelegramClient('zxban_session', API_ID, API_HASH)

print(f"--- Юзербот Zxban запущен! Префикс: {PREFIX} ---")

# --- КОМАНДЫ ---

# Команда !инфо
@client.on(events.NewMessage(outgoing=True, pattern=f'\\{PREFIX}инфо'))
async def info(event):
    cfg = load_config()
    await event.edit(cfg["info_template"])

# Команда !хелп
@client.on(events.NewMessage(outgoing=True, pattern=f'\\{PREFIX}хелп'))
async def help_cmd(event):
    cfg = load_config()
    await event.edit(cfg["help_template"])

# Команда !пинг
@client.on(events.NewMessage(outgoing=True, pattern=f'\\{PREFIX}пинг'))
async def ping(event):
    cfg = load_config()
    start = time.time()
    await event.edit("🚀 Проверяю...")
    end = time.time()
    ms = round((end - start) * 1000)
    text = cfg["ping_template"].replace("{time}", str(ms))
    await event.edit(text)

# Команда !кфг
@client.on(events.NewMessage(outgoing=True, pattern=f'\\{PREFIX}кфг'))
async def config_cmd(event):
    cfg = load_config()
    args = event.text.split(maxsplit=2)
    if len(args) < 3:
        return await event.edit(f"**Формат:** `{PREFIX}кфг [пинг/инфо/хелп] [текст]`")

    key = args[1].lower()
    value = args[2]

    if key in ["пинг", "инфо", "хелп"]:
        cfg[f"{key}_template"] = value
        save_config(cfg)
        await event.edit(f"✅ Настройка `{key}` обновлена!")
    else:
        await event.edit("❌ Используй: пинг, инфо, хелп")

# Команда !е (Exec)
@client.on(events.NewMessage(outgoing=True, pattern=f'\\{PREFIX}е'))
async def execute_cmd(event):
    code = event.text.split(maxsplit=1)
    if len(code) < 2: return await event.edit("Введите код!")
    await event.edit("<b>Выполняю...</b>", parse_mode='html')
    f = io.StringIO()
    try:
        with redirect_stdout(f):
            exec(code[1])
        out = f.getvalue()
        await event.edit(f"**Код:**\n`{code[1]}`\n\n**Результат:**\n`{out}`")
    except Exception as e:
        await event.edit(f"**Ошибка:**\n`{e}`")

# Команда !терминал
@client.on(events.NewMessage(outgoing=True, pattern=f'\\{PREFIX}терминал'))
async def terminal_cmd(event):
    cmd = event.text.split(maxsplit=1)
    if len(cmd) < 2: return await event.edit("Введите команду!")
    await event.edit(f"<code>Запуск: {cmd[1]}</code>", parse_mode='html')
    process = subprocess.Popen(cmd[1], shell=True, stdout=subprocess.PIPE, stderr=subprocess.PIPE, text=True)
    stdout, stderr = process.communicate()
    await event.edit(f"**Терминал:**\n`{stdout or stderr}`")

# Команда !апдейт
@client.on(events.NewMessage(outgoing=True, pattern=f'\\{PREFIX}апдейт'))
async def update_cmd(event):
    await event.edit("🔄 **Обновление с GitHub...**")
    try:
        # Выполняем git pull
        process = subprocess.Popen(["git", "pull"], stdout=subprocess.PIPE, stderr=subprocess.PIPE, text=True)
        stdout, stderr = process.communicate()
        
        if "Already up to date" in stdout:
            return await event.edit("✅ **У вас последняя версия!**")
        
        await event.edit(f"✅ **Обновлено! Рестарт...**\n`{stdout}`")
        # Перезапуск скрипта
        os.execl(sys.executable, sys.executable, *sys.argv)
    except Exception as e:
        await event.edit(f"❌ **Ошибка:** `{e}`")

async def main():
    await client.start()
    await client.run_until_disconnected()

if __name__ == '__main__':
    client.loop.run_until_complete(main())
