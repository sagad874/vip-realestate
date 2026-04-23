import streamlit as st
import pandas as pd
from datetime import datetime
import requests
import re

# 1. إعدادات الصفحة
st.set_page_config(page_title="Pro Data Matrix | Secured", layout="wide")

# --- الربط بجدول الإدارة السري (المحرك الجديد) ---
MASTER_CSV = "https://docs.google.com/spreadsheets/d/1sba6QhfnF5e4IlP8uV0Mku8X50OBIkzy_VekT63d_hI/export?format=csv"

@st.cache_data(ttl=60)
def load_master_data():
    try: return pd.read_csv(MASTER_CSV)
    except: return None

df_master = load_master_data()

# التحقق من نوع الواجهة
query_params = st.query_params
office_id = query_params.get("id", "bayaa")

if df_master is not None:
    try:
        # جلب بيانات المكتب ديناميكياً من جدول الإدارة
        office_info = df_master[df_master['office_id'] == office_id].iloc[0]
        OFFICE_NAME = office_info['office_name']
        SHEET_ID = office_info['sheet_id']
        WEBHOOK_URL = office_info['webhook_url']
        PASSWORD = str(office_info['password'])
        CSV_URL = f"https://docs.google.com/spreadsheets/d/{SHEET_ID}/export?format=csv"
    except:
        st.error("المكتب غير مسجل في النظام."); st.stop()
else:
    st.error("فشل الاتصال بجدول الإدارة السري."); st.stop()

is_client = query_params.get("view") == "client"

# --- واجهة الزبون (بصمة سجاد) ---
if is_client:
    if "submitted" not in st.session_state: st.session_state.submitted = False

    if not st.session_state.submitted:
        st.markdown(f"<h2 style='text-align: center; color: #d4af37;'>🏢 {OFFICE_NAME} - تسجيل طلب</h2>", unsafe_allow_html=True)
        with st.form("client_form", clear_on_submit=True):
            name = st.text_input("الاسم الكامل")
            phone = st.text_input("رقم الهاتف (واتساب)")
            region = st.selectbox("المنطقة المطلوبة", ["شهداء البياع", "المنصور", "حي الجامعة", "السيدية", "أخرى"])
            budget = st.text_input("الميزانية التقريبية")
            details = st.text_area("تفاصيل العقار المطلوب")
            send_btn = st.form_submit_button("إرسال الطلب الآن 🚀")
            
            if send_btn:
                if name and phone:
                    payload = {"name": name, "phone": phone, "region": region, "budget": budget, "details": details}
                    try:
                        response = requests.post(WEBHOOK_URL, params=payload)
                        if response.status_code in [200, 201]:
                            st.session_state.submitted = True
                            st.rerun()
                        else: st.error("عذراً، حدث خطأ في إرسال البيانات.")
                    except: st.error("فشل الاتصال بالخادم.")
                else: st.warning("يرجى ملء الاسم ورقم الهاتف لإتمام الطلب.")
    else:
        st.balloons()
        st.markdown(f"""
            <div style="text-align: center; padding: 50px; background-color: #1a1c24; border-radius: 20px; border: 2px solid #d4af37; margin-top: 50px;">
                <h1 style="color: #d4af37; margin-bottom: 20px;">✅ تم استلام طلبك بنجاح!</h1>
                <p style="color: white; font-size: 1.3em;">شكراً لاختياركم مكتبنا، نحن نقدّر ثقتكم بنا وسنتصل بك قريباً.</p>
                <hr style="border-color: #333; margin: 30px 0;">
                <p style="color: #888; font-style: italic; font-size: 0.9em;">تم تطوير هذا النظام الذكي بواسطة المبرمج <b style="color: #d4af37;">سجاد</b></p>
            </div>
        """, unsafe_allow_html=True)
        if st.button("إرسال طلب آخر جديد"):
            st.session_state.submitted = False
            st.rerun()
    st.stop()

# --- واجهة الإدارة ---
if "authenticated" not in st.session_state: st.session_state["authenticated"] = False
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
        # البحث عن الأعمدة بمسمياتك (Customer_Name, Target_Region, إلخ)
        def find_c(names):
            for c in df.columns:
                if any(n.lower() in str(c).lower() for n in names): return c
            return df.columns[0]

        # ربط الأعمدة لضمان عدم ظهور N/A
        col_name = find_c(['customer_name', 'name', 'الاسم'])
        col_budget = find_c(['budget_range', 'budget', 'الميزانية'])
        col_region = find_c(['target_region', 'region', 'المنطقة'])
        col_analysis = find_c(['ai_analysis', 'analysis', 'تحليل'])
        col_time = find_c(['submission', 'time', 'date', 'تاريخ'])
        col_phone = find_c(['phone', 'هاتف', 'واتساب'])

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

        df['sort_t'] = pd.to_datetime(df[col_time], dayfirst=True, errors='coerce')
        df['sort_b'] = df[col_budget].apply(get_unified_value)
        df = df.sort_values(by=['sort_t', 'sort_b'], ascending=[False, False])
        
        st.markdown(f"<h3 style='color:#d4af37;'>📊 إجمالي طلبات {OFFICE_NAME}: {len(df)}</h3>", unsafe_allow_html=True)

        for _, row in df.iterrows():
            c_name = str(row.get(col_name, "زبون"))
            c_time = str(row.get(col_time, "N/A"))
            c_budget = str(row.get(col_budget, "غير محدد"))
            c_region = str(row.get(col_region, "غير محدد"))
            c_analysis = str(row.get(col_analysis, "لا يوجد تحليل"))
            c_phone = str(row.get(col_phone, ""))
            
            with st.container():
                st.markdown(f"""
                <div class="property-card">
                    <div style="display: flex; justify-content: space-between;">
                        <h2 style='color:white; margin:0;'>👤 {c_name}</h2>
                        <span style="color: #888;">📅 {c_time}</span>
                    </div>
                    <p style='color:white; margin-top:10px;'>📍 المنطقة المطلوبة: <b>{c_region}</b></p>
                    <p style="color: #2ecc71 !important; font-weight: bold; font-size: 1.3em;">💰 الميزانية: {c_budget}</p>
                    <div style="background-color: #2c3e50; padding: 15px; border-radius: 10px; border-left: 5px solid #d4af37;">
                        <p style='color:white; margin-bottom:5px;'>🤖 <b>تحليل النظام الذكي:</b></p>
                        <p style='color:#ecf0f1;'>{c_analysis}</p>
                    </div>
                </div>
                """, unsafe_allow_html=True)
                
                p_num = re.sub(r'\D', '', c_phone)
                st.link_button(f"تواصل مع {c_name} عبر واتساب 💬", f"https://wa.me/{p_num}", use_container_width=True)
                st.markdown("<br>", unsafe_allow_html=True)
    else:
        st.info("لا توجد طلبات مسجلة.")
except Exception as e:
    st.error(f"حدث خطأ: {e}")
    
