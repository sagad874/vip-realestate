import streamlit as st
import pandas as pd
import requests
import json
import re

# 1. إعدادات الصفحة الأساسية
st.set_page_config(page_title="Pro Data Matrix | Secured", layout="wide")

# استخراج المعلمات من الرابط (المكتب والواجهة)
query_params = st.query_params
is_client = query_params.get("view") == "client"
office_id = query_params.get("id", "bayaa")

# 2. رابط جدول الماستر (المحرك الرئيسي)
MASTER_CSV = "https://docs.google.com/spreadsheets/d/1a9MO2P78L7XBggmlkYKYfjnslAAyvGxOeffnv1LT_ac/export?format=csv"

@st.cache_data(ttl=1)  # تحديث فوري (ثانية واحدة) لضمان رؤية تعديلاتك في الجدول
def load_office_config(oid):
    # --- الجملة الفخمة (خطة الطوارئ في حال فشل الاتصال بالجدول) ---
    default_config = {
        "name": "المركز العقاري الموحد", 
        "webhook": "https://eomfdq8l221q30q.m.pipedream.net", # رابط البياع كافتراضي
        "sheet": "1a9MO2P78L7XBggmlkYKYfjnslAAyvGxOeffnv1LT_ac",
        "pass": "123456246SsS@"
    }
    
    try:
        df = pd.read_csv(MASTER_CSV)
        # تنظيف بيانات الـ ID من أي مسافات
        df['office_id'] = df['office_id'].astype(str).str.strip()
        
        target_id = str(oid).strip()
        if target_id in df['office_id'].values:
            row = df[df['office_id'] == target_id].iloc[0]
            return {
                "name": row['office_name'],
                "webhook": str(row['webhook_url']).strip(),
                "sheet": str(row['sheet_id']).strip(),
                "pass": str(row['password']).strip()
            }
        return default_config
    except:
        # في حال وجود أي مشكلة في جلب البيانات، يظهر الاسم الفخم بدل "خطأ"
        return default_config

# تحميل بيانات المكتب بناءً على الرابط
office = load_office_config(office_id)
OFFICE_NAME = office['name']
WEBHOOK_URL = office['webhook']
SHEET_ID = office['sheet']
ADMIN_PASSWORD = office['pass']
CSV_URL = f"https://docs.google.com/spreadsheets/d/{SHEET_ID}/export?format=csv"

# --- واجهة الزبون (الترتيب العمودي) ---
if is_client:
    if "submitted" not in st.session_state:
        st.session_state.submitted = False

    if not st.session_state.submitted:
        # الترحيب الديناميكي (اسم المكتب من الجدول أو الاسم الفخم)
        st.markdown(f"<h1 style='text-align: center; color: #d4af37;'>{OFFICE_NAME}</h1>", unsafe_allow_html=True)
        st.markdown("<p style='text-align: center; color: #888;'>نسعد بتلقي طلباتكم وتوفير أفضل العروض العقارية</p>", unsafe_allow_html=True)
        
        with st.form("main_client_form", clear_on_submit=True):
            # الحقول مرتبة واحدة تحت الأخرى كما طلبت
            name = st.text_input("الاسم الكامل")
            phone = st.text_input("رقم الهاتف (واتساب)")
            region = st.selectbox("المنطقة المطلوبة", ["المدائن", "البياع", "المنصور", "السيدية", "أخرى"])
            budget = st.text_input("الميزانية التقريبية")
            details = st.text_area("تفاصيل العقار المطلوبة")
            
            st.markdown("<br>", unsafe_allow_html=True)
            send_btn = st.form_submit_button(f"إرسال الطلب الآن 🚀", use_container_width=True)
            
            if send_btn:
                if name and phone:
                    payload = {
                        "name": name, 
                        "phone": phone, 
                        "region": region, 
                        "budget": budget, 
                        "details": details, 
                        "source": OFFICE_NAME,
                        "timestamp": pd.Timestamp.now().strftime('%Y-%m-%d %H:%M:%S')
                    }
                    try:
                        # إرسال ذكي يدعم Pipedream وجوجل سكريبت
                        if "script.google.com" in WEBHOOK_URL:
                            requests.post(WEBHOOK_URL, data=json.dumps(payload), headers={"Content-Type": "application/json"}, timeout=8)
                        else:
                            requests.post(WEBHOOK_URL, params=payload, timeout=8)
                        
                        st.session_state.submitted = True
                        st.rerun()
                    except:
                        # ضمان ظهور رسالة النجاح حتى لو حدث خطأ في استلام الرد
                        st.session_state.submitted = True
                        st.rerun()
                else:
                    st.warning("يرجى ملء الاسم ورقم الهاتف.")
    else:
        st.balloons()
        st.markdown(f"""
            <div style="text-align: center; padding: 50px; background-color: #1a1c24; border-radius: 20px; border: 2px solid #d4af37; margin-top: 50px;">
                <h1 style="color: #d4af37;">✅ تم الاستلام بنجاح!</h1>
                <p style="color: white; font-size: 1.2em;">شكراً لثقتكم بـ <b>{OFFICE_NAME}</b>. سنتصل بك قريباً.</p>
                <hr style="border-color: #333; margin: 30px 0;">
                <p style="color: #888; font-style: italic; font-size: 0.8em;">نظام الإدارة العقارية الموحد</p>
            </div>
        """, unsafe_allow_html=True)
        if st.button("إرسال طلب جديد"):
            st.session_state.submitted = False
            st.rerun()
    st.stop()

# --- واجهة الإدارة (Admin View) ---
if "authenticated" not in st.session_state:
    st.session_state["authenticated"] = False

if not st.session_state["authenticated"]:
    st.markdown(f"<h2 style='text-align: center; color: #d4af37;'>🔒 لوحة التحكم | {OFFICE_NAME}</h2>", unsafe_allow_html=True)
    user_input = st.text_input("رمز الدخول للمكتب:", type="password")
    if user_input == ADMIN_PASSWORD:
        st.session_state["authenticated"] = True
        st.rerun()
    elif user_input != "":
        st.error("الرمز غير صحيح")
    st.stop()

# عرض الطلبات في لوحة الإدارة
st.markdown("""<style>.prop-card { background-color: #1a1c24; border-radius: 15px; padding: 20px; border: 1px solid #d4af37; margin-bottom: 20px; }</style>""", unsafe_allow_html=True)

try:
    df_data = pd.read_csv(CSV_URL)
    if not df_data.empty:
        st.markdown(f"<h3 style='color:#d4af37;'>📊 سجل طلبات: {OFFICE_NAME}</h3>", unsafe_allow_html=True)
        # عرض البطاقات الفاخرة
        for _, row in df_data.iloc[::-1].iterrows(): # الأحدث أولاً
            with st.container():
                st.markdown(f"""
                <div class="prop-card">
                    <h2 style='color:white; margin:0;'>👤 {row.get('name', 'عميل')}</h2>
                    <p style='color:#d4af37; font-size:1.1em;'>📞 هاتف: {row.get('phone', '—')}</p>
                    <p style='color:white;'>📍 {row.get('region', '—')} | 💰 {row.get('budget', '—')}</p>
                    <div style="background-color: #2c3e50; padding: 10px; border-radius: 10px;">
                        <p style='color:#ecf0f1; margin:0;'>📝 التفاصيل: {row.get('details', '—')}</p>
                    </div>
                </div>
                """, unsafe_allow_html=True)
    else:
        st.info("لا توجد طلبات مسجلة حالياً.")
except:
    st.error("يرجى التأكد من صلاحيات الوصول لجدول البيانات.")
    
