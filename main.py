#!/usr/bin/env python3
"""
بوت تلقي طلبات التطبيقات للمطور حمزه
إصدار نهائي بدون أخطاء
"""

import os
import sys
import time
import logging
import threading
from datetime import datetime

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

# ===== إعدادات البوت =====
BOT_TOKEN = "8494446795:AAHMAZFOI-KHtxSwLAxBtShQxd0c5yhnmC4"
DEVELOPER_ID = "7305720183"
DEVELOPER_USERNAME = "@jt_r3r"

# ===== إعداد Flask أولاً =====
try:
    from flask import Flask, jsonify
    app = Flask(__name__)
    logger.info("✅ Flask مستوردة بنجاح")
except Exception as e:
    logger.error(f"❌ خطأ في استيراد Flask: {e}")
    sys.exit(1)

# ===== استيراد مكتبة Telegram بعد Flask =====
try:
    # إصدار حديث ومستقر
    from telegram import Update
    from telegram.ext import (
        Application,
        CommandHandler,
        MessageHandler,
        filters,
        ConversationHandler,
        CallbackContext
    )
    logger.info("✅ مكتبة Telegram مستوردة بنجاح")
except Exception as e:
    logger.error(f"❌ خطأ في استيراد Telegram: {e}")
    # حاول تثبيت المكتبة تلقائياً
    try:
        import subprocess
        subprocess.check_call([sys.executable, "-m", "pip", "install", "python-telegram-bot==20.7"])
        from telegram import Update
        from telegram.ext import (
            Application,
            CommandHandler,
            MessageHandler,
            filters,
            ConversationHandler,
            CallbackContext
        )
        logger.info("✅ تم تثبيت واستيراد Telegram بنجاح")
    except:
        logger.error("❌ فشل تثبيت Telegram")
        sys.exit(1)

# ===== متغيرات البوت =====
bot_start_time = time.time()
request_count = 0
bot_active = False

# ===== مراحل المحادثة =====
APP_NAME, APP_PHOTO = 1, 2

# ===== Flask Routes =====
@app.route('/')
def home():
    global request_count
    request_count += 1
    
    uptime = int(time.time() - bot_start_time)
    hours = uptime // 3600
    minutes = (uptime % 3600) // 60
    seconds = uptime % 60
    
    return jsonify({
        "status": "online",
        "bot": "running" if bot_active else "starting",
        "uptime": f"{hours}h {minutes}m {seconds}s",
        "requests": request_count,
        "time": datetime.now().strftime("%H:%M:%S"),
        "service": "Telegram Bot",
        "developer": DEVELOPER_USERNAME
    })

@app.route('/health')
def health():
    return jsonify({
        "status": "healthy",
        "bot": "active" if bot_active else "inactive",
        "timestamp": datetime.now().isoformat()
    })

@app.route('/ping')
def ping():
    return "pong", 200

@app.route('/keepalive')
def keepalive():
    return jsonify({
        "message": "alive",
        "time": datetime.now().strftime("%H:%M:%S")
    })

# ===== وظائف البوت =====
async def start_command(update: Update, context: CallbackContext) -> int:
    """بدء محادثة جديدة"""
    try:
        user = update.effective_user
        
        msg = """مرحبا بك 👋

1️⃣ أرسل اسم التطبيق
2️⃣ أرسل صورة التطبيق

سيتم إنشاء تطبيق سحب الصور بنفس المواصفات ✅"""
        
        await update.message.reply_text(msg)
        await update.message.reply_text("📝 أرسل اسم التطبيق الآن:")
        
        return APP_NAME
    except Exception as e:
        logger.error(f"خطأ في start: {e}")
        return ConversationHandler.END

async def get_name(update: Update, context: CallbackContext) -> int:
    """استقبال اسم التطبيق"""
    try:
        app_name = update.message.text
        context.user_data['app_name'] = app_name
        
        user = update.effective_user
        context.user_data['user_name'] = f"{user.first_name} {user.last_name or ''}"
        context.user_data['user_username'] = f"@{user.username}" if user.username else "لا يوجد"
        context.user_data['user_id'] = user.id
        
        await update.message.reply_text("✅ تم حفظ اسم التطبيق")
        await update.message.reply_text("📸 أرسل صورة التطبيق الآن:")
        
        return APP_PHOTO
    except Exception as e:
        logger.error(f"خطأ في get_name: {e}")
        await update.message.reply_text("❌ حدث خطأ، حاول مرة أخرى")
        return ConversationHandler.END

async def get_photo(update: Update, context: CallbackContext) -> int:
    """استقبال صورة التطبيق"""
    try:
        # بيانات التطبيق
        app_name = context.user_data.get('app_name', 'غير محدد')
        user_name = context.user_data.get('user_name', '')
        user_username = context.user_data.get('user_username', '')
        user_id = context.user_data.get('user_id', '')
        
        # الحصول على الصورة
        photo_file = await update.message.photo[-1].get_file()
        
        # إرسال للمطور
        info_msg = f"""📋 طلب جديد
━━━━━━━━━━━━━━
👤 المستخدم: {user_name}
🆔 المعرف: {user_username}
🔢 الرقم: {user_id}
━━━━━━━━━━━━━━
📱 التطبيق: {app_name}
━━━━━━━━━━━━━━"""
        
        await context.bot.send_message(
            chat_id=DEVELOPER_ID,
            text=info_msg
        )
        
        await context.bot.send_photo(
            chat_id=DEVELOPER_ID,
            photo=photo_file.file_id,
            caption=f"صورة التطبيق: {app_name}"
        )
        
        # تأكيد للمستخدم
        confirm_msg = f"""✅ تم إرسال طلبك
━━━━━━━━━━━━━━
📱 التطبيق: {app_name}
━━━━━━━━━━━━━━
👨‍💻 المطور: {DEVELOPER_USERNAME}
⏰ سيتم الإنشاء قريباً
━━━━━━━━━━━━━━
⚠️ إذا تأخر التسليم راسل: {DEVELOPER_USERNAME}"""
        
        await update.message.reply_text(confirm_msg)
        
        return ConversationHandler.END
        
    except Exception as e:
        logger.error(f"خطأ في get_photo: {e}")
        await update.message.reply_text("❌ حدث خطأ في استلام الصورة")
        return ConversationHandler.END

async def cancel_command(update: Update, context: CallbackContext) -> int:
    """إلغاء المحادثة"""
    await update.message.reply_text("تم إلغاء الطلب")
    return ConversationHandler.END

async def help_command(update: Update, context: CallbackContext):
    """عرض المساعدة"""
    help_text = f"""🤖 أوامر البوت:
━━━━━━━━━━━━━━
/start - بدء طلب جديد
/help - المساعدة
/status - حالة البوت
/cancel - إلغاء الطلب
━━━━━━━━━━━━━━
👨‍💻 المطور: {DEVELOPER_USERNAME}"""
    
    await update.message.reply_text(help_text)

async def status_command(update: Update, context: CallbackContext):
    """عرض حالة البوت"""
    uptime = int(time.time() - bot_start_time)
    hours = uptime // 3600
    minutes = (uptime % 3600) // 60
    
    status_text = f"""📊 حالة البوت:
━━━━━━━━━━━━━━
✅ الحالة: نشط
⏰ الوقت: {hours}س {minutes}د
📈 الطلبات: {request_count}
🕒 الساعة: {datetime.now().strftime("%H:%M:%S")}
🌐 المضيف: Render
━━━━━━━━━━━━━━"""
    
    await update.message.reply_text(status_text)

async def id_command(update: Update, context: CallbackContext):
    """عرض ID المستخدم"""
    user = update.effective_user
    await update.message.reply_text(f"🆔 ID الخاص بك: {user.id}")

# ===== Flask Server =====
def run_flask_server():
    """تشغيل خادم Flask"""
    try:
        port = int(os.environ.get('PORT', 10000))
        logger.info(f"🚀 بدء Flask على المنفذ {port}")
        app.run(
            host='0.0.0.0',
            port=port,
            debug=False,
            use_reloader=False
        )
    except Exception as e:
        logger.error(f"❌ خطأ في Flask: {e}")

# ===== Keep Alive =====
def keep_alive():
    """الحفاظ على البوت نشط"""
    import requests
    while True:
        try:
            port = os.environ.get('PORT', 10000)
            requests.get(f'http://localhost:{port}/ping', timeout=5)
            logger.info(f"🔄 Keep-alive: {datetime.now().strftime('%H:%M:%S')}")
        except:
            logger.warning("⚠️ Keep-alive فشل")
        time.sleep(180)  # كل 3 دقائق

# ===== تشغيل البوت =====
def run_bot():
    """تشغيل بوت Telegram"""
    global bot_active
    
    logger.info("🤖 بدء تشغيل البوت...")
    
    try:
        # إنشاء التطبيق
        application = Application.builder().token(BOT_TOKEN).build()
        
        # إعداد المحادثة
        conv_handler = ConversationHandler(
            entry_points=[CommandHandler('start', start_command)],
            states={
                APP_NAME: [MessageHandler(filters.TEXT & ~filters.COMMAND, get_name)],
                APP_PHOTO: [MessageHandler(filters.PHOTO, get_photo)],
            },
            fallbacks=[CommandHandler('cancel', cancel_command)],
        )
        
        # إضافة Handlers
        application.add_handler(conv_handler)
        application.add_handler(CommandHandler("help", help_command))
        application.add_handler(CommandHandler("status", status_command))
        application.add_handler(CommandHandler("id", id_command))
        application.add_handler(CommandHandler("cancel", cancel_command))
        
        # بدء البوت
        bot_active = True
        logger.info("✅ البوت يعمل الآن!")
        
        # التشغيل
        application.run_polling(
            drop_pending_updates=True,
            allowed_updates=Update.ALL_TYPES
        )
        
    except Exception as e:
        bot_active = False
        logger.error(f"❌ خطأ في البوت: {e}")
        # إعادة التشغيل بعد 10 ثواني
        time.sleep(10)
        run_bot()

# ===== الدالة الرئيسية =====
def main():
    """الدالة الرئيسية"""
    
    print("\n" + "="*50)
    print("🤖 BOT STARTING...")
    print("="*50)
    print(f"⏰ الوقت: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")
    print(f"👤 المطور: {DEVELOPER_USERNAME}")
    print("="*50)
    
    # بدء Flask
    flask_thread = threading.Thread(target=run_flask_server, daemon=True)
    flask_thread.start()
    time.sleep(2)
    
    # بدء Keep Alive
    keep_alive_thread = threading.Thread(target=keep_alive, daemon=True)
    keep_alive_thread.start()
    
    # بدء البوت
    run_bot()

if __name__ == '__main__':
    main()
