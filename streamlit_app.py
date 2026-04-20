import datetime

def handler(pd: "pipedream"):
    # 1. سحب البيانات من الرابط
    query = pd.steps.get("trigger", {}).get("event", {}).get("query", {})
    
    name = query.get("name") or "Unknown"
    phone = query.get("phone") or ""
    budget = query.get("budget") or "N/A"
    region = query.get("region") or "N/A"
    
    # 2. صناعة رابط الواتساب الأنيق
    if phone:
        # تنظيف الرقم من أي علامات زائد أو فراغات
        clean_phone = str(phone).replace("+", "").replace(" ", "")
        wa_url = f"https://wa.me/{clean_phone}?text=Hello%20{name}"
        whatsapp_display = f'=HYPERLINK("{wa_url}", "Chat Now 💬")'
    else:
        whatsapp_display = "No Number"
    
    # 3. التحليل الذكي (عربي احترافي)
    budget_clean = str(budget).upper()
    if any(x in budget_clean for x in ["M", "MILLION", "مليون"]):
        analysis = f"💎 لقطة استثمارية! ميزانية ضخمة في {region}."
        quality = "VIP"
    elif any(x in budget_clean for x in ["K", "THOUSAND", "الف"]):
        analysis = f"✅ زبون جاد بميزانية متوسطة في {region}."
        quality = "Serious"
    else:
        analysis = f"⚠️ مهتم بـ {region}، يحتاج تدقيق ميزانية."
        quality = "Follow-up"

    # 4. توقيت بغداد بنظام 12 ساعة (السنة-الشهر-اليوم الساعة:الدقيقة AM/PM)
    # إضافة 3 ساعات لتوقيت UTC ليطابق توقيت العراق
    # %I تعني نظام 12 ساعة، %p تعني صباحاً أو مساءً
    iraq_time = (datetime.datetime.utcnow() + datetime.timedelta(hours=3)).strftime("%Y-%m-%d %I:%M %p")

    # 5. المخرجات النهائية (يجب أن تطابق أسماء الأعمدة في Google Sheets)
    return {
        "Customer_Name": name,
        "Phone_Number": phone,
        "WhatsApp_Link": whatsapp_display,
        "Budget_Range": budget,
        "Target_Region": region,
        "Ai_Analysis": analysis,
        "Lead_Quality": quality,
        "Submission_Date": iraq_time
    }
    
