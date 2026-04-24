import streamlit as st
import pandas as pd
from datetime import datetime
import requests
import re
from io import StringIO

# 1. إعدادات الصفحة
st.set_page_config(page_title="Matrix Pro | عقارات البياع", layout="wide")

# --- 🛠️ الإعدادات (بياناتك كاملة) ---
OFFICE_NAME = "عقارات البياع" 
ADMIN_PWD = "123456246SsS@" 
MY_SHEET_ID = "1a9MO2P78L7XBggmlkYKYfjnslAAyvGxOeffnv1LT_ac" 
WEBHOOK_URL = "https://eomfdq8l221q30q.m.pipedream.net"
DATA_CSV_URL = f"https://docs.google.com/spreadsheets/d/{MY_SHEET_ID}/export?format=csv"

# التحقق من نوع الواجهة
is_client = st.query_params.get("view") == "client"

# --- 📊 دالة الترتيب الذكي (وحدت لك منطق الميزانية) ---
def get_unified_budget(v):
    try:
        if pd.isna(v): return 0
        v_str = str(v).lower()
        nums = re.findall(r'\d+', v_str)
        if not nums: return 0
        n = int(nums[0])
        if any(x in v_str for x in ['$', 'دولار', 'دفتر', 'ورقة']):
            return n * 1500000 
        return n
    except: return 0

# --- 📱 أولاً: واجهة الزبائن (مع البالونات واسم المكتب) ---
if is_client:
    if "submitted" not in st.session_state: st.session_state.submitted = False

    if not st.session_state.submitted:
        st.markdown(f"<h1 style='text-align: center; color: #d4af37;'>🏢 {OFFICE_NAME}</h1>", unsafe_allow_html=True)
        with st.form("client_form", clear_on_submit=True):
            st.markdown("### سجل طلبك العقاري")
            name = st.text_input("الاسم الكامل")
            phone = st.text_input("رقم الهاتف (واتساب)")
            region = st.selectbox("المنطقة المطلوبة", ["البياع", "شهداء البياع", "السيدية", "أخرى"])
            budget = st.text_input("الميزانية التقريبية")
            details = st.text_area("تفاصيل العقار")
            if st.form_submit_button("إرسال الطلب الآن 🚀"):
                if name and phone:
                    requests.post(WEBHOOK_URL, params={"name":name, "phone":phone, "region":region, "budget":budget, "details":details, "source":OFFICE_NAME})
                    st.session_state.submitted = True
                    st.rerun()
                else: st.warning("يرجى ملء البيانات.")
    else:
        st.balloons()
        st.markdown(f"""
            <div style='text-align: center; padding: 40px; background-color: #1a1c24; border: 2px solid #d4af37; border-radius: 20px;'>
                <h1 style='color: #d4af37;'>✅ تم الإرسال بنجاح!</h1>
                <p style='color: white;'>شكراً لثقتكم بمكتب <b>{OFFICE_NAME}</b>.</p>
                <p style='color: #666; font-size: 0.8em; margin-top: 20px;'>تم التطوير بواسطة المبرمج سجاد</p>
            </div>
        """, unsafe_allow_html=True)
        if st.button("إرسال طلب جديد"):
            st.session_state.submitted = False
            st.rerun()
    st.stop()

# --- 🔒 ثانياً: واجهة الإدارة (مع اسم المكتب والترتيب) ---
if "auth" not in st.session_state: st.session_state.auth = False

if not st.session_state.auth:
    st.markdown(f"<h2 style='text-align: center; color: #d4af37;'>🔒 دخول إدارة {OFFICE_NAME}</h2>", unsafe_allow_html=True)
    col_a, col_b, col_c = st.columns([1,2,1])
    with col_b:
        pwd = st.text_input("الرمز السري:", type="password")
        if st.button("تسجيل الدخول", use_container_width=True):
            if pwd == ADMIN_PWD:
                st.session_state.auth = True
                st.rerun()
            else: st.error("الرمز السري خطأ!")
    st.stop()

# --- عرض سجل الطلبات للإدارة ---
st.markdown(f"<h2 style='color: #d4af37;'>📊 سجل طلبات {OFFICE_NAME}</h2>", unsafe_allow_html=True)

try:
    # جلب البيانات مع ضمان ترميز العربي
    resp = requests.get(f"{DATA_CSV_URL}&cb={datetime.now().timestamp()}", timeout=15)
    resp.encoding = 'utf-8'
    df = pd.read_csv(StringIO(resp.text))
    df.columns = [c.strip() for c in df.columns]

    if not df.empty:
        # نظام الترتيب: الأحدث ثم الأعلى ميزانية
        df['sort_t'] = pd.to_datetime(df['Submission_Date'], dayfirst=True, errors='coerce')
        df['sort_b'] = df['Budget_Range'].apply(get_unified_budget)
        df = df.sort_values(by=['sort_t', 'sort_b'], ascending=[False, False])

        for _, row in df.iterrows():
            st.markdown(f"""
            <div style="background-color: #1a1c24; border-radius: 15px; padding: 20px; border-right: 5px solid #d4af37; margin-bottom: 20px; direction: rtl; text-align: right;">
                <div style="display: flex; justify-content: space-between;">
                    <h3 style="color: white; margin: 0;">👤 {row.get('Customer_Name', 'N/A')}</h3>
                    <span style="background-color: #d4af37; color: black; padding: 2px 10px; border-radius: 10px; font-weight: bold; font-size: 0.8em;">{row.get('Lead_Quality', 'N/A')}</span>
                </div>
                <p style="color: #888; font-size: 0.8em; margin: 5px 0;">📅 {row.get('Submission_Date', '')}</p>
                <hr style="border: 0.1px solid #333;">
                <p style="color: #2ecc71;"><b>💰 الميزانية:</b> {row.get('Budget_Range', '')}</p>
                <p style="color: #3498db;"><b>📍 المنطقة:</b> {row.get('Target_Region', '')}</p>
                <div style="background-color: #252833; padding: 12px; border-radius: 8px; margin-top: 10px;">
                    <p style="color: #ecf0f1; font-size: 0.95em;"><b>🤖 التحليل:</b><br>{row.get('Ai_Analysis', '')}</p>
                </div>
            </div>
            """, unsafe_allow_html=True)
            p = re.sub(r'\D', '', str(row.get('Phone_Number', '')))
            st.link_button(f"تواصل واتساب مباشر 💬", f"https://wa.me/{p}", use_container_width=True)
            st.markdown("<br>", unsafe_allow_html=True)
    else: st.info("الجدول فارغ حالياً.")
except Exception as e: st.error(f"حدث خطأ: {e}")
    
