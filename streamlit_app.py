دimport streamlit as st
import pandas as pd
from datetime import datetime
import requests
import re
from io import StringIO

# 1. إعدادات الصفحة
st.set_page_config(page_title="Matrix Real Estate Pro", layout="wide")

# تنظيف المعرف من الرابط لضمان عدم التداخل بين المكاتب
params = st.query_params
office_id = params.get("id", "bayaa").strip().lower()

# 2. رابط الماستر الصحيح الذي زودتنا به
NEW_MASTER_ID = "1sba6QhfnF5e4IlP8uV0Mku8X50OBIkzy_VekT63d_hI"
MASTER_CSV_URL = f"https://docs.google.com/spreadsheets/d/{NEW_MASTER_ID}/export?format=csv&gid=0"

@st.cache_data(ttl=0)
def load_config(oid):
    try:
        # جلب البيانات مع كسر الكاش لضمان التحديث اللحظي
        headers = {'Cache-Control': 'no-cache', 'Pragma': 'no-cache'}
        response = requests.get(f"{MASTER_CSV_URL}&cb={datetime.now().timestamp()}", headers=headers, timeout=15)
        
        if response.status_code != 200:
            return {"found": False, "err": f"خطأ اتصال (Error {response.status_code})"}
        
        df = pd.read_csv(StringIO(response.text))
        
        # تنظيف شامل للأعمدة (حذف المسافات وتحويلها لأصغر)
        df.columns = [str(c).strip().lower() for c in df.columns]
        
        if 'office_id' not in df.columns:
            return {"found": False, "err": "لم يتم العثور على عمود office_id في الجدول الجديد."}

        df['office_id'] = df['office_id'].astype(str).str.strip().str.lower()
        row = df[df['office_id'] == oid]
        
        if not row.empty:
            res = row.iloc[0]
            # تنظيف الـ Sheet ID (استخراج المعرف حتى لو كان رابطاً كاملاً)
            raw_sid = str(res.get('sheet_id', '')).strip()
            sid_match = re.search(r"/d/([a-zA-Z0-9-_]+)", raw_sid)
            final_sid = sid_match.group(1) if sid_match else raw_sid
            
            return {
                "found": True,
                "name": res.get('office_name', 'مكتب غير مسمى'),
                "webhook": str(res.get('webhook_url', '')).strip(),
                "sheet": final_sid,
                "pass": str(res.get('password', '1234'))
            }
    except Exception as e:
        return {"found": False, "err": str(e)}
    return {"found": False, "err": "المكتب غير مسجل في الجدول الحالي."}

# تحميل الإعدادات
config = load_config(office_id)

# حائط الصد في حال فشل النظام
if not config.get("found"):
    st.error(f"❌ خطأ: المكتب '{office_id}' غير متاح.")
    st.warning(f"التفاصيل الفنية: {config.get('err')}")
    st.info("تأكد من أن الجدول الجديد مفتوح للمشاركة (Anyone with the link) وأنك أضفت بيانات المكتب فيه.")
    st.stop()

# المتغيرات الأساسية
OFFICE_NAME = config['name']
WEBHOOK_URL = config['webhook']
SHEET_ID = config['sheet']
ADMIN_PWD = config['pass']
DATA_CSV = f"https://docs.google.com/spreadsheets/d/{SHEET_ID}/export?format=csv"

# --- 🟢 واجهة الزبون (Client View) ---
if params.get("view") == "client":
    if "submitted" not in st.session_state: st.session_state.submitted = False

    if not st.session_state.submitted:
        st.markdown(f"<h1 style='text-align: center; color: #d4af37;'>🏢 {OFFICE_NAME}</h1>", unsafe_allow_html=True)
        st.markdown("<p style='text-align: center; color: #aaa;'>يرجى ملء الطلب وسنقوم بالتواصل معك فوراً</p>", unsafe_allow_html=True)
        
        with st.form("client_order_form", clear_on_submit=True):
            col1, col2 = st.columns(2)
            with col1:
                name = st.text_input("الأسم الكامل")
                phone = st.text_input("رقم الهاتف (واتساب)")
            with col2:
                regions = ["البياع", "المدائن", "المنصور", "السيدية", "أخرى"]
                region = st.selectbox("المنطقة المطلوبة", regions)
                budget = st.text_input("الميزانية التقريبية")
            
            details = st.text_area("تفاصيل إضافية عن العقار")
            
            if st.form_submit_button(f"إرسال الطلب إلى {OFFICE_NAME} 🚀"):
                if name and phone:
                    payload = {"name": name, "phone": phone, "region": region, "budget": budget, "details": details, "source": OFFICE_NAME}
                    try:
                        requests.post(WEBHOOK_URL, params=payload, timeout=5)
                        st.session_state.submitted = True
                        st.rerun()
                    except:
                        st.session_state.submitted = True
                        st.rerun()
                else:
                    st.warning("يرجى إدخال الأسم ورقم الهاتف.")
    else:
        st.balloons()
        st.markdown(f"""
            <div style="text-align: center; padding: 40px; background-color: #1a1c24; border-radius: 20px; border: 2px solid #d4af37; margin-top: 30px;">
                <h1 style="color: #d4af37;">✅ تم الاستلام بنجاح!</h1>
                <p style="color: white; font-size: 1.1em;">شكراً لثقتكم بمكتب <b>{OFFICE_NAME}</b>. سنتصل بك قريباً.</p>
            </div>
        """, unsafe_allow_html=True)
        if st.button("إرسال طلب جديد"):
            st.session_state.submitted = False
            st.rerun()
    st.stop()

# --- 🔴 واجهة الإدارة (Admin Dashboard) ---
if "is_auth" not in st.session_state: st.session_state.is_auth = False

if not st.session_state.is_auth:
    st.markdown(f"<h2 style='text-align: center; color: #d4af37;'>🔒 لوحة إدارة {OFFICE_NAME}</h2>", unsafe_allow_html=True)
    password_input = st.text_input("رمز الدخول:", type="password")
    if st.button("دخول"):
        if password_input == ADMIN_PWD:
            st.session_state.is_auth = True
            st.rerun()
        else:
            st.error("رمز الدخول غير صحيح.")
    st.stop()

# عرض السجلات للإدارة
st.markdown(f"<h2 style='color:#d4af37;'>📊 سجل طلبات {OFFICE_NAME}</h2>", unsafe_allow_html=True)

try:
    # جلب بيانات الشيت الفرعي مع كسر الكاش
    res_leads = requests.get(f"{DATA_CSV}?cb={datetime.now().timestamp()}", timeout=10)
    df_leads = pd.read_csv(StringIO(res_leads.text))
    
    if not df_leads.empty:
        for idx, row in df_leads.iloc[::-1].iterrows():
            with st.container():
                st.markdown(f"""
                <div style="background-color: #1a1c24; border-radius: 12px; padding: 15px; border: 1px solid #d4af37; margin-bottom: 15px;">
                    <h3 style="color: white; margin: 0;">👤 {row.iloc[0]}</h3>
                    <p style="color: #2ecc71; margin: 5px 0;">💰 الميزانية: {row.iloc[3] if len(row)>3 else '—'}</p>
                    <p style="color: #aaa; font-size: 0.9em;">📝 {row.iloc[4] if len(row)>4 else 'بدون تفاصيل'}</p>
                </div>
                """, unsafe_allow_html=True)
                
                # زر التواصل عبر واتساب
                clean_phone = re.sub(r'\D', '', str(row.iloc[1]))
                st.link_button(f"تواصل عبر واتساب 💬", f"https://wa.me/{clean_phone}", use_container_width=True)
                st.markdown("<br>", unsafe_allow_html=True)
    else:
        st.info("لا توجد طلبات مسجلة حتى الآن.")
except:
    st.error("فشل جلب الطلبات. تأكد من إعدادات المشاركة (Anyone with link) في الجدول الخاص بالمكتب.")
        
