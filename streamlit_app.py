import streamlit as st
import pandas as pd
from datetime import datetime
import requests
import re
from io import StringIO

# 1. إعدادات الصفحة الفنية
st.set_page_config(page_title="عقارات البياع | Matrix Pro", layout="wide")

# --- 🛠️ القسم الذي قمت بتعديله ببياناتك الصحيحة من الصور ---
OFFICE_NAME = "عقارات البياع" 
ADMIN_PWD = "123456246SsS@"  # الرمز السري الخاص بك من الصورة

# معرف الجدول الخاص بك (المستخرج من الصورة 1000030523.jpg)
MY_SHEET_ID = "1a9MO2P78L7XBggmlkYKYfjnslAAyvGxOeffnv1LT_ac" 

# رابط الويب هوك الخاص بك (المستخرج من الصورة 1000030524.jpg)
WEBHOOK_URL = "https://eomfdq8l221q30q.m.pipedream.net"

# رابط تصدير البيانات من جوجل شيت
DATA_CSV_URL = f"https://docs.google.com/spreadsheets/d/{MY_SHEET_ID}/export?format=csv"

# -------------------------------------------------------

# قراءة الباراميترات من الرابط
params = st.query_params
view_type = params.get("view", "admin") 

# --- 📱 واجهة الزبون (تظهر عند إضافة ?view=client للرابط) ---
if view_type == "client":
    if "submitted" not in st.session_state: st.session_state.submitted = False

    if not st.session_state.submitted:
        st.markdown(f"<h1 style='text-align: center; color: #d4af37;'>🏢 {OFFICE_NAME}</h1>", unsafe_allow_html=True)
        st.markdown("<p style='text-align: center; color: #aaa;'>يرجى ملء الطلب وسنقوم بالتواصل معك فوراً</p>", unsafe_allow_html=True)
        
        with st.form("order_form", clear_on_submit=True):
            col1, col2 = st.columns(2)
            with col1:
                name = st.text_input("الأسم الكامل")
                phone = st.text_input("رقم الهاتف (واتساب)")
            with col2:
                region = st.selectbox("المنطقة المطلوب", ["البياع", "شهداء البياع", "السيدية", "أخرى"])
                budget = st.text_input("الميزانية")
            
            details = st.text_area("تفاصيل إضافية (مساحة العقار، نوعه، إلخ)")
            
            if st.form_submit_button("إرسال الطلب 🚀"):
                if name and phone:
                    payload = {
                        "name": name, 
                        "phone": phone, 
                        "region": region, 
                        "budget": budget, 
                        "details": details, 
                        "source": OFFICE_NAME
                    }
                    try:
                        requests.post(WEBHOOK_URL, params=payload, timeout=5)
                    except:
                        pass
                    st.session_state.submitted = True
                    st.rerun()
                else:
                    st.warning("يرجى إدخال الأسم ورقم الهاتف.")
    else:
        st.balloons()
        st.markdown(f"""
            <div style="text-align: center; padding: 40px; background-color: #1a1c24; border-radius: 20px; border: 2px solid #d4af37; margin-top: 30px;">
                <h1 style="color: #d4af37;">✅ تم الإرسال بنجاح</h1>
                <p style="color: white;">شكراً لثقتكم بمكتب <b>{OFFICE_NAME}</b>. سنتصل بك قريباً.</p>
            </div>
        """, unsafe_allow_html=True)
        if st.button("إرسال طلب جديد"):
            st.session_state.submitted = False
            st.rerun()
    st.stop()

# --- 🔒 واجهة الإدارة (Dashboard) ---
if "auth" not in st.session_state: st.session_state.auth = False

if not st.session_state.auth:
    st.markdown(f"<h2 style='text-align: center; color: #d4af37;'>🔒 لوحة إدارة {OFFICE_NAME}</h2>", unsafe_allow_html=True)
    col_a, col_b, col_c = st.columns([1,2,1])
    with col_b:
        pwd = st.text_input("رمز الدخول:", type="password")
        if st.button("دخول", use_container_width=True):
            if pwd == ADMIN_PWD:
                st.session_state.auth = True
                st.rerun()
            else:
                st.error("رمز الدخول غير صحيح")
    st.stop()

# عرض الطلبات للإدارة
st.markdown(f"<h2 style='color:#d4af37;'>📊 سجل عقارات وطلبات {OFFICE_NAME}</h2>", unsafe_allow_html=True)

try:
    # جلب البيانات مباشرة مع كسر الكاش لضمان الحداثة
    res = requests.get(f"{DATA_CSV_URL}?cb={datetime.now().timestamp()}", timeout=10)
    if res.status_code == 200:
        df = pd.read_csv(StringIO(res.text))
        
        if not df.empty:
            for idx, row in df.iloc[::-1].iterrows():
                with st.container():
                    st.markdown(f"""
                    <div style="background-color: #1a1c24; border-radius: 12px; padding: 15px; border: 1px solid #333; margin-bottom: 10px;">
                        <h3 style="color: white; margin: 0;">👤 {row.iloc[0]}</h3>
                        <p style="color: #2ecc71; margin: 5px 0;">📍 {row.iloc[2] if len(row)>2 else ''} | 💰 {row.iloc[3] if len(row)>3 else ''}</p>
                        <p style="color: #aaa;">{row.iloc[4] if len(row)>4 else ''}</p>
                    </div>
                    """, unsafe_allow_html=True)
                    
                    # زر واتساب
                    phone_val = str(row.iloc[1])
                    clean_phone = re.sub(r'\D', '', phone_val)
                    st.link_button(f"تواصل مع الزبون 💬", f"https://wa.me/{clean_phone}", use_container_width=True)
                    st.markdown("<br>", unsafe_allow_html=True)
        else:
            st.info("الجدول فارغ حالياً. لا توجد طلبات.")
    else:
        st.error(f"خطأ في الوصول للجدول: {res.status_code}")
except Exception as e:
    st.error("حدث خطأ أثناء جلب البيانات. تأكد من أن جدول جوجل متاح للمشاركة 'Anyone with link can view'.")
    
