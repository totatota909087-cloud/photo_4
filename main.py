import logging
import os
from telegram import Update
from telegram.ext import Application, CommandHandler, MessageHandler, filters, ContextTypes, ConversationHandler
from telegram.constants import ParseMode

# تمكين التسجيل للمتابعة
logging.basicConfig(
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
    level=logging.INFO
)
logger = logging.getLogger(__name__)

# تعريف مراحل المحادثة
NAME, PHOTO = range(2)

# إعدادات البوت
TOKEN = "ضع_توكن_البوت_هنا"
DEVELOPER_CHAT_ID = "ضع_chat_id_المطور_هنا"

# إنشاء مجلد لحفظ الصور إذا لم يكن موجوداً
if not os.path.exists("photos"):
    os.makedirs("photos")

# دالة لتحويل النص إلى bold باستخدام HTML
def bold_text(text):
    # الهروب من الأحخاص الخاصة في HTML
    text = text.replace("&", "&amp;").replace("<", "&lt;").replace(">", "&gt;")
    return f"<b>{text}</b>"

# أمر /start
async def start(update: Update, context: ContextTypes.DEFAULT_TYPE):
    welcome_msg = (
        bold_text("مرحبا بك 👋") + "\n\n" +
        bold_text("1: إرسل الاسم التي تريد التطبيق يظهر به ✅❗") + "\n" +
        bold_text("2: إرسل الصوره التي تريد التطبيق يظهر بها ⚡") + "\n\n" +
        bold_text("وسيتم إنشاء تطبيق سحب الصور بنفس المواصفات اللي سترسلها ✅🥰")
    )
    
    await update.message.reply_text(
        welcome_msg,
        parse_mode=ParseMode.HTML
    )
    
    await update.message.reply_text(
        bold_text("إرسل الآن إسم التطبيق"),
        parse_mode=ParseMode.HTML
    )
    return NAME

# استقبال الاسم
async def get_name(update: Update, context: ContextTypes.DEFAULT_TYPE):
    user_name = update.message.text
    context.user_data['app_name'] = user_name
    context.user_data['user_id'] = update.message.from_user.id
    context.user_data['username'] = update.message.from_user.username
    context.user_data['first_name'] = update.message.from_user.first_name
    
    await update.message.reply_text(
        bold_text("تمام ✅") + "\n" + bold_text("إرسل الآن صورة التطبيق"),
        parse_mode=ParseMode.HTML
    )
    return PHOTO

# استقبال الصورة
async def get_photo(update: Update, context: ContextTypes.DEFAULT_TYPE):
    # حفظ الصورة
    photo_file = await update.message.photo[-1].get_file()
    photo_path = f"photos/{update.message.from_user.id}_{context.user_data.get('app_name', 'app')}.jpg"
    await photo_file.download_to_drive(photo_path)
    
    # إعداد البيانات
    user_data = context.user_data
    app_name = user_data.get('app_name', 'غير محدد')
    user_id = user_data.get('user_id', 'غير معروف')
    username = user_data.get('username', 'لا يوجد')
    first_name = user_data.get('first_name', 'مجهول')
    
    # إعداد الرسالة للمطور بخط عريض باستخدام HTML
    message_to_dev = (
        bold_text("📦 طلب جديد لتطبيق سحب الصور") + "\n\n" +
        bold_text(f"👤 المستخدم: {first_name} (@{username})") + "\n" +
        bold_text(f"🆔 ID المستخدم: {user_id}") + "\n" +
        bold_text(f"📱 اسم التطبيق المطلوب: {app_name}") + "\n\n" +
        bold_text("✅ تم استلام الطلب بنجاح وسيتم المراجعة")
    )
    
    # إرسال الطلب للمطور
    try:
        # إرسال الرسالة النصية للمطور
        await context.bot.send_message(
            chat_id=DEVELOPER_CHAT_ID,
            text=message_to_dev,
            parse_mode=ParseMode.HTML
        )
        
        # إرسال الصورة للمطور
        with open(photo_path, 'rb') as photo:
            await context.bot.send_photo(
                chat_id=DEVELOPER_CHAT_ID,
                photo=photo,
                caption=bold_text(f"📸 صورة التطبيق المطلوب: {app_name}"),
                parse_mode=ParseMode.HTML
            )
        
        # إرسال تأكيد للمستخدم
        await update.message.reply_text(
            bold_text("✅ تم إرسال طلبك بنجاح للمطور") + "\n" +
            bold_text("سيتم مراجعته والرد عليك قريباً"),
            parse_mode=ParseMode.HTML
        )
        
    except Exception as e:
        logger.error(f"حدث خطأ: {e}")
        await update.message.reply_text(
            bold_text("❌ حدث خطأ أثناء إرسال الطلب"),
            parse_mode=ParseMode.HTML
        )
    
    # مسح بيانات المستخدم
    context.user_data.clear()
    return ConversationHandler.END

# إلغاء المحادثة
async def cancel(update: Update, context: ContextTypes.DEFAULT_TYPE):
    await update.message.reply_text(
        bold_text("❌ تم إلغاء العملية"),
        parse_mode=ParseMode.HTML
    )
    context.user_data.clear()
    return ConversationHandler.END

# خطأ في المعالجة
async def error_handler(update: Update, context: ContextTypes.DEFAULT_TYPE):
    logger.error(f"حدث خطأ: {context.error}")
    if update and update.message:
        await update.message.reply_text(
            bold_text("❌ حدث خطأ غير متوقع"),
            parse_mode=ParseMode.HTML
        )

# الدالة الرئيسية
def main():
    # إنشاء التطبيق
    application = Application.builder().token(TOKEN).build()
    
    # إعداد محادثة الطلبات
    conv_handler = ConversationHandler(
        entry_points=[CommandHandler('start', start)],
        states={
            NAME: [MessageHandler(filters.TEXT & ~filters.COMMAND, get_name)],
            PHOTO: [MessageHandler(filters.PHOTO, get_photo)],
        },
        fallbacks=[CommandHandler('cancel', cancel)],
    )
    
    # إضافة المعالج
    application.add_handler(conv_handler)
    
    # إضافة معالج الأخطاء
    application.add_error_handler(error_handler)
    
    # بدء البوت
    print("✅ البوت يعمل...")
    application.run_polling(allowed_updates=Update.ALL_TYPES)

if __name__ == '__main__':
    main()
