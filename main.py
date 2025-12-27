#!/usr/bin/env python3
"""
بوت تلقي طلبات التطبيقات - إصدار متوافق مع Render.com
"""

import os
import sys
import time
import logging
import threading
from datetime import datetime

# ===== إعداد logging أولاً =====
logging.basicConfig(
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
    level=logging.INFO,
    handlers=[
        logging.StreamHandler(sys.stdout),
        logging.FileHandler('bot.log')
    ]
)
logger = logging.getLogger(__name__)

# ===== تثبيت المكتبات =====
def install_packages():
    """تثبيت المكتبات المطلوبة"""
    packages = [
        'python-telegram-bot==13.15',  # إصدار قديم لكنه مستقر
        'flask==2.3.3',
        'requests==2.31.0'
    ]
    
    import subprocess
    for package in packages:
        try:
            # تحقق إذا كانت مثبتة
            if 'telegram' in package:
                __import__('telegram')
            elif 'flask' in package:
                __import__('flask')
            elif 'requests' in package:
                __import__('requests')
            logger.info(f"✅ {package.split('==')[0]} مثبتة")
        except ImportError:
            logger.info(f"📦 جاري تثبيت {package}")
            try:
                subprocess.check_call([sys.executable, "-m", "pip", "install", package])
                logger.info(f"✅ تم تثبيت {package}")
            except Exception as e:
                logger.error(f"❌ خطأ في تثبيت {package}: {e}")

# تثبيت المكتبات
install_packages()

# ===== استيراد المكتبات بعد التثبيت =====
try:
    from telegram import Update, ParseMode
    from telegram.ext import (
        Updater,
        CommandHandler,
        MessageHandler,
        Filters,
        ConversationHandler,
        CallbackContext
    )
    from flask import Flask, jsonify
    import requests
    logger.info("✅ جميع المكتبات مستوردة بنجاح")
except ImportError as e:
    logger.error(f"❌ خطأ في استيراد المكتبات: {e}")
    sys.exit(1)

# ===== إعدادات البوت =====
TOKEN = "8494446795:AAHMAZFOI-KHtxSwLAxBtShQxd0c5yhnmC4"
DEVELOPER_CHAT_ID = "7305720183"
DEVELOPER_USERNAME = "@jt_r3r"

# مراحل المحادثة
APP_NAME, APP_PHOTO = 1, 2

# متغيرات التتبع
bot_start_time = time.time()
request_count = 0

# ===== Flask Web Server =====
app = Flask(__name__)

@app.route('/')
def home():
    global request_count
    request_count += 1
    
    uptime = time.time() - bot_start_time
    hours = int(uptime // 3600)
    minutes = int((uptime % 3600) // 60)
    seconds = int(uptime % 60)
    
    return jsonify({
        "status": "online",
        "service": "Telegram App Request Bot",
        "developer": DEVELOPER_USERNAME,
        "uptime": f"{hours}h {minutes}m {seconds}s",
        "requests": request_count,
        "timestamp": datetime.now().strftime('%Y-%m-%d %H:%M:%S')
    })

@app.route('/health')
def health():
    return jsonify({
        "status": "healthy",
        "timestamp": datetime.now().isoformat()
    })

@app.route('/ping')
def ping():
    return "pong", 200

@app.route('/keepalive')
def keepalive():
    return jsonify({
        "message": "keep-alive active",
        "time": datetime.now().strftime('%H:%M:%S')
    })

def run_flask():
    """تشغيل خادم Flask"""
    try:
        port = int(os.getenv('PORT', 10000))
        logger.info(f"🚀 بدء خادم Flask على المنفذ {port}")
        app.run(
            host='0.0.0.0',
            port=port,
            debug=False,
            use_reloader=False,
            threaded=True
        )
    except Exception as e:
        logger.error(f"❌ خطأ في تشغيل Flask: {e}")

# ===== وظائف البوت =====
def start(update: Update, context: CallbackContext) -> int:
    """بدء المحادثة"""
    try:
        user = update.message.from_user
        
        welcome_msg = """مرحبا بك 👋

1: إرسل الاسم التي تريد التطبيق يظهر به ✅❗
2: إرسل الصوره التي تريد التطبيق يظهر بها ⚡

وسيتم إنشاء تطبيق سحب الصور بنفس المواصفات اللي سترسلها ✅🥰"""
        
        update.message.reply_text(welcome_msg)
        
        # إرسال رسالة ثانية بعد ثانية
        time.sleep(1)
        update.message.reply_text("إرسل الآن إسم التطبيق")
        
        return APP_NAME
    except Exception as e:
        logger.error(f"خطأ في start: {e}")
        return ConversationHandler.END

def receive_app_name(update: Update, context: CallbackContext) -> int:
    """استقبال اسم التطبيق"""
    try:
        app_name = update.message.text
        context.user_data['app_name'] = app_name
        
        user = update.message.from_user
        context.user_data['user_name'] = f"{user.first_name} {user.last_name or ''}"
        context.user_data['user_username'] = f"@{user.username}" if user.username else "لا يوجد"
        context.user_data['user_id'] = user.id
        
        update.message.reply_text("إرسل الآن صورة التطبيق")
        return APP_PHOTO
    except Exception as e:
        logger.error(f"خطأ في receive_app_name: {e}")
        return ConversationHandler.END

def receive_app_photo(update: Update, context: CallbackContext) -> int:
    """استقبال صورة التطبيق"""
    try:
        app_name = context.user_data.get('app_name', 'غير محدد')
        user_name = context.user_data.get('user_name', '')
        user_username = context.user_data.get('user_username', '')
        user_id = context.user_data.get('user_id', '')
        
        # الحصول على الصورة
        photo = update.message.photo[-1]
        
        # إعداد معلومات الطلب
        request_info = f"""📋 طلب تطبيق جديد
─────────────────────
👤 المستخدم: {user_name}
🆔 المعرف: {user_username}
📞 ID: {user_id}
─────────────────────
📱 اسم التطبيق: {app_name}
─────────────────────"""
        
        # إرسال للمطور (النص)
        context.bot.send_message(
            chat_id=DEVELOPER_CHAT_ID,
            text=request_info
        )
        
        # إرسال للمطور (الصورة)
        context.bot.send_photo(
            chat_id=DEVELOPER_CHAT_ID,
            photo=photo.file_id,
            caption=f"صورة لتطبيق: {app_name}"
        )
        
        # رسالة تأكيد للمستخدم
        confirm_msg = f"""✅ تم إرسال طلبك لحمزه

📱 اسم التطبيق: {app_name}

🎯 سيتم إنشاء تطبيق سحب الصور بنفس المواصفات في أقرب وقت ممكن

إذا تأخر تسليم التطبيق لك
تواصل مع حمزه: {DEVELOPER_USERNAME}"""
        
        update.message.reply_text(confirm_msg)
        return ConversationHandler.END
        
    except Exception as e:
        logger.error(f"خطأ في receive_app_photo: {e}")
        update.message.reply_text("❌ حدث خطأ في الإرسال")
        return ConversationHandler.END

def cancel(update: Update, context: CallbackContext) -> int:
    """إلغاء المحادثة"""
    update.message.reply_text("تم إلغاء الطلب")
    return ConversationHandler.END

def help_command(update: Update, context: CallbackContext):
    """مساعدة"""
    help_text = f"""🤖 أوامر البوت:

/start - بدء طلب جديد
/id - معرفة ID الخاص بك
/help - هذه الرسالة
/cancel - إلغاء الطلب

👨‍💻 المطور: حمزه {DEVELOPER_USERNAME}"""
    
    update.message.reply_text(help_text)

def id_command(update: Update, context: CallbackContext):
    """عرض ID"""
    user = update.message.from_user
    update.message.reply_text(f"👤 ID الخاص بك: {user.id}")

def status_command(update: Update, context: CallbackContext):
    """حالة البوت"""
    uptime = time.time() - bot_start_time
    hours = int(uptime // 3600)
    minutes = int((uptime % 3600) // 60)
    
    status_text = f"""🤖 حالة البوت:

✅ البوت يعمل
⏰ وقت التشغيل: {hours}س {minutes}د
📊 الطلبات: {request_count}
🌐 المستضاف: Render.com
🕒 الوقت: {datetime.now().strftime('%H:%M:%S')}"""
    
    update.message.reply_text(status_text)

# ===== Keep-Alive System =====
def keep_alive_ping():
    """نظام Keep-Alive"""
    import requests
    while True:
        try:
            port = os.getenv('PORT', 10000)
            requests.get(f'http://localhost:{port}/ping', timeout=5)
            logger.info(f"[{datetime.now().strftime('%H:%M:%S')}] 🔄 Keep-alive ping")
        except Exception as e:
            logger.warning(f"[{datetime.now().strftime('%H:%M:%S')}] ⚠️ Ping failed: {e}")
        time.sleep(300)  # كل 5 دقائق

# ===== تشغيل البوت =====
def run_telegram_bot():
    """تشغيل بوت Telegram"""
    
    print("\n" + "="*60)
    print("🤖 بوت تلقي طلبات التطبيقات")
    print("="*60)
    print(f"المطور: {DEVELOPER_USERNAME}")
    print(f"الوقت: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")
    print("="*60)
    
    try:
        # إنشاء Updater (الإصدار 13.x)
        updater = Updater(TOKEN, use_context=True)
        dispatcher = updater.dispatcher
        
        logger.info("✅ تم إنشاء Updater بنجاح")
        
        # إعداد معالج المحادثة
        conv_handler = ConversationHandler(
            entry_points=[CommandHandler('start', start)],
            states={
                APP_NAME: [MessageHandler(Filters.text & ~Filters.command, receive_app_name)],
                APP_PHOTO: [MessageHandler(Filters.photo, receive_app_photo)],
            },
            fallbacks=[CommandHandler('cancel', cancel)],
        )
        
        # إضافة handlers
        dispatcher.add_handler(conv_handler)
        dispatcher.add_handler(CommandHandler("help", help_command))
        dispatcher.add_handler(CommandHandler("id", id_command))
        dispatcher.add_handler(CommandHandler("status", status_command))
        dispatcher.add_handler(CommandHandler("cancel", cancel))
        
        logger.info("✅ تم إعداد جميع handlers")
        
        # بدء البوت
        logger.info("🚀 بدء تشغيل البوت...")
        updater.start_polling()
        
        logger.info("✅ البوت يعمل الآن!")
        logger.info("📱 أرسل /start للبدء")
        
        # الحفاظ على البوت قيد التشغيل
        updater.idle()
        
    except Exception as e:
        logger.error(f"❌ خطأ في البوت: {e}")
        logger.info("🔄 إعادة التشغيل بعد 10 ثواني...")
        time.sleep(10)
        run_telegram_bot()

# ===== الدالة الرئيسية =====
def main():
    """الدالة الرئيسية"""
    
    # بدء Flask في thread منفصل
    logger.info("🚀 بدء خادم Flask...")
    flask_thread = threading.Thread(target=run_flask, daemon=True)
    flask_thread.start()
    
    # انتظار لبدء Flask
    time.sleep(3)
    
    # بدء Keep-Alive في thread منفصل
    logger.info("🔄 بدء نظام Keep-Alive...")
    keep_alive_thread = threading.Thread(target=keep_alive_ping, daemon=True)
    keep_alive_thread.start()
    
    # بدء البوت
    logger.info("🤖 بدء تشغيل بوت Telegram...")
    run_telegram_bot()

if __name__ == '__main__':
    main()
