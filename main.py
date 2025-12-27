#!/usr/bin/env python3
"""
بوت تلقي طلبات التطبيقات - إصدار مضمون
"""

import os
import sys
import time
import logging
import threading
from datetime import datetime
import asyncio

# ===== إعداد LOGGING =====
logging.basicConfig(
    format='%(asctime)s - %(levelname)s - %(message)s',
    level=logging.INFO,
    handlers=[
        logging.StreamHandler(sys.stdout),
        logging.FileHandler('bot.log')
    ]
)
logger = logging.getLogger(__name__)

print("\n" + "="*50)
print("🤖 BOT STARTING...")
print("="*50)

# ===== تثبيت المكتبات إذا لم تكن موجودة =====
try:
    from telegram import Update
    from telegram.ext import Application, CommandHandler, MessageHandler, filters, ConversationHandler, CallbackContext
    from flask import Flask, jsonify
    import requests
    print("✅ جميع المكتبات مثبتة")
except ImportError:
    print("📦 جاري تثبيت المكتبات...")
    import subprocess
    subprocess.check_call([sys.executable, "-m", "pip", "install", "python-telegram-bot==20.7", "flask==2.3.3", "requests==2.31.0"])
    from telegram import Update
    from telegram.ext import Application, CommandHandler, MessageHandler, filters, ConversationHandler, CallbackContext
    from flask import Flask, jsonify
    import requests
    print("✅ تم تثبيت المكتبات")

# ===== إعدادات البوت =====
BOT_TOKEN = "8494446795:AAHMAZFOI-KHtxSwLAxBtShQxd0c5yhnmC4"
DEVELOPER_ID = "7305720183"
DEVELOPER_USERNAME = "@jt_r3r"

# ===== مراحل المحادثة =====
APP_NAME, APP_PHOTO = 1, 2

# ===== متغيرات التتبع =====
bot_start_time = time.time()
request_count = 0

# ===== Flask App =====
app = Flask(__name__)

@app.route('/')
def home():
    global request_count
    request_count += 1
    
    uptime = int(time.time() - bot_start_time)
    hours = uptime // 3600
    minutes = (uptime % 3600) // 60
    
    return jsonify({
        "status": "online",
        "service": "Telegram App Bot",
        "developer": DEVELOPER_USERNAME,
        "uptime": f"{hours}h {minutes}m",
        "requests": request_count,
        "time": datetime.now().strftime("%H:%M:%S")
    })

@app.route('/health')
def health():
    return jsonify({"status": "healthy", "bot": "running"})

@app.route('/ping')
def ping():
    return "pong", 200

@app.route('/keepalive')
def keepalive():
    return jsonify({
        "message": "active",
        "timestamp": datetime.now().isoformat()
    })

def run_flask():
    """تشغيل خادم Flask"""
    try:
        port = int(os.environ.get('PORT', 10000))
        print(f"🚀 Flask running on port {port}")
        app.run(host='0.0.0.0', port=port, debug=False, use_reloader=False)
    except Exception as e:
        print(f"❌ Flask error: {e}")

# ===== وظائف البوت =====
async def start(update: Update, context: CallbackContext) -> int:
    """بدء المحادثة"""
    try:
        user = update.effective_user
        await update.message.reply_text(
            f"مرحبا {user.first_name}! 👋\n\n"
            "أرسل اسم التطبيق الذي تريده..."
        )
        return APP_NAME
    except Exception as e:
        print(f"Error in start: {e}")
        return ConversationHandler.END

async def get_app_name(update: Update, context: CallbackContext) -> int:
    """استقبال اسم التطبيق"""
    try:
        app_name = update.message.text
        context.user_data['app_name'] = app_name
        await update.message.reply_text(f"✅ تم حفظ الاسم: {app_name}\n\nالآن أرسل صورة التطبيق...")
        return APP_PHOTO
    except Exception as e:
        print(f"Error in get_app_name: {e}")
        await update.message.reply_text("❌ حدث خطأ، حاول مرة أخرى")
        return ConversationHandler.END

async def get_app_photo(update: Update, context: CallbackContext) -> int:
    """استقبال صورة التطبيق"""
    try:
        app_name = context.user_data.get('app_name', 'غير معروف')
        user = update.effective_user
        
        # الحصول على الصورة
        photo = update.message.photo[-1]
        photo_file = await photo.get_file()
        
        # إرسال للمطور
        await context.bot.send_message(
            DEVELOPER_ID,
            f"📋 طلب جديد\n👤 المستخدم: {user.first_name}\n🆔 المعرف: @{user.username if user.username else 'لا يوجد'}\n📱 التطبيق: {app_name}"
        )
        
        await context.bot.send_photo(
            DEVELOPER_ID,
            photo=photo_file.file_id,
            caption=f"صورة التطبيق: {app_name}"
        )
        
        # تأكيد للمستخدم
        await update.message.reply_text(
            f"✅ تم إرسال طلبك للمطور {DEVELOPER_USERNAME}\n\n"
            f"📱 اسم التطبيق: {app_name}\n"
            "⏰ سيتم الإنشاء قريباً\n\n"
            f"📞 للتواصل: {DEVELOPER_USERNAME}"
        )
        
        return ConversationHandler.END
    except Exception as e:
        print(f"Error in get_app_photo: {e}")
        await update.message.reply_text("❌ حدث خطأ في إرسال الطلب")
        return ConversationHandler.END

async def cancel(update: Update, context: CallbackContext) -> int:
    """إلغاء المحادثة"""
    await update.message.reply_text("تم إلغاء الطلب")
    return ConversationHandler.END

async def help_cmd(update: Update, context: CallbackContext):
    """مساعدة"""
    await update.message.reply_text(
        f"🤖 أوامر البوت:\n\n"
        "/start - بدء طلب جديد\n"
        "/help - المساعدة\n"
        "/status - حالة البوت\n"
        "/id - معرفة ID الخاص بك\n"
        "/cancel - إلغاء الطلب\n\n"
        f"👨‍💻 المطور: {DEVELOPER_USERNAME}"
    )

async def status_cmd(update: Update, context: CallbackContext):
    """حالة البوت"""
    uptime = int(time.time() - bot_start_time)
    hours = uptime // 3600
    minutes = (uptime % 3600) // 60
    
    await update.message.reply_text(
        f"📊 حالة البوت:\n\n"
        f"✅ الحالة: نشط\n"
        f"⏰ التشغيل: {hours}س {minutes}د\n"
        f"📈 الطلبات: {request_count}\n"
        f"🕒 الوقت: {datetime.now().strftime('%H:%M:%S')}\n"
        f"🌐 المضيف: Render.com"
    )

async def id_cmd(update: Update, context: CallbackContext):
    """عرض ID المستخدم"""
    user = update.effective_user
    await update.message.reply_text(f"🆔 ID الخاص بك: {user.id}")

# ===== Keep Alive System =====
def keep_alive():
    """الحفاظ على البوت نشط"""
    import requests
    while True:
        try:
            port = os.environ.get('PORT', 10000)
            response = requests.get(f'http://localhost:{port}/ping', timeout=5)
            if response.status_code == 200:
                print(f"[{datetime.now().strftime('%H:%M:%S')}] 🔄 Keep-alive ping")
        except:
            print(f"[{datetime.now().strftime('%H:%M:%S')}] ⚠️ Keep-alive failed")
        time.sleep(300)  # كل 5 دقائق

# ===== تشغيل البوت =====
async def main():
    """الدالة الرئيسية"""
    print("🤖 Creating bot application...")
    
    # إنشاء التطبيق - بدون Updater
    application = Application.builder().token(BOT_TOKEN).build()
    print("✅ Application created successfully")
    
    # إعداد معالج المحادثة
    conv_handler = ConversationHandler(
        entry_points=[CommandHandler('start', start)],
        states={
            APP_NAME: [MessageHandler(filters.TEXT & ~filters.COMMAND, get_app_name)],
            APP_PHOTO: [MessageHandler(filters.PHOTO, get_app_photo)],
        },
        fallbacks=[CommandHandler('cancel', cancel)],
    )
    
    # إضافة handlers
    application.add_handler(conv_handler)
    application.add_handler(CommandHandler("help", help_cmd))
    application.add_handler(CommandHandler("status", status_cmd))
    application.add_handler(CommandHandler("id", id_cmd))
    application.add_handler(CommandHandler("cancel", cancel))
    
    print("✅ Handlers added successfully")
    print("🚀 Starting bot...")
    
    # بدء البوت
    await application.initialize()
    await application.start()
    await application.updater.start_polling()
    
    print("✅ Bot is running!")
    print("📱 Send /start to your bot")
    
    # البقاء نشطاً
    while True:
        await asyncio.sleep(3600)

# ===== تشغيل كل شيء =====
def run_all():
    """تشغيل كل المكونات"""
    
    # بدء Flask في thread
    print("🚀 Starting Flask server...")
    flask_thread = threading.Thread(target=run_flask, daemon=True)
    flask_thread.start()
    time.sleep(3)
    
    # بدء Keep Alive في thread
    print("🔄 Starting keep-alive system...")
    keep_alive_thread = threading.Thread(target=keep_alive, daemon=True)
    keep_alive_thread.start()
    
    # بدء البوت
    print("🤖 Starting Telegram bot...")
    asyncio.run(main())

if __name__ == '__main__':
    try:
        run_all()
    except KeyboardInterrupt:
        print("\n🛑 Bot stopped by user")
    except Exception as e:
        print(f"❌ Unexpected error: {e}")
        print("🔄 Restarting in 10 seconds...")
        time.sleep(10)
        run_all()
