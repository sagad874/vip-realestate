import streamlit as st
import pandas as pd

# إعدادات الفخامة
st.set_page_config(page_title="VIP Real Estate", layout="wide")

st.markdown("""
    <style>
    .main { background-color: #0e1117; }
    .property-card {
        background-color: #1a1c24;
        border-radius: 15px;
        padding: 20px;
        border: 1px solid #d4af37;
        margin-bottom: 20px;
    }
    .vip-badge {
        background: #d4af37;
        color: black;
        padding: 2px 10px;
        border-radius: 10px;
        font-weight: bold;
    }
    h2, p { color: white !important; }
    </style>
    """, unsafe_allow_html=True)

# الرابط الخاص بك (تم تحديثه)
SHEET_ID = "1a9MO2P78L7XBggmlkYKYfjnslAAyvGxOeffnv1LT_ac"
CSV_URL = f"https://docs.google.com/spreadsheets/d/{SHEET_ID}/export?format=csv"

st.markdown("<h1 style='text-align: center; color: #d4af37;'>🏰 VIP Real Estate Engine</h1>", unsafe_allow_html=True)

try:
    df = pd.read_csv(CSV_URL)
    for _, row in df.iterrows():
        with st.container():
            st.markdown(f"""
            <div class="property-card">
                <span class="vip-badge">💎 {row['Lead_Quality']}</span>
                <h2>👤 {row['Customer_Name']}</h2>
                <p>📍 المنطقة: {row['Target_Region']}</p>
                <p style="color: #2ecc71 !important;">💰 الميزانية: {row['Budget_Range']}</p>
                <div style="background-color: #2c3e50; padding: 15px; border-radius: 10px;">
                    <p>🤖 <b>التحليل الذكي:</b><br>{row['Ai_Analysis']}</p>
                </div>
            </div>
            """, unsafe_allow_html=True)
            
            # زر الواتساب (باستخدام الرابط الموجود في الشيت أصلاً)
            st.link_button(f"تواصل مع {row['Customer_Name']} 💬", f"https://wa.me/{row['Phone_Number']}", use_container_width=True)
            st.markdown("<br>", unsafe_allow_html=True)
except Exception as e:
    st.error("تأكد من تفعيل المشاركة في الجوجل شيت")
  
