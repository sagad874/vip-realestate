import streamlit as st
import pandas as pd
from datetime import datetime
import requests

# 1. إعدادات الصفحة
st.set_page_config(page_title="Pro Data Matrix | Secured", layout="wide")

# التحقق من "الوضع" (هل هو زبون عبر QR أم مدير؟)
query_params = st.query_params
is_client = query_params.get("view") == "client"

# رابط البيانات (للقراءة فقط من الشيت)
SHEET_ID = "1a9MO2P78L7XBggmlkYKYfjnslAAyvGxOeffnv1LT_ac"
CSV_URL = f"https://docs.google.com/spreadsheets/d/{SHEET_ID}/export?format=csv"

# رابط Pipedream الخاص بك
WEBHOOK_URL = "https://eomfdq8l221q30q.m.pipedream.net"

# --- واجهة الزبون (واجهة الـ QR Code) ---
if is_client:
    st.markdown("<h2 style='text-align: center; color: #d4af37;'>🏢 مكتب العقار - تسجيل طلب</h2>", unsafe_allow_html=True)
    st.markdown("<p style='text-align: center; color: #888;'>يرجى ملء البيانات لنتواصل معك بأقرب وقت</p>", unsafe_allow_html=True)
    
    with st.form("client_form", clear_on_submit=True):
        name = st.text_input("الاسم الكامل")
        phone = st.text_input("رقم الهاتف (واتساب)")
        region = st.selectbox("المنطقة المطلوبة", ["شهداء البياع", "المنصور", "حي الجامعة", "السيدية", "البياع", "أخرى"])
        budget = st.text_input("الميزانية التقريبية")
        property_details = st.text_area("ما هو نوع العقار الذي تبحث عنه؟")
        
        submitted = st.form_submit_button("إرسال الطلب الآن 🚀")
        
        if submitted:
            if name and phone:
                # تجهيز البيانات لتطابق Pipedream 100% حسب صورك
                data_to_send = {
                    "Name": name,
                    "Phone": phone,
                    "region": region,
                    "budget": budget,
                    "AI_Analysis": property_details,
                    "Lead_Quality": "New",
                    "WhatsApp": f"https://wa.me/{phone}",
                    "Time": datetime.now().strftime("%Y-%m-%d %H:%M:%S")
                }
                try:
                    response = requests.post(WEBHOOK_URL, json=data_to_send)
                    if response.status_code == 200 or response.status_code == 201:
                        st.success("✅ تم استلام طلبك بنجاح!")
                    else:
                        st.error("فشل الإرسال، تأكد من إعدادات Pipedream.")
                except:
                    st.error("عذراً، تعذر الاتصال بالنظام.")
            else:
                st.warning("يرجى ملء الاسم ورقم الهاتف.")
    st.stop()

# --- واجهة المدير (المحمية بكلمة سر) ---
PASSWORD = "123456246SsS@"

if "authenticated" not in st.session_state:
    st.session_state["authenticated"] = False

if not st.session_state["authenticated"]:
    st.markdown("<h2 style='text-align: center; color: #d4af37;'>🔒 لوحة التحكم المحمية</h2>", unsafe_allow_html=True)
    user_input = st.text_input("رمز الوصول:", type="password")
    if user_input == PASSWORD:
        st.session_state["authenticated"] = True
        st.rerun()
    elif user_input:
        st.error("⚠️ الرمز غير صحيح.")
    st.stop()

# تنسيق لوحة التحكم
st.markdown("""
    <style>
    .property-card { background-color: #1a1c24; border-radius: 15px; padding: 20px; border: 1px solid #d4af37; margin-bottom: 20px; }
    .vip-badge { background: #d4af37; color: black; padding: 2px 10px; border-radius: 10px; font-weight: bold; }
    </style>
    """, unsafe_allow_html=True)

col_title, col_logout = st.columns([0.8, 0.2])
with col_title:
    st.markdown("<h1 style='color: #d4af37;'>📊 Pro Data Matrix Engine</h1>", unsafe_allow_html=True)
with col_logout:
    if st.button("🔴 خروج"):
        st.session_state["authenticated"] = False
        st.rerun()

try:
    df = pd.read_csv(CSV_URL)
    if not df.empty:
        df_display = df.iloc[::-1] 
        for _, row in df_display.iterrows():
            with st.container():
                # هنا نستخدم get_val للبحث عن العمود مهما كان اسمه
                def get_v(key):
                    for col in row.index:
                        if key.lower() in str(col).lower(): return row[col]
                    return "N/A"

                st.markdown(f"""
                <div class="property-card">
                    <span class="vip-badge">💎 {get_v('Quality')}</span>
                    <h2 style='color:white;'>👤 {get_v('Name')}</h2>
                    <p style='color:white;'>📍 المنطقة: {get_v('Region')}</p>
                    <p style="color: #2ecc71 !important; font-weight: bold;">💰 الميزانية: {get_v('Budget')}</p>
                    <p style="color: #888; font-size: 0.8em;">📅 {get_v('Date') or get_v('Time')}</p>
                    <div style="background-color: #2c3e50; padding: 15px; border-radius: 10px;">
                        <p style='color:white;'>🤖 <b>الطلب:</b><br>{get_v('Analysis')}</p>
                    </div>
                </div>
                """, unsafe_allow_html=True)
                phone_num = str(get_v('Phone')).replace('.0','')
                st.link_button("واتساب 💬", f"https://wa.me/{phone_num}", use_container_width=True)
except:
    st.warning("جاري التحديث...")
                        
