import streamlit as st
import pandas as pd
from datetime import datetime
import requests
import re

# 1. إعدادات الصفحة
st.set_page_config(page_title="Pro Data Matrix | Secured", layout="wide")

# التحقق من نوع الواجهة (زبون أم مدير)
query_params = st.query_params
is_client = query_params.get("view") == "client"

# روابط البيانات (تأكد من صحتها)
SHEET_ID = "1a9MO2P78L7XBggmlkYKYfjnslAAyvGxOeffnv1LT_ac"
CSV_URL = f"https://docs.google.com/spreadsheets/d/{SHEET_ID}/export?format=csv"
WEBHOOK_URL = "https://eomfdq8l221q30q.m.pipedream.net"

# --- واجهة الزبون ---
if is_client:
    # استخدام حالة الجلسة لإدارة عرض الفورم أو رسالة الشكر
    if "submitted" not in st.session_state:
        st.session_state.submitted = False

    if not st.session_state.submitted:
        st.markdown("<h2 style='text-align: center; color: #d4af37;'>🏢 مكتب العقار - تسجيل طلب</h2>", unsafe_allow_html=True)
        with st.form("client_form", clear_on_submit=True):
            name = st.text_input("الاسم الكامل")
            phone = st.text_input("رقم الهاتف (واتساب)")
            region = st.selectbox("المنطقة المطلوبة", ["شهداء البياع", "المنصور", "حي الجامعة", "السيدية", "أخرى"])
            budget = st.text_input("الميزانية التقريبية")
            details = st.text_area("تفاصيل العقار المطلوب")
            send_btn = st.form_submit_button("إرسال الطلب الآن 🚀")
            
            if send_btn:
                if name and phone:
                    payload = {"name": name, "phone": phone, "region": region, "budget": budget, "details": details}
                    try:
                        response = requests.post(WEBHOOK_URL, params=payload)
                        if response.status_code in [200, 201]:
                            st.session_state.submitted = True
                            st.rerun()
                        else:
                            st.error("عذراً، حدث خطأ في إرسال البيانات.")
                    except:
                        st.error("فشل الاتصال بالخادم.")
                else:
                    st.warning("يرجى ملء الاسم ورقم الهاتف لإتمام الطلب.")
    else:
        # لوحة الشكر الفخمة ببصمة المبرمج سجاد
        st.balloons()
        st.markdown(f"""
            <div style="text-align: center; padding: 50px; background-color: #1a1c24; border-radius: 20px; border: 2px solid #d4af37; margin-top: 50px;">
                <h1 style="color: #d4af37; margin-bottom: 20px;">✅ تم استلام طلبك بنجاح!</h1>
                <p style="color: white; font-size: 1.3em;">شكراً لاختياركم مكتبنا، نحن نقدّر ثقتكم بنا وسنتصل بك قريباً.</p>
                <hr style="border-color: #333; margin: 30px 0;">
                <p style="color: #888; font-style: italic; font-size: 0.9em;">
                    تم تطوير هذا النظام الذكي بواسطة المبرمج <b style="color: #d4af37;">سجاد</b>
                </p>
            </div>
        """, unsafe_allow_html=True)
        if st.button("إرسال طلب آخر جديد"):
            st.session_state.submitted = False
            st.rerun()
    st.stop()

# --- واجهة الإدارة ---
PASSWORD = "123456246SsS@"
if "authenticated" not in st.session_state:
    st.session_state["authenticated"] = False

if not st.session_state["authenticated"]:
    st.markdown("<h2 style='text-align: center; color: #d4af37;'>🔒 لوحة التحكم - تسجيل الدخول</h2>", unsafe_allow_html=True)
    user_input = st.text_input("ادخل رمز الوصول:", type="password")
    if user_input == PASSWORD:
        st.session_state["authenticated"] = True
        st.rerun()
    st.stop()

# تنسيق بطاقات العرض
st.markdown("""<style>.property-card { background-color: #1a1c24; border-radius: 15px; padding: 20px; border: 1px solid #d4af37; margin-bottom: 20px; }</style>""", unsafe_allow_html=True)

try:
    df = pd.read_csv(CSV_URL)
    if not df.empty:
        # البحث التلقائي عن أسماء الأعمدة لضمان عدم حدوث خطأ
        def find_c(names):
            for c in df.columns:
                if any(n.lower() in c.lower() for n in names): return c
            return df.columns[0]

        c_budget = find_c(['budget', 'الميزانية', 'سعر'])
        c_time = find_c(['submission', 'time', 'date', 'التاريخ'])

        # دالة توحيد العملات للترتيب (تحويل الدولار لدينار ذهنياً)
        def get_unified_value(v):
            try:
                if pd.isna(v): return 0
                val_str = str(v).lower()
                nums = re.findall(r'\d+', val_str)
                if not nums: return 0
                number = int(nums[0])
                if any(x in val_str for x in ['$', 'usd', 'dollar', 'دولار']):
                    if number < 10000: return number * 1000000 * 1500 # ملايين دولار
                    return number * 1500
                return number
            except: return 0

        # إنشاء أعمدة الترتيب المخفية
        df['sort_t'] = pd.to_datetime(df[c_time], dayfirst=True, errors='coerce')
        df['sort_b'] = df[c_budget].apply(get_unified_value)

        # الترتيب الذهبي: الوقت الأحدث أولاً (False) ثم الميزانية الأعلى (False)
        df = df.sort_values(by=['sort_t', 'sort_b'], ascending=[False, False]).reset_index(drop=True)
        
        st.markdown(f"<h3 style='color:#d4af37;'>📊 إجمالي الطلبات المستلمة: {len(df)}</h3>", unsafe_allow_html=True)

        for _, row in df.iterrows():
            def v(k):
                for col in row.index:
                    if k.lower() in str(col).lower(): return str(row[col])
                return "غير متوفر"
            
            display_time = str(row[c_time]) if c_time in row else "N/A"
            
            with st.container():
                st.markdown(f"""
                <div class="property-card">
                    <div style="display: flex; justify-content: space-between;">
                        <h2 style='color:white; margin:0;'>👤 {v('Name')}</h2>
                        <span style="color: #888;">📅 {display_time}</span>
                    </div>
                    <p style='color:white; margin-top:10px;'>📍 المنطقة المطلوبة: <b>{v('Region')}</b></p>
                    <p style="color: #2ecc71 !important; font-weight: bold; font-size: 1.3em;">💰 الميزانية: {v('Budget')}</p>
                    <div style="background-color: #2c3e50; padding: 15px; border-radius: 10px; border-left: 5px solid #d4af37;">
                        <p style='color:white; margin-bottom:5px;'>🤖 <b>تحليل النظام الذكي:</b></p>
                        <p style='color:#ecf0f1;'>{v('Analysis')}</p>
                    </div>
                </div>
                """, unsafe_allow_html=True)
                
                # زر الواتساب الذكي
                p_raw = v('Phone')
                p_num = re.sub(r'\D', '', str(p_raw))
                st.link_button(f"تواصل مع {v('Name')} عبر واتساب 💬", f"https://wa.me/{p_num}", use_container_width=True)
                st.markdown("<br>", unsafe_allow_html=True)
    else:
        st.info("لا توجد طلبات مسجلة حالياً في النظام.")
except Exception as e:
    st.error(f"حدث خطأ أثناء تحميل البيانات: {e}")
    
