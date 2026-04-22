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

# رابط Pipedream القديم الخاص بك
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
        property_details = st.text_area("ما هو نوع العقار الذي تبحث عنه؟ (دار، شقة، مجمع..)")
        
        submitted = st.form_submit_button("إرسال الطلب الآن 🚀")
        
        if submitted:
            if name and phone:
                # تجهيز البيانات للإرسال لـ Pipedream
                data_to_send = {
                    "Customer_Name": name,
                    "Phone_Number": phone,
                    "Target_Region": region,
                    "Budget_Range": budget,
                    "Ai_Analysis": property_details,
                    "Lead_Quality": "New",
                    "Submission_Date": datetime.now().strftime("%Y-%m-%d %H:%M:%S")
                }
                try:
                    response = requests.post(WEBHOOK_URL, json=data_to_send)
                    if response.status_code == 200 or response.status_code == 201:
                        st.success("✅ تم استلام طلبك بنجاح! شكراً لثقتك بنا.")
                    else:
                        st.error("حدثت مشكلة بسيطة في الإرسال، يرجى المحاولة مرة أخرى.")
                except:
                    st.error("عذراً، تعذر الاتصال بالنظام. يرجى المحاولة لاحقاً.")
            else:
                st.warning("يرجى ملء الاسم ورقم الهاتف لإكمال الطلب.")
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
        st.error("⚠️ الرمز غير صحيح. الوصول مرفوض.")
    st.stop()

# --- تنسيق لوحة التحكم (CSS) ---
st.markdown("""
    <style>
    .property-card { background-color: #1a1c24; border-radius: 15px; padding: 20px; border: 1px solid #d4af37; margin-bottom: 20px; }
    .vip-badge { background: #d4af37; color: black; padding: 2px 10px; border-radius: 10px; font-weight: bold; }
    h2, p { color: white !important; }
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
    if df.empty:
        st.info("لا توجد بيانات حالياً. بانتظار تسجيل أول زبون عبر QR Code.")
    else:
        # عرض البيانات من الأحدث إلى الأقدم
        df_display = df.iloc[::-1] 
        for _, row in df_display.iterrows():
            with st.container():
                st.markdown(f"""
                <div class="property-card">
                    <span class="vip-badge">💎 {row.get('Lead_Quality', 'New')}</span>
                    <h2>👤 {row.get('Customer_Name', 'Unknown')}</h2>
                    <p>📍 المنطقة: {row.get('Target_Region', 'N/A')}</p>
                    <p style="color: #2ecc71 !important; font-weight: bold;">💰 الميزانية: {row.get('Budget_Range', 'N/A')}</p>
                    <p style="color: #888; font-size: 0.9em;">📅 {row.get('Submission_Date', 'N/A')}</p>
                    <div style="background-color: #2c3e50; padding: 15px; border-radius: 10px; margin-top: 10px;">
                        <p>🤖 <b>الطلب:</b><br>{row.get('Ai_Analysis', 'لا توجد تفاصيل إضافية')}</p>
                    </div>
                </div>
                """, unsafe_allow_html=True)
                st.link_button(f"تواصل عبر واتساب 💬", f"https://wa.me/{str(row.get('Phone_Number', '')).replace('.0','')}", use_container_width=True)
                st.markdown("<br>", unsafe_allow_html=True)
except Exception as e:
    st.warning("جاري مزامنة البيانات... تأكد من اتصالك بالإنترنت.")
    
