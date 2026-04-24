import streamlit as st
import pandas as pd
from datetime import datetime
import requests
import re
from io import StringIO

# 1. إعدادات الصفحة (ثيم احترافي)
st.set_page_config(page_title="Matrix Real Estate | Pro", layout="wide", initial_sidebar_state="collapsed")

# 2. نظام التطهير ومنع التداخل
params = st.query_params
office_id = params.get("id", "bayaa").strip().lower()

if "active_office" not in st.session_state:
    st.session_state.active_office = office_id

if st.session_state.active_office != office_id:
    for key in list(st.session_state.keys()):
        del st.session_state[key]
    st.cache_data.clear()
    st.session_state.active_office = office_id
    st.rerun()

# 3. رابط الماستر - (تأكد أن هذا الجدول "Anyone with link can view")
MASTER_CSV = "https://docs.google.com/spreadsheets/d/1a9MO2P78L7XBggmlkYKYfjnslAAyvGxOeffnv1LT_ac/export?format=csv&gid=0"

@st.cache_data(ttl=0)
def fetch_master_config(oid):
    try:
        # محاولة الاتصال بجوجل مع كسر الكاش القوي
        headers = {'Cache-Control': 'no-cache', 'Pragma': 'no-cache'}
        response = requests.get(f"{MASTER_CSV}&timestamp={datetime.now().timestamp()}", headers=headers, timeout=15)
        
        if response.status_code != 200:
            return {"found": False, "error": f"Google Status: {response.status_code}"}
            
        df = pd.read_csv(StringIO(response.text))
        
        # تنظيف شامل للأعمدة والبيانات من المسافات
        df.columns = [str(c).strip().lower() for c in df.columns]
        
        if 'office_id' not in df.columns:
            return {"found": False, "error": "Column 'office_id' missing"}

        df['office_id'] = df['office_id'].astype(str).str.strip().str.lower()
        
        # البحث عن المكتب
        row = df[df['office_id'] == oid]
        
        if not row.empty:
            res = row.iloc[0]
            # استخراج المعرف فقط من الخلية (سواء كان رابط أو كود)
            raw_sid = str(res.get('sheet_id', '')).strip()
            sid_match = re.search(r"/d/([a-zA-Z0-9-_]+)", raw_sid)
            final_sid = sid_match.group(1) if sid_match else raw_sid
            
            return {
                "found": True,
                "name": res.get('office_name', 'مكتب عقاري'),
                "webhook": str(res.get('webhook_url', '')).strip(),
                "sheet": final_sid,
                "pass": str(res.get('password', '1234'))
            }
    except Exception as e:
        return {"found": False, "error": str(e)}
    return {"found": False}

# تنفيذ جلب الإعدادات
config = fetch_master_config(office_id)

# --- حائط الصد: إذا فشل النظام في العثور على المكتب ---
if not config.get("found"):
    st.error(f"❌ خطأ: المكتب '{office_id}' غير متاح حالياً.")
    st.warning(f"التفاصيل: {config.get('error', 'المكتب غير مسجل بالجدول')}")
    st.info("💡 حل سريع: اذهب لجدول جوجل واضغط 'Share' ثم اجعله 'Anyone with the link can view'.")
    st.stop()

# تعريف المتغيرات بعد النجاح
OFFICE_NAME = config['name']
WEBHOOK = config['webhook']
SHEET_ID = config['sheet']
PWD = config['pass']
DATA_URL = f"https://docs.google.com/spreadsheets/d/{SHEET_ID}/export?format=csv"

# --- واجهة الزبون (view=client) ---
if params.get("view") == "client":
    if "is_sent" not in st.session_state: st.session_state.is_sent = False
    
    if not st.session_state.is_sent:
        st.markdown(f"<h1 style='text-align:center; color:#d4af37;'>🏢 {OFFICE_NAME}</h1>", unsafe_allow_html=True)
        with st.form("client_submission"):
            name = st.text_input("الأسم الكامل")
            phone = st.text_input("رقم الواتساب")
            area = st.selectbox("المنطقة", ["البياع", "المدائن", "السيدية", "حي الجامعة", "أخرى"])
            price = st.text_input("الميزانية")
            notes = st.text_area("تفاصيل العقار المطلوب")
            
            if st.form_submit_button("إرسال الطلب 🚀"):
                if name and phone:
                    requests.post(WEBHOOK, params={"name":name, "phone":phone, "area":area, "price":price, "notes":notes, "source":OFFICE_NAME})
                    st.session_state.is_sent = True
                    st.rerun()
                else: st.warning("يرجى كتابة الاسم والهاتف.")
    else:
        st.balloons()
        st.success("تم إرسال طلبك بنجاح! شكراً لك.")
    st.stop()

# --- واجهة الإدارة ---
if "admin_ok" not in st.session_state: st.session_state.admin_ok = False

if not st.session_state.admin_ok:
    st.markdown(f"<h2 style='text-align:center;'>🔒 تسجيل دخول: {OFFICE_NAME}</h2>", unsafe_allow_html=True)
    if st.text_input("كلمة السر:", type="password") == PWD:
        st.session_state.admin_ok = True
        st.rerun()
    st.stop()

# عرض البيانات للإدارة
try:
    df_data = pd.read_csv(f"{DATA_URL}&cb={datetime.now().timestamp()}")
    st.markdown(f"### 📊 سجل طلبات {OFFICE_NAME}")
    
    for i, row in df_data.iloc[::-1].iterrows():
        with st.expander(f"👤 {row.iloc[0]} - {row.iloc[2] if len(row)>2 else ''}"):
            st.write(f"**الهاتف:** {row.iloc[1]}")
            st.write(f"**الميزانية:** {row.iloc[3] if len(row)>3 else 'غير محدد'}")
            st.write(f"**التفاصيل:** {row.iloc[4] if len(row)>4 else '-'}")
            p_clean = re.sub(r'\D', '', str(row.iloc[1]))
            st.link_button("فتح واتساب 💬", f"https://wa.me/{p_clean}")
except:
    st.error("فشل في قراءة بيانات الجدول الخاص. تأكد من إعدادات المشاركة داخل الشيت.")
    
