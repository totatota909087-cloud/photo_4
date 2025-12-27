import subprocess
import sys
import time
import threading
import os
from flask import Flask, jsonify
import requests
import logging

# تثبيت المكتبات المطلوبة تلقائياً
def install_packages():
    required_packages = [
        'python-telegram-bot[job-queue]==20.7',
        'flask==3.0.0', 
        'requests==2.31.0'
    ]
    
    print("📦 جاري تثبيت المكتبات المطلوبة...")
    for package in required_packages:
        package_name = package.split('==')[0]
        try:
            __import__(package_name.replace('-', '_').replace('[job_queue]', ''))
            print(f"✅ {package_name} مثبت بالفعل")
        except ImportError:
            print(f"📦 جاري تثبيت {package}...")
            subprocess.check_call([sys.executable, "-m", "pip", "install", package], stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL)
            print(f"✅ تم تثبيت {package} بنجاح")

# تثبيت المكتبات
install_packages()

# الآن استيراد المكتبات بعد التثبيت
from telegram import Update
from telegram.ext import Application, CommandHandler, MessageHandler, filters, CallbackContext, ConversationHandler
import asyncio

# تمكين التسجيل للتصحيح
logging.basicConfig(
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
    level=logging.INFO,
    handlers=[
        logging.StreamHandler(sys.stdout),
        logging.FileHandler('bot.log')
    ]
)
logger = logging.getLogger(__name__)

# تعريف مراحل المحادثة
APP_NAME, APP_PHOTO = range(2)

# معرف المطور
DEVELOPER_CHAT_ID = "7305720183"
DEVELOPER_USERNAME = "@jt_r3r"

# بيانات التواصل مع المطور
CONTACT_INFO = f"""
<b>إذا تأخر تسليم التطبيق لك</b>
<b>تواصل مع حمزه: {DEVELOPER_USERNAME}</b>
"""

# إنشاء تطبيق Flask
flask_app = Flask(__name__)

# متغيرات للحالة
bot_start_time = time.time()
request_count = 0

@flask_app.route('/')
def home():
    global request_count
    request_count += 1
    
    uptime = time.time() - bot_start_time
    hours, remainder = divmod(uptime, 3600)
    minutes, seconds = divmod(remainder, 60)
    
    return jsonify({
        "status": "online",
        "service": "Telegram Bot",
        "uptime": f"{int(hours)}h {int(minutes)}m {int(seconds)}s",
        "request_count": request_count,
        "timestamp": time.strftime('%Y-%m-%d %H:%M:%S'),
        "message": "✅ البوت يعمل بنجاح!",
        "developer": DEVELOPER_USERNAME
    })

@flask_app.route('/health')
def health_check():
    return jsonify({
        "status": "healthy",
        "bot": "running",
        "flask": "running",
        "timestamp": time.time()
    })

@flask_app.route('/keepalive')
def keep_alive_endpoint():
    return jsonify({
        "message": "Keep-alive successful",
        "time": time.strftime('%Y-%m-%d %H:%M:%S'),
        "status": "active"
    })

@flask_app.route('/logs')
def show_logs():
    try:
        with open('bot.log', 'r') as f:
            logs = f.read()
        return f"<pre>{logs[-5000:]}</pre>"
    except:
        return "No logs available"

def run_flask():
    """تشغيل خادم Flask"""
    try:
        port = int(os.environ.get('PORT', 10000))
        print(f"🚀 بدء خادم Flask على المنفذ {port}")
        flask_app.run(
            host='0.0.0.0',
            port=port,
            debug=False,
            use_reloader=False,
            threaded=True
        )
    except Exception as e:
        print(f"❌ خطأ في تشغيل Flask: {e}")
        logger.error(f"Flask error: {e}")

# ===== وظائف البوت =====
async def start(update: Update, context: CallbackContext) -> int:
    """يبدأ المحادثة ويرسل الرسالة الأولى."""
    try:
        user = update.effective_user
        
        welcome_message = """<b>مرحبا بك 👋</b>

<b>1: إرسل الاسم التي تريد التطبيق يظهر به ✅❗</b>
<b>2: إرسل الصوره التي تريد التطبيق يظهر بها ⚡</b>

<b>وسيتم إنشاء تطبيق سحب الصور بنفس المواصفات اللي سترسلها ✅🥰</b>"""
        
        await update.message.reply_text(
            f"{welcome_message}",
            parse_mode='HTML'
        )
        
        await asyncio.sleep(2)
        
        await update.message.reply_text(
            "<b>إرسل الآن إسم التطبيق</b>",
            parse_mode='HTML'
        )
        
        return APP_NAME
    except Exception as e:
        logger.error(f"Error in start: {e}")
        return ConversationHandler.END

async def get_id(update: Update, context: CallbackContext):
    """يرجع الـ ID الخاص بالمستخدم."""
    try:
        user = update.effective_user
        chat_id = update.effective_chat.id
        
        await update.message.reply_text(
            f"<b>👤 معرفك: {user.id}</b>\n"
            f"<b>💬 معرف الدردشة: {chat_id}</b>\n\n"
            f"<b>📝 أرسل المعرف هذا إلى المطور</b>",
            parse_mode='HTML'
        )
    except Exception as e:
        logger.error(f"Error in get_id: {e}")

async def receive_app_name(update: Update, context: CallbackContext) -> int:
    """يستقبل اسم التطبيق من المستخدم."""
    try:
        app_name = update.message.text
        context.user_data['app_name'] = app_name
        
        user = update.effective_user
        context.user_data['user_name'] = f"{user.first_name} {user.last_name or ''}"
        context.user_data['user_username'] = f"@{user.username}" if user.username else "لا يوجد"
        context.user_data['user_id'] = user.id
        
        await update.message.reply_text(
            "<b>إرسل الآن صورة التطبيق</b>",
            parse_mode='HTML'
        )
        
        return APP_PHOTO
    except Exception as e:
        logger.error(f"Error in receive_app_name: {e}")
        return ConversationHandler.END

async def receive_app_photo(update: Update, context: CallbackContext) -> int:
    """يستقبل صورة التطبيق من المستخدم."""
    try:
        user = update.effective_user
        app_name = context.user_data.get('app_name', 'غير محدد')
        user_name = context.user_data.get('user_name', '')
        user_username = context.user_data.get('user_username', '')
        user_id = context.user_data.get('user_id', '')
        
        if not update.message.photo:
            await update.message.reply_text("<b>❌ لم يتم إرسال صورة. أرسل صورة من فضلك.</b>", parse_mode='HTML')
            return APP_PHOTO
        
        photo_file = await update.message.photo[-1].get_file()
        
        request_info = f"""<b>📋 طلب تطبيق جديد</b>
<b>─────────────────────</b>
<b>👤 المستخدم:</b> <code>{user_name}</code>
<b>🆔 المعرف:</b> <code>{user_username}</code>
<b>📞 ID:</b> <code>{user_id}</code>
<b>─────────────────────</b>
<b>📱 اسم التطبيق:</b> <code>{app_name}</code>
<b>─────────────────────</b>"""
        
        await context.bot.send_message(
            chat_id=DEVELOPER_CHAT_ID,
            text=request_info,
            parse_mode='HTML'
        )
        
        await context.bot.send_photo(
            chat_id=DEVELOPER_CHAT_ID,
            photo=photo_file.file_id,
            caption=f"<b>صورة لتطبيق:</b> <code>{app_name}</code>",
            parse_mode='HTML'
        )
        
        confirmation_message = f"""<b>✅ تم إرسال طلبك لحمزه</b>

<b>📱 اسم التطبيق:</b> <code>{app_name}</code>

<b>🎯 سيتم إنشاء تطبيق سحب الصور بنفس المواصفات في أقرب وقت ممكن</b>

{CONTACT_INFO}"""
        
        await update.message.reply_text(
            confirmation_message,
            parse_mode='HTML'
        )
        
        return ConversationHandler.END
    except Exception as e:
        logger.error(f"Error in receive_app_photo: {e}")
        await update.message.reply_text(
            "<b>❌ حدث خطأ. يرجى المحاولة مرة أخرى.</b>",
            parse_mode='HTML'
        )
        return ConversationHandler.END

async def cancel(update: Update, context: CallbackContext) -> int:
    """يلغي المحادثة."""
    await update.message.reply_text(
        "<b>تم إلغاء الطلب. يمكنك البدء مرة أخرى باستخدام /start</b>",
        parse_mode='HTML'
    )
    return ConversationHandler.END

async def help_command(update: Update, context: CallbackContext):
    """يرسل رسالة المساعدة."""
    help_text = f"""<b>🤖 أوامر البوت:</b>

<b>/start</b> - بدء طلب تطبيق جديد
<b>/id</b> - معرفة رقم ID الخاص بك
<b>/help</b> - عرض هذه الرسالة
<b>/cancel</b> - إلغاء الطلب الحالي

<b>👨‍💻 المطور:</b> حمزه {DEVELOPER_USERNAME}"""
    
    await update.message.reply_text(help_text, parse_mode='HTML')

async def status_command(update: Update, context: CallbackContext):
    """عرض حالة البوت."""
    uptime = time.time() - bot_start_time
    hours, remainder = divmod(uptime, 3600)
    minutes, seconds = divmod(remainder, 60)
    
    status_text = f"""<b>🤖 حالة البوت:</b>

<b>✅ البوت يعمل بنجاح</b>
<b>⏰ وقت التشغيل:</b> {int(hours)}س {int(minutes)}د {int(seconds)}ث
<b>📊 عدد الطلبات:</b> {request_count}
<b>🕒 آخر تحديث:</b> {time.strftime('%H:%M:%S')}

<b>🌐 مستضاف على:</b> Render.com"""
    
    await update.message.reply_text(status_text, parse_mode='HTML')

# ===== وظائف Keep-Alive =====
def keep_alive_ping():
    """إرسال طلبات Keep-Alive إلى Render."""
    try:
        port = os.environ.get('PORT', '10000')
        render_url = os.environ.get('RENDER_EXTERNAL_URL', f'http://0.0.0.0:{port}')
        
        # محاولة ping للرابط
        response = requests.get(f'{render_url}/keepalive', timeout=10)
        current_time = time.strftime('%H:%M:%S')
        
        if response.status_code == 200:
            print(f"[{current_time}] ✅ Keep-Alive successful")
            logger.info(f"Keep-Alive successful at {current_time}")
        else:
            print(f"[{current_time}] ⚠️ Keep-Alive status: {response.status_code}")
            logger.warning(f"Keep-Alive status: {response.status_code}")
    except Exception as e:
        current_time = time.strftime('%H:%M:%S')
        print(f"[{current_time}] ❌ Keep-Alive failed: {e}")
        logger.error(f"Keep-Alive failed: {e}")

def keep_alive_loop():
    """حلقة Keep-Alive."""
    while True:
        try:
            keep_alive_ping()
            # الانتظار 5 دقائق (أقل من 15 دقيقة ليتفادى سكون Render)
            time.sleep(300)
        except Exception as e:
            logger.error(f"Error in keep_alive_loop: {e}")
            time.sleep(60)

# ===== وظيفة التشغيل الرئيسية =====
def run_bot():
    """تشغيل البوت مع معالجة الأخطاء."""
    TOKEN = "8494446795:AAHMAZFOI-KHtxSwLAxBtShQxd0c5yhnmC4"
    
    print("\n" + "="*60)
    print("🤖 بدء تشغيل بوت تلقي طلبات التطبيقات")
    print("="*60)
    print(f"⏰ وقت البدء: {time.strftime('%Y-%m-%d %H:%M:%S')}")
    print(f"🔧 إصدار python-telegram-bot: 20.7")
    print("="*60)
    
    try:
        # إنشاء تطبيق Telegram
        application = Application.builder().token(TOKEN).build()
        
        # إعداد معالج المحادثة
        conv_handler = ConversationHandler(
            entry_points=[CommandHandler('start', start)],
            states={
                APP_NAME: [
                    MessageHandler(filters.TEXT & ~filters.COMMAND, receive_app_name)
                ],
                APP_PHOTO: [
                    MessageHandler(filters.PHOTO, receive_app_photo)
                ],
            },
            fallbacks=[CommandHandler('cancel', cancel)],
        )
        
        # إضافة المعالجات
        application.add_handler(conv_handler)
        application.add_handler(CommandHandler("id", get_id))
        application.add_handler(CommandHandler("help", help_command))
        application.add_handler(CommandHandler("status", status_command))
        application.add_handler(CommandHandler("cancel", cancel))
        
        print("✅ تم إنشاء تطبيق Telegram بنجاح")
        print("📱 جاري بدء استقبال الرسائل...")
        
        # بدء البوت
        application.run_polling(
            drop_pending_updates=True,
            allowed_updates=Update.ALL_TYPES,
            close_loop=False
        )
        
    except Exception as e:
        print(f"❌ خطأ في تشغيل البوت: {e}")
        logger.error(f"Bot startup error: {e}")
        
        # محاولة إعادة التشغيل بعد 30 ثانية
        print("🔄 جاري إعادة التشغيل بعد 30 ثانية...")
        time.sleep(30)
        run_bot()

def main():
    """الدالة الرئيسية."""
    
    # بدء Flask في thread منفصل
    print("🚀 بدء خادم Flask...")
    flask_thread = threading.Thread(target=run_flask, daemon=True)
    flask_thread.start()
    
    # انتظار لبدء Flask
    time.sleep(3)
    
    # بدء Keep-Alive في thread منفصل
    print("🔄 بدء نظام Keep-Alive...")
    keep_alive_thread = threading.Thread(target=keep_alive_loop, daemon=True)
    keep_alive_thread.start()
    
    print("⏳ جاري بدء البوت...")
    time.sleep(2)
    
    # بدء البوت
    run_bot()

if __name__ == '__main__':
    main()
