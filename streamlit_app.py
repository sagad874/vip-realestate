import streamlit as st
import pandas as pd
from datetime import datetime
import requests
import re

# 1. إعدادات الصفحة
st.set_page_config(page_title="Matrix System | Multi-Office", layout="wide")

# --- ميكانيكية "تصفير السيرفر" القسرية ---
# قراءة الرابط مباشرة
current_params = st.query_params
active_id = current_params.get("id", "bayaa")

# إذا لاحظ الكود أي تغيير في الـ ID، يمسح الذاكرة بالكامل فوراً
if "session_id_tracker" not in st.session_state:
    st.session_state.session_id_tracker = active_id

if st.session_state.session_id_tracker != active_id:
    for key in st.session_state.keys():
        del st.session_state[key]
    st.cache_data.clear()
    st.session_state.session_id_tracker = active_id
    st.rerun()

# 2. جلب الإعدادات من جدول الماستر (مع كسر الكاش)
MASTER_CSV = "https://docs.google.com/spreadsheets/d/1a9MO2P78L7XBggmlkYKYfjnslAAyvGxOeffnv1LT_ac/export?format=csv"

@st.cache_data(ttl=0) # تصفير الوقت تماماً لضمان عدم التخزين
def get_config(oid):
    try:
        # إضافة ختم زمني للرابط لضمان جلب بيانات جديدة من جوجل
        df = pd.read_csv(f"{MASTER_CSV}?cb={datetime.now().timestamp()}")
        df['office_id'] = df['office_id'].astype(str).str.strip()
        
        row = df[df['office_id'] == str(oid).strip()]
        if not row.empty:
            res = row.iloc[0]
            return {
                "name": res['office_name'],
                "webhook": str(res['webhook_url']).strip(),
                "sheet": str(res['sheet_id']).strip(),
                "pass": str(res['password']).strip()
            }
    except: pass
    return {"name": "المركز العقاري الموحد", "webhook": "https://eomfdq8l221q30q.m.pipedream.net", "sheet": "1a9MO2P78L7XBggmlkYKYfjnslAAyvGxOeffnv1LT_ac", "pass": "123456246SsS@"}

# تفعيل الإعدادات
cfg = get_config(active_id)
OFFICE_NAME = cfg['name']
WEBHOOK_URL = cfg['webhook']
SHEET_ID = cfg['sheet']
ADMIN_PWD = cfg['pass']
DATA_CSV = f"https://docs.google.com/spreadsheets/d/{SHEET_ID}/export?format=csv"

# --- واجهة الزبون ---
if current_params.get("view") == "client":
    if "is_done" not in st.session_state: st.session_state.is_done = False
    
    if not st.session_state.is_done:
        st.markdown(f"<h1 style='text-align:center; color:#d4af37;'>🏢 {OFFICE_NAME}</h1>", unsafe_allow_html=True)
        with st.form("main_form", clear_on_submit=True):
            name = st.text_input("الاسم الكامل")
            phone = st.text_input("رقم الهاتف")
            regions = ["شهداء البياع", "البياع", "المنصور", "حي الجامعة", "السيدية", "أخرى"]
            area = st.selectbox("المنطقة", regions)
            budget = st.text_input("الميزانية")
            msg = st.text_area("التفاصيل")
            
            if st.form_submit_button(f"إرسال الطلب إلى {OFFICE_NAME} 🚀"):
                if name and phone:
                    payload = {"name": name, "phone": phone, "region": area, "budget": budget, "details": msg, "source": OFFICE_NAME}
                    requests.post(WEBHOOK_URL, params=payload, timeout=5)
                    st.session_state.is_done = True
                    st.rerun()
                else: st.warning("املأ البيانات الأساسية")
    else:
        st.balloons()
        st.markdown(f"<div style='text-align:center; padding:40px; border:2px solid #d4af37; border-radius:20px;'><h2>✅ تم الاستلام!</h2><p>شكراً لثقتكم بـ {OFFICE_NAME}</p><hr><p>المبرمج سجاد</p></div>", unsafe_allow_html=True)
        if st.button("إرسال طلب جديد"):
            st.session_state.is_done = False
            st.rerun()
    st.stop()

# --- واجهة الإدارة ---
if "is_auth" not in st.session_state: st.session_state.is_auth = False
if not st.session_state.is_auth:
    st.markdown(f"<h2 style='text-align:center;'>🔒 لوحة {OFFICE_NAME}</h2>", unsafe_allow_html=True)
    if st.text_input("رمز الدخول:", type="password") == ADMIN_PWD:
        st.session_state.is_auth = True
        st.rerun()
    st.stop()

# عرض البيانات
try:
    df_leads = pd.read_csv(f"{DATA_CSV}?cb={datetime.now().timestamp()}")
    st.markdown(f"<h3 style='color:#d4af37;'>📊 سجل: {OFFICE_NAME}</h3>", unsafe_allow_html=True)
    
    # البحث الذكي عن الأعمدة
    cols = df_leads.columns
    def find(lst):
        for c in cols:
            if any(x.lower() in str(c).lower() for x in lst): return c
        return cols[0]

    c_n, c_p, c_r, c_b, c_t = find(['name', 'الاسم']), find(['phone', 'هاتف']), find(['region', 'منطقة']), find(['budget', 'ميزانية']), find(['time', 'timestamp', 'التاريخ'])
    
    for _, r in df_leads.iloc[::-1].iterrows():
        st.markdown(f"""
        <div style="background:#1a1c24; padding:20px; border-radius:15px; border:1px solid #d4af37; margin-bottom:15px;">
            <div style="display:flex; justify-content:space-between;">
                <h3 style="color:white; margin:0;">👤 {r[c_n]}</h3>
                <span style="color:#888;">📅 {r[c_t]}</span>
            </div>
            <p style="color:#2ecc71; font-weight:bold; font-size:1.2em;">💰 {r[c_b]}</p>
            <p style="color:white;">📍 {r[c_r]}</p>
        </div>
        """, unsafe_allow_html=True)
        num = re.sub(r'\D', '', str(r[c_p]))
        st.link_button(f"واتساب {r[c_n]} 💬", f"https://wa.me/{num}", use_container_width=True)
except: st.error("فشل جلب البيانات")
    
