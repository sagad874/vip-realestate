import streamlit as st
import pandas as pd
from datetime import datetime
import requests
import re
import json

# 1. إعدادات الصفحة الأساسية
st.set_page_config(page_title="Pro Data Matrix | Secured", layout="wide")

# --- معالجة ذكية للرابط لمنع تداخل المكاتب ---
if "id" in st.query_params:
    office_id = st.query_params["id"]
else:
    office_id = "bayaa"  # الافتراضي

# نظام تطهير الجلسة عند تغيير المكتب
if "current_office" not in st.session_state:
    st.session_state.current_office = office_id

if st.session_state.current_office != office_id:
    # مسح الذاكرة المؤقتة فوراً عند الانتقال من مكتب لآخر
    st.session_state.authenticated = False
    st.session_state.submitted = False
    st.session_state.current_office = office_id
    st.cache_data.clear() # مسح الكاش لضمان جلب البيانات الصحيحة

# 2. إدارة البيانات المركزية (رابط الماستر)
MASTER_CSV = "https://docs.google.com/spreadsheets/d/1a9MO2P78L7XBggmlkYKYfjnslAAyvGxOeffnv1LT_ac/export?format=csv"

@st.cache_data(ttl=1)
def load_office_config(oid):
    default_config = {
        "name": "المركز العقاري المعتمد", 
        "webhook": "https://eomfdq8l221q30q.m.pipedream.net",
        "sheet": "1a9MO2P78L7XBggmlkYKYfjnslAAyvGxOeffnv1LT_ac",
        "pass": "123456246SsS@"
    }
    try:
        df = pd.read_csv(MASTER_CSV)
        df['office_id'] = df['office_id'].astype(str).str.strip()
        target = str(oid).strip()
        if target in df['office_id'].values:
            row = df[df['office_id'] == target].iloc[0]
            return {
                "name": row['office_name'],
                "webhook": str(row['webhook_url']).strip(),
                "sheet": str(row['sheet_id']).strip(),
                "pass": str(row['password']).strip()
            }
        return default_config
    except:
        return default_config

# تحميل الإعدادات بناءً على ID الرابط
config = load_office_config(office_id)
OFFICE_NAME = config['name']
WEBHOOK_URL = config['webhook']
SHEET_ID = config['sheet']
CSV_URL = f"https://docs.google.com/spreadsheets/d/{SHEET_ID}/export?format=csv"
PASSWORD = config['pass']

# --- واجهة الزبون ---
is_client = st.query_params.get("view") == "client"

if is_client:
    if "submitted" not in st.session_state:
        st.session_state.submitted = False

    if not st.session_state.submitted:
        st.markdown(f"<h2 style='text-align: center; color: #d4af37;'>🏢 {OFFICE_NAME} - تسجيل طلب</h2>", unsafe_allow_html=True)
        with st.form("client_form", clear_on_submit=True):
            name = st.text_input("الاسم الكامل")
            phone = st.text_input("رقم الهاتف (واتساب)")
            
            # قائمة مناطق بغداد المنبثقة
            baghdad_regions = ["شهداء البياع", "البياع", "المنصور", "حي الجامعة", "السيدية", "العامرية", "الغزالية", "الدورة", "اليرموك", "زيونة", "أخرى"]
            region = st.selectbox("المنطقة المطلوبة", baghdad_regions)
            
            budget = st.text_input("الميزانية التقريبية")
            details = st.text_area("تفاصيل العقار المطلوب")
            
            send_btn = st.form_submit_button(f"إرسال الطلب إلى {OFFICE_NAME} 🚀")
            
            if send_btn:
                if name and phone:
                    payload = {"name": name, "phone": phone, "region": region, "budget": budget, "details": details, "source": OFFICE_NAME}
                    try:
                        requests.post(WEBHOOK_URL, params=payload, timeout=8)
                        st.session_state.submitted = True
                        st.rerun()
                    except:
                        st.session_state.submitted = True
                        st.rerun()
                else:
                    st.warning("يرجى ملء الاسم ورقم الهاتف.")
    else:
        st.balloons()
        st.markdown(f"""
            <div style="text-align: center; padding: 50px; background-color: #1a1c24; border-radius: 20px; border: 2px solid #d4af37; margin-top: 50px;">
                <h1 style="color: #d4af37;">✅ تم استلام طلبك بنجاح!</h1>
                <p style="color: white; font-size: 1.3em;">شكراً لاختياركم <b>{OFFICE_NAME}</b>، سنتصل بك قريباً.</p>
                <hr style="border-color: #333; margin: 30px 0;">
                <p style="color: #888; font-style: italic; font-size: 0.9em;">تم تطوير النظام بواسطة المبرمج سجاد</p>
            </div>
        """, unsafe_allow_html=True)
        if st.button("إرسال طلب جديد"):
            st.session_state.submitted = False
            st.rerun()
    st.stop()

# --- واجهة الإدارة ---
if "authenticated" not in st.session_state:
    st.session_state["authenticated"] = False

if not st.session_state["authenticated"]:
    st.markdown(f"<h2 style='text-align: center; color: #d4af37;'>🔒 لوحة تحكم {OFFICE_NAME}</h2>", unsafe_allow_html=True)
    user_input = st.text_input("ادخل رمز الوصول:", type="password")
    if user_input == PASSWORD:
        st.session_state["authenticated"] = True
        st.rerun()
    st.stop()

st.markdown("""<style>.property-card { background-color: #1a1c24; border-radius: 15px; padding: 20px; border: 1px solid #d4af37; margin-bottom: 20px; }</style>""", unsafe_allow_html=True)

try:
    df = pd.read_csv(CSV_URL)
    if not df.empty:
        # البحث الذكي عن الأعمدة لضمان عدم ظهور بيانات فارغة
        def find_c(names):
            for c in df.columns:
                if any(n.lower() in str(c).lower() for n in names): return c
            return df.columns[0]

        c_name = find_c(['name', 'الاسم'])
        c_phone = find_c(['phone', 'هاتف', 'رقم'])
        c_budget = find_c(['budget', 'الميزانية'])
        c_region = find_c(['region', 'المنطقة'])
        c_time = find_c(['time', 'التاريخ', 'Timestamp'])
        c_details = find_c(['details', 'تفاصيل'])
        c_analysis = find_c(['analysis', 'تحليل'])

        df['sort_t'] = pd.to_datetime(df[c_time], dayfirst=True, errors='coerce')
        df = df.sort_values(by='sort_t', ascending=False).reset_index(drop=True)
        
        st.markdown(f"<h3 style='color:#d4af37;'>📊 سجل طلبات {OFFICE_NAME}</h3>", unsafe_allow_html=True)

        for _, row in df.iterrows():
            with st.container():
                st.markdown(f"""
                <div class="property-card">
                    <div style="display: flex; justify-content: space-between;">
                        <h2 style='color:white; margin:0;'>👤 {row.get(c_name, 'عميل')}</h2>
                        <span style="color: #888;">📅 {str(row.get(c_time, ''))}</span>
                    </div>
                    <p style='color:white; margin-top:10px;'>📍 المنطقة: <b>{row.get(c_region, '—')}</b></p>
                    <p style="color: #2ecc71 !important; font-weight: bold; font-size: 1.3em;">💰 الميزانية: {row.get(c_budget, '—')}</p>
                    <div style="background-color: #2c3e50; padding: 15px; border-radius: 10px; border-left: 5px solid #d4af37;">
                        <p style='color:#ecf0f1; margin:0;'>📝 {row.get(c_details, 'لا توجد تفاصيل')}</p>
                    </div>
                </div>
                """, unsafe_allow_html=True)
                p_num = re.sub(r'\D', '', str(row.get(c_phone, '')))
                st.link_button(f"تواصل عبر واتساب 💬", f"https://wa.me/{p_num}", use_container_width=True)
                st.markdown("<br>", unsafe_allow_html=True)
    else:
        st.info(f"لا توجد طلبات حالياً في {OFFICE_NAME}")
except Exception as e:
    st.error(f"تأكد من إعدادات الجدول الخاص بمكتب {OFFICE_NAME}")
    
