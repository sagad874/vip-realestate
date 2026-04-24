import streamlit as st
import pandas as pd
from datetime import datetime
import requests
import re
import json

# 1. إعدادات الصفحة الأساسية
st.set_page_config(page_title="Pro Data Matrix | Secured", layout="wide")

# --- نظام الفصل الذكي ومنع التداخل ---
params = st.query_params
office_id = params.get("id", "bayaa")

if "last_office" not in st.session_state:
    st.session_state.last_office = office_id

if st.session_state.last_office != office_id:
    st.session_state.authenticated = False
    st.session_state.submitted = False
    st.session_state.last_office = office_id
    st.cache_data.clear()

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
        # كسر الكاش لضمان جلب أحدث بيانات المكاتب
        df = pd.read_csv(f"{MASTER_CSV}&cb={datetime.now().timestamp()}")
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

# تحميل البيانات بناءً على الرابط
config = load_office_config(office_id)
OFFICE_NAME = config['name']
WEBHOOK_URL = config['webhook']
SHEET_ID = config['sheet']
CSV_URL = f"https://docs.google.com/spreadsheets/d/{SHEET_ID}/export?format=csv"
PASSWORD = config['pass']

# --- واجهة الزبون (النسخة الفخمة) ---
is_client = params.get("view") == "client"

if is_client:
    if "submitted" not in st.session_state:
        st.session_state.submitted = False

    if not st.session_state.submitted:
        st.markdown(f"<h2 style='text-align: center; color: #d4af37;'>🏢 {OFFICE_NAME} - تسجيل طلب</h2>", unsafe_allow_html=True)
        with st.form("client_form", clear_on_submit=True):
            name = st.text_input("الاسم الكامل")
            phone = st.text_input("رقم الهاتف (واتساب)")
            
            # قائمة مناطق بغداد المنبثقة كاملة
            baghdad_regions = [
                "شهداء البياع", "البياع", "المنصور", "حي الجامعة", "السيدية", "العامرية", 
                "الغزالية", "الدورة", "اليرموك", "القادسية", "زيونة", "بغداد الجديدة", "أخرى"
            ]
            region = st.selectbox("المنطقة المطلوبة في بغداد", baghdad_regions)
            
            budget = st.text_input("الميزانية التقريبية")
            details = st.text_area("تفاصيل العقار المطلوب")
            
            send_btn = st.form_submit_button(f"إرسال الطلب الآن 🚀")
            
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
                    st.warning("يرجى ملء الاسم ورقم الهاتف لإتمام الطلب.")
    else:
        st.balloons()
        st.markdown(f"""
            <div style="text-align: center; padding: 50px; background-color: #1a1c24; border-radius: 20px; border: 2px solid #d4af37; margin-top: 50px;">
                <h1 style="color: #d4af37; margin-bottom: 20px;">✅ تم استلام طلبك بنجاح!</h1>
                <p style="color: white; font-size: 1.3em;">شكراً لاختياركم <b>{OFFICE_NAME}</b>، نحن نقدّر ثقتكم بنا وسنتصل بك قريباً.</p>
                <hr style="border-color: #333; margin: 30px 0;">
                <p style="color: #888; font-style: italic; font-size: 0.9em;">
                    تم تطوير هذا النظام الذكي بواسطة المبرمج <b style="color: #d4af37;">سجاد</b>
                </p>
            </div>
        """, unsafe_allow_html=True)
        if st.button("إرسال طلب آخر جديد"):
            st.session_state.submitted = False
            st.rerun()
    st.stop()

# --- واجهة الإدارة (لوحة التحكم الشاملة) ---
if "authenticated" not in st.session_state:
    st.session_state["authenticated"] = False

if not st.session_state["authenticated"]:
    st.markdown(f"<h2 style='text-align: center; color: #d4af37;'>🔒 لوحة تحكم {OFFICE_NAME}</h2>", unsafe_allow_html=True)
    user_input = st.text_input("ادخل رمز الوصول:", type="password")
    if user_input == PASSWORD:
        st.session_state["authenticated"] = True
        st.rerun()
    st.stop()

# تنسيق بطاقات العرض
st.markdown("""<style>.property-card { background-color: #1a1c24; border-radius: 15px; padding: 20px; border: 1px solid #d4af37; margin-bottom: 20px; }</style>""", unsafe_allow_html=True)

try:
    # جلب بيانات المكتب المحدد من جدول جوجل
    df = pd.read_csv(f"{CSV_URL}&cb={datetime.now().timestamp()}")
    if not df.empty:
        # البحث الذكي عن الأعمدة (عربي/إنجليزي)
        def find_c(names):
            for c in df.columns:
                if any(n.lower() in str(c).lower() for n in names): return c
            return df.columns[0]

        c_name = find_c(['name', 'الاسم'])
        c_phone = find_c(['phone', 'هاتف', 'رقم'])
        c_budget = find_c(['budget', 'الميزانية', 'سعر'])
        c_region = find_c(['region', 'المنطقة'])
        c_time = find_c(['time', 'التاريخ', 'Timestamp'])
        c_details = find_c(['details', 'تفاصيل'])
        c_analysis = find_c(['analysis', 'تحليل'])

        # دالة الترتيب (توحيد القيم)
        def get_unified_value(v):
            try:
                if pd.isna(v): return 0
                val_str = str(v).lower()
                nums = re.findall(r'\d+', val_str)
                if not nums: return 0
                number = int(nums[0])
                if any(x in val_str for x in ['$', 'usd', 'دولار']): return number * 1500
                return number
            except: return 0

        df['sort_t'] = pd.to_datetime(df[c_time], dayfirst=True, errors='coerce')
        df['sort_b'] = df[c_budget].apply(get_unified_value)
        df = df.sort_values(by=['sort_t', 'sort_b'], ascending=[False, False]).reset_index(drop=True)
        
        st.markdown(f"<h3 style='color:#d4af37;'>📊 سجل طلبات {OFFICE_NAME} | العدد: {len(df)}</h3>", unsafe_allow_html=True)

        for _, row in df.iterrows():
            display_time = str(row[c_time]) if c_time in row else "N/A"
            analysis_text = str(row[c_analysis]) if (c_analysis in row and pd.notna(row[c_analysis])) else "جاري تحليل الطلب..."
            
            with st.container():
                st.markdown(f"""
                <div class="property-card">
                    <div style="display: flex; justify-content: space-between;">
                        <h2 style='color:white; margin:0;'>👤 {row.get(c_name, 'عميل')}</h2>
                        <span style="color: #888;">📅 {display_time}</span>
                    </div>
                    <p style='color:white; margin-top:10px;'>📍 المنطقة: <b>{row.get(c_region, '—')}</b></p>
                    <p style="color: #2ecc71 !important; font-weight: bold; font-size: 1.3em;">💰 الميزانية: {row.get(c_budget, '—')}</p>
                    <div style="background-color: #2c3e50; padding: 15px; border-radius: 10px; border-left: 5px solid #d4af37;">
                        <p style='color:white; margin-bottom:5px;'>🤖 <b>تحليل النظام الذكي:</b></p>
                        <p style='color:#ecf0f1;'>{analysis_text}</p>
                    </div>
                </div>
                """, unsafe_allow_html=True)
                
                # زر الواتساب
                p_num = re.sub(r'\D', '', str(row.get(c_phone, '')))
                st.link_button(f"تواصل عبر واتساب 💬", f"https://wa.me/{p_num}", use_container_width=True)
                st.markdown("<br>", unsafe_allow_html=True)
    else:
        st.info(f"لا توجد طلبات في {OFFICE_NAME} حالياً.")
except Exception as e:
    st.error(f"حدث خطأ في جلب بيانات {OFFICE_NAME}: {e}")
                
