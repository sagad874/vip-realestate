import streamlit as st
import pandas as pd
from datetime import datetime
import requests
import re
from io import StringIO

# 1. إعدادات الصفحة الأساسية
st.set_page_config(page_title="Pro Data Matrix | Master System", layout="wide")

# --- نظام كسر العناد (تصفير الجلسة عند تغيير المكتب) ---
params = st.query_params
office_id = params.get("id", "bayaa").strip().lower()

if "current_office" not in st.session_state:
    st.session_state.current_office = office_id

if st.session_state.current_office != office_id:
    # مسح شامل لكل الذاكرة المؤقتة لضمان عدم تداخل البيانات
    for key in list(st.session_state.keys()):
        del st.session_state[key]
    st.cache_data.clear()
    st.session_state.current_office = office_id
    st.rerun()

# 2. إدارة البيانات المركزية (رابط الماستر)
MASTER_CSV = "https://docs.google.com/spreadsheets/d/1a9MO2P78L7XBggmlkYKYfjnslAAyvGxOeffnv1LT_ac/export?format=csv"

@st.cache_data(ttl=0)
def load_office_config(oid):
    try:
        # كسر الكاش لضمان جلب أحدث بيانات المكاتب من جوجل
        res = requests.get(f"{MASTER_CSV}?cb={datetime.now().timestamp()}", timeout=10)
        df = pd.read_csv(StringIO(res.text))
        
        # تنظيف البيانات لضمان المطابقة
        df.columns = [c.strip().lower() for c in df.columns]
        df['office_id'] = df['office_id'].astype(str).str.strip().str.lower()
        
        target = str(oid).strip().lower()
        row = df[df['office_id'] == target]
        
        if not row.empty:
            data = row.iloc[0]
            # دالة لاستخراج الـ ID فقط حتى لو تم وضع رابط كامل في الشيت
            raw_sid = str(data.get('sheet_id', '')).strip()
            sid_match = re.search(r"/d/([a-zA-Z0-9-_]+)", raw_sid)
            final_sid = sid_match.group(1) if sid_match else raw_sid
            
            return {
                "found": True,
                "name": data.get('office_name', 'المركز العقاري'),
                "webhook": str(data.get('webhook_url', '')).strip(),
                "sheet": final_sid,
                "pass": str(data.get('password', '1234'))
            }
    except: pass
    return {"found": False}

# تحميل الإعدادات
config = load_office_config(office_id)

# فحص وجود المكتب
if not config.get("found"):
    st.error(f"⚠️ المكتب '{office_id}' غير مسجل في النظام.")
    st.info("يرجى إضافة البيانات في جدول الماستر (office_id, name, sheet_id) والتأكد من ترتيب الأعمدة.")
    st.stop()

# تعريف المتغيرات النهائية
OFFICE_NAME = config['name']
WEBHOOK_URL = config['webhook']
SHEET_ID = config['sheet']
ADMIN_PASSWORD = config['pass']
DATA_CSV_URL = f"https://docs.google.com/spreadsheets/d/{SHEET_ID}/export?format=csv"

# --- واجهة الزبون (النسخة الفخمة) ---
is_client = params.get("view") == "client"

if is_client:
    if "submitted" not in st.session_state:
        st.session_state.submitted = False

    if not st.session_state.submitted:
        st.markdown(f"<h1 style='text-align: center; color: #d4af37;'>🏢 {OFFICE_NAME}</h1>", unsafe_allow_html=True)
        st.markdown("<p style='text-align: center;'>يرجى ملء الاستمارة أدناه لطلب عقار</p>", unsafe_allow_html=True)
        
        with st.form("main_client_form", clear_on_submit=True):
            col1, col2 = st.columns(2)
            with col1:
                name = st.text_input("الاسم الكامل")
                phone = st.text_input("رقم الهاتف (واتساب)")
            with col2:
                baghdad_regions = ["شهداء البياع", "البياع", "المنصور", "حي الجامعة", "السيدية", "العامرية", "أخرى"]
                region = st.selectbox("المنطقة المطلوبة", baghdad_regions)
                budget = st.text_input("الميزانية التقريبية")
            
            details = st.text_area("تفاصيل العقار (المساحة، الغرف، إلخ)")
            
            submit_btn = st.form_submit_button(f"إرسال الطلب إلى {OFFICE_NAME} 🚀")
            
            if submit_btn:
                if name and phone:
                    payload = {"name": name, "phone": phone, "region": region, "budget": budget, "details": details, "source": OFFICE_NAME}
                    try:
                        requests.post(WEBHOOK_URL, params=payload, timeout=5)
                        st.session_state.submitted = True
                        st.rerun()
                    except:
                        st.session_state.submitted = True
                        st.rerun()
                else:
                    st.warning("الرجاء إدخال الاسم ورقم الهاتف.")
    else:
        st.balloons()
        st.markdown(f"""
            <div style="text-align: center; padding: 50px; background-color: #1a1c24; border-radius: 20px; border: 2px solid #d4af37; margin-top: 50px;">
                <h1 style="color: #d4af37;">✅ تم استلام طلبك!</h1>
                <p style="color: white; font-size: 1.2em;">شكراً لثقتكم بـ <b>{OFFICE_NAME}</b>. سيقوم فريقنا بالاتصال بك قريباً.</p>
                <hr style="border-color: #333; margin: 30px 0;">
                <p style="color: #888;">النظام العقاري الذكي - تطوير سجاد</p>
            </div>
        """, unsafe_allow_html=True)
        if st.button("إرسال طلب جديد"):
            st.session_state.submitted = False
            st.rerun()
    st.stop()

# --- واجهة الإدارة (Dashboard) ---
if "authenticated" not in st.session_state:
    st.session_state.authenticated = False

if not st.session_state.authenticated:
    st.markdown(f"<h2 style='text-align: center; color: #d4af37;'>🔒 لوحة تحكم {OFFICE_NAME}</h2>", unsafe_allow_html=True)
    pwd = st.text_input("رمز الوصول الخاص بالمكتب:", type="password")
    if st.button("دخول"):
        if pwd == ADMIN_PASSWORD:
            st.session_state.authenticated = True
            st.rerun()
        else:
            st.error("رمز الوصول غير صحيح.")
    st.stop()

# عرض البيانات للإدارة
st.markdown(f"<h2 style='color:#d4af37;'>📊 سجل طلبات {OFFICE_NAME}</h2>", unsafe_allow_html=True)

try:
    # جلب بيانات الشيت الخاص بالمكتب
    res_data = requests.get(f"{DATA_CSV_URL}&cb={datetime.now().timestamp()}", timeout=10)
    df_leads = pd.read_csv(StringIO(res_data.text))
    
    if not df_leads.empty:
        # عرض البطاقات
        for index, row in df_leads.iloc[::-1].iterrows():
            with st.container():
                st.markdown(f"""
                <div style="background-color: #1a1c24; border-radius: 15px; padding: 20px; border: 1px solid #d4af37; margin-bottom: 20px;">
                    <div style="display: flex; justify-content: space-between;">
                        <h3 style="color: white; margin: 0;">👤 {row.iloc[0]}</h3>
                        <span style="color: #888;">#{len(df_leads)-index}</span>
                    </div>
                    <p style="color: #2ecc71; font-weight: bold; font-size: 1.2em; margin: 10px 0;">💰 الميزانية: {row.iloc[3] if len(row)>3 else '—'}</p>
                    <p style="color: white;">📍 المنطقة: {row.iloc[2] if len(row)>2 else '—'}</p>
                    <div style="background-color: #2c3e50; padding: 10px; border-radius: 8px;">
                        <p style="color: #ecf0f1; font-size: 0.9em; margin: 0;">📝 التفاصيل: {row.iloc[4] if len(row)>4 else 'لا يوجد'}</p>
                    </div>
                </div>
                """, unsafe_allow_html=True)
                
                # زر الواتساب الذكي
                phone_num = re.sub(r'\D', '', str(row.iloc[1]))
                st.link_button(f"تواصل مع {row.iloc[0]} عبر واتساب 💬", f"https://wa.me/{phone_num}", use_container_width=True)
                st.markdown("<br>", unsafe_allow_html=True)
    else:
        st.info("لا توجد طلبات مسجلة حالياً.")
except Exception as e:
    st.error("فشل في جلب البيانات. تأكد من أن جدول البيانات 'Public' وأن المعرف (Sheet ID) في الماستر صحيح.")
    
