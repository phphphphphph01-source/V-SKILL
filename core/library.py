"""V-SKILL Knowledge Learning Library.

The library is deliberately evidence-safe: reading content never changes a skill score.
Articles are linked to real Skill and Mission rows and are seeded idempotently.
"""
from __future__ import annotations

import re
from datetime import datetime
from pathlib import Path

from sqlalchemy import or_

from database.database import db
from database.models import (
    Department,
    LibraryArticle,
    LibraryCategory,
    LibraryMedia,
    Mission,
    Skill,
)


# Only aliases that represent the same department are merged. Departments that have
# different curricula (for example Accounting and Business) are intentionally kept.
DEPARTMENT_ALIASES = {
    "Computer Technology": "เทคโนโลยีคอมพิวเตอร์",
    "Electrical": "ไฟฟ้า",
    "Electronics": "อิเล็กทรอนิกส์/เมคคาทรอนิกส์",
    "Automotive": "ช่างยนต์",
    "Business / Marketing": "บริหารธุรกิจ",
}

DOMAIN_PROFILES = {
    "เทคโนโลยีคอมพิวเตอร์": {
        "icon": "💻",
        "categories": ["ฮาร์ดแวร์และระบบ", "การพัฒนาโปรแกรม", "เครือข่ายและฐานข้อมูล", "การวิเคราะห์ปัญหา"],
        "tools": "เครื่องมือวัดอุณหภูมิ, Task Manager, Event Viewer, terminal และ test case",
        "core": "แยกอาการออกจากสาเหตุ เก็บหลักฐานก่อนเปลี่ยนตัวแปร และทดสอบซ้ำหลังแก้ไข",
        "safety": "สำรองข้อมูลก่อนแก้ไขระบบ ปิดเครื่องและถอดแหล่งจ่ายก่อนเปิดอุปกรณ์ และไม่ใช้ข้อมูลผู้ใช้จริงในการทดสอบโดยไม่จำเป็น",
        "mistakes": "รีบเปลี่ยนชิ้นส่วนโดยไม่มีหลักฐาน, แก้หลายจุดพร้อมกัน, ไม่บันทึกสภาพก่อนแก้",
        "cover": "computer-technology.svg",
    },
    "Information Technology": {
        "icon": "🌐",
        "categories": ["เครือข่ายและระบบ", "การพัฒนาซอฟต์แวร์", "ฐานข้อมูลและ API", "ความปลอดภัยไซเบอร์"],
        "tools": "ping, traceroute, browser DevTools, server log, SQL explain plan และ API client",
        "core": "ตรวจจากชั้นล่างไปชั้นบน เก็บ timestamp และแยกข้อเท็จจริงออกจากสมมติฐาน",
        "safety": "ใช้ระบบทดสอบและข้อมูลจำลอง ห้ามทดสอบเจาะระบบที่ไม่ได้รับอนุญาต และรักษาความลับของ token/log",
        "mistakes": "รีสตาร์ตโดยไม่เก็บ log, เปลี่ยนหลาย configuration พร้อมกัน, เปิดเผยข้อมูลลับในรายงาน",
        "cover": "information-technology.svg",
    },
    "ไฟฟ้า": {
        "icon": "⚡",
        "categories": ["พื้นฐานวงจร", "การวัดและคำนวณ", "ระบบควบคุม", "ความปลอดภัยไฟฟ้า"],
        "tools": "มัลติมิเตอร์, clamp meter, wiring diagram, nameplate และตารางพิกัดอุปกรณ์",
        "core": "ยืนยันสถานะปลอดพลังงาน เลือกโหมดวัดให้ถูก และเปรียบเทียบค่าที่วัดกับพิกัดหรือค่าคาดหมาย",
        "safety": "ตัดแหล่งจ่ายและตรวจยืนยันก่อนสัมผัสวงจร ใช้ PPE และไม่วัดกระแสแบบต่อคร่อมแหล่งจ่าย",
        "mistakes": "ใช้โหมดวัดผิด, ไม่ตรวจพิกัดสาย/อุปกรณ์, ข้ามขั้นตอน lockout/tagout",
        "cover": "electrical.svg",
    },
    "อิเล็กทรอนิกส์/เมคคาทรอนิกส์": {
        "icon": "🔌",
        "categories": ["อุปกรณ์และวงจร", "ไมโครคอนโทรลเลอร์", "เซนเซอร์และสัญญาณ", "ระบบควบคุมและแก้ปัญหา"],
        "tools": "มัลติมิเตอร์, oscilloscope, datasheet, breadboard และ serial monitor",
        "core": "ตรวจขั้ว พิกัด แหล่งจ่าย และสัญญาณตามลำดับ พร้อมแยก power path ออกจาก signal path",
        "safety": "จำกัดกระแสเมื่อทดลอง ป้องกันไฟฟ้าสถิต และตัดไฟก่อนปรับสายหรือเปลี่ยนโมดูล",
        "mistakes": "ต่อขั้วกลับ, ใช้แรงดันเกินพิกัด, สรุปจากค่า sensor ครั้งเดียวโดยไม่ดู noise",
        "cover": "electronics.svg",
    },
    "ช่างยนต์": {
        "icon": "🚗",
        "categories": ["เครื่องยนต์และระบบไฟ", "การวิเคราะห์อาการ", "เบรกและความปลอดภัย", "การบำรุงรักษา"],
        "tools": "scan tool, multimeter, service manual, torque specification และ inspection checklist",
        "core": "ถามอาการให้ครบ ตรวจสภาพพื้นฐานก่อน และยืนยัน root cause ก่อนเปลี่ยนอะไหล่",
        "safety": "ป้องกันรถเคลื่อนที่ ใช้ขาตั้งที่เหมาะสม ระวังชิ้นส่วนร้อนและระบบแรงดันสูง และทำตามคู่มือผู้ผลิต",
        "mistakes": "เปลี่ยนอะไหล่ตามอาการอย่างเดียว, ข้ามการตรวจขั้ว/ฟิวส์, ทดลองขับโดยไม่ประเมินความเสี่ยง",
        "cover": "automotive.svg",
    },
    "เทคนิคการผลิต": {
        "icon": "⚙️",
        "categories": ["เครื่องมือและการวัด", "กระบวนการผลิต", "การบำรุงรักษา", "คุณภาพและความปลอดภัย"],
        "tools": "เวอร์เนียร์, ไมโครมิเตอร์, ใบงานเครื่องจักร, maintenance log และ quality checklist",
        "core": "อ่านแบบและพิกัดก่อนทำงาน เลือกเครื่องมือให้เหมาะ และตรวจชิ้นงานด้วยหลักฐานวัดได้",
        "safety": "สวม PPE ป้องกันจุดหนีบ/เศษวัสดุ และหยุดเครื่องตามขั้นตอนก่อนปรับตั้งหรือบำรุงรักษา",
        "mistakes": "วัดโดยไม่ตั้งศูนย์, ใช้เครื่องมือผิดช่วง, เร่งผลิตจนข้าม quality gate",
        "cover": "mechanical.svg",
    },
    "Mechanical": {
        "icon": "⚙️",
        "categories": ["เครื่องมือและการวัด", "ระบบกลไก", "การบำรุงรักษา", "คุณภาพและความปลอดภัย"],
        "tools": "เวอร์เนียร์, ไมโครมิเตอร์, vibration meter, maintenance log และ technical drawing",
        "core": "อ่านแบบและพิกัดก่อนทำงาน ประเมินโหลด/แรงเสียดทาน และตรวจสภาพชิ้นส่วนจากข้อมูลวัดได้",
        "safety": "หยุดและแยกพลังงานก่อนบำรุงรักษา ป้องกันจุดหนีบ เศษวัสดุ และใช้ PPE ตามงาน",
        "mistakes": "วัดโดยไม่ตั้งศูนย์, หล่อลื่นโดยไม่ดูชนิด, เร่งเครื่องเพื่อทดสอบโดยไม่ประเมินความเสี่ยง",
        "cover": "mechanical.svg",
    },
    "Accounting": {
        "icon": "📊",
        "categories": ["พื้นฐานบัญชี", "เอกสารและรายการ", "การตรวจสอบข้อมูล", "ต้นทุนและการวางแผน"],
        "tools": "เอกสารต้นทาง, spreadsheet, ledger, reconciliation checklist และ audit trail",
        "core": "ตรวจความครบถ้วน ความถูกต้อง และความสามารถในการตรวจสอบย้อนกลับก่อนสรุปยอด",
        "safety": "ปกป้องข้อมูลส่วนบุคคล แยกสิทธิ์การเข้าถึง และเก็บหลักฐานการแก้ไขรายการ",
        "mistakes": "ปรับยอดโดยไม่มีเอกสาร, ละเลยรายการซ้ำ, สรุปความผิดจากตัวเลขโดยไม่ตรวจบริบท",
        "cover": "accounting.svg",
    },
    "บริหารธุรกิจ": {
        "icon": "📣",
        "categories": ["ลูกค้าและตลาด", "การขายและบริการ", "การวางแผนธุรกิจ", "ข้อมูลและการทดลอง"],
        "tools": "customer journey, spreadsheet, KPI dashboard, interview guide และ experiment log",
        "core": "กำหนดปัญหาและกลุ่มเป้าหมายให้ชัด ใช้ข้อมูลตามช่วงเวลา และทดสอบสมมติฐานอย่างควบคุม",
        "safety": "เคารพความเป็นส่วนตัว ไม่ใช้ข้อมูลลูกค้าเกินวัตถุประสงค์ และสื่อสารเงื่อนไขอย่างโปร่งใส",
        "mistakes": "ตัดสินใจจากตัวเลขเดียว, สรุปเร็วจากกลุ่มตัวอย่างเล็ก, เปลี่ยนหลายตัวแปรพร้อมกัน",
        "cover": "business-marketing.svg",
    },
    "ดิจิทัล/กราฟิก": {
        "icon": "🎨",
        "categories": ["พื้นฐานงานออกแบบ", "ภาพและองค์ประกอบ", "สื่อดิจิทัล", "การส่งมอบงาน"],
        "tools": "moodboard, grid, color palette, version history และ export checklist",
        "core": "เริ่มจาก brief และกลุ่มเป้าหมาย ใช้ลำดับชั้นทางสายตา และตรวจไฟล์ตามช่องทางใช้งานจริง",
        "safety": "ใช้ภาพและฟอนต์ที่มีสิทธิ์ใช้งาน ไม่เผยข้อมูลส่วนบุคคล และเก็บไฟล์ต้นฉบับเป็นเวอร์ชัน",
        "mistakes": "ออกแบบโดยไม่ถามวัตถุประสงค์, ใช้สี/ฟอนต์มากเกินไป, ส่งไฟล์ผิดขนาดหรือโปรไฟล์สี",
        "cover": "business-marketing.svg",
    },
    "อาหาร/คหกรรม": {
        "icon": "🍳",
        "categories": ["วัตถุดิบและสุขอนามัย", "กระบวนการเตรียม", "คุณภาพและต้นทุน", "การบริการและบรรจุ"],
        "tools": "เครื่องชั่ง, thermometer, recipe sheet, sanitation checklist และ cost sheet",
        "core": "ควบคุมวัตถุดิบ เวลา อุณหภูมิ และความสะอาดให้ตรวจสอบได้ทุกขั้น",
        "safety": "ป้องกันการปนเปื้อน แยกดิบ/สุก ระวังความร้อนและสารก่อภูมิแพ้ และทำตามสุขลักษณะอาหาร",
        "mistakes": "กะปริมาณด้วยสายตา, ไม่บันทึกอุณหภูมิ, ใช้อุปกรณ์ร่วมระหว่างวัตถุดิบดิบและสุก",
        "cover": "business-marketing.svg",
    },
    "ก่อสร้าง": {
        "icon": "🏗️",
        "categories": ["การอ่านแบบ", "วัสดุและปริมาณ", "ควบคุมงาน", "ความปลอดภัยหน้างาน"],
        "tools": "แบบ revision ล่าสุด, measuring tools, BOQ, site checklist และ daily report",
        "core": "ตรวจแบบและเงื่อนไขหน้างานก่อนลงมือ ควบคุม revision และบันทึกหลักฐานการตรวจรับ",
        "safety": "กั้นพื้นที่เสี่ยง ใช้ PPE ตรวจนั่งร้าน/เครื่องมือ และหยุดงานเมื่อเงื่อนไขไม่ปลอดภัย",
        "mistakes": "ใช้แบบเก่า, ประเมินปริมาณจากการเดา, เปิดพื้นที่เสี่ยงโดยไม่ทำ control",
        "cover": "mechanical.svg",
    },
    "โลจิสติกส์": {
        "icon": "📦",
        "categories": ["คลังสินค้า", "สต็อกและข้อมูล", "การขนส่ง", "การวางแผนซัพพลายเชน"],
        "tools": "barcode scanner, stock card, WMS report, route sheet และ temperature log",
        "core": "ติดตาม movement ตั้งแต่รับเข้าไปจนส่งมอบ ใช้ข้อมูลเวลา ปริมาณ และข้อจำกัดจริง",
        "safety": "จัดเก็บตามพิกัดน้ำหนัก/อุณหภูมิ ใช้ท่าทางยกของที่ถูกต้อง และควบคุมพื้นที่รถยก",
        "mistakes": "ปรับสต็อกโดยไม่ตรวจ movement, วางของโดยไม่ดูความถี่, เลือกเส้นทางโดยไม่ดู time window",
        "cover": "mechanical.svg",
    },
    "การโรงแรมและท่องเที่ยว": {
        "icon": "🏨",
        "categories": ["งานบริการ", "การจองและปฏิบัติการ", "ประสบการณ์ลูกค้า", "การวางแผนและความปลอดภัย"],
        "tools": "reservation system, service checklist, occupancy report, guest feedback และ incident log",
        "core": "ยืนยันข้อมูลก่อนรับปากลูกค้า สื่อสารทางเลือก และติดตามเคสจนปิดอย่างมีหลักฐาน",
        "safety": "คำนึงถึงความปลอดภัยของผู้เข้าพัก ความเป็นส่วนตัว และข้อจำกัดของสถานที่/กิจกรรม",
        "mistakes": "รับปากโดยไม่ตรวจ capacity, ส่งต่อเคสโดยไม่บันทึก, แก้เฉพาะหน้าโดยไม่หาสาเหตุ",
        "cover": "business-marketing.svg",
    },
}

FALLBACK_TOPICS = {
    "Information Technology": [
        ("ตรวจสอบ API ที่ตอบ 500", "ฐานข้อมูลและ API"),
        ("แยกปัญหา DNS กับ Gateway", "เครือข่ายและระบบ"),
        ("อ่าน Log อย่างมีหลักฐาน", "ความปลอดภัยไซเบอร์"),
        ("ออกแบบ Query ให้ตรวจสอบได้", "ฐานข้อมูลและ API"),
        ("จัดการ Secret ในระบบทดสอบ", "ความปลอดภัยไซเบอร์"),
        ("ทดสอบ Endpoint ด้วย Boundary Case", "การพัฒนาซอฟต์แวร์"),
        ("วางแผน Backup และ Recovery", "เครือข่ายและระบบ"),
        ("ติดตามปัญหาด้วย Incident Timeline", "ความปลอดภัยไซเบอร์"),
    ],
}


EXTRA_TOPICS = {
    "Information Technology": [
        ("แยกปัญหา DNS กับ Gateway", "เครือข่ายและระบบ"), ("ตรวจสอบ API ที่ตอบ 500", "ฐานข้อมูลและ API"),
        ("อ่าน Server Log อย่างมีหลักฐาน", "ความปลอดภัยไซเบอร์"), ("ออกแบบ Query ให้ตรวจสอบได้", "ฐานข้อมูลและ API"),
        ("จัดการ Secret ในระบบทดสอบ", "ความปลอดภัยไซเบอร์"), ("ทดสอบ Endpoint ด้วย Boundary Case", "การพัฒนาซอฟต์แวร์"),
        ("วางแผน Backup และ Recovery", "เครือข่ายและระบบ"), ("ติดตามปัญหาด้วย Incident Timeline", "ความปลอดภัยไซเบอร์"),
    ],
    "Accounting": [
        ("ตรวจเอกสารต้นทางก่อนลงรายการ", "พื้นฐานบัญชี"), ("กระทบยอดธนาคารอย่างเป็นขั้นตอน", "การตรวจสอบข้อมูล"),
        ("แยกรายการซ้ำในบัญชีเจ้าหนี้", "การตรวจสอบข้อมูล"), ("วิเคราะห์ต้นทุนต่อหน่วย", "ต้นทุนและการวางแผน"),
        ("ตรวจวันตัดรอบและเอกสารค้าง", "เอกสารและรายการ"), ("สร้าง Audit Trail ที่ตรวจสอบได้", "การตรวจสอบข้อมูล"),
        ("วางแผนงบประมาณจากข้อมูลจริง", "ต้นทุนและการวางแผน"), ("สื่อสารความผิดปกติของยอดอย่างมืออาชีพ", "เอกสารและรายการ"),
    ],
    "Mechanical": [
        ("ตรวจแรงสั่นของเครื่องจักร", "การบำรุงรักษา"), ("อ่านแบบและพิกัดชิ้นงาน", "เครื่องมือและการวัด"),
        ("เลือกวัสดุให้เหมาะกับโหลด", "ระบบกลไก"), ("ตรวจการเยื้องศูนย์ของเพลา", "การบำรุงรักษา"),
        ("วางแผน Preventive Maintenance", "การบำรุงรักษา"), ("ตรวจคุณภาพผิวและขนาด", "คุณภาพและความปลอดภัย"),
        ("วิเคราะห์สาเหตุชิ้นงานคลาดเคลื่อน", "คุณภาพและความปลอดภัย"), ("จัดลำดับงานในเวิร์กช็อป", "ระบบกลไก"),
    ],
}


def _slug(text: str) -> str:
    value = re.sub(r"[^a-zA-Z0-9ก-๙]+", "-", text).strip("-").lower()
    return value or "article"


def _split_names(value):
    if isinstance(value, (list, tuple, set)):
        return [str(x).strip() for x in value if str(x).strip()]
    return [x.strip() for x in str(value or "").split(",") if x.strip()]


def _ensure_skill(name: str) -> Skill:
    skill = Skill.query.filter_by(name=name).first()
    if not skill:
        skill = Skill(name=name, description=f"ทักษะที่ใช้ในงาน {name}")
        db.session.add(skill)
        db.session.flush()
    return skill


def _merge_department_aliases():
    """Move relations from legacy English aliases to the active Thai department IDs.

    The merge is intentionally conservative and only runs when both records exist.
    It does not delete a department until its user, mission, career and library
    relations have been moved.
    """
    for old_name, canonical_name in DEPARTMENT_ALIASES.items():
        old = Department.query.filter_by(name=old_name).first()
        canonical = Department.query.filter_by(name=canonical_name).first()
        if not old or not canonical or old.id == canonical.id:
            continue
        for user in list(old.users or []):
            if canonical not in user.departments:
                user.departments.append(canonical)
            if old in user.departments:
                user.departments.remove(old)
        for mission in Mission.query.filter_by(department_id=old.id).all():
            mission.department_id = canonical.id
        from database.models import Career
        for career in Career.query.filter_by(department_id=old.id).all():
            career.department_id = canonical.id
        for category in list(LibraryCategory.query.filter_by(department_id=old.id).all()):
            existing_category = LibraryCategory.query.filter_by(department_id=canonical.id, name=category.name).first()
            if existing_category and existing_category.id != category.id:
                for article in list(category.articles or []):
                    article.category_id = existing_category.id
                    article.department_id = canonical.id
                db.session.delete(category)
            else:
                category.department_id = canonical.id
        for article in LibraryArticle.query.filter_by(department_id=old.id).all():
            article.department_id = canonical.id
        db.session.flush()
        if not old.users and not Mission.query.filter_by(department_id=old.id).first() and not LibraryCategory.query.filter_by(department_id=old.id).first():
            db.session.delete(old)
    db.session.commit()


def _article_payload(department_name, profile, mission, index, topic_override=None, category_override=None):
    categories = profile["categories"]
    category = category_override or categories[index % len(categories)]
    skills = [s.name for s in (mission.skills or [])]
    skill_text = ", ".join(skills) if skills else "Problem Solving"
    stages = [step.prompt for step in (mission.steps or [])]
    checklist = "\n".join(f"- {stage}" for stage in stages[:5])
    scenario = mission.scenario or f"สถานการณ์งานจริงของ {department_name}"
    topic = topic_override or mission.title
    objective = "\n".join([
        f"- อธิบายปัญหา {topic} ด้วยคำศัพท์ของสายงาน {department_name}",
        "- เลือกข้อมูลหรือเครื่องมือที่ช่วยแยกสาเหตุได้",
        "- บันทึกผลตรวจและตัดสินใจโดยมีเหตุผลรองรับ",
    ])
    mistakes_text = profile['mistakes'].replace(', ', '\n- ')
    content = "\n\n".join([
        "## บทนำ\nบทนี้ใช้สถานการณ์จริงเป็นจุดตั้งต้น เพื่อให้ผู้เรียนฝึกคิดก่อนลงมือ ไม่ใช่การท่องจำคำตอบของข้อสอบ",
        f"## สิ่งที่ควรเรียนรู้\n{objective}",
        f"## ความรู้หลัก\n{profile['core']}\n\nเครื่องมือ/ข้อมูลที่มักใช้: {profile['tools']}",
        f"## ตัวอย่างในงานจริง\n{scenario}\n\nให้เริ่มจากการบันทึกอาการ เงื่อนไขที่เกิด และสิ่งที่ตรวจได้ ก่อนเปลี่ยนค่าอุปกรณ์หรือขั้นตอน",
        f"## สถานการณ์ให้คิด\nหากผลตรวจรอบแรกยังไม่ชัดเจนในกรณี '{topic}' คุณจะเลือกการตรวจครั้งถัดไปอย่างไรให้ลดความเสี่ยงและเพิ่มข้อมูลใหม่",
        f"## ข้อผิดพลาดที่พบบ่อย\n- {mistakes_text}",
        f"## ความปลอดภัย\n{profile['safety']}",
        f"## Checklist ก่อนส่งงาน\n{checklist or '- ระบุอาการ - เก็บหลักฐาน - ทดสอบซ้ำ - บันทึกผล'}",
        "## Mini Challenge\nให้เขียนลำดับการตรวจ 3 ขั้น โดยระบุข้อมูลที่คาดว่าจะได้จากแต่ละขั้น และเงื่อนไขที่จะทำให้คุณเปลี่ยนสมมติฐาน",
    ])
    tags = ",".join([department_name, topic, category, *skills[:4]])
    slug = _slug(f"{department_name}-{topic}")
    return {
        "category": category,
        "title": f"{topic}: คู่มือเรียนรู้จากสถานการณ์จริง",
        "slug": slug,
        "summary": f"เรียนรู้วิธีวิเคราะห์ {scenario} ด้วยกระบวนการที่ตรวจสอบได้สำหรับสาย {department_name}",
        "difficulty": {1: "พื้นฐาน", 2: "กำลังพัฒนา", 3: "ประยุกต์", 4: "ท้าทาย"}.get(mission.difficulty, "กำลังพัฒนา"),
        "minutes": 7 + (index % 4),
        "content": content,
        "skills": skills,
        "tags": tags,
        "objectives": objective,
        "practical_example": f"จำลองสถานการณ์ '{topic}' ด้วยข้อมูลที่ไม่ระบุตัวตน แล้วบันทึกอาการ เครื่องมือ ผลตรวจ และข้อสรุปแยกกัน",
        "scenario": scenario,
        "mistakes": profile["mistakes"],
        "safety": profile["safety"],
        "checklist": checklist,
        "challenge": "เลือกการตรวจ 3 ขั้นที่ให้ข้อมูลใหม่ โดยไม่เปลี่ยนหลายปัจจัยพร้อมกัน",
        "cover": f"/static/img/library/{profile['cover']}",
        "mission": mission,
    }


def _fallback_missions(department):
    return Mission.query.filter_by(department_id=department.id).order_by(Mission.id).limit(8).all()


def seed_library():
    """Create/update department-specific learning content without duplicating rows."""
    _merge_department_aliases()
    from core.department_missions import DEPARTMENT_CATALOG

    for department_name, profile in DOMAIN_PROFILES.items():
        department = Department.query.filter_by(name=department_name).first()
        if not department:
            continue
        missions = list(Mission.query.filter_by(department_id=department.id, discovery=True).order_by(Mission.id).limit(8).all())
        if len(missions) < 8:
            missions = _fallback_missions(department)
        if not missions:
            continue
        category_map = {}
        for order, category_name in enumerate(profile["categories"]):
            category = LibraryCategory.query.filter_by(department_id=department.id, name=category_name).first()
            if not category:
                category = LibraryCategory(department_id=department.id, name=category_name, icon=profile["icon"], sort_order=order)
                db.session.add(category)
                db.session.flush()
            category_map[category_name] = category
        topics = EXTRA_TOPICS.get(department_name, [])
        for index in range(8):
            mission = missions[index % len(missions)]
            topic_override = topics[index][0] if index < len(topics) else None
            category_override = topics[index][1] if index < len(topics) and topics[index][1] in category_map else None
            payload = _article_payload(department_name, profile, mission, index, topic_override, category_override)
            article = LibraryArticle.query.filter_by(slug=payload["slug"]).first()
            category = category_map[payload["category"]]
            if not article:
                article = LibraryArticle(
                    department_id=department.id,
                    category_id=category.id,
                    title=payload["title"],
                    slug=payload["slug"],
                )
                db.session.add(article)
            else:
                article.department_id = department.id
                article.category_id = category.id
            article.title = payload["title"]
            article.summary = payload["summary"]
            article.content = payload["content"]
            article.difficulty = payload["difficulty"]
            article.estimated_minutes = payload["minutes"]
            article.cover_image = payload["cover"]
            article.tags = payload["tags"]
            article.related_skills = ",".join(payload["skills"])
            article.related_topics = payload["tags"]
            article.learning_objectives = payload["objectives"]
            article.practical_example = payload["practical_example"]
            article.real_world_scenario = payload["scenario"]
            article.common_mistakes = payload["mistakes"]
            article.safety_notes = payload["safety"]
            article.checklist = payload["checklist"]
            article.mini_challenge = payload["challenge"]
            article.status = article.status or "published"
            article.skills = [_ensure_skill(name) for name in payload["skills"]]
            article.missions = [payload["mission"]]
            if not article.media:
                db.session.add(LibraryMedia(article_id=article.id, image=payload["cover"], caption=f"ภาพประกอบ {payload['title']}", media_type="image", alt_text=payload["title"], sort_order=0))
        db.session.flush()
    db.session.commit()


def validate_library():
    """Return human-readable data-quality warnings for admin/CI use."""
    warnings = []
    articles = LibraryArticle.query.all()
    seen_titles = {}
    seen_slugs = {}
    for article in articles:
        seen_titles.setdefault((article.department_id, (article.title or '').strip().lower()), []).append(article.id)
        seen_slugs.setdefault(article.slug, []).append(article.id)
        if not article.department_id:
            warnings.append(f"article {article.id}: missing department")
        if not article.category_id:
            warnings.append(f"article {article.id}: missing category")
        if not (article.content or '').strip() or len((article.content or '').strip()) < 120:
            warnings.append(f"article {article.id}: content too short")
        if not article.skills:
            warnings.append(f"article {article.id}: missing skill relationship")
        if not article.missions:
            warnings.append(f"article {article.id}: missing mission relationship")
        if not (article.cover_image or '').strip():
            warnings.append(f"article {article.id}: missing cover image")
    for key, ids in seen_titles.items():
        if len(ids) > 1:
            warnings.append(f"duplicate title in department {key[0]}: {key[1]} ({ids})")
    for slug, ids in seen_slugs.items():
        if len(ids) > 1:
            warnings.append(f"duplicate slug: {slug} ({ids})")
    return warnings


def _search_text(article):
    values = [
        article.title, article.summary, article.content, article.tags,
        article.related_topics, article.learning_objectives,
        article.category.name if article.category else "",
        article.department.name if article.department else "",
    ]
    return " ".join(str(x or "") for x in values).lower()


def _tokens(text):
    raw = re.findall(r"[a-zA-Z0-9ก-๙]+", (text or "").lower())
    aliases = {
        "คอม": ["คอมพิวเตอร์", "computer", "pc"],
        "เปิดไม่ติด": ["boot", "power", "hardware"],
        "เน็ต": ["network", "เครือข่าย", "internet"],
        "ไฟไม่ติด": ["วงจร", "led", "power"],
    }
    out = list(raw)
    lowered = (text or "").lower()
    for key, words in aliases.items():
        if key in lowered:
            out.extend(words)
    return set(out)


def rank_library_articles(articles, query=""):
    if not query:
        return sorted(articles, key=lambda a: (a.updated_at or datetime.min, a.id), reverse=True)
    terms = _tokens(query)
    ranked = []
    for article in articles:
        text = _search_text(article)
        title = (article.title or "").lower()
        summary = (article.summary or "").lower()
        score = 0
        for term in terms:
            if term in title:
                score += 12
            elif term in summary:
                score += 7
            elif term in text:
                score += 2
        if score:
            ranked.append((score, article.updated_at or datetime.min, article.id, article))
    ranked.sort(key=lambda x: (x[0], x[1], x[2]), reverse=True)
    return [x[3] for x in ranked]


def related_articles(article, limit=4):
    candidates = LibraryArticle.query.filter(
        LibraryArticle.department_id == article.department_id,
        LibraryArticle.status == "published",
        LibraryArticle.id != article.id,
    ).all()
    base_tags = set(_split_names(article.tags))
    base_skills = {skill.id for skill in article.skills}
    scored = []
    for candidate in candidates:
        tags = set(_split_names(candidate.tags))
        skills = {skill.id for skill in candidate.skills}
        score = len(base_tags & tags) * 3 + len(base_skills & skills) * 5
        if candidate.category_id == article.category_id:
            score += 2
        scored.append((score, candidate.updated_at or datetime.min, candidate))
    scored.sort(key=lambda x: (x[0], x[1]), reverse=True)
    return [x[2] for x in scored[:limit]]
