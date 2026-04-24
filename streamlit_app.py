import streamlit as st
import pandas as pd
from datetime import datetime
import requests
import re
from io import StringIO

# 1. إعدادات الصفحة
st.set_page_config(page_title="عقارات البياع | Matrix Pro", layout="wide")

# --- 🛠️ الإعدادات (بياناتك المباشرة من الصور والروابط) ---
OFFICE_NAME = "عقارات البياع" 
ADMIN_PWD = "123456246SsS@" #
MY_SHEET_ID = "1a9MO2P78L7XBggmlkYKYfjnslAAyvGxOeffnv1LT_ac" #
WEBHOOK_URL = "https://eomfdq8l221q30q.m.pipedream.net" #
DATA_CSV_URL = f"https://docs.google.com/spreadsheets/d/{MY_SHEET_ID}/export?format=csv"

# -------------------------------------------------------

params = st.query_params
view_type = params.get("view", "admin") 

# --- 📱 واجهة الزبون (view=client) ---
if view_type == "client":
    st.markdown(f"<h1 style='text-align: center; color: #d4af37;'>🏢 {OFFICE_NAME}</h1>", unsafe_allow_html=True)
    with st.form("c_form", clear_on_submit=True):
        name = st.text_input("الأسم الكامل")
        phone = st.text_input("رقم الهاتف")
        region = st.selectbox("المنطقة", ["البياع", "شهداء البياع", "السيدية", "أخرى"])
        budget = st.text_input("الميزانية")
        if st.form_submit_button("إرسال الطلب 🚀"):
            if name and phone:
                requests.post(WEBHOOK_URL, params={"name": name, "phone": phone, "region": region, "budget": budget, "source": OFFICE_NAME})
                st.success("✅ تم استلام طلبك")
    st.stop()

# --- 🔒 واجهة الإدارة ---
if "auth" not in st.session_state: st.session_state.auth = False

if not st.session_state.auth:
    st.markdown(f"<h2 style='text-align: center; color: #d4af37;'>🔒 دخول إدارة {OFFICE_NAME}</h2>", unsafe_allow_html=True)
    pwd = st.text_input("أدخل الرمز السري:", type="password")
    if st.button("تسجيل الدخول"):
        if pwd == ADMIN_PWD:
            st.session_state.auth = True
            st.rerun()
        else:
            st.error("الرمز السري غير صحيح")
    st.stop()

# --- 📊 عرض البيانات (الكروت الاحترافية بناءً على أعمدتك) ---
st.markdown(f"### 📊 سجل الطلبات والتحليل الذكي")

try:
    # جلب البيانات مع كسر الكاش لضمان التحديث اللحظي
    response = requests.get(f"{DATA_CSV_URL}&cb={datetime.now().timestamp()}", timeout=10)
    if response.status_code == 200:
        df = pd.read_csv(StringIO(response.text))
        
        # تنظيف أسماء الأعمدة لضمان المطابقة
        df.columns = [c.strip() for c in df.columns]
        
        if not df.empty:
            for idx, row in df.iloc[::-1].iterrows():
                # استخراج البيانات حسب مسمياتك
                c_name = row.get('Customer_Name', 'غير معروف')
                budget = row.get('Budget_Range', 'غير محدد')
                region = row.get('Target_Region', 'غير محدد')
                ai_analysis = row.get('Ai_Analysis', 'لا يوجد تحليل حالي')
                quality = row.get('Lead_Quality', 'N/A')
                phone = str(row.get('Phone_Number', ''))
                wa_link = row.get('WhatsApp_Link', '#')
                s_date = row.get('Submission_Date', '')

                # تصميم الكارت
                st.markdown(f"""
                <div style="background-color: #1a1c24; border-radius: 15px; padding: 20px; border-right: 5px solid #d4af37; margin-bottom: 20px; direction: rtl; text-align: right;">
                    <div style="display: flex; justify-content: space-between; align-items: center;">
                        <h3 style="color: white; margin: 0;">👤 {c_name}</h3>
                        <span style="background-color: #d4af37; color: black; padding: 2px 12px; border-radius: 10px; font-weight: bold; font-size: 0.8em;">{quality}</span>
                    </div>
                    <p style="color: #aaa; font-size: 0.85em; margin: 5px 0;">📅 التاريخ: {s_date}</p>
                    <div style="display: flex; gap: 20px; margin: 15px 0;">
                        <div style="color: #2ecc71;"><b>💰 الميزانية:</b> {budget}</div>
                        <div style="color: #3498db;"><b>📍 المنطقة:</b> {region}</div>
                    </div>
                    <div style="background-color: #252833; padding: 12px; border-radius: 8px; border: 1px solid #333;">
                        <p style="color: #ecf0f1; font-size: 0.9em; margin: 0;"><b>🤖 تحليل الذكاء الاصطناعي:</b><br>{ai_analysis}</p>
                    </div>
                </div>
                """, unsafe_allow_html=True)
                
                # أزرار الاتصال
                col1, col2 = st.columns(2)
                with col1:
                    p_clean = re.sub(r'\D', '', phone)
                    final_wa = wa_link if (isinstance(wa_link, str) and wa_link.startswith('http')) else f"https://wa.me/{p_clean}"
                    st.link_button("💬 واتساب مباشر", final_wa, use_container_width=True)
                with col2:
                    st.link_button("📞 اتصال هاتف", f"tel:{phone}", use_container_width=True)
                st.markdown("<br>", unsafe_allow_html=True)
        else:
            st.info("الجدول فارغ حالياً.")
    else:
        st.error(f"خطأ {response.status_code}: تأكد من إعدادات المشاركة في جدول جوجل.")
except Exception as e:
    st.error(f"حدث خطأ في عرض البيانات: {e}")
    
