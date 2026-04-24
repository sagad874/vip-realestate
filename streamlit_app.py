import streamlit as st
import pandas as pd
from datetime import datetime
import requests
import re
from io import StringIO

# 1. إعدادات الصفحة الفنية
st.set_page_config(page_title="Matrix Real Estate Pro", layout="wide")

# --- 🛠️ قسم الإعدادات اليدوية (تعدل مرة واحدة فقط) ---
OFFICE_NAME = "عقارات البياع" 
ADMIN_PWD = "123"  # الرمز السري للوحة الإدارة

# ضع هنا معرف الشيت الخاص بطلبات الزبائن (الموجود في الرابط بعد /d/)
MY_SHEET_ID = "1a9MO2P78L7XBggmlkYKYfjnslAAyvGxOeffnv1LT_ac" 

# ضع هنا رابط الـ Webhook الخاص بك لاستلام الإشعارات
WEBHOOK_URL = "https://eomfdq8l221q30q.m.pipedream.net"

# رابط تصدير البيانات من جوجل شيت الخاص بك
DATA_CSV_URL = f"https://docs.google.com/spreadsheets/d/{MY_SHEET_ID}/export?format=csv"

# -------------------------------------------------------

# تنظيف الرابط ومعرفة الواجهة المطلوبة
params = st.query_params
view_type = params.get("view", "admin") # الافتراضي إدارة إلا إذا كتب في الرابط view=client

# --- 📱 أولاً: واجهة الزبون (تظهر عند إضافة ?view=client للرابط) ---
if view_type == "client":
    if "submitted" not in st.session_state: st.session_state.submitted = False

    if not st.session_state.submitted:
        st.markdown(f"<h1 style='text-align: center; color: #d4af37;'>🏢 {OFFICE_NAME}</h1>", unsafe_allow_html=True)
        st.markdown("<p style='text-align: center;'>يرجى إرسال تفاصيل طلبك وسنتواصل معك فوراً</p>", unsafe_allow_html=True)
        
        with st.form("order_form", clear_on_submit=True):
            col1, col2 = st.columns(2)
            with col1:
                name = st.text_input("الأسم الكامل")
                phone = st.text_input("رقم الهاتف (واتساب)")
            with col2:
                region = st.selectbox("المنطقة", ["البياع", "شهداء البياع", "المدائن", "السيدية", "أخرى"])
                budget = st.text_input("الميزانية التقريبية")
            
            details = st.text_area("تفاصيل العقار المطلوب (مساحة، طابق، إلخ)")
            
            if st.form_submit_button("إرسال الطلب 🚀"):
                if name and phone:
                    # إرسال البيانات للـ Webhook
                    payload = {
                        "name": name, 
                        "phone": phone, 
                        "region": region, 
                        "budget": budget, 
                        "details": details, 
                        "source": OFFICE_NAME
                    }
                    try:
                        requests.post(WEBHOOK_URL, params=payload, timeout=5)
                    except:
                        pass # استمرار حتى لو فشل الويب هوك لضمان تجربة الزبون
                    
                    st.session_state.submitted = True
                    st.rerun()
                else:
                    st.warning("يرجى كتابة الأسم ورقم الهاتف.")
    else:
        st.balloons()
        st.markdown(f"""
            <div style="text-align: center; padding: 40px; background-color: #1a1c24; border-radius: 20px; border: 2px solid #d4af37; margin-top: 30px;">
                <h1 style="color: #d4af37;">✅ تم الإرسال بنجاح!</h1>
                <p style="color: white; font-size: 1.2em;">شكراً لثقتكم بمكتب <b>{OFFICE_NAME}</b>. سيقوم فريقنا بالتواصل معكم في أقرب وقت.</p>
            </div>
        """, unsafe_allow_html=True)
        if st.button("إرسال طلب آخر"):
            st.session_state.submitted = False
            st.rerun()
    st.stop()

# --- 🔒 ثانياً: واجهة الإدارة (Dashboard) ---
if "auth" not in st.session_state: st.session_state.auth = False

if not st.session_state.auth:
    st.markdown(f"<h2 style='text-align: center; color: #d4af37;'>🔒 لوحة إدارة {OFFICE_NAME}</h2>", unsafe_allow_html=True)
    col_a, col_b, col_c = st.columns([1,2,1])
    with col_b:
        pwd = st.text_input("أدخل الرمز السري للدخول:", type="password")
        if st.button("تسجيل الدخول", use_container_width=True):
            if pwd == ADMIN_PWD:
                st.session_state.auth = True
                st.rerun()
            else:
                st.error("الرمز السري غير صحيح!")
    st.stop()

# عرض السجلات للإدارة بعد تسجيل الدخول
st.markdown(f"<h2 style='color:#d4af37;'>📊 سجل الطلبات المستلمة</h2>", unsafe_allow_html=True)

try:
    # جلب البيانات من جوجل شيت مع كسر الكاش لضمان التحديث
    res = requests.get(f"{DATA_CSV_URL}?cb={datetime.now().timestamp()}", timeout=10)
    df = pd.read_csv(StringIO(res.text))
    
    if not df.empty:
        # عرض الطلبات من الأحدث إلى الأقدم
        for idx, row in df.iloc[::-1].iterrows():
            with st.container():
                st.markdown(f"""
                <div style="background-color: #1a1c24; border-radius: 12px; padding: 15px; border: 1px solid #333; margin-bottom: 10px;">
                    <h3 style="color: white; margin: 0;">👤 {row.iloc[0]}</h3>
                    <p style="color: #2ecc71; margin: 5px 0;">📍 المنطقة: {row.iloc[2] if len(row)>2 else '—'} | 💰 الميزانية: {row.iloc[3] if len(row)>3 else '—'}</p>
                    <p style="color: #aaa; font-size: 0.9em;">📝 {row.iloc[4] if len(row)>4 else '-'}</p>
                </div>
                """, unsafe_allow_html=True)
                
                # زر الاتصال السريع عبر واتساب
                raw_phone = str(row.iloc[1])
                clean_phone = re.sub(r'\D', '', raw_phone)
                st.link_button(f"تواصل مع {row.iloc[0]} عبر واتساب 💬", f"https://wa.me/{clean_phone}", use_container_width=True)
                st.markdown("<hr style='border: 0.5px solid #222;'>", unsafe_allow_html=True)
    else:
        st.info("لا توجد طلبات مسجلة في الجدول حتى الآن.")
except Exception as e:
    st.error("فشل في جلب البيانات من جوجل شيت.")
    st.info("تأكد من أن الجدول (الخاص بالطلبات) مضبوط على: 'أي شخص لديه الرابط يمكنه العرض' (Anyone with link can view).")
    
