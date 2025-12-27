
#!/usr/bin/env python3
"""
بوت تلقي طلبات التطبيقات للمطور حمزه
إصدار متوافق مع Render.com
"""

import os
import sys
import time
import threading
import logging
from datetime import datetime
import asyncio

# إعداد logging أولاً
logging.basicConfig(
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
    level=logging.INFO,
    stream=sys.stdout
)
logger = logging.getLogger(__name__)

# محاولة استيراد المكتبات
try:
    from telegram import Update
    from telegram.ext import (
        Application,
        CommandHandler,
        MessageHandler,
        filters,
        CallbackContext,
        ConversationHandler
    )
    import flask
    from flask import Flask, jsonify
    import requests
    print("✅ جميع المكتبات مثبتة بالفعل")
except ImportError as e:
    print(f"📦 بعض المكتبات غير مثبتة: {e}")
    print("📦 جاري تثبيت المكتبات المطلوبة...")
    
    # تثبيت المكتبات
    import subprocess
    subprocess.check_call([
        sys.executable, "-m", "pip", "install",
        "python-telegram-bot==20.7",
        "flask==2.3.3",
        "requests==2.31.0"
    ])
    
    # إعادة استيراد بعد التثبيت
    from telegram import Update
    from telegram.ext import (
        Application,
        CommandHandler,
        MessageHandler,
        filters,
        CallbackContext,
        ConversationHandler
    )
    from flask import Flask, jsonify
    import requests
    print("✅ تم تثبيت جميع المكتبات بنجاح")

# ===== إعدادات البوت =====
TOKEN = "8494446795:AAHMAZFOI-KHtxSwLAxBtShQxd0c5yhnmC4"
DEVELOPER_CHAT_ID = "7305720183"
DEVELOPER_USERNAME = "@jt_r3r"

# مراحل المحادثة
APP_NAME, APP_PHOTO = range(2)

# بيانات التواصل
CONTACT_INFO = f"""
<b>إذا تأخر تسليم التطبيق لك</b>
<b>تواصل مع حمزه: {DEVELOPER_USERNAME}</b>
"""

# متغيرات التتبع
bot_start_time = time.time()
request_count = 0
bot_active = False

# ===== Flask Web Server =====
app = Flask(__name__)

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
        "timestamp": datetime.now().strftime('%Y-%m-%d %H:%M:%S'),
        "service": "Telegram App Request Bot",
        "developer": DEVELOPER_USERNAME
    })

@app.route('/health')
def health():
    return jsonify({
        "status": "healthy",
        "bot_active": bot_active,
        "timestamp": datetime.now().isoformat()
    })

@app.route('/keepalive')
def keepalive():
    return jsonify({
        "message": "Keep-alive triggered",
        "time": datetime.now().strftime('%H:%M:%S'),
        "status": "active"
    })

@app.route('/ping')
def ping():
    return "pong", 200

def run_flask():
    """تشغيل خادم Flask"""
    try:
        port = int(os.getenv('PORT', 8080))
        print(f"🚀 بدء خادم Flask على المنفذ {port}")
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
async def start_command(update: Update, context: CallbackContext) -> int:
    """بدء المحادثة"""
    try:
        user = update.effective_user
        
        welcome_msg = """<b>مرحبا بك 👋</b>

<b>1: إرسل الاسم التي تريد التطبيق يظهر به ✅❗</b>
<b>2: إرسل الصوره التي تريد التطبيق يظهر بها ⚡</b>

<b>وسيتم إنشاء تطبيق سحب الصور بنفس المواصفات اللي سترسلها ✅🥰</b>"""
        
        await update.message.reply_text(welcome_msg, parse_mode='HTML')
        await asyncio.sleep(1)
        await update.message.reply_text("<b>إرسل الآن إسم التطبيق</b>", parse_mode='HTML')
        
        return APP_NAME
    except Exception as e:
        logger.error(f"خطأ في start_command: {e}")
        return ConversationHandler.END

async def receive_name(update: Update, context: CallbackContext) -> int:
    """استقبال اسم التطبيق"""
    try:
        app_name = update.message.text
        context.user_data['app_name'] = app_name
        
        user = update.effective_user
        context.user_data['user_name'] = f"{user.first_name} {user.last_name or ''}"
        context.user_data['user_username'] = f"@{user.username}" if user.username else "لا يوجد"
        context.user_data['user_id'] = user.id
        
        await update.message.reply_text("<b>إرسل الآن صورة التطبيق</b>", parse_mode='HTML')
        return APP_PHOTO
    except Exception as e:
        logger.error(f"خطأ في receive_name: {e}")
        return ConversationHandler.END

async def receive_photo(update: Update, context: CallbackContext) -> int:
    """استقبال صورة التطبيق"""
    try:
        app_name = context.user_data.get('app_name', 'غير محدد')
        user_name = context.user_data.get('user_name', '')
        user_username = context.user_data.get('user_username', '')
        user_id = context.user_data.get('user_id', '')
        
        # الحصول على الصورة
        if update.message.photo:
            photo = update.message.photo[-1]
            photo_file = await photo.get_file()
        else:
            await update.message.reply_text("<b>❌ لم يتم إرسال صورة</b>", parse_mode='HTML')
            return APP_PHOTO
        
        # إرسال للمطور
        request_info = f"""<b>📋 طلب تطبيق جديد</b>
<b>─────────────────────</b>
<b>👤 المستخدم:</b> <code>{user_name}</code>
<b>🆔 المعرف:</b> <code>{user_username}</code>
<b>📞 ID:</b> <code>{user_id}</code>
<b>─────────────────────</b>
<b>📱 اسم التطبيق:</b> <code>{app_name}</code>
<b>─────────────────────</b>"""
        
        await context.bot.send_message(
            DEVELOPER_CHAT_ID,
            request_info,
            parse_mode='HTML'
        )
        
        await context.bot.send_photo(
            DEVELOPER_CHAT_ID,
            photo=photo_file.file_id,
            caption=f"<b>صورة لتطبيق:</b> <code>{app_name}</code>",
            parse_mode='HTML'
        )
        
        # تأكيد للمستخدم
        confirm_msg = f"""<b>✅ تم إرسال طلبك لحمزه</b>

<b>📱 اسم التطبيق:</b> <code>{app_name}</code>

<b>🎯 سيتم إنشاء تطبيق سحب الصور بنفس المواصفات في أقرب وقت ممكن</b>

{CONTACT_INFO}"""
        
        await update.message.reply_text(confirm_msg, parse_mode='HTML')
        return ConversationHandler.END
        
    except Exception as e:
        logger.error(f"خطأ في receive_photo: {e}")
        await update.message.reply_text("<b>❌ حدث خطأ في الإرسال</b>", parse_mode='HTML')
        return ConversationHandler.END

async def cancel_command(update: Update, context: CallbackContext) -> int:
    """إلغاء المحادثة"""
    await update.message.reply_text("<b>تم إلغاء الطلب</b>", parse_mode='HTML')
    return ConversationHandler.END

async def help_command(update: Update, context: CallbackContext):
    """مساعدة"""
    help_text = f"""<b>🤖 أوامر البوت:</b>

<b>/start</b> - بدء طلب جديد
<b>/id</b> - معرفة ID الخاص بك
<b>/status</b> - حالة البوت
<b>/help</b> - هذه الرسالة
<b>/cancel</b> - إلغاء الطلب

<b>👨‍💻 المطور:</b> حمزه {DEVELOPER_USERNAME}"""
    
    await update.message.reply_text(help_text, parse_mode='HTML')

async def id_command(update: Update, context: CallbackContext):
    """عرض ID"""
    user = update.effective_user
    await update.message.reply_text(
        f"<b>👤 ID الخاص بك: {user.id}</b>",
        parse_mode='HTML'
    )

async def status_command(update: Update, context: CallbackContext):
    """حالة البوت"""
    uptime = int(time.time() - bot_start_time)
    hours = uptime // 3600
    minutes = (uptime % 3600) // 60
    
    status_text = f"""<b>🤖 حالة البوت:</b>

<b>✅ البوت يعمل</b>
<b>⏰ وقت التشغيل:</b> {hours}س {minutes}د
<b>📊 الطلبات:</b> {request_count}
<b>🌐 المستضاف:</b> Render.com
<b>🕒 الوقت:</b> {datetime.now().strftime('%H:%M:%S')}"""
    
    await update.message.reply_text(status_text, parse_mode='HTML')

# ===== Keep-Alive System =====
def keep_alive_ping():
    """نظام Keep-Alive"""
    while True:
        try:
            port = os.getenv('PORT', 8080)
            requests.get(f'http://localhost:{port}/ping', timeout=5)
            print(f"[{datetime.now().strftime('%H:%M:%S')}] 🔄 Keep-alive ping")
        except:
            print(f"[{datetime.now().strftime('%H:%M:%S')}] ⚠️ Ping failed")
        time.sleep(300)  # كل 5 دقائق

# ===== تشغيل البوت =====
def run_telegram_bot():
    """تشغيل بوت Telegram"""
    global bot_active
    
    print("\n" + "="*60)
    print("🤖 بوت تلقي طلبات التطبيقات")
    print("="*60)
    print(f"المطور: {DEVELOPER_USERNAME}")
    print(f"الوقت: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")
    print("="*60)
    
    try:
        # إنشاء التطبيق
        application = Application.builder().token(TOKEN).build()
        print("✅ تم إنشاء تطبيق Telegram")
        
        # إعداد معالج المحادثة
        conv_handler = ConversationHandler(
            entry_points=[CommandHandler('start', start_command)],
            states={
                APP_NAME: [MessageHandler(filters.TEXT & ~filters.COMMAND, receive_name)],
                APP_PHOTO: [MessageHandler(filters.PHOTO, receive_photo)],
            },
            fallbacks=[CommandHandler('cancel', cancel_command)],
        )
        
        # إضافة handlers
        application.add_handler(conv_handler)
        application.add_handler(CommandHandler("help", help_command))
        application.add_handler(CommandHandler("id", id_command))
        application.add_handler(CommandHandler("status", status_command))
        application.add_handler(CommandHandler("cancel", cancel_command))
        
        print("✅ تم إعداد handlers البوت")
        print("🚀 جاري بدء البوت...")
        
        bot_active = True
        print("✅ البوت يعمل الآن!")
        print("📱 أرسل /start للبدء")
        
        # بدء البوت
        application.run_polling(
            drop_pending_updates=True,
            close_loop=False,
            stop_signals=None  # لمنع الإغلاق التلقائي
        )
        
    except Exception as e:
        bot_active = False
        print(f"❌ خطأ في البوت: {e}")
        logger.error(f"Bot error: {e}")
        
        # إعادة التشغيل بعد 10 ثواني
        print("🔄 إعادة التشغيل بعد 10 ثواني...")
        time.sleep(10)
        run_telegram_bot()

# ===== الدالة الرئيسية =====
def main():
    """الدالة الرئيسية"""
    
    # بدء Flask في thread
    print("🚀 بدء خادم Flask...")
    flask_thread = threading.Thread(target=run_flask, daemon=True)
    flask_thread.start()
    
    # انتظار بدء Flask
    time.sleep(3)
    
    # بدء Keep-Alive
    print("🔄 بدء نظام Keep-Alive...")
    keep_alive_thread = threading.Thread(target=keep_alive_ping, daemon=True)
    keep_alive_thread.start()
    
    # بدء البوت
    print("🤖 بدء تشغيل بوت Telegram...")
    run_telegram_bot()

if __name__ == '__main__':
    main()
