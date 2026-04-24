import streamlit as st
import pandas as pd
from datetime import datetime
import requests
import re
from io import StringIO

# 1. إعدادات الصفحة واللغة
st.set_page_config(page_title="عقارات البياع | Matrix Pro", layout="wide")

# --- 🛠️ الإعدادات الثابتة المستخرجة من بياناتك ---
OFFICE_NAME = "عقارات البياع" 
ADMIN_PWD = "123456246SsS@" # الرمز السري من صورتك
MY_SHEET_ID = "1a9MO2P78L7XBggmlkYKYfjnslAAyvGxOeffnv1LT_ac" # رابط جدول العقارات
DATA_CSV_URL = f"https://docs.google.com/spreadsheets/d/{MY_SHEET_ID}/export?format=csv"

# -------------------------------------------------------

# --- 🔒 واجهة الإدارة والدخول ---
if "auth" not in st.session_state: st.session_state.auth = False

if not st.session_state.auth:
    st.markdown("<h2 style='text-align: center; color: #d4af37;'>🔒 دخول إدارة عقارات البياع</h2>", unsafe_allow_html=True)
    col_a, col_b, col_c = st.columns([1,2,1])
    with col_b:
        pwd = st.text_input("أدخل الرمز السري:", type="password")
        if st.form_submit_button or st.button("تسجيل الدخول", use_container_width=True):
            if pwd == ADMIN_PWD:
                st.session_state.auth = True
                st.rerun()
            else:
                st.error("الرمز السري غير صحيح!")
    st.stop()

# --- 📊 عرض البيانات المستخرجة من جدولك ---
st.markdown(f"### 📊 سجل الطلبات والتحليل الذكي")

try:
    # جلب البيانات مع فرض ترميز UTF-8 لضمان ظهور العربية بشكل سليم [علاج لصورة 1000030531.jpg]
    response = requests.get(f"{DATA_CSV_URL}&cb={datetime.now().timestamp()}", timeout=15)
    response.encoding = 'utf-8' 
    
    if response.status_code == 200:
        # قراءة البيانات وتنظيف أسماء الأعمدة من أي مسافات زائدة
        df = pd.read_csv(StringIO(response.text))
        df.columns = [c.strip() for c in df.columns]
        
        if not df.empty:
            for idx, row in df.iloc[::-1].iterrows():
                # قراءة الأعمدة السبعة التي حددتها
                c_name = str(row.get('Customer_Name', 'غير معروف'))
                budget = str(row.get('Budget_Range', 'غير محدد'))
                region = str(row.get('Target_Region', 'غير محدد'))
                ai_analysis = str(row.get('Ai_Analysis', 'لا يوجد تحليل'))
                quality = str(row.get('Lead_Quality', 'N/A'))
                phone = str(row.get('Phone_Number', ''))
                s_date = str(row.get('Submission_Date', ''))

                # تصميم الكارت الاحترافي (اتجاه النص يمين RTL)
                st.markdown(f"""
                <div style="background-color: #1a1c24; border-radius: 15px; padding: 20px; border-right: 5px solid #d4af37; margin-bottom: 20px; direction: rtl; text-align: right;">
                    <div style="display: flex; justify-content: space-between; align-items: center;">
                        <h3 style="color: white; margin: 0;">👤 {c_name}</h3>
                        <span style="background-color: #d4af37; color: black; padding: 2px 12px; border-radius: 10px; font-weight: bold; font-size: 0.8em;">{quality}</span>
                    </div>
                    <p style="color: #888; font-size: 0.85em; margin: 5px 0;">📅 تاريخ الطلب: {s_date}</p>
                    <hr style="border: 0.1px solid #333;">
                    <div style="display: flex; gap: 30px; margin: 10px 0;">
                        <p style="color: #2ecc71; margin: 0;"><b>💰 الميزانية:</b> {budget}</p>
                        <p style="color: #3498db; margin: 0;"><b>📍 المنطقة:</b> {region}</p>
                    </div>
                    <div style="background-color: #252833; padding: 12px; border-radius: 8px; border: 1px solid #333; margin-top: 10px;">
                        <p style="color: #ecf0f1; font-size: 0.95em; margin: 0;"><b>🤖 تحليل الذكاء الاصطناعي:</b><br>{ai_analysis}</p>
                    </div>
                </div>
                """, unsafe_allow_html=True)
                
                # أزرار الاتصال
                col1, col2 = st.columns(2)
                with col1:
                    p_clean = re.sub(r'\D', '', phone)
                    st.link_button(f"💬 واتساب مباشر", f"https://wa.me/{p_clean}", use_container_width=True)
                with col2:
                    st.link_button(f"📞 اتصال هاتف", f"tel:{phone}", use_container_width=True)
                st.markdown("<br>", unsafe_allow_html=True)
        else:
            st.info("الجدول فارغ حالياً في جوجل شيت.")
    else:
        st.error(f"خطأ {response.status_code}: تأكد من إعدادات مشاركة الجدول 'Anyone with link'.")
except Exception as e:
    st.error(f"حدث خطأ تقني: {e}")
    
