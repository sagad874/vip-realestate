import streamlit as st
import pandas as pd
from datetime import datetime
import requests
import re

# 1. إعدادات الصفحة
st.set_page_config(page_title="Pro Data Matrix | Secured", layout="wide")

# التحقق من "الوضع" (زبون أم مدير)
query_params = st.query_params
is_client = query_params.get("view") == "client"

# روابط البيانات
SHEET_ID = "1a9MO2P78L7XBggmlkYKYfjnslAAyvGxOeffnv1LT_ac"
CSV_URL = f"https://docs.google.com/spreadsheets/d/{SHEET_ID}/export?format=csv"
WEBHOOK_URL = "https://eomfdq8l221q30q.m.pipedream.net"

# --- واجهة الزبون (واجهة الـ QR Code) ---
if is_client:
    st.markdown("<h2 style='text-align: center; color: #d4af37;'>🏢 مكتب العقار - تسجيل طلب</h2>", unsafe_allow_html=True)
    with st.form("client_form", clear_on_submit=True):
        name = st.text_input("الاسم الكامل")
        phone = st.text_input("رقم الهاتف (واتساب)")
        region = st.selectbox("المنطقة المطلوبة", ["شهداء البياع", "المنصور", "حي الجامعة", "السيدية", "أخرى"])
        budget = st.text_input("الميزانية التقريبية")
        details = st.text_area("تفاصيل العقار المطلوب")
        submitted = st.form_submit_button("إرسال الطلب الآن 🚀")
        
        if submitted:
            if name and phone:
                payload = {
                    "name": name,
                    "phone": phone,
                    "region": region,
                    "budget": budget,
                    "details": details
                }
                try:
                    response = requests.post(WEBHOOK_URL, params=payload)
                    if response.status_code in [200, 201]:
                        st.success("✅ تم استلام طلبك بنجاح!")
                    else:
                        st.error("خطأ في الربط مع النظام.")
                except:
                    st.error("فشل الاتصال بالخادم.")
            else:
                st.warning("يرجى ملء الاسم والهاتف.")
    st.stop()

# --- واجهة الإدارة (المحمية) ---
PASSWORD = "123456246SsS@"
if "authenticated" not in st.session_state:
    st.session_state["authenticated"] = False

if not st.session_state["authenticated"]:
    st.markdown("<h2 style='text-align: center; color: #d4af37;'>🔒 لوحة التحكم</h2>", unsafe_allow_html=True)
    user_input = st.text_input("رمز الوصول:", type="password")
    if user_input == PASSWORD:
        st.session_state["authenticated"] = True
        st.rerun()
    st.stop()

# تنسيق العرض للمدير
st.markdown("""<style>.property-card { background-color: #1a1c24; border-radius: 15px; padding: 20px; border: 1px solid #d4af37; margin-bottom: 20px; }</style>""", unsafe_allow_html=True)

try:
    df = pd.read_csv(CSV_URL)
    if not df.empty:
        # --- ميزة الترتيب الجديدة حسب الميزانية ---
        def extract_numeric_budget(val):
            # استخراج الأرقام فقط من نص الميزانية (مثلاً "500 مليون" تصبح 500)
            numbers = re.findall(r'\d+', str(val))
            return int(numbers[0]) if numbers else 0

        # إنشاء عمود مؤقت للترتيب (لن يظهر للزبون)
        df['temp_sort'] = df.apply(lambda x: extract_numeric_budget(x.get('Budget', '0')), axis=1)
        
        # ترتيب الجدول من الأعلى إلى الأقل
        df_display = df.sort_values(by='temp_sort', ascending=False)
        
        for _, row in df_display.iterrows():
            def get_v(key):
                for col in row.index:
                    if key.lower() in str(col).lower(): return str(row[col])
                return "N/A"
            
            with st.container():
                st.markdown(f"""
                <div class="property-card">
                    <h2 style='color:white;'>👤 {get_v('Name')}</h2>
                    <p style='color:white;'>📍 المنطقة: {get_v('Region')}</p>
                    <p style="color: #2ecc71 !important; font-weight: bold; font-size: 1.2em;">💰 الميزانية: {get_v('Budget')}</p>
                    <p style="color: #888;">📅 {get_v('Time')}</p>
                    <div style="background-color: #2c3e50; padding: 15px; border-radius: 10px;">
                        <p style='color:white;'>🤖 <b>التحليل الذكي:</b><br>{get_v('Analysis')}</p>
                    </div>
                </div>
                """, unsafe_allow_html=True)
                phone_num = str(get_v('Phone')).replace('.0','')
                st.link_button("واتساب 💬", f"https://wa.me/{phone_num}", use_container_width=True)
                st.markdown("<br>", unsafe_allow_html=True)
except Exception as e:
    st.warning("جاري مزامنة البيانات...")
    
