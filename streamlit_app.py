import streamlit as st
import pandas as pd
from datetime import datetime
import requests
import re
from io import StringIO

# 1. إعدادات الصفحة
st.set_page_config(page_title="Matrix Real Estate Pro", layout="wide")

# تنظيف المعرف من الرابط
params = st.query_params
office_id = params.get("id", "bayaa").strip().lower()

# 2. رابط الماستر الصحيح
NEW_MASTER_ID = "1sba6QhfnF5e4IlP8uV0Mku8X50OBIkzy_VekT63d_hI"
MASTER_CSV_URL = f"https://docs.google.com/spreadsheets/d/{NEW_MASTER_ID}/export?format=csv&gid=0"

@st.cache_data(ttl=0)
def load_config(oid):
    try:
        headers = {'Cache-Control': 'no-cache', 'Pragma': 'no-cache'}
        response = requests.get(f"{MASTER_CSV_URL}&cb={datetime.now().timestamp()}", headers=headers, timeout=15)
        
        if response.status_code != 200:
            return {"found": False, "err": f"خطأ اتصال (Error {response.status_code})"}
        
        df = pd.read_csv(StringIO(response.text))
        df.columns = [str(c).strip().lower() for c in df.columns]
        
        if 'office_id' not in df.columns:
            return {"found": False, "err": "لم يتم العثور على عمود office_id."}

        df['office_id'] = df['office_id'].astype(str).str.strip().str.lower()
        row = df[df['office_id'] == oid]
        
        if not row.empty:
            res = row.iloc[0]
            raw_sid = str(res.get('sheet_id', '')).strip()
            sid_match = re.search(r"/d/([a-zA-Z0-9-_]+)", raw_sid)
            final_sid = sid_match.group(1) if sid_match else raw_sid
            
            return {
                "found": True,
                "name": res.get('office_name', 'مكتب غير مسمى'),
                "webhook": str(res.get('webhook_url', '')).strip(),
                "sheet": final_sid,
                "pass": str(res.get('password', '1234'))
            }
    except Exception as e:
        return {"found": False, "err": str(e)}
    return {"found": False, "err": "المكتب غير مسجل."}

config = load_config(office_id)

if not config.get("found"):
    st.error(f"❌ خطأ: المكتب '{office_id}' غير متاح.")
    st.stop()

OFFICE_NAME = config['name']
WEBHOOK_URL = config['webhook']
SHEET_ID = config['sheet']
ADMIN_PWD = config['pass']
DATA_CSV = f"https://docs.google.com/spreadsheets/d/{SHEET_ID}/export?format=csv"

# --- واجهة الزبون ---
if params.get("view") == "client":
    if "submitted" not in st.session_state: st.session_state.submitted = False
    if not st.session_state.submitted:
        st.markdown(f"<h1 style='text-align: center; color: #d4af37;'>🏢 {OFFICE_NAME}</h1>", unsafe_allow_html=True)
        with st.form("client_form", clear_on_submit=True):
            name = st.text_input("الأسم الكامل")
            phone = st.text_input("رقم الهاتف")
            region = st.selectbox("المنطقة", ["البياع", "المدائن", "السيدية", "أخرى"])
            if st.form_submit_button("إرسال الطلب 🚀"):
                if name and phone:
                    requests.post(WEBHOOK_URL, params={"name": name, "phone": phone, "region": region, "source": OFFICE_NAME})
                    st.session_state.submitted = True
                    st.rerun()
    else:
        st.balloons()
        st.success("✅ تم الاستلام بنجاح!")
    st.stop()

# --- واجهة الإدارة ---
if "is_auth" not in st.session_state: st.session_state.is_auth = False
if not st.session_state.is_auth:
    st.markdown(f"### 🔒 دخول الإدارة: {OFFICE_NAME}")
    if st.text_input("الرمز السري:", type="password") == ADMIN_PWD:
        st.session_state.is_auth = True
        st.rerun()
    st.stop()

try:
    res_leads = requests.get(f"{DATA_CSV}?cb={datetime.now().timestamp()}", timeout=10)
    df_leads = pd.read_csv(StringIO(res_leads.text))
    st.markdown(f"### 📊 سجل طلبات {OFFICE_NAME}")
    st.dataframe(df_leads, use_container_width=True)
except:
    st.error("فشل جلب الطلبات. تأكد من إعدادات المشاركة في جدول المكتب.")
    
