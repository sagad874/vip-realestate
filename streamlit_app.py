import streamlit as st
import pandas as pd
from datetime import datetime
import requests
import re
import json

# 1. إعدادات الصفحة
st.set_page_config(page_title="Pro Data Matrix | Secured", layout="wide")

# استخراج المعلمات من الرابط (المكتب والواجهة)
query_params = st.query_params
is_client = query_params.get("view") == "client"
office_id = query_params.get("id", "bayaa")

# 2. إدارة البيانات المركزية (رابط الماستر شيت الخاص بك)
MASTER_CSV = "https://docs.google.com/spreadsheets/d/1a9MO2P78L7XBggmlkYKYfjnslAAyvGxOeffnv1LT_ac/export?format=csv"

@st.cache_data(ttl=1) # تحديث فوري كل ثانية
def load_office_config(oid):
    # إعدادات افتراضية فخمة في حال فشل الاتصال
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

# تحميل بيانات المكتب الحالي
config = load_office_config(office_id)
OFFICE_NAME = config['name']
WEBHOOK_URL = config['webhook']
SHEET_ID = config['sheet']
CSV_URL = f"https://docs.google.com/spreadsheets/d/{SHEET_ID}/export?format=csv"
PASSWORD = config['pass']

# --- واجهة الزبون ---
if is_client:
    if "submitted" not in st.session_state:
        st.session_state.submitted = False

    if not st.session_state.submitted:
        # اسم المكتب يظهر هنا ديناميكياً
        st.markdown(f"<h2 style='text-align: center; color: #d4af37;'>🏢 {OFFICE_NAME} - تسجيل طلب</h2>", unsafe_allow_html=True)
        with st.form("client_form", clear_on_submit=True):
            name = st.text_input("الاسم الكامل")
            phone = st.text_input("رقم الهاتف (واتساب)")
            region = st.selectbox("المنطقة المطلوبة", ["شهداء البياع", "المنصور", "حي الجامعة", "السيدية", "أخرى"])
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
        if st.button("إرسال طلب آخر جديد"):
            st.session_state.submitted = False
            st.rerun()
    st.stop()

# --- واجهة الإدارة (مع ميزة الترتيب والتحليل من كودك) ---
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
        # البحث الذكي عن الأعمدة من كودك
        def find_c(names):
            for c in df.columns:
                if any(n.lower() in str(c).lower() or n in str(c) for n in names): return c
            return df.columns[0]

        c_name = find_c(['name', 'الاسم', 'Name'])
        c_phone = find_c(['phone', 'هاتف', 'رقم', 'Phone'])
        c_budget = find_c(['budget', 'الميزانية', 'سعر', 'Budget'])
        c_region = find_c(['region', 'المنطقة', 'Region'])
        c_time = find_c(['submission', 'time', 'date', 'التاريخ', 'Timestamp'])
        c_details = find_c(['details', 'تفاصيل', 'Details'])
        c_analysis = find_c(['analysis', 'تحليل', 'Analysis'])

        # دالة توحيد القيم للترتيب من كودك
        def get_unified_value(v):
            try:
                if pd.isna(v): return 0
                val_str = str(v).lower()
                nums = re.findall(r'\d+', val_str)
                if not nums: return 0
                number = int(nums[0])
                if any(x in val_str for x in ['$', 'usd', 'دولار']):
                    return number * 1500
                return number
            except: return 0

        df['sort_t'] = pd.to_datetime(df[c_time], dayfirst=True, errors='coerce')
        df['sort_b'] = df[c_budget].apply(get_unified_value)
        df = df.sort_values(by=['sort_t', 'sort_b'], ascending=[False, False]).reset_index(drop=True)
        
        st.markdown(f"<h3 style='color:#d4af37;'>📊 إجمالي طلبات {OFFICE_NAME}: {len(df)}</h3>", unsafe_allow_html=True)

        for _, row in df.iterrows():
            display_time = str(row[c_time]) if c_time in row else "N/A"
            analysis_text = str(row[c_analysis]) if c_analysis in row else "جاري تحليل الطلب..."
            
            with st.container():
                st.markdown(f"""
                <div class="property-card">
                    <div style="display: flex; justify-content: space-between;">
                        <h2 style='color:white; margin:0;'>👤 {row[c_name]}</h2>
                        <span style="color: #888;">📅 {display_time}</span>
                    </div>
                    <p style='color:white; margin-top:10px;'>📍 المنطقة: <b>{row[c_region]}</b></p>
                    <p style="color: #2ecc71 !important; font-weight: bold; font-size: 1.3em;">💰 الميزانية: {row[c_budget]}</p>
                    <div style="background-color: #2c3e50; padding: 15px; border-radius: 10px; border-left: 5px solid #d4af37;">
                        <p style='color:white; margin-bottom:5px;'>🤖 <b>تحليل النظام الذكي:</b></p>
                        <p style='color:#ecf0f1;'>{analysis_text}</p>
                    </div>
                </div>
                """, unsafe_allow_html=True)
                
                # زر الواتساب الذكي من كودك
                p_num = re.sub(r'\D', '', str(row[c_phone]))
                st.link_button(f"تواصل مع {row[c_name]} عبر واتساب 💬", f"https://wa.me/{p_num}", use_container_width=True)
                st.markdown("<br>", unsafe_allow_html=True)
    else:
        st.info(f"لا توجد طلبات في {OFFICE_NAME} حالياً.")
except Exception as e:
    st.error(f"حدث خطأ: {e}")
    
