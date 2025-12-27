import logging
import os
import json
from datetime import datetime
from flask import Flask, render_template, request, jsonify
from telegram import Update
from telegram.ext import Application, CommandHandler, MessageHandler, filters, ContextTypes, ConversationHandler
from telegram.constants import ParseMode
import threading
from flask_cors import CORS

# ============ إعدادات Flask ============
app = Flask(__name__)
CORS(app)

# إعدادات التخزين
REQUESTS_FILE = "requests.json"
PHOTOS_DIR = "photos"

# ============ إعدادات البوت ============
logging.basicConfig(
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
    level=logging.INFO
)
logger = logging.getLogger(__name__)

# تعريف مراحل المحادثة
NAME, PHOTO = range(2)

# إعدادات البوت (يجب تغييرها)
TOKEN = "8494446795:AAHMAZFOI-KHtxSwLAxBtShQxd0c5yhnmC4"
DEVELOPER_CHAT_ID = "7305720183"

# إنشاء المجلدات إذا لم تكن موجودة
if not os.path.exists(PHOTOS_DIR):
    os.makedirs(PHOTOS_DIR)

if not os.path.exists(REQUESTS_FILE):
    with open(REQUESTS_FILE, 'w', encoding='utf-8') as f:
        json.dump([], f, ensure_ascii=False, indent=2)

# ============ دوال المساعدة ============
def bold_text(text):
    """تحويل النص إلى خط عريض باستخدام HTML"""
    if not text:
        return ""
    text = str(text).replace("&", "&amp;").replace("<", "&lt;").replace(">", "&gt;")
    return f"<b>{text}</b>"

def save_request(request_data):
    """حفظ الطلب في ملف JSON"""
    try:
        with open(REQUESTS_FILE, 'r', encoding='utf-8') as f:
            requests = json.load(f)
        
        request_data['id'] = len(requests) + 1
        request_data['timestamp'] = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
        request_data['status'] = 'pending'  # pending, approved, rejected
        
        requests.append(request_data)
        
        with open(REQUESTS_FILE, 'w', encoding='utf-8') as f:
            json.dump(requests, f, ensure_ascii=False, indent=2)
        
        return request_data['id']
    except Exception as e:
        logger.error(f"خطأ في حفظ الطلب: {e}")
        return None

def update_request_status(request_id, status, notes=""):
    """تحديث حالة الطلب"""
    try:
        with open(REQUESTS_FILE, 'r', encoding='utf-8') as f:
            requests = json.load(f)
        
        for req in requests:
            if req['id'] == request_id:
                req['status'] = status
                req['updated_at'] = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
                if notes:
                    req['notes'] = notes
                break
        
        with open(REQUESTS_FILE, 'w', encoding='utf-8') as f:
            json.dump(requests, f, ensure_ascii=False, indent=2)
        
        return True
    except Exception as e:
        logger.error(f"خطأ في تحديث الطلب: {e}")
        return False

# ============ دوال البوت ============
async def start(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """معالج أمر /start"""
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

async def get_name(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """استقبال اسم التطبيق"""
    user_name = update.message.text
    context.user_data['app_name'] = user_name
    context.user_data['user_id'] = update.message.from_user.id
    context.user_data['username'] = update.message.from_user.username or "لا يوجد"
    context.user_data['first_name'] = update.message.from_user.first_name or "مجهول"
    context.user_data['chat_id'] = update.message.chat_id
    
    await update.message.reply_text(
        bold_text("تمام ✅") + "\n" + bold_text("إرسل الآن صورة التطبيق"),
        parse_mode=ParseMode.HTML
    )
    return PHOTO

async def get_photo(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """استقبال صورة التطبيق"""
    try:
        # حفظ الصورة
        photo_file = await update.message.photo[-1].get_file()
        
        # إعداد البيانات
        user_data = context.user_data
        app_name = user_data.get('app_name', 'غير محدد')
        user_id = user_data.get('user_id', 'غير معروف')
        
        # اسم فريد للصورة
        timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
        photo_filename = f"{user_id}_{timestamp}.jpg"
        photo_path = os.path.join(PHOTOS_DIR, photo_filename)
        
        await photo_file.download_to_drive(photo_path)
        
        # تحضير بيانات الطلب
        request_data = {
            'app_name': app_name,
            'user_id': user_id,
            'username': user_data.get('username'),
            'first_name': user_data.get('first_name'),
            'chat_id': user_data.get('chat_id'),
            'photo_filename': photo_filename,
            'photo_path': photo_path,
            'created_at': datetime.now().strftime("%Y-%m-%d %H:%M:%S")
        }
        
        # حفظ الطلب
        request_id = save_request(request_data)
        
        # إعداد الرسالة للمطور
        message_to_dev = (
            bold_text("📦 طلب جديد لتطبيق سحب الصور") + "\n\n" +
            bold_text(f"🆔 رقم الطلب: {request_id}") + "\n" +
            bold_text(f"👤 المستخدم: {user_data.get('first_name')} (@{user_data.get('username')})") + "\n" +
            bold_text(f"🆔 ID المستخدم: {user_id}") + "\n" +
            bold_text(f"📱 اسم التطبيق المطلوب: {app_name}") + "\n\n" +
            bold_text("✅ تم استلام الطلب بنجاح")
        )
        
        # إرسال الطلب للمطور
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
            bold_text(f"📋 رقم طلبك: {request_id}") + "\n" +
            bold_text("سيتم مراجعته والرد عليك قريباً"),
            parse_mode=ParseMode.HTML
        )
        
    except Exception as e:
        logger.error(f"حدث خطأ في get_photo: {e}")
        await update.message.reply_text(
            bold_text("❌ حدث خطأ أثناء معالجة طلبك"),
            parse_mode=ParseMode.HTML
        )
    
    # مسح بيانات المستخدم
    context.user_data.clear()
    return ConversationHandler.END

async def cancel(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """إلغاء المحادثة"""
    await update.message.reply_text(
        bold_text("❌ تم إلغاء العملية"),
        parse_mode=ParseMode.HTML
    )
    context.user_data.clear()
    return ConversationHandler.END

# ============ واجهة Flask ============
@app.route('/')
def index():
    """الصفحة الرئيسية"""
    return render_template('index.html')

@app.route('/api/requests', methods=['GET'])
def get_requests():
    """الحصول على جميع الطلبات"""
    try:
        with open(REQUESTS_FILE, 'r', encoding='utf-8') as f:
            requests = json.load(f)
        
        # إضافة مسار الصورة الكامل
        for req in requests:
            if 'photo_filename' in req:
                req['photo_url'] = f"/photos/{req['photo_filename']}"
        
        return jsonify({
            'success': True,
            'count': len(requests),
            'requests': requests
        })
    except Exception as e:
        return jsonify({'success': False, 'error': str(e)}), 500

@app.route('/api/requests/<int:request_id>', methods=['GET'])
def get_request(request_id):
    """الحصول على طلب محدد"""
    try:
        with open(REQUESTS_FILE, 'r', encoding='utf-8') as f:
            requests = json.load(f)
        
        request_data = next((req for req in requests if req['id'] == request_id), None)
        
        if request_data:
            if 'photo_filename' in request_data:
                request_data['photo_url'] = f"/photos/{request_data['photo_filename']}"
            return jsonify({'success': True, 'request': request_data})
        else:
            return jsonify({'success': False, 'error': 'الطلب غير موجود'}), 404
    except Exception as e:
        return jsonify({'success': False, 'error': str(e)}), 500

@app.route('/api/requests/<int:request_id>/status', methods=['PUT'])
def update_status(request_id):
    """تحديث حالة الطلب"""
    try:
        data = request.json
        status = data.get('status')
        notes = data.get('notes', '')
        
        if status not in ['pending', 'approved', 'rejected']:
            return jsonify({'success': False, 'error': 'حالة غير صالحة'}), 400
        
        # تحديث حالة الطلب في الملف
        success = update_request_status(request_id, status, notes)
        
        if success:
            # إرسال إشعار للمستخدم عبر البوت
            async def send_notification():
                try:
                    with open(REQUESTS_FILE, 'r', encoding='utf-8') as f:
                        requests = json.load(f)
                    
                    req = next((r for r in requests if r['id'] == request_id), None)
                    if req and 'chat_id' in req:
                        bot_app = Application.builder().token(TOKEN).build()
                        
                        status_messages = {
                            'approved': '✅ تم الموافقة على طلبك',
                            'rejected': '❌ تم رفض طلبك',
                            'pending': '🔄 طلبك قيد المراجعة'
                        }
                        
                        message = bold_text(status_messages.get(status, 'تم تحديث حالة طلبك'))
                        if notes:
                            message += "\n" + bold_text(f"📝 ملاحظة: {notes}")
                        
                        await bot_app.bot.send_message(
                            chat_id=req['chat_id'],
                            text=message,
                            parse_mode=ParseMode.HTML
                        )
                except Exception as e:
                    logger.error(f"خطأ في إرسال الإشعار: {e}")
            
            # تشغيل الإشعار في خيط منفصل
            thread = threading.Thread(target=lambda: asyncio.run(send_notification()))
            thread.start()
            
            return jsonify({'success': True, 'message': 'تم تحديث الحالة بنجاح'})
        else:
            return jsonify({'success': False, 'error': 'فشل في تحديث الحالة'}), 500
            
    except Exception as e:
        return jsonify({'success': False, 'error': str(e)}), 500

@app.route('/photos/<filename>')
def serve_photo(filename):
    """خدمة ملفات الصور"""
    try:
        return send_from_directory(PHOTOS_DIR, filename)
    except:
        return "الصورة غير موجودة", 404

@app.route('/api/stats', methods=['GET'])
def get_stats():
    """الحصول على إحصائيات الطلبات"""
    try:
        with open(REQUESTS_FILE, 'r', encoding='utf-8') as f:
            requests = json.load(f)
        
        stats = {
            'total': len(requests),
            'pending': len([r for r in requests if r.get('status') == 'pending']),
            'approved': len([r for r in requests if r.get('status') == 'approved']),
            'rejected': len([r for r in requests if r.get('status') == 'rejected']),
            'today': len([r for r in requests if r.get('created_at', '').startswith(datetime.now().strftime("%Y-%m-%d"))])
        }
        
        return jsonify({'success': True, 'stats': stats})
    except Exception as e:
        return jsonify({'success': False, 'error': str(e)}), 500

# ============ صفحة HTML لواجهة الإدارة ============
@app.route('/admin')
def admin_panel():
    """لوحة تحكم الإدارة"""
    return '''
    <!DOCTYPE html>
    <html lang="ar" dir="rtl">
    <head>
        <meta charset="UTF-8">
        <meta name="viewport" content="width=device-width, initial-scale=1.0">
        <title>لوحة إدارة طلبات التطبيقات</title>
        <style>
            * {
                margin: 0;
                padding: 0;
                box-sizing: border-box;
                font-family: 'Segoe UI', Tahoma, Geneva, Verdana, sans-serif;
            }
            
            body {
                background: linear-gradient(135deg, #667eea 0%, #764ba2 100%);
                color: #333;
                min-height: 100vh;
            }
            
            .container {
                max-width: 1200px;
                margin: 0 auto;
                padding: 20px;
            }
            
            header {
                background: rgba(255, 255, 255, 0.95);
                padding: 20px;
                border-radius: 10px;
                margin-bottom: 20px;
                box-shadow: 0 2px 10px rgba(0,0,0,0.1);
            }
            
            h1 {
                color: #2d3748;
                margin-bottom: 10px;
            }
            
            .stats {
                display: grid;
                grid-template-columns: repeat(auto-fit, minmax(200px, 1fr));
                gap: 15px;
                margin-bottom: 30px;
            }
            
            .stat-card {
                background: white;
                padding: 20px;
                border-radius: 8px;
                text-align: center;
                box-shadow: 0 2px 5px rgba(0,0,0,0.1);
            }
            
            .stat-card h3 {
                color: #4a5568;
                margin-bottom: 10px;
            }
            
            .stat-value {
                font-size: 2em;
                font-weight: bold;
            }
            
            .filters {
                background: white;
                padding: 20px;
                border-radius: 8px;
                margin-bottom: 20px;
                display: flex;
                gap: 10px;
                flex-wrap: wrap;
            }
            
            select, button {
                padding: 10px 15px;
                border: 1px solid #e2e8f0;
                border-radius: 5px;
                background: white;
                color: #2d3748;
            }
            
            button {
                background: #4299e1;
                color: white;
                border: none;
                cursor: pointer;
                transition: background 0.3s;
            }
            
            button:hover {
                background: #3182ce;
            }
            
            .requests-container {
                background: white;
                border-radius: 8px;
                overflow: hidden;
            }
            
            .request-card {
                padding: 20px;
                border-bottom: 1px solid #e2e8f0;
                display: grid;
                grid-template-columns: auto 1fr auto;
                gap: 20px;
                align-items: center;
            }
            
            .request-card:last-child {
                border-bottom: none;
            }
            
            .request-img {
                width: 100px;
                height: 100px;
                object-fit: cover;
                border-radius: 5px;
            }
            
            .request-info h3 {
                color: #2d3748;
                margin-bottom: 5px;
            }
            
            .request-meta {
                color: #718096;
                font-size: 0.9em;
                margin-bottom: 10px;
            }
            
            .status-badge {
                padding: 5px 10px;
                border-radius: 20px;
                font-size: 0.8em;
                font-weight: bold;
            }
            
            .status-pending {
                background: #fed7d7;
                color: #c53030;
            }
            
            .status-approved {
                background: #c6f6d5;
                color: #276749;
            }
            
            .status-rejected {
                background: #e2e8f0;
                color: #4a5568;
            }
            
            .actions {
                display: flex;
                gap: 10px;
            }
            
            @media (max-width: 768px) {
                .request-card {
                    grid-template-columns: 1fr;
                    text-align: center;
                }
                
                .stats {
                    grid-template-columns: 1fr;
                }
            }
        </style>
    </head>
    <body>
        <div class="container">
            <header>
                <h1>📱 لوحة إدارة طلبات التطبيقات</h1>
                <p>إدارة جميع طلبات إنشاء تطبيقات سحب الصور</p>
            </header>
            
            <div class="stats" id="statsContainer">
                <!-- سيتم ملء الإحصائيات بواسطة JavaScript -->
            </div>
            
            <div class="filters">
                <select id="statusFilter">
                    <option value="all">جميع الطلبات</option>
                    <option value="pending">قيد الانتظار</option>
                    <option value="approved">مقبولة</option>
                    <option value="rejected">مرفوضة</option>
                </select>
                <button onclick="loadRequests()">🔍 تصفية</button>
                <button onclick="loadRequests()" style="background: #48bb78;">🔄 تحديث</button>
            </div>
            
            <div class="requests-container" id="requestsContainer">
                <!-- سيتم ملء الطلبات بواسطة JavaScript -->
            </div>
        </div>
        
        <script>
            let allRequests = [];
            
            async function loadStats() {
                try {
                    const response = await fetch('/api/stats');
                    const data = await response.json();
                    
                    if (data.success) {
                        const stats = data.stats;
                        const statsHTML = `
                            <div class="stat-card">
                                <h3>📊 إجمالي الطلبات</h3>
                                <div class="stat-value" style="color: #4299e1;">${stats.total}</div>
                            </div>
                            <div class="stat-card">
                                <h3>⏳ قيد الانتظار</h3>
                                <div class="stat-value" style="color: #ed8936;">${stats.pending}</div>
                            </div>
                            <div class="stat-card">
                                <h3>✅ مقبولة</h3>
                                <div class="stat-value" style="color: #48bb78;">${stats.approved}</div>
                            </div>
                            <div class="stat-card">
                                <h3>❌ مرفوضة</h3>
                                <div class="stat-value" style="color: #f56565;">${stats.rejected}</div>
                            </div>
                            <div class="stat-card">
                                <h3>📅 اليوم</h3>
                                <div class="stat-value" style="color: #9f7aea;">${stats.today}</div>
                            </div>
                        `;
                        document.getElementById('statsContainer').innerHTML = statsHTML;
                    }
                } catch (error) {
                    console.error('Error loading stats:', error);
                }
            }
            
            async function loadRequests() {
                try {
                    const statusFilter = document.getElementById('statusFilter').value;
                    const response = await fetch('/api/requests');
                    const data = await response.json();
                    
                    if (data.success) {
                        allRequests = data.requests;
                        
                        // ترتيب الطلبات من الأحدث إلى الأقدم
                        allRequests.sort((a, b) => new Date(b.created_at) - new Date(a.created_at));
                        
                        // تطبيق التصفية
                        let filteredRequests = allRequests;
                        if (statusFilter !== 'all') {
                            filteredRequests = allRequests.filter(req => req.status === statusFilter);
                        }
                        
                        if (filteredRequests.length === 0) {
                            document.getElementById('requestsContainer').innerHTML = 
                                '<div style="text-align: center; padding: 40px; color: #718096;">لا توجد طلبات لعرضها</div>';
                            return;
                        }
                        
                        const requestsHTML = filteredRequests.map(request => {
                            const statusClass = `status-${request.status}`;
                            const statusText = {
                                'pending': 'قيد الانتظار',
                                'approved': 'مقبولة',
                                'rejected': 'مرفوضة'
                            }[request.status] || request.status;
                            
                            return `
                                <div class="request-card">
                                    <div>
                                        <img src="${request.photo_url || '/placeholder.jpg'}" 
                                             alt="${request.app_name}" 
                                             class="request-img"
                                             onerror="this.src='/placeholder.jpg'">
                                    </div>
                                    <div class="request-info">
                                        <h3>${request.app_name}</h3>
                                        <div class="request-meta">
                                            👤 ${request.first_name} (@${request.username})<br>
                                            🆔 ${request.user_id}<br>
                                            📅 ${request.created_at}<br>
                                            🆔 رقم الطلب: ${request.id}
                                        </div>
                                        <span class="status-badge ${statusClass}">${statusText}</span>
                                    </div>
                                    <div class="actions">
                                        <button onclick="updateStatus(${request.id}, 'approved')" 
                                                style="background: #48bb78;">✅ قبول</button>
                                        <button onclick="updateStatus(${request.id}, 'rejected')" 
                                                style="background: #f56565;">❌ رفض</button>
                                        <button onclick="showDetails(${request.id})" 
                                                style="background: #4299e1;">📄 تفاصيل</button>
                                    </div>
                                </div>
                            `;
                        }).join('');
                        
                        document.getElementById('requestsContainer').innerHTML = requestsHTML;
                    }
                } catch (error) {
                    console.error('Error loading requests:', error);
                    document.getElementById('requestsContainer').innerHTML = 
                        '<div style="text-align: center; padding: 40px; color: #f56565;">خطأ في تحميل الطلبات</div>';
                }
            }
            
            async function updateStatus(requestId, status) {
                const notes = prompt('أدخل ملاحظة (اختياري):');
                
                try {
                    const response = await fetch(`/api/requests/${requestId}/status`, {
                        method: 'PUT',
                        headers: {
                            'Content-Type': 'application/json',
                        },
                        body: JSON.stringify({
                            status: status,
                            notes: notes || ''
                        })
                    });
                    
                    const data = await response.json();
                    
                    if (data.success) {
                        alert('✅ تم تحديث حالة الطلب بنجاح');
                        loadRequests();
                        loadStats();
                    } else {
                        alert('❌ ' + data.error);
                    }
                } catch (error) {
                    console.error('Error updating status:', error);
                    alert('❌ حدث خطأ أثناء تحديث الحالة');
                }
            }
            
            function showDetails(requestId) {
                const request = allRequests.find(r => r.id === requestId);
                if (request) {
                    const details = `
                        📱 اسم التطبيق: ${request.app_name}
                        👤 المستخدم: ${request.first_name} (@${request.username})
                        🆔 ID المستخدم: ${request.user_id}
                        📅 تاريخ الطلب: ${request.created_at}
                        📊 الحالة: ${request.status}
                        ${request.notes ? '📝 الملاحظات: ' + request.notes : ''}
                    `;
                    alert(details);
                }
            }
            
            // تحميل البيانات عند فتح الصفحة
            document.addEventListener('DOMContentLoaded', () => {
                loadStats();
                loadRequests();
                
                // تحديث البيانات كل 30 ثانية
                setInterval(() => {
                    loadStats();
                    loadRequests();
                }, 30000);
            });
        </script>
    </body>
    </html>
    '''

# ============ تشغيل البوت وFlask ============
def run_bot():
    """تشغيل بوت تليجرام"""
    # إنشاء تطبيق البوت
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
    
    # بدء البوت
    print("🤖 بوت تليجرام يعمل...")
    application.run_polling(allowed_updates=Update.ALL_TYPES)

def run_flask():
    """تشغيل خادم Flask"""
    print("🌐 خادم ويب يعمل على http://localhost:5000")
    app.run(host='0.0.0.0', port=5000, debug=False)

if __name__ == '__main__':
    import threading
    import asyncio
    
    # تشغيل البوت في خيط منفصل
    bot_thread = threading.Thread(target=run_bot, daemon=True)
    bot_thread.start()
    
    # تشغيل Flask في الخيط الرئيسي
    run_flask()
