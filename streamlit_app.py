import streamlit as st
import pandas as pd

# 1. إعدادات الأمان والقفل الفائق
st.set_page_config(page_title="Pro Data Matrix | Secured", layout="wide")

# كلمة السر الخاصة بك التي اخترتها
PASSWORD = "123456246SsS@"

# التحقق من حالة تسجيل الدخول باستخدام Session State
if "authenticated" not in st.session_state:
    st.session_state["authenticated"] = False

if not st.session_state["authenticated"]:
    # واجهة قفل أنيقة
    st.markdown("<h2 style='text-align: center; color: #d4af37;'>🔒 نظام إدارة البيانات محمي</h2>", unsafe_allow_html=True)
    st.markdown("<p style='text-align: center; color: #888;'>يرجى إدخال رمز الوصول للمتابعة</p>", unsafe_allow_html=True)
    
    # خانة إدخال كلمة السر
    user_input = st.text_input("رمز الوصول:", type="password", help="أدخل كلمة السر الخاصة بالمدير")
    
    if user_input:
        if user_input == PASSWORD:
            st.session_state["authenticated"] = True
            st.rerun()
        else:
            st.error("⚠️ الرمز الذي أدخلته غير صحيح. الوصول مرفوض.")
    st.stop() # إيقاف تنفيذ بقية الكود تماماً

# --- إذا وصل الكود هنا، فهذا يعني أن الدخول ناجح ---

# تنسيق الواجهة الاحترافية (CSS)
st.markdown("""
    <style>
    .main { background-color: #0e1117; }
    .property-card {
        background-color: #1a1c24;
        border-radius: 15px;
        padding: 20px;
        border: 1px solid #d4af37;
        margin-bottom: 20px;
        transition: 0.3s;
    }
    .property-card:hover {
        border-color: #ffffff;
        box-shadow: 0px 4px 15px rgba(212, 175, 55, 0.3);
    }
    .vip-badge {
        background: #d4af37;
        color: black;
        padding: 2px 10px;
        border-radius: 10px;
        font-weight: bold;
    }
    .date-text { color: #888888 !important; font-size: 0.85em; }
    h2, p { color: white !important; }
    </style>
    """, unsafe_allow_html=True)

# رابط البيانات من Google Sheets
SHEET_ID = "1a9MO2P78L7XBggmlkYKYfjnslAAyvGxOeffnv1LT_ac"
CSV_URL = f"https://docs.google.com/spreadsheets/d/{SHEET_ID}/export?format=csv"

# الهيدر وزر تسجيل الخروج
col_title, col_logout = st.columns([0.8, 0.2])
with col_title:
    st.markdown("<h1 style='color: #d4af37;'>📊 Pro Data Matrix Engine</h1>", unsafe_allow_html=True)
with col_logout:
    if st.button("🔴 خروج"):
        st.session_state["authenticated"] = False
        st.rerun()

try:
    # جلب البيانات
    df = pd.read_csv(CSV_URL)
    
    if df.empty:
        st.info("النظام يعمل بنجاح، بانتظار وصول بيانات جديدة من العملاء.")
    else:
        # عرض البيانات بشكل كروت مرتبة
        for _, row in df.iterrows():
            with st.container():
                st.markdown(f"""
                <div class="property-card">
                    <span class="vip-badge">💎 {row['Lead_Quality']}</span>
                    <h2>👤 {row['Customer_Name']}</h2>
                    <p>📍 المنطقة: {row['Target_Region']}</p>
                    <p style="color: #2ecc71 !important; font-weight: bold;">💰 الميزانية: {row['Budget_Range']}</p>
                    <p class="date-text">📅 توقيت التسجيل: {row['Submission_Date']}</p>
                    <div style="background-color: #2c3e50; padding: 15px; border-radius: 10px; margin-top: 10px;">
                        <p>🤖 <b>التحليل الذكي للبيانات:</b><br>{row['Ai_Analysis']}</p>
                    </div>
                </div>
                """, unsafe_allow_html=True)
                
                # زر التواصل (يستخدم رقم الهاتف من الشيت)
                st.link_button(f"فتح محادثة واتساب مع {row['Customer_Name']} 💬", f"https://wa.me/{row['Phone_Number']}", use_container_width=True)
                st.markdown("<br>", unsafe_allow_html=True)

except Exception as e:
    st.warning("جاري الاتصال بقاعدة البيانات... يرجى التأكد من توفر الإنترنت.")
    
