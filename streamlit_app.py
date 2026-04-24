import streamlit as st
import pandas as pd
from datetime import datetime
import requests
import re
from io import StringIO

# 1. إعدادات الصفحة واللغة
st.set_page_config(page_title="عقارات البياع | Pro Data Matrix", layout="wide")

# --- 🛠️ الإعدادات الثابتة ---
OFFICE_NAME = "عقارات البياع" 
ADMIN_PWD = "123456246SsS@" 
SHEET_ID = "1a9MO2P78L7XBggmlkYKYfjnslAAyvGxOeffnv1LT_ac" 
WEBHOOK_URL = "https://eomfdq8l221q30q.m.pipedream.net"
CSV_URL = f"https://docs.google.com/spreadsheets/d/{SHEET_ID}/export?format=csv"

# التحقق من نوع الواجهة
query_params = st.query_params
is_client = query_params.get("view") == "client"

# --- 📊 دالة الترتيب الذكي للميزانية ---
def get_unified_budget(v):
    try:
        if pd.isna(v): return 0
        v_str = str(v).lower()
        nums = re.findall(r'\d+', v_str)
        if not nums: return 0
        n = int(nums[0])
        if any(x in v_str for x in ['$', 'دولار', 'دفتر', 'ورقة', 'شدة']):
            return n * 1500000 
        return n
    except: return 0

# --- 📱 واجهة الزبائن ---
if is_client:
    if "submitted" not in st.session_state: st.session_state.submitted = False
    if not st.session_state.submitted:
        st.markdown(f"<h1 style='text-align: center; color: #d4af37;'>🏢 {OFFICE_NAME}</h1>", unsafe_allow_html=True)
        with st.form("client_form", clear_on_submit=True):
            st.markdown("### سجل طلبك العقاري")
            name = st.text_input("الأسم الكامل")
            phone = st.text_input("رقم الهاتف (واتساب)")
            region = st.selectbox("المنطقة المطلوبة", ["البياع", "شهداء البياع", "السيدية", "أخرى"])
            budget = st.text_input("الميزانية التقريبية")
            details = st.text_area("تفاصيل العقار")
            if st.form_submit_button("إرسال الطلب الآن 🚀"):
                if name and phone:
                    requests.post(WEBHOOK_URL, params={"name":name,"phone":phone,"region":region,"budget":budget,"details":details,"source":OFFICE_NAME}, timeout=5)
                    st.session_state.submitted = True; st.rerun()
                else: st.warning("يرجى ملء الاسم ورقم الهاتف.")
    else:
        st.balloons()
        st.markdown(f"<div style='text-align: center; padding: 40px; background-color: #1a1c24; border: 2px solid #d4af37; border-radius: 20px;'><h1 style='color: #d4af37;'>✅ تم الإرسال!</h1><p>شكراً لثقتكم بمكتب <b>{OFFICE_NAME}</b>.</p></div>", unsafe_allow_html=True)
        if st.button("إرسال طلب جديد"): st.session_state.submitted = False; st.rerun()
    st.stop()

# --- 🔒 واجهة الإدارة ---
if "auth" not in st.session_state: st.session_state.auth = False
if not st.session_state.auth:
    st.markdown(f"<h2 style='text-align: center; color: #d4af37;'>🔒 دخول إدارة {OFFICE_NAME}</h2>", unsafe_allow_html=True)
    if st.text_input("أدخل الرمز السري:", type="password") == ADMIN_PWD:
        st.session_state.auth = True; st.rerun()
    st.stop()

st.markdown(f"<h2 style='color: #d4af37;'>📊 سجل طلبات {OFFICE_NAME}</h2>", unsafe_allow_html=True)

try:
    resp = requests.get(f"{CSV_URL}&cb={datetime.now().timestamp()}", timeout=15)
    resp.encoding = 'utf-8' 
    df = pd.read_csv(StringIO(resp.text))
    df.columns = [c.strip() for c in df.columns]

    if not df.empty:
        df['sort_t'] = pd.to_datetime(df['Submission_Date'], dayfirst=True, errors='coerce')
        df['sort_b'] = df['Budget_Range'].apply(get_unified_budget)
        df = df.sort_values(by=['sort_t', 'sort_b'], ascending=[False, False])

        for idx, row in df.iterrows():
            st.markdown(f"""
            <div style="background-color: #1a1c24; border-radius: 15px; padding: 20px; border-right: 5px solid #d4af37; margin-bottom: 10px; direction: rtl; text-align: right;">
                <div style="display: flex; justify-content: space-between; align-items: center;">
                    <h3 style="color: white; margin: 0;">👤 {row.get('Customer_Name', 'N/A')}</h3>
                    <span style="background-color: #d4af37; color: black; padding: 2px 12px; border-radius: 10px; font-weight: bold;">{row.get('Lead_Quality', 'N/A')}</span>
                </div>
                <p style="color: #888; font-size: 0.85em;">📅 التاريخ: {row.get('Submission_Date', '')}</p>
                <p style="color: #2ecc71;"><b>💰 الميزانية:</b> {row.get('Budget_Range', '')}</p>
                <p style="color: #3498db;"><b>📍 المنطقة:</b> {row.get('Target_Region', '')}</p>
                <div style="background-color: #252833; padding: 12px; border-radius: 8px; margin-top: 10px; border: 1px solid #333;">
                    <p style="color: #ecf0f1; font-size: 0.95em;"><b>🤖 التحليل:</b> {row.get('Ai_Analysis', '')}</p>
                </div>
            </div>
            """, unsafe_allow_html=True)
            
            # --- أزرار الاتصال (واتساب + اتصال هاتفي) ---
            phone_val = str(row.get('Phone_Number', ''))
            p_clean = re.sub(r'\D', '', phone_val)
            
            col1, col2 = st.columns(2)
            with col1:
                st.link_button(f"💬 واتساب", f"https://wa.me/{p_clean}", use_container_width=True)
            with col2:
                # زر الاتصال المباشر
                st.link_button(f"📞 اتصال هاتفي", f"tel:{p_clean}", use_container_width=True)
            st.markdown("<br>", unsafe_allow_html=True)
    else: st.info("لا توجد بيانات.")
except Exception as e: st.error(f"خطأ: {e}")
    
