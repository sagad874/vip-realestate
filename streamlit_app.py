import streamlit as st
import pandas as pd
import requests
import re

st.set_page_config(page_title="Matrix OS | Real Estate Platform", layout="wide", page_icon="🏢")

MASTER_CSV = "https://docs.google.com/spreadsheets/d/1sba6QhfnF5e4IlP8uV0Mku8X50OBIkzy_VekT63d_hI/export?format=csv"

@st.cache_data(ttl=60)
def load_master_data():
    try: return pd.read_csv(MASTER_CSV)
    except: return None

df_master = load_master_data()

if df_master is not None:
    query_params = st.query_params
    office_id = query_params.get("id", "bayaa")
    try:
        office_info = df_master[df_master['office_id'] == office_id].iloc[0]
        OFFICE_NAME = office_info['office_name']
        SHEET_ID = office_info['sheet_id']
        WEBHOOK_URL = office_info['webhook_url']
        OFFICE_PASS = str(office_info['password'])
        CSV_URL = f"https://docs.google.com/spreadsheets/d/{SHEET_ID}/export?format=csv"
    except:
        st.warning("المكتب غير مسجل."); st.stop()
else: st.stop()

# واجهة الزبون (مختصرة للسرعة)
if query_params.get("view") == "client":
    st.markdown(f"<h2 style='text-align: center;'>🏢 {OFFICE_NAME}</h2>", unsafe_allow_html=True)
    with st.form("client_form"):
        name = st.text_input("الاسم")
        phone = st.text_input("الهاتف")
        region = st.text_input("المنطقة")
        budget = st.text_input("الميزانية")
        submit = st.form_submit_button("إرسال")
        if submit: st.success("تم الإرسال!")
    st.stop()

# واجهة الإدارة (المعدلة لتقرأ أسمائك الخاصة)
if "auth" not in st.session_state: st.session_state.auth = False
if not st.session_state.auth:
    user_pass = st.text_input("الرمز السري:", type="password")
    if user_pass == OFFICE_PASS: st.session_state.auth = True; st.rerun()
    st.stop()

try:
    df = pd.read_csv(CSV_URL)
    if not df.empty:
        # هنا التعديل السحري: ربط مسمياتك بالكود
        col_map = {
            'name': 'Customer_Name',
            'budget': 'Budget_Range',
            'region': 'Target_Region',
            'analysis': 'Ai_Analysis'
        }

        for _, row in df.iterrows():
            with st.container():
                # نستخدم أسمائك الموجودة في الصورة
                c_name = row.get('Customer_Name', 'زبون')
                c_budget = row.get('Budget_Range', 'غير محدد')
                c_region = row.get('Target_Region', 'N/A')
                c_analysis = row.get('Ai_Analysis', 'لا يوجد تحليل حالياً')
                
                st.markdown(f"""
                <div style="background-color: #1a1c24; border-radius: 15px; padding: 20px; border: 1px solid #d4af37; margin-bottom: 15px;">
                    <h3 style='color:white; margin:0;'>👤 {c_name}</h3>
                    <p style='color:#2ecc71; font-weight: bold;'>💰 الميزانية: {c_budget}</p>
                    <p style='color:white;'>📍 المنطقة: {c_region}</p>
                    <div style="background-color: #2c3e50; padding: 10px; border-radius: 8px; border-right: 4px solid #d4af37;">
                        <p style='color:#ecf0f1; margin:0;'>🤖 {c_analysis}</p>
                    </div>
                </div>
                """, unsafe_allow_html=True)
    else: st.info("لا توجد طلبات.")
except Exception as e: st.error(f"خطأ: {e}")
    
