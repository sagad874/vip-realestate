import streamlit as st
import pandas as pd
from datetime import datetime
import requests
import re

# 1. إعدادات الصفحة
st.set_page_config(page_title="Pro Data Matrix | Secured", layout="wide")

# قراءة الـ ID من الرابط مع تنظيفه فوراً
params = st.query_params
office_id = params.get("id", "none").strip().lower()

# 2. رابط جدول الماستر الرئيسي
MASTER_CSV = "https://docs.google.com/spreadsheets/d/1a9MO2P78L7XBggmlkYKYfjnslAAyvGxOeffnv1LT_ac/export?format=csv"

@st.cache_data(ttl=0) # تصفير الكاش لضمان القراءة الحية من الجدول
def load_office_config(oid):
    try:
        # كسر كاش جوجل بختم زمني فريد
        master_url_with_cb = f"{MASTER_CSV}?cb={datetime.now().timestamp()}"
        df = pd.read_csv(master_url_with_cb)
        
        # تنظيف أسماء الأعمدة: مسح المسافات وتحويلها لأحرف صغيرة
        df.columns = [c.strip().lower() for c in df.columns]
        
        # تنظيف البيانات داخل عمود office_id: مسح المسافات وتحويلها لأحرف صغيرة
        df['office_id'] = df['office_id'].astype(str).str.strip().str.lower()
        
        # البحث عن المكتب المطابق
        row = df[df['office_id'] == oid]
        
        if not row.empty:
            res = row.iloc[0]
            return {
                "found": True,
                "name": res.get('office_name', 'مكتب غير مسمى'),
                "webhook": str(res.get('webhook_url', '')).strip(),
                "sheet": str(res.get('sheet_id', '')).strip(),
                "pass": str(res.get('password', '1234'))
            }
    except Exception as e:
        st.error(f"فشل الاتصال بجدول الماستر: {e}")
    return {"found": False}

# تحميل الإعدادات بناءً على ID الرابط
config = load_office_config(office_id)

# --- نظام الحماية: إذا لم يجد المكتب ---
if not config.get("found"):
    st.error(f"⚠️ تنبيه: المكتب '{office_id}' غير مسجل حالياً في جدول المكاتب.")
    st.info("يرجى التأكد من كتابة الـ office_id في جدول جوجل بدقة (بدون مسافات زائدة).")
    st.stop()

# تعريف المتغيرات بعد التأكد من وجود المكتب
OFFICE_NAME = config['name']
WEBHOOK_URL = config['webhook']
SHEET_ID = config['sheet']
CSV_URL = f"https://docs.google.com/spreadsheets/d/{SHEET_ID}/export?format=csv"
PASSWORD = config['pass']

# --- واجهة الزبون (Client View) ---
is_client = params.get("view") == "client"

if is_client:
    if "submitted" not in st.session_state:
        st.session_state.submitted = False

    if not st.session_state.submitted:
        st.markdown(f"<h2 style='text-align: center; color: #d4af37;'>🏢 {OFFICE_NAME} - طلب عقار</h2>", unsafe_allow_html=True)
        with st.form("client_form", clear_on_submit=True):
            name = st.text_input("الاسم الكامل")
            phone = st.text_input("رقم الهاتف (واتساب)")
            
            # قائمة مناطق بغداد المنبثقة
            baghdad_regions = [
                "شهداء البياع", "البياع", "المنصور", "حي الجامعة", "السيدية", "العامرية", 
                "الغزالية", "الدورة", "اليرموك", "القادسية", "زيونة", "أخرى"
            ]
            region = st.selectbox("المنطقة المطلوبة", baghdad_regions)
            
            budget = st.text_input("الميزانية التقريبية")
            details = st.text_area("تفاصيل الطلب")
            
            if st.form_submit_button(f"إرسال الطلب إلى {OFFICE_NAME} 🚀"):
                if name and phone:
                    try:
                        requests.post(WEBHOOK_URL, params={"name": name, "phone": phone, "region": region, "budget": budget, "details": details, "source": OFFICE_NAME}, timeout=5)
                        st.session_state.submitted = True
                        st.rerun()
                    except:
                        st.session_state.submitted = True
                        st.rerun()
                else:
                    st.warning("يرجى ملء الاسم والهاتف.")
    else:
        st.balloons()
        st.markdown(f"""
            <div style="text-align: center; padding: 50px; background-color: #1a1c24; border-radius: 20px; border: 2px solid #d4af37; margin-top: 50px;">
                <h1 style="color: #d4af37;">✅ تم الاستلام بنجاح!</h1>
                <p style="color: white; font-size: 1.2em;">شكراً لثقتكم بـ <b>{OFFICE_NAME}</b>. سنتصل بك قريباً.</p>
                <hr style="border-color: #333; margin: 30px 0;">
                <p style="color: #888; font-style: italic;">تم تطوير النظام بواسطة المبرمج سجاد</p>
            </div>
        """, unsafe_allow_html=True)
        if st.button("إرسال طلب جديد"):
            st.session_state.submitted = False
            st.rerun()
    st.stop()

# --- واجهة الإدارة (Admin View) ---
if "auth" not in st.session_state:
    st.session_state.auth = False

if not st.session_state.auth:
    st.markdown(f"<h2 style='text-align: center; color: #d4af37;'>🔒 لوحة تحكم {OFFICE_NAME}</h2>", unsafe_allow_html=True)
    if st.text_input("رمز الوصول:", type="password") == PASSWORD:
        st.session_state.auth = True
        st.rerun()
    st.stop()

st.markdown("""<style>.card { background-color: #1a1c24; border-radius: 15px; padding: 20px; border: 1px solid #d4af37; margin-bottom: 20px; }</style>""", unsafe_allow_html=True)

try:
    # جلب البيانات مع كسر الكاش لضمان التحديث اللحظي
    df_data = pd.read_csv(f"{CSV_URL}?cb={datetime.now().timestamp()}")
    if not df_data.empty:
        st.markdown(f"<h3 style='color:#d4af37;'>📊 سجل طلبات {OFFICE_NAME}</h3>", unsafe_allow_html=True)
        
        # عرض البيانات من الأحدث إلى الأقدم
        for _, row in df_data.iloc[::-1].iterrows():
            with st.container():
                st.markdown(f"""
                <div class="card">
                    <h2 style='color:white; margin:0;'>👤 {row.iloc[0]}</h2>
                    <p style="color: #2ecc71; font-weight: bold; font-size: 1.2em; margin: 10px 0;">💰 الميزانية: {row.iloc[3] if len(row)>3 else '—'}</p>
                    <p style='color:white;'>📍 المنطقة: {row.iloc[2] if len(row)>2 else '—'}</p>
                    <p style='color:#aaa; font-size: 0.9em;'>📝 {row.iloc[4] if len(row)>4 else 'لا توجد تفاصيل'}</p>
                </div>
                """, unsafe_allow_html=True)
                
                # زر الواتساب
                raw_phone = str(row.iloc[1])
                clean_phone = re.sub(r'\D', '', raw_phone)
                st.link_button(f"تواصل عبر واتساب 💬", f"https://wa.me/{clean_phone}", use_container_width=True)
                st.markdown("<br>", unsafe_allow_html=True)
    else:
        st.info(f"لا توجد طلبات مسجلة لمكتب {OFFICE_NAME}.")
except Exception as e:
    st.error("فشل في تحميل جدول البيانات. تأكد من إعدادات المشاركة (Anyone with link).")
    
