import streamlit as st
import pandas as pd
import requests
import json

# 1. إعدادات الصفحة
st.set_page_config(page_title="Pro Data Matrix | Secured", layout="wide")

query_params = st.query_params
is_client = query_params.get("view") == "client"
office_id = query_params.get("id", "bayaa")

# 2. رابط جدول الماستر
MASTER_CSV = "https://docs.google.com/spreadsheets/d/1a9MO2P78L7XBggmlkYKYfjnslAAyvGxOeffnv1LT_ac/export?format=csv"

@st.cache_data(ttl=1)
def load_office_config(oid):
    default_config = {
        "name": "المركز العقاري الموحد", 
        "webhook": "https://eomfdq8l221q30q.m.pipedream.net",
        "sheet": "1a9MO2P78L7XBggmlkYKYfjnslAAyvGxOeffnv1LT_ac",
        "pass": "123456246SsS@"
    }
    try:
        df = pd.read_csv(MASTER_CSV)
        df['office_id'] = df['office_id'].astype(str).str.strip()
        if str(oid).strip() in df['office_id'].values:
            row = df[df['office_id'] == str(oid).strip()].iloc[0]
            return {
                "name": row['office_name'],
                "webhook": str(row['webhook_url']).strip(),
                "sheet": str(row['sheet_id']).strip(),
                "pass": str(row['password']).strip()
            }
        return default_config
    except:
        return default_config

office = load_office_config(office_id)
OFFICE_NAME = office['name']
CSV_URL = f"https://docs.google.com/spreadsheets/d/{office['sheet']}/export?format=csv"

# --- واجهة الزبون (مختصرة للسرعة) ---
if is_client:
    st.markdown(f"<h1 style='text-align: center; color: #d4af37;'>{OFFICE_NAME}</h1>", unsafe_allow_html=True)
    with st.form("c_form"):
        name = st.text_input("الاسم")
        phone = st.text_input("الهاتف")
        reg = st.text_input("المنطقة")
        bud = st.text_input("الميزانية")
        det = st.text_area("التفاصيل")
        if st.form_submit_button("إرسال"):
            payload = {"name": name, "phone": phone, "region": reg, "budget": bud, "details": det, "source": OFFICE_NAME}
            requests.post(office['webhook'], json=payload)
            st.success("تم الإرسال")
    st.stop()

# --- واجهة الإدارة الذكية ---
if "auth" not in st.session_state: st.session_state.auth = False
if not st.session_state.auth:
    pwd = st.text_input("رمز الدخول:", type="password")
    if pwd == office['pass']: 
        st.session_state.auth = True
        st.rerun()
    st.stop()

st.markdown(f"<h3 style='color:#d4af37;'>📊 سجل طلبات: {OFFICE_NAME}</h3>", unsafe_allow_html=True)

try:
    df_data = pd.read_csv(CSV_URL)
    if not df_data.empty:
        # وظيفة ذكية للبحث عن العمود مهما كان اسمه
        def get_col(names_list):
            for col in df_data.columns:
                if any(n.lower() in col.lower() for n in names_list):
                    return col
            return None

        # تحديد الأعمدة برمجياً
        c_name = get_col(['name', 'الاسم', 'Name'])
        c_phone = get_col(['phone', 'هاتف', 'رقم', 'Phone'])
        c_region = get_col(['region', 'منطقة', 'المنطقة', 'Region'])
        c_budget = get_col(['budget', 'ميزانية', 'الميزانية', 'Budget'])
        c_details = get_col(['details', 'تفاصيل', 'التفاصيل', 'Details'])

        for _, row in df_data.iloc[::-1].iterrows():
            st.markdown(f"""
            <div style="background-color: #1a1c24; border-radius: 15px; padding: 20px; border: 1px solid #d4af37; margin-bottom: 20px;">
                <h2 style='color:white; margin:0;'>👤 {row[c_name] if c_name else 'عميل'}</h2>
                <p style='color:#d4af37;'>📞 هاتف: {row[c_phone] if c_phone else '—'}</p>
                <p style='color:white;'>📍 {row[c_region] if c_region else '—'} | 💰 {row[c_budget] if c_budget else '—'}</p>
                <div style="background-color: #2c3e50; padding: 10px; border-radius: 10px;">
                    <p style='color:#ecf0f1; margin:0;'>📝 التفاصيل: {row[c_details] if c_details else '—'}</p>
                </div>
            </div>
            """, unsafe_allow_html=True)
    else:
        st.info("الجدول فارغ حالياً.")
except Exception as e:
    st.error(f"خطأ في جلب البيانات: {e}")
