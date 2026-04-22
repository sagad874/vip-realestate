try:
    df = pd.read_csv(CSV_URL)
    if not df.empty:
        # تأكد من وجود الأعمدة أو استبدلها بأسماء افتراضية
        col_budget = 'Budget' if 'Budget' in df.columns else df.columns[3] # العمود الرابع غالباً
        col_time = 'Time' if 'Time' in df.columns else df.columns[0]     # العمود الأول غالباً

        # دالة استخراج الأرقام
        def extract_numeric_budget(val):
            try:
                numbers = re.findall(r'\d+', str(val))
                return int(numbers[0]) if numbers else 0
            except: return 0

        # إنشاء الأعمدة المؤقتة بأمان
        df['temp_budget'] = df[col_budget].apply(extract_numeric_budget)
        df['temp_time'] = pd.to_datetime(df[col_time], errors='coerce')

        # الترتيب (الأعلى ميزانية ثم الأحدث وقتاً)
        df_display = df.sort_values(by=['temp_budget', 'temp_time'], ascending=[False, False])
        
        for _, row in df_display.iterrows():
            # دالة مرنة لجلب البيانات حتى لو اختلف اسم العمود
            def get_v(key):
                for col in row.index:
                    if key.lower() in str(col).lower(): return str(row[col])
                return "N/A"
            
            with st.container():
                st.markdown(f"""
                <div class="property-card">
                    <h2 style='color:white;'>👤 {get_v('Name')}</h2>
                    <p style='color:white;'>📍 المنطقة: {get_v('Region')}</p>
                    <p style="color: #2ecc71 !important; font-weight: bold; font-size: 1.2em;">💰 الميزانية: {get_v('Budget')}</p>
                    <p style="color: #888;">📅 {get_v('Time')}</p>
                    <div style="background-color: #2c3e50; padding: 15px; border-radius: 10px;">
                        <p style='color:white;'>🤖 <b>التحليل الذكي:</b><br>{get_v('Analysis')}</p>
                    </div>
                </div>
                """, unsafe_allow_html=True)
                phone_num = str(get_v('Phone')).replace('.0','')
                st.link_button("واتساب 💬", f"https://wa.me/{phone_num}", use_container_width=True)
                st.markdown("<br>", unsafe_allow_html=True)
    else:
        st.info("لا توجد بيانات حالياً في الجدول.")
except Exception as e:
    st.error(f"حدث خطأ في قراءة البيانات: {e}") # هذا السطر سيخبرك بالضبط ما هي المشكلة
