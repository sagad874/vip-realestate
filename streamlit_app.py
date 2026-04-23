import streamlit as st
import pandas as pd
from datetime import datetime
import requests
import re
import json

# 1. إعدادات الصفحة الفخمة
st.set_page_config(page_title="Pro Data Matrix | Secured", layout="wide", initial_sidebar_state="collapsed")

# استخراج المعلمات من الرابط
query_params = st.query_params
is_client = query_params.get("view") == "client"
office_id = query_params.get("id", "bayaa") # البياع هو المكتب الافتراضي

# 2. إدارة البيانات المركزية (Master Sheet)
MASTER_SHEET_ID = "1a9MO2P78L7XBggmlkYKYfjnslAAyvGxOeffnv1LT_ac"
MASTER_CSV_URL = f"https://docs.google.com/spreadsheets/d/{MASTER_SHEET_ID}/export?format=csv"

@st.cache_data(ttl=60)
def get_office_config(oid):
    """جلب إعدادات المكتب من جدول الماستر تلقائياً"""
    try:
        m_df = pd.read_csv(MASTER_CSV_URL)
        # تنظيف البيانات لضمان المطابقة
        m_df['office_id'] = m_df['office_id'].astype(str).str.strip()
        row = m_df[m_df['office_id'] == str(oid).strip()].iloc[0]
        return {
            "sheet_id": row['sheet_id'],
            "webhook": row['webhook_url'],
            "name": row['office_name']
        }
    except Exception as e:
        # بيانات الطوارئ في حال فشل الاتصال بجدول الماستر
        return {
            "sheet_id": MASTER_SHEET_ID,
            "webhook": "https://eomfdq8l221q30q.m.pipedream.net",
            "name": "مكتب العقارات المتطور"
        }

# تحميل إعدادات المكتب الحالي
config = get_office_config(office_id)
SHEET_ID = config['sheet_id']
WEBHOOK_URL = str(config['webhook']).strip()
OFFICE_NAME = config['name']
CSV_URL = f"https://docs.google.com/spreadsheets/d/{SHEET_ID}/export?format=csv"

# --- واجهة الزبون (Client View) ---
if is_client:
    if "submitted" not in st.session_state:
        st.session_state.submitted = False

    if not st.session_state.submitted:
        st.markdown(f"<h2 style='text-align: center; color: #d4af37;'>🏢 {OFFICE_NAME}</h2>", unsafe_allow_html=True)
        st.markdown("<p style='text-align: center; color: #888;'>يرجى ملء الاستمارة لتقديم طلبك وسنتواصل معك قريباً</p>", unsafe_allow_html=True)
        
        with st.form("client_form", clear_on_submit=True):
            col1, col2 = st.columns(2)
            with col1:
                name = st.text_input("الاسم الكامل")
                phone = st.text_input("رقم الهاتف (واتساب)")
            with col2:
                region = st.selectbox("المنطقة المطلوبة", ["شهداء البياع", "المنصور", "حي الجامعة", "السيدية", "أخرى"])
                budget = st.text_input("الميزانية التقريبية")
            
            details = st.text_area("تفاصيل العقار المطلوب (اختياري)")
            
            st.markdown("<br>", unsafe_allow_html=True)
            send_btn = st.form_submit_button("إرسال الطلب الآن 🚀", use_container_width=True)
            
            if send_btn:
                if name and phone:
                    payload = {
                        "name": name, 
                        "phone": phone, 
                        "region": region, 
                        "budget": budget, 
                        "details": details,
                        "office": OFFICE_NAME
                    }
                    try:
                        # نظام الإرسال الذكي الهجين
                        if "script.google.com" in WEBHOOK_URL:
                            # إرسال كـ JSON لضمان توافق Google Apps Script
                            resp = requests.post(WEBHOOK_URL, data=json.dumps(payload), 
                                               headers={"Content-Type": "application/json"}, timeout=15)
                        else:
                            # إرسال كـ Query Params لتوافق Pipedream
                            resp = requests.post(WEBHOOK_URL, params=payload, timeout=15)
                        
                        # معالجة أكواد النجاح المختلفة (بما فيها 302 الخاص بجوجل)
                        if resp.status_code in [200, 201, 302]:
                            st.session_state.submitted = True
                            st.rerun()
                        else:
                            st.error(f"فشل الإرسال. الكود: {resp.status_code}")
                    except Exception as e:
                        st.error("فشل الاتصال بالخادم. تأكد من صحة الرابط في جدول الإدارة.")
                else:
                    st.warning("الاسم ورقم الهاتف ضروريان لإتمام العملية.")
    else:
        st.balloons()
        st.markdown(f"""
            <div style="text-align: center; padding: 50px; background-color: #1a1c24; border-radius: 20px; border: 2px solid #d4af37; margin-top: 50px;">
                <h1 style="color: #d4af37;">✅ تم استلام طلبك!</h1>
                <p style="color: white; font-size: 1.2em;">شكراً لثقتكم بمكتب <b>{OFFICE_NAME}</b>. سيقوم فريقنا بمراجعة طلبك والاتصال بك.</p>
                <hr style="border-color: #333; margin: 30px 0;">
                <p style="color: #888; font-size: 0.8em;">Developed by <span style="color:#d4af37;">Sajad</span></p>
            </div>
        """, unsafe_allow_html=True)
        if st.button("إرسال طلب جديد"):
            st.session_state.submitted = False
            st.rerun()
    st.stop()

# --- واجهة الإدارة (Admin Dashboard) ---
PASSWORD = "123456246SsS@"
if "authenticated" not in st.session_state:
    st.session_state["authenticated"] = False

if not st.session_state["authenticated"]:
    st.markdown("<h2 style='text-align: center; color: #d4af37;'>🔒 تسجيل دخول الإدارة</h2>", unsafe_allow_html=True)
    user_input = st.text_input("رمز الوصول:", type="password")
    if user_input == PASSWORD:
        st.session_state["authenticated"] = True
        st.rerun()
    st.stop()

# تنسيق البطاقات العقارية
st.markdown("""<style>.prop-card { background-color: #1a1c24; border-radius: 15px; padding: 20px; border: 1px solid #333; border-right: 5px solid #d4af37; margin-bottom: 20px; }</style>""", unsafe_allow_html=True)

try:
    df = pd.read_csv(CSV_URL)
    if not df.empty:
        def find_col(possible_names):
            for col in df.columns:
                if any(name.lower() in col.lower() for name in possible_names): return col
            return df.columns[0]

        c_time = find_col(['time', 'date', 'تاريخ', 'timestamp'])
        c_budget = find_col(['budget', 'ميزانية', 'سعر'])

        # دالة الترتيب الذكي
        def parse_val(v):
            try:
                s = str(v).lower()
                n = int(re.findall(r'\d+', s)[0])
                if any(x in s for x in ['$', 'usd', 'دولار']): return n * 1500
                return n
            except: return 0

        df['t_sort'] = pd.to_datetime(df[c_time], dayfirst=True, errors='coerce')
        df['b_sort'] = df[c_budget].apply(parse_val)
        df = df.sort_values(by=['t_sort', 'b_sort'], ascending=[False, False])

        st.markdown(f"<h3 style='color:#d4af37;'>📊 لوحة تحكم: {OFFICE_NAME} ({len(df)} طلب)</h3>", unsafe_allow_html=True)

        for _, row in df.iterrows():
            def get_val(key):
                for c in row.index:
                    if key.lower() in str(c).lower(): return str(row[c])
                return "—"

            with st.container():
                st.markdown(f"""
                <div class="prop-card">
                    <div style="display: flex; justify-content: space-between; align-items: center;">
                        <h3 style='color:#d4af37; margin:0;'>👤 {get_val('name')}</h3>
                        <span style='color:#666; font-size:0.8em;'>{str(row[c_time])}</span>
                    </div>
                    <p style='color:#ccc; margin: 10px 0;'>📍 المنطقة: <b>{get_val('region')}</b> | 💰 الميزانية: <b style='color:#2ecc71;'>{get_val('budget')}</b></p>
                    <div style='background:#0e1117; padding:10px; border-radius:8px; border:1px solid #222;'>
                        <small style='color:#888;'>🤖 تحليل النظام:</small>
                        <p style='color:#eee; margin:5px 0;'>{get_val('analysis')}</p>
                    </div>
                </div>
                """, unsafe_allow_html=True)
                
                # زر واتساب مباشر
                p_clean = re.sub(r'\D', '', get_val('phone'))
                st.link_button(f"تواصل مع الزبون 💬", f"https://wa.me/{p_clean}", use_container_width=True)
                st.markdown("<br>", unsafe_allow_html=True)
    else:
        st.info(f"لا توجد بيانات حالية لمكتب {OFFICE_NAME}")
except Exception as e:
    st.error(f"خطأ في تحميل الجدول: {e}")
    
