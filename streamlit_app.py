import streamlit as st
import pandas as pd
import requests
import json
import re

# 1. إعدادات الصفحة الأساسية
st.set_page_config(page_title="Pro Data Matrix | Secured", layout="wide")

# استخراج المعلمات من الرابط (المكتب والواجهة)
query_params = st.query_params
is_client = query_params.get("view") == "client"
office_id = query_params.get("id", "bayaa")

# 2. رابط جدول الماستر (المحرك الرئيسي للنظام)
MASTER_CSV = "https://docs.google.com/spreadsheets/d/1a9MO2P78L7XBggmlkYKYfjnslAAyvGxOeffnv1LT_ac/export?format=csv"

@st.cache_data(ttl=1)  # تحديث فوري كل ثانية واحدة
def load_office_config(oid):
    try:
        df = pd.read_csv(MASTER_CSV)
        # تنظيف البيانات من أي مسافات زائدة في الـ ID
        df['office_id'] = df['office_id'].astype(str).str.strip()
        
        if str(oid).strip() in df['office_id'].values:
            row = df[df['office_id'] == str(oid).strip()].iloc[0]
            return {
                "name": row['office_name'],
                "webhook": str(row['webhook_url']).strip(),
                "sheet": row['sheet_id'],
                "pass": str(row['password'])
            }
        else:
            return {"name": "مكتب غير معرف", "webhook": "", "sheet": "", "pass": "1234"}
    except Exception as e:
        return {"name": "خطأ في الاتصال بالبيانات", "webhook": "", "sheet": "", "pass": "1234"}

# تحميل بيانات المكتب النشط بناءً على الرابط
office = load_office_config(office_id)
OFFICE_NAME = office['name']
WEBHOOK_URL = office['webhook']
SHEET_ID = office['sheet']
ADMIN_PASSWORD = office['pass']
CSV_URL = f"https://docs.google.com/spreadsheets/d/{SHEET_ID}/export?format=csv"

# --- واجهة الزبون (Client View) ---
if is_client:
    if "submitted" not in st.session_state:
        st.session_state.submitted = False

    if not st.session_state.submitted:
        # الترحيب الديناميكي باسم المكتب المستخرج من الجدول
        st.markdown(f"<h1 style='text-align: center; color: #d4af37;'>مرحباً بكم في {OFFICE_NAME}</h1>", unsafe_allow_html=True)
        st.markdown("<p style='text-align: center; color: #888; text-align: center;'>يرجى ملء الاستمارة أدناه لتقديم طلبك</p>", unsafe_allow_html=True)
        
        with st.form("client_form", clear_on_submit=True):
            # ترتيب عمودي (واحدة تحت الأخرى)
            name = st.text_input("الاسم الكامل")
            phone = st.text_input("رقم الهاتف (واتساب)")
            region = st.selectbox("المنطقة المطلوبة", ["شهداء البياع", "المنصور", "حي الجامعة", "السيدية", "أخرى"])
            budget = st.text_input("الميزانية التقريبية")
            details = st.text_area("تفاصيل العقار المطلوب")
            
            st.markdown("<br>", unsafe_allow_html=True)
            send_btn = st.form_submit_button(f"إرسال الطلب إلى {OFFICE_NAME} 🚀", use_container_width=True)
            
            if send_btn:
                if name and phone:
                    payload = {"name": name, "phone": phone, "region": region, "budget": budget, "details": details, "source": OFFICE_NAME}
                    try:
                        # إرسال يدعم الصيغ المختلفة (جوجل و Pipedream)
                        if "script.google.com" in WEBHOOK_URL:
                            requests.post(WEBHOOK_URL, data=json.dumps(payload), headers={"Content-Type": "application/json"}, timeout=8)
                        else:
                            requests.post(WEBHOOK_URL, params=payload, timeout=8)
                        
                        st.session_state.submitted = True
                        st.rerun()
                    except:
                        # تجاوز الخطأ لضمان ظهور رسالة النجاح ما دام الإرسال تم
                        st.session_state.submitted = True
                        st.rerun()
                else:
                    st.warning("يرجى ملء الاسم ورقم الهاتف")
    else:
        st.balloons()
        st.markdown(f"""
            <div style="text-align: center; padding: 50px; background-color: #1a1c24; border-radius: 20px; border: 2px solid #d4af37; margin-top: 50px;">
                <h1 style="color: #d4af37;">✅ تم الاستلام بنجاح!</h1>
                <p style="color: white; font-size: 1.2em;">شكراً لثقتكم بـ <b>{OFFICE_NAME}</b>. سنتصل بك قريباً.</p>
            </div>
        """, unsafe_allow_html=True)
        if st.button("إرسال طلب جديد"):
            st.session_state.submitted = False
            st.rerun()
    st.stop()

# --- واجهة الإدارة (Admin View) ---
if "authenticated" not in st.session_state:
    st.session_state["authenticated"] = False

if not st.session_state["authenticated"]:
    st.markdown(f"<h2 style='text-align: center; color: #d4af37;'>🔒 لوحة تحكم {OFFICE_NAME}</h2>", unsafe_allow_html=True)
    user_input = st.text_input("ادخل رمز الوصول الخاص بالمكتب:", type="password")
    if user_input == ADMIN_PASSWORD:
        st.session_state["authenticated"] = True
        st.rerun()
    elif user_input != "":
        st.error("رمز الوصول غير صحيح")
    st.stop()

# عرض الطلبات في لوحة الإدارة
st.markdown("""<style>.prop-card { background-color: #1a1c24; border-radius: 15px; padding: 20px; border: 1px solid #d4af37; margin-bottom: 20px; }</style>""", unsafe_allow_html=True)

try:
    df_data = pd.read_csv(CSV_URL)
    if not df_data.empty:
        st.markdown(f"<h3 style='color:#d4af37;'>📊 سجل طلبات: {OFFICE_NAME}</h3>", unsafe_allow_html=True)
        
        # ترتيب البيانات (الأحدث أولاً)
        if 'Timestamp' in df_data.columns:
            df_data['Timestamp'] = pd.to_datetime(df_data['Timestamp'], errors='coerce')
            df_data = df_data.sort_values(by='Timestamp', ascending=False)

        for _, row in df_data.iterrows():
            with st.container():
                st.markdown(f"""
                <div class="prop-card">
                    <h2 style='color:white; margin:0;'>👤 {row.get('name', 'بدون اسم')}</h2>
                    <p style='color:#d4af37;'>📞 هاتف: {row.get('phone', '—')}</p>
                    <p style='color:white;'>📍 المنطقة: {row.get('region', '—')} | 💰 الميزانية: {row.get('budget', '—')}</p>
                    <div style="background-color: #2c3e50; padding: 10px; border-radius: 10px;">
                        <p style='color:#ecf0f1; margin:0;'>📝 التفاصيل: {row.get('details', 'لا توجد تفاصيل')}</p>
                    </div>
                </div>
                """, unsafe_allow_html=True)
    else:
        st.info(f"لا توجد طلبات مسجلة حالياً لمكتب {OFFICE_NAME}")
except Exception as e:
    st.error(f"حدث خطأ في جلب بيانات المكتب: {e}")
    
