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

@st.cache_data(ttl=60)
def get_office_config(oid):
    try:
        m_df = pd.read_csv(MASTER_CSV_URL)
        m_df['office_id'] = m_df['office_id'].astype(str).str.strip()
        row = m_df[m_df['office_id'] == str(oid).strip()].iloc[0]
        return {
            "sheet_id": row['sheet_id'],
            "webhook": str(row['webhook_url']).strip(),
            "name": row['office_name']
        }
    except:
        return {
            "sheet_id": MASTER_SHEET_ID,
            "webhook": "https://eomfdq8l221q30q.m.pipedream.net",
            "name": "مكتب العقارات"
        }

config = get_office_config(office_id)
SHEET_ID = config['sheet_id']
WEBHOOK_URL = config['webhook']
OFFICE_NAME = config['name']
CSV_URL = f"https://docs.google.com/spreadsheets/d/{SHEET_ID}/export?format=csv"

# --- واجهة الزبون (الترتيب العمودي - واحدة تحت الأخرى) ---
if is_client:
    if "submitted" not in st.session_state:
        st.session_state.submitted = False

    if not st.session_state.submitted:
        st.markdown(f"<h2 style='text-align: center; color: #d4af37;'>🏢 {OFFICE_NAME} - تسجيل طلب</h2>", unsafe_allow_html=True)
        with st.form("client_form", clear_on_submit=True):
            # الحقول مرتبة عمودياً كما طلبت
            name = st.text_input("الاسم الكامل")
            phone = st.text_input("رقم الهاتف (واتساب)")
            region = st.selectbox("المنطقة المطلوبة", ["شهداء البياع", "المنصور", "حي الجامعة", "السيدية", "أخرى"])
            budget = st.text_input("الميزانية التقريبية")
            details = st.text_area("تفاصيل العقار المطلوب")
            
            st.markdown("<br>", unsafe_allow_html=True)
            send_btn = st.form_submit_button("إرسال الطلب الآن 🚀", use_container_width=True)
            
            if send_btn:
                if name and phone:
                    payload = {"name": name, "phone": phone, "region": region, "budget": budget, "details": details}
                    try:
                        if "script.google.com" in WEBHOOK_URL:
                            requests.post(WEBHOOK_URL, data=json.dumps(payload), headers={"Content-Type": "application/json"}, timeout=8)
                        else:
                            requests.post(WEBHOOK_URL, params=payload, timeout=8)
                        
                        st.session_state.submitted = True
                        st.rerun()
                    except:
                        # تجاوز أي خطأ في الرد لضمان ظهور رسالة النجاح
                        st.session_state.submitted = True
                        st.rerun()
                else:
                    st.warning("يرجى ملء الاسم ورقم الهاتف.")
    else:
        st.balloons()
        st.markdown(f"""
            <div style="text-align: center; padding: 50px; background-color: #1a1c24; border-radius: 20px; border: 2px solid #d4af37; margin-top: 50px;">
                <h1 style="color: #d4af37;">✅ تم استلام طلبك بنجاح!</h1>
                <p style="color: white; font-size: 1.2em;">شكراً لاختياركم <b>{OFFICE_NAME}</b>، سنتصل بك قريباً.</p>
                <hr style="border-color: #333; margin: 30px 0;">
                <p style="color: #888; font-style: italic; font-size: 0.9em;">تم تطوير النظام بواسطة المبرمج <b style="color: #d4af37;">سجاد</b></p>
            </div>
        """, unsafe_allow_html=True)
        if st.button("إرسال طلب آخر جديد"):
            st.session_state.submitted = False
            st.rerun()
    st.stop()

# --- واجهة الإدارة ---
PASSWORD = "123456246SsS@"
if "authenticated" not in st.session_state:
    st.session_state["authenticated"] = False

if not st.session_state["authenticated"]:
    st.markdown("<h2 style='text-align: center; color: #d4af37;'>🔒 لوحة التحكم - تسجيل الدخول</h2>", unsafe_allow_html=True)
    user_input = st.text_input("ادخل رمز الوصول:", type="password")
    if user_input == PASSWORD:
        st.session_state["authenticated"] = True
        st.rerun()
    st.stop()

st.markdown("""<style>.prop-card { background-color: #1a1c24; border-radius: 15px; padding: 20px; border: 1px solid #d4af37; margin-bottom: 20px; }</style>""", unsafe_allow_html=True)

try:
    df = pd.read_csv(CSV_URL)
    if not df.empty:
        def find_c(names):
            for c in df.columns:
                if any(n.lower() in c.lower() for n in names): return c
            return df.columns[0]

        c_time = find_c(['time', 'date', 'التاريخ'])
        c_budget = find_c(['budget', 'الميزانية'])

        def get_sort_val(v):
            try:
                s = str(v).lower()
                n = int(re.findall(r'\d+', s)[0])
                if any(x in s for x in ['$', 'usd', 'دولار']): return n * 1500
                return n
            except: return 0

        df['sort_t'] = pd.to_datetime(df[c_time], dayfirst=True, errors='coerce')
        df['sort_b'] = df[c_budget].apply(get_sort_val)
        df = df.sort_values(by=['sort_t', 'sort_b'], ascending=[False, False])
        
        st.markdown(f"<h3 style='color:#d4af37;'>📊 مكتب: {OFFICE_NAME} | الطلبات: {len(df)}</h3>", unsafe_allow_html=True)

        for _, row in df.iterrows():
            def v(k):
                for col in row.index:
                    if k.lower() in str(col).lower(): return str(row[col])
                return "—"
            
            with st.container():
                st.markdown(f"""
                <div class="prop-card">
                    <div style="display: flex; justify-content: space-between;">
                        <h2 style='color:white; margin:0;'>👤 {v('Name')}</h2>
                        <span style="color: #888;">📅 {str(row[c_time])}</span>
                    </div>
                    <p style='color:white; margin-top:10px;'>📍 المنطقة: <b>{v('Region')}</b> | 💰 الميزانية: <b style='color:#2ecc71;'>{v('Budget')}</b></p>
                    <div style="background-color: #2c3e50; padding: 15px; border-radius: 10px; border-left: 5px solid #d4af37;">
                        <p style='color:white; margin-bottom:5px;'>🤖 <b>تحليل النظام الذكي:</b></p>
                        <p style='color:#ecf0f1;'>{v('Analysis')}</p>
                    </div>
                </div>
                """, unsafe_allow_html=True)
                
                p_num = re.sub(r'\D', '', v('Phone'))
                st.link_button(f"تواصل مع {v('Name')} عبر واتساب 💬", f"https://wa.me/{p_num}", use_container_width=True)
                st.markdown("<br>", unsafe_allow_html=True)
    else:
        st.info(f"لا توجد طلبات حالياً لمكتب {OFFICE_NAME}")
except Exception as e:
    st.error(f"حدث خطأ في تحميل البيانات: {e}")
    
