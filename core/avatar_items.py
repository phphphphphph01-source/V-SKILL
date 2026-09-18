"""Curated V-SKILL cosmetic/skill-item catalog.

These are visual items only. They never modify Quiz questions, choices,
difficulty, scoring, or assessment results. Gameplay Skill Perks remain in
Skill Lab and are evaluated only after an activity is completed.
"""
from database.database import db
from database.models import AvatarItem, UserAvatarItem

# Every item here corresponds to a real standalone asset supplied for the
# Avatar Studio. Screenshot-like/"asset sheet" images are intentionally not
# part of this catalog.
SKILL_ITEMS = [
    ("เสื้อกั๊ก V-SKILL", "ชุดสำรวจสำหรับสาย Mission", "skill_item", "explorer_vest", "COMMON", "missions", 4, "mission_hunter"),
    ("ชุดยูนิฟอร์ม V-SKILL", "ชุดทำงานสำหรับพัฒนาทักษะอย่างต่อเนื่อง", "skill_item", "engineer_uniform", "COMMON", "missions", 0, "skill_accelerator"),
    ("ชุดเกราะพิเศษ", "ชุดเทคโนโลยีสำหรับสายพัฒนาทักษะ", "skill_item", "ai_tech_suit", "EPIC", "missions", 4, "skill_accelerator"),
    ("แว่นตา AR Explorer", "ช่วยเปิดมุมมองการสำรวจ Mission", "skill_item", "explorer_goggles", "COMMON", "missions", 2, "explorer_compass"),
    ("แว่นตาอัจฉริยะ", "อุปกรณ์มองภาพรวมเส้นทางอาชีพ", "skill_item", "smart_glasses", "RARE", "missions", 4, "career_compass"),
    ("หูฟัง V-Buddy", "คู่หูสำหรับคำแนะนำหลังจบกิจกรรม", "skill_item", "vbuddy_assistant", "RARE", "missions", 3, "vbuddy_coach"),
    ("หมวก V-SKILL", "หมวกประจำตัวสำหรับสายสะสม XP", "skill_item", "vskill_cap", "COMMON", "missions", 0, "xp_spark"),
    ("หมวกนิรภัย Engineer", "หมวกสำหรับสาย Mission และงานเทคนิค", "skill_item", "engineer_helmet", "RARE", "missions", 4, "mission_hunter"),
    ("กระเป๋าสำรวจ", "กระเป๋าคู่ใจสำหรับการค้นพบเส้นทางใหม่", "skill_item", "explorer_backpack", "COMMON", "missions", 2, "explorer_compass"),
    ("เป้สะพายหลัง Tech", "อุปกรณ์สำหรับเก็บหลักฐานและพัฒนาทักษะ", "skill_item", "tech_backpack", "RARE", "missions", 4, "skill_analyzer"),
    ("แท็บเล็ต V-SKILL", "แดชบอร์ดสำหรับดูหลักฐานและภาพรวม Skill", "skill_item", "smart_tablet", "EPIC", "missions", 2, "skill_analyzer"),
    ("กล่องอุปกรณ์", "ชุดเครื่องมือสำหรับรักษา Momentum", "skill_item", "digital_toolkit", "RARE", "missions", 2, "combo_core"),
    ("อุปกรณ์สแกน Holo", "เครื่องมือสำรวจสิ่งที่ควรตามหา", "skill_item", "holographic_scanner", "EPIC", "missions", 6, "rare_hunter"),
    ("คริสตัลพลังงาน", "พลังสำหรับผู้พิชิต Achievement ใหม่", "skill_item", "v_core", "LEGENDARY", "missions", 1, "achievement_magnet"),
    ("จุดส่งตัว Mission", "จุดวาร์ปสำหรับนักล่าโอกาสใหม่", "skill_item", "skill_aura", "EPIC", "missions", 8, "lucky_finder"),
]

# Four additional names/legacy assets are deliberately NOT shown because
# their source files are screenshot-like composites rather than clean items.
ALLOWED_SKILL_ITEM_KEYS = {row[3] for row in SKILL_ITEMS}

def ensure_catalog():
    changed = False
    for name, desc, slot, key, rarity, unlock_type, unlock_value, _skill_id in SKILL_ITEMS:
        row = AvatarItem.query.filter_by(name=name).first()
        if not row:
            db.session.add(AvatarItem(name=name, description=desc, slot=slot,
                                      asset_key=key, rarity=rarity.lower(),
                                      unlock_type=unlock_type, unlock_value=unlock_value))
            changed = True
        else:
            vals = (row.description, row.slot, row.asset_key, row.rarity,
                    row.unlock_type, row.unlock_value)
            newvals = (desc, slot, key, rarity.lower(), unlock_type, unlock_value)
            if vals != newvals:
                row.description, row.slot, row.asset_key, row.rarity, row.unlock_type, row.unlock_value = newvals
                changed = True
    if changed:
        db.session.commit()


def skill_id_for_item(asset_key):
    for row in SKILL_ITEMS:
        if row[3] == asset_key:
            return row[7]
    return None


def curated_items():
    ensure_catalog()
    rows = AvatarItem.query.filter(AvatarItem.slot == "skill_item").all()
    return [r for r in rows if r.asset_key in ALLOWED_SKILL_ITEM_KEYS]


def owned_curated(user_id):
    ids = {x.item_id for x in UserAvatarItem.query.filter_by(user_id=user_id).all()}
    return ids
