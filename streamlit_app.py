import streamlit as st
import pandas as pd
import requests
import re

# 1. إعدادات المنصة الاحترافية
st.set_page_config(page_title="Matrix OS | Real Estate Platform", layout="wide", page_icon="🏢")

# --- رابط جدول الإدارة السري الخاص بك (تم تحديثه) ---
MASTER_CSV = "https://docs.google.com/spreadsheets/d/1sba6QhfnF5e4IlP8uV0Mku8X50OBIkzy_VekT63d_hI/export?format=csv"

@st.cache_data(ttl=60)
def load_master_data():
    try:
        return pd.read_csv(MASTER_CSV)
    except Exception as e:
        st.error(f"⚠️ خطأ في الاتصال بجدول الإدارة السري. تأكد من إعدادات المشاركة.")
        return None

# جلب بيانات المكاتب
df_master = load_master_data()

if df_master is not None:
    # الحصول على معرف المكتب من الرابط (مثلاً ?id=bayaa)
    query_params = st.query_params
    office_id = query_params.get("id", "bayaa") # الافتراضي هو البياع
    
    try:
        # البحث عن بيانات المكتب في جدولك السري
        office_info = df_master[df_master['office_id'] == office_id].iloc[0]
        OFFICE_NAME = office_info['office_name']
        SHEET_ID = office_info['sheet_id']
        WEBHOOK_URL = office_info['webhook_url']
        OFFICE_PASS = str(office_info['password'])
        
        CSV_URL = f"https://docs.google.com/spreadsheets/d/{SHEET_ID}/export?format=csv"
    except:
        st.warning(f"⚠️ المعرف '{office_id}' غير مسجل في النظام.")
        st.stop()
else:
    st.stop()

# --- دالة تحليل الميزانية الذكية ---
def analyze_budget(budget_str, details):
    try:
        nums = re.findall(r'\d+', str(budget_str))
        num = int(nums[0]) if nums else 0
        is_usd = any(x in str(budget_str).lower() for x in ['$', 'usd', 'دولار'])
        val = num * 1500 if is_usd else num
        
        if val < 50: analysis = "⚠️ ميزانية محدودة."
        elif val <= 150: analysis = "🏠 ميزانية متوسطة."
        elif val <= 450: analysis = "✅ ميزانية جيدة جداً."
        else: analysis = "💎 ميزانية VIP."
        return f"{analysis} | {details}" if details else analysis
    except: return "تحليل تلقائي"

# --- تحديد نوع الواجهة ---
is_client = query_params.get("view") == "client"

# --- واجهة الزبون ---
if is_client:
    if "submitted" not in st.session_state: st.session_state.submitted = False

    if not st.session_state.submitted:
        st.markdown(f"<h2 style='text-align: center; color: #d4af37;'>🏢 {OFFICE_NAME}</h2>", unsafe_allow_html=True)
        with st.form("client_form", clear_on_submit=True):
            name = st.text_input("الاسم الكامل")
            phone = st.text_input("رقم الهاتف (واتساب)")
            region = st.selectbox("المنطقة المطلوبة", ["شهداء البياع", "المنصور", "حي الجامعة", "السيدية", "أخرى"])
            budget = st.text_input("الميزانية (مثلاً: 200 مليون أو 100 ألف دولار)")
            details = st.text_area("تفاصيل إضافية")
            submit = st.form_submit_button("إرسال الطلب الآن 🚀")

            if submit:
                if name and phone:
                    analysis_text = analyze_budget(budget, details)
                    payload = {
                        "name": name, "phone": phone, "region": region,
                        "budget": budget, "details": details, "analysis": analysis_text
                    }
                    try:
                        # دعم تلقائي لنوع الرابط (Pipedream أو Google Apps Script)
                        if "script.google" in WEBHOOK_URL:
                            res = requests.post(WEBHOOK_URL, data=payload)
                        else:
                            res = requests.post(WEBHOOK_URL, params=payload)
                        
                        if res.status_code == 200:
                            st.session_state.submitted = True
                            st.rerun()
                        else: st.error("فشل في الإرسال.")
                    except: st.error("خطأ في الاتصال بالسيرفر.")
                else: st.warning("يرجى ملء الحقول الأساسية.")
    else:
        st.balloons()
        st.markdown(f"<div style='text-align: center; padding: 50px;'><h2>✅ تم الاستلام!</h2><p>شكراً لثقتك بـ {OFFICE_NAME}</p></div>", unsafe_allow_html=True)
        if st.button("تقديم طلب آخر"):
            st.session_state.submitted = False
            st.rerun()
    st.stop()

# --- واجهة الإدارة ---
else:
    if "auth" not in st.session_state: st.session_state.auth = False

    if not st.session_state.auth:
        st.markdown(f"<h2 style='text-align: center; color: #d4af37;'>🔒 لوحة تحكم {OFFICE_NAME}</h2>", unsafe_allow_html=True)
        user_pass = st.text_input("رمز الوصول:", type="password")
        if user_pass == OFFICE_PASS:
            st.session_state.auth = True
            st.rerun()
        st.stop()

    st.markdown(f"<h2 style='color:#d4af37;'>📊 سجل طلبات {OFFICE_NAME}</h2>", unsafe_allow_html=True)
    
    try:
        df = pd.read_csv(CSV_URL)
        if not df.empty:
            def find_col(keys):
                for c in df.columns:
                    if any(k.lower() in str(c).lower() for k in keys): return c
                return df.columns[0]

            c_budget = find_col(['budget', 'ميزانية', 'سعر'])
            c_time = find_col(['time', 'date', 'تاريخ'])

            def get_val(v):
                try:
                    nums = re.findall(r'\d+', str(v))
                    n = int(nums[0]) if nums else 0
                    return n * 1500 if any(x in str(v).lower() for x in ['$', 'usd', 'دولار']) else n
                except: return 0

            df['sort_t'] = pd.to_datetime(df[c_time], dayfirst=True, errors='coerce')
            df['sort_b'] = df[c_budget].apply(get_val)
            df = df.sort_values(by=['sort_t', 'sort_b'], ascending=[False, False])

            for _, row in df.iterrows():
                with st.container():
                    st.markdown(f"""
                    <div style="background-color: #1a1c24; border-radius: 15px; padding: 20px; border: 1px solid #d4af37; margin-bottom: 15px;">
                        <div style="display: flex; justify-content: space-between;">
                            <h3 style='color:white; margin:0;'>👤 {row.get('name', 'زبون')}</h3>
                            <span style="color: #888;">📅 {row.get(c_time, 'N/A')}</span>
                        </div>
                        <p style='color:#2ecc71; font-weight: bold;'>💰 الميزانية: {row.get(c_budget, 'N/A')}</p>
                        <p style='color:white;'>📍 المنطقة: {row.get('region', 'N/A')}</p>
                        <div style="background-color: #2c3e50; padding: 10px; border-radius: 8px; border-right: 4px solid #d4af37;">
                            <p style='color:#ecf0f1; margin:0;'>🤖 {row.get('analysis', 'لا يوجد تحليل')}</p>
                        </div>
                    </div>
                    """, unsafe_allow_html=True)
                    p_num = re.sub(r'\D', '', str(row.get('phone', '')))
                    st.link_button(f"تواصل عبر واتساب 💬", f"https://wa.me/{p_num}", use_container_width=True)
        else:
            st.info("لا توجد طلبات مسجلة.")
    except Exception as e:
        st.error(f"خطأ في البيانات: {e}")
        
