KB={
 "network":"ตรวจ Physical link, IP configuration, gateway, DNS และทดสอบทีละชั้นก่อนเปลี่ยนค่า",
 "debug":"อ่าน error message, แยกปัญหาเป็นส่วนเล็ก ๆ, ทำ reproduction และตรวจ assumption ก่อนแก้",
 "electrical":"เริ่มจากความปลอดภัยและแหล่งจ่าย จากนั้นไล่วงจรเป็นลำดับ อย่าวัดจุดเสี่ยงโดยไม่มีอุปกรณ์ที่เหมาะสม",
 "default":"แยกปัญหาเป็นข้อเท็จจริง → สมมติฐาน → ตรวจสอบ → เลือกวิธีที่มีความเสี่ยงต่ำ → ตรวจผลลัพธ์"
}
def fallback_answer(message, context=""):
    text=(message+" "+context).lower()
    key="network" if "network" in text or "internet" in text else "debug" if "debug" in text or "code" in text else "electrical" if "ไฟ" in text or "electric" in text else "default"
    return {"provider":"local","answer":KB[key],"hint_level":1}
