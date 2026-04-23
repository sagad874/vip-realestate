import streamlit as st
import pandas as pd
from datetime import datetime
import requests
import re
import json

# 1. إعدادات الصفحة
st.set_page_config(page_title="Pro Data Matrix | Secured", layout="wide")

# استخراج المعلمات من الرابط
query_params = st.query_params
is_client = query_params.get("view") == "client"
office_id = query_params.get("id", "bayaa")

# 2. إدارة البيانات المركزية (Master Sheet)
MASTER_SHEET_ID = "1a9MO2P78L7XBggmlkYKYfjnslAAyvGxOeffnv1LT_ac"
MASTER_CSV_URL = f"https://docs.google.com/spreadsheets/d/{MASTER_SHEET_ID}/export?format=csv"

# تعديل الـ TTL إلى 1 ثانية فقط لضمان التحديث الفوري لكل تغييراتك في الجدول
@st.cache_data(ttl=1)
def get_office_config(oid):
    try:
        m_df = pd.read_csv(MASTER_CSV_URL)
        m_df['office_id'] = m_df['office_id'].astype(str).str.strip()
        # البحث عن بيانات المكتب المفتوح حالياً
        row = m_df[m_df['office_id'] == str(oid).strip()].iloc[0]
        return {
            "sheet_id": row['sheet_id'],
            "webhook": str(row['webhook_url']).strip(),
            "name": row['office_name'],
            "pass": str(row['password'])
        }
    except:
        # بيانات افتراضية في حال وجود خطأ
        return {
            "sheet_id": "1a9MO2P78L7XBggmlkYKYfjnslAAyvGxOeffnv1LT_ac",
            "webhook": "https://eomfdq8l221q30q.m.pipedream.net",
            "name": "مكتب العقارات المتطور",
            "pass": "123456246SsS@"
        }

# تحميل بيانات المكتب النشط
config = get_office_config(office_id)
SHEET_ID = config['sheet_id']
WEBHOOK_URL = config['webhook']
OFFICE_NAME = config['name']
ADMIN_PASSWORD = config['pass']
CSV_URL = f"https://docs.google.com/spreadsheets/d/{SHEET_ID}/export?format=csv"

# --- واجهة الزبون ---
if is_client:
    if "submitted" not in st.session_state:
        st.session_state.submitted = False

    if not st.session_state.submitted:
        # ميزة الترحيب الديناميكي باسم المكتب
        st.markdown(f"""
            <div style="text-align: center; padding: 10px;">
                <h1 style='color: #d4af37;'>مرحباً بكم في {OFFICE_NAME}</h1>
                <p style='color: #888;'>نسعد بخدمتكم، يرجى ملء التفاصيل أدناه</p>
            </div>
        """, unsafe_allow_html=True)
        
        with st.form("client_form", clear_on_submit=True):
            name = st.text_input("الاسم الكامل")
            phone = st.text_input("رقم الهاتف (واتساب)")
            region = st.selectbox("المنطقة المطلوبة", ["شهداء البياع", "المنصور", "حي الجامعة", "السيدية", "أخرى"])
            budget = st.text_input("الميزانية التقريبية")
            details = st.text_area("تفاصيل العقار المطلوب")
            
            st.markdown("<br>", unsafe_allow_html=True)
            send_btn = st.form_submit_button(f"إرسال الطلب إلى {OFFICE_NAME} 🚀", use_container_width=True)
            
            if send_btn:
                if name and phone:
                    payload = {"name": name, "phone": phone, "region": region, "budget": budget, "details": details, "source": OFFICE_NAME}
                    try:
                        if "script.google.com" in WEBHOOK_URL:
                            requests.post(WEBHOOK_URL, data=json.dumps(payload), headers={"Content-Type": "application/json"}, timeout=8)
                        else:
                            requests.post(WEBHOOK_URL, params=payload, timeout=8)
                        st.session_state.submitted = True
                        st.rerun()
                    except:
                        st.session_state.submitted = True
                        st.rerun()
                else:
                    st.warning("يرجى ملء الحقول المطلوبة")
    else:
        st.balloons()
        st.markdown(f"""
            <div style="text-align: center; padding: 50px; background-color: #1a1c24; border-radius: 20px; border: 2px solid #d4af37; margin-top: 50px;">
                <h1 style="color: #d4af37;">✅ تم الاستلام!</h1>
                <p style="color: white; font-size: 1.2em;">شكراً لثقتكم بـ <b>{OFFICE_NAME}</b>. سيتم التواصل معكم قريباً.</p>
            </div>
        """, unsafe_allow_html=True)
    st.stop()

# --- واجهة الإدارة ---
if "authenticated" not in st.session_state:
    st.session_state["authenticated"] = False

if not st.session_state["authenticated"]:
    st.markdown(f"<h2 style='text-align: center; color: #d4af37;'>🔒 دخول إدارة {OFFICE_NAME}</h2>", unsafe_allow_html=True)
    user_input = st.text_input("رمز الوصول:", type="password")
    if user_input == ADMIN_PASSWORD:
        st.session_state["authenticated"] = True
        st.rerun()
    st.stop()

# عرض البيانات في لوحة الإدارة
st.markdown("""<style>.prop-card { background-color: #1a1c24; border-radius: 15px; padding: 20px; border: 1px solid #d4af37; margin-bottom: 20px; }</style>""", unsafe_allow_html=True)

try:
    df = pd.read_csv(CSV_URL)
    if not df.empty:
        st.markdown(f"<h3 style='color:#d4af37;'>📊 سجل طلبات: {OFFICE_NAME}</h3>", unsafe_allow_html=True)
        # (كود عرض البطاقات كما هو في النسخة السابقة)
        # ...
    else:
        st.info(f"لا توجد طلبات حالياً في {OFFICE_NAME}")
except:
    st.error("فشل في تحميل البيانات.")
    
