"""V-SKILL Skill Perks engine.

Perks are post-activity modifiers only. They never receive or alter Quiz
questions/answers and never modify assessment results.
"""
from datetime import datetime, date, timedelta
import json, random
from database.database import db
from core.avatar_items import ALLOWED_SKILL_ITEM_KEYS, curated_items, skill_id_for_item
from database.models import (
    SkillPerk, UserSkillPerk, UserProgress, SkillRewardLog, UserAvatar,
    MissionAttempt, Achievement, UserAchievement, SkillScore, Skill
)

PERKS = [
    dict(skill_id="xp_spark", skill_name="XP Spark", category="PROGRESSION", rarity="COMMON", icon="⚡",
         description="เพิ่ม XP และ Progress จากกิจกรรมที่สำเร็จเล็กน้อย", effect_type="progress_pct", effect_value=0.05,
         unlock_requirement="เริ่มต้นใช้งาน V-SKILL"),
    dict(skill_id="combo_core", skill_name="Combo Core", category="PROGRESSION", rarity="RARE", icon="🔥",
         description="สะสม Combo จากการทำกิจกรรมสำเร็จต่อเนื่อง และรับโบนัสแบบค่อยเป็นค่อยไป", effect_type="combo_bonus", effect_value=0.03,
         unlock_requirement="ทำ Mission สำเร็จ 2 ครั้ง"),
    dict(skill_id="skill_accelerator", skill_name="Skill Accelerator", category="PROGRESSION", rarity="EPIC", icon="🚀",
         description="โบนัส Progress เล็กน้อยเมื่อทำกิจกรรมหลายประเภทสำเร็จ", effect_type="variety_bonus", effect_value=0.05,
         unlock_requirement="ทำ Mission สำเร็จ 4 ครั้ง"),
    dict(skill_id="explorer_compass", skill_name="Explorer Compass", category="EXPLORATION", rarity="COMMON", icon="🧭",
         description="ปลดล็อก Mission Discovery เพิ่มเติมในหน้าค้นหาภารกิจ", effect_type="mission_discovery", effect_value=1,
         unlock_requirement="ทำ Mission สำเร็จ 2 ครั้ง"),
    dict(skill_id="mission_hunter", skill_name="Mission Hunter", category="EXPLORATION", rarity="RARE", icon="🎯",
         description="เพิ่มโอกาสพบ Mission พิเศษจากระบบ Discovery", effect_type="special_mission_chance", effect_value=0.08,
         unlock_requirement="ทำ Mission สำเร็จ 4 ครั้ง"),
    dict(skill_id="rare_hunter", skill_name="Rare Hunter", category="EXPLORATION", rarity="EPIC", icon="💎",
         description="เพิ่มโอกาสได้รับ Cosmetic หรือ Reward ระดับหายาก หลังจบกิจกรรม", effect_type="rare_reward_chance", effect_value=0.10,
         unlock_requirement="ทำ Mission สำเร็จ 6 ครั้ง"),
    dict(skill_id="lucky_finder", skill_name="Lucky Finder", category="EXPLORATION", rarity="LEGENDARY", icon="🍀",
         description="มีโอกาสได้รับ Bonus Reward หลังทำ Mission สำเร็จ", effect_type="lucky_reward_chance", effect_value=0.12,
         unlock_requirement="ทำ Mission สำเร็จ 8 ครั้ง"),
    dict(skill_id="skill_analyzer", skill_name="Skill Analyzer", category="PERSONAL GROWTH", rarity="RARE", icon="📊",
         description="เปิดข้อมูลวิเคราะห์ Skill และแนวโน้มการพัฒนาเพิ่มเติม", effect_type="analytics", effect_value=1,
         unlock_requirement="ทำ Mission สำเร็จ 2 ครั้ง"),
    dict(skill_id="career_compass", skill_name="Career Compass", category="PERSONAL GROWTH", rarity="EPIC", icon="🗺️",
         description="เพิ่มบริบทและเหตุผลประกอบ Career Recommendation จากหลักฐานจริง", effect_type="career_context", effect_value=1,
         unlock_requirement="ทำ Mission สำเร็จ 4 ครั้ง"),
    dict(skill_id="vbuddy_coach", skill_name="V-Buddy Coach", category="PERSONAL GROWTH", rarity="EPIC", icon="🤖",
         description="ให้คำแนะนำหลังจบกิจกรรมโดยอิง Progress และพฤติกรรมการเรียน ไม่เฉลย Quiz", effect_type="coach", effect_value=1,
         unlock_requirement="ทำ Mission สำเร็จ 3 ครั้ง"),
    dict(skill_id="achievement_magnet", skill_name="Achievement Magnet", category="PERSONAL GROWTH", rarity="LEGENDARY", icon="🏆",
         description="รับ Bonus เมื่อปลด Achievement ใหม่", effect_type="achievement_bonus", effect_value=0.10,
         unlock_requirement="ปลด Achievement 1 รายการ"),
]

def ensure_catalog():
    changed=False
    for spec in PERKS:
        row=SkillPerk.query.filter_by(skill_id=spec["skill_id"]).first()
        if not row:
            db.session.add(SkillPerk(**spec)); changed=True
        else:
            for k,v in spec.items():
                if getattr(row,k)!=v:
                    setattr(row,k,v); changed=True
    if changed: db.session.commit()

def _progress(user_id):
    row=UserProgress.query.filter_by(user_id=user_id).first()
    if not row:
        row=UserProgress(user_id=user_id); db.session.add(row); db.session.commit()
    return row

def mission_count(user_id):
    return MissionAttempt.query.filter_by(user_id=user_id).count()

def achievement_count(user_id):
    return UserAchievement.query.filter_by(user_id=user_id).count()

def unlock_available(user_id):
    ensure_catalog()
    missions=mission_count(user_id)
    achievements=achievement_count(user_id)
    values={"missions":missions,"achievements":achievements}
    out=[]
    for perk in SkillPerk.query.filter_by(active=True).all():
        req=0
        if perk.skill_id=="xp_spark": req=0
        elif perk.skill_id=="combo_core": req=2
        elif perk.skill_id=="skill_accelerator": req=4
        elif perk.skill_id=="explorer_compass": req=2
        elif perk.skill_id=="mission_hunter": req=4
        elif perk.skill_id=="rare_hunter": req=6
        elif perk.skill_id=="lucky_finder": req=8
        elif perk.skill_id=="skill_analyzer": req=2
        elif perk.skill_id=="career_compass": req=4
        elif perk.skill_id=="vbuddy_coach": req=3
        elif perk.skill_id=="achievement_magnet": req=1
        val=achievements if perk.skill_id=="achievement_magnet" else missions
        if val>=req:
            row=UserSkillPerk.query.filter_by(user_id=user_id,skill_id=perk.skill_id).first()
            if not row:
                row=UserSkillPerk(user_id=user_id,skill_id=perk.skill_id,equipped=False)
                db.session.add(row); db.session.flush()
            out.append(perk.skill_id)
    db.session.commit()
    return out

def equipped_from_items(user_id):
    """Return active Skill Perks strictly from equipped Skill Items.

    Skill Lab is view-only: there is no independent Skill equip state. The
    only way to activate a Skill Perk is to equip its linked Skill Item in
    Avatar Studio.
    """
    av=UserAvatar.query.filter_by(user_id=user_id).first()
    if not av:
        return []
    try:
        data=json.loads(av.equipped_items or '{}')
    except Exception:
        data={}
    keys=data.get('skill_items',[]) if isinstance(data,dict) else []
    if not isinstance(keys,list): keys=[keys] if keys else []
    allowed={x.asset_key for x in curated_items()}
    out=[]
    for key in keys[:3]:
        if key not in allowed: continue
        sid=skill_id_for_item(key)
        if sid and sid not in out: out.append(sid)
    return out

def sync_skill_perks_from_items(user_id):
    """Mirror item loadout into legacy UserSkillPerk rows for compatibility."""
    unlock_available(user_id)
    active=set(equipped_from_items(user_id))
    rows=UserSkillPerk.query.filter_by(user_id=user_id).all()
    for row in rows:
        row.equipped=row.skill_id in active
    db.session.commit()
    return list(active)

def equipped(user_id):
    return sync_skill_perks_from_items(user_id)

def equip(user_id, skill_id):
    return False,"Skill Lab เป็นหน้าดูความสามารถ — ต้องใส่ไอเทมประจำ Skill ใน Avatar Studio เพื่อเปิดใช้งาน"

def unequip(user_id, skill_id):
    row=UserSkillPerk.query.filter_by(user_id=user_id,skill_id=skill_id).first()
    if not row: return False,"ไม่พบ Skill"
    row.equipped=False; db.session.commit()
    return True,"unequipped"

def _variety_bonus(user_id, now):
    # Mission-only implementation for now: count distinct mission departments
    # in the last 7 days. This is post-activity analytics, not question logic.
    from database.models import Mission
    rows=(MissionAttempt.query.filter(MissionAttempt.user_id==user_id, MissionAttempt.completed_at!=None)
          .order_by(MissionAttempt.id.desc()).limit(12).all())
    deps=set()
    for a in rows:
        if a.mission and a.mission.department_id: deps.add(a.mission.department_id)
    return min(0.05, len(deps)*0.0125)

def apply_mission_completion(user_id, attempt_id, base_progress=100, base_xp=50):
    ensure_catalog()
    p=_progress(user_id)
    now=datetime.utcnow()
    today=now.date()
    if p.last_activity_day == today:
        p.mission_streak=max(1,p.mission_streak or 1)
    elif p.last_activity_day == today-timedelta(days=1):
        p.mission_streak=(p.mission_streak or 0)+1
    else:
        p.mission_streak=1
    p.combo=(p.combo or 0)+1
    if p.combo>20: p.combo=20

    active=equipped(user_id)
    bonuses=[]
    progress=float(base_progress); xp=float(base_xp); coins=10

    if "xp_spark" in active:
        progress*=1.05; xp*=1.05; bonuses.append(("XP Spark","+5% XP / Progress"))
    if "skill_accelerator" in active:
        vb=_variety_bonus(user_id,now)
        progress*=1+vb; bonuses.append(("Skill Accelerator",f"+{round(vb*100,1)}% Progress"))
    if "combo_core" in active and p.combo>=3:
        cb=min(0.08, 0.03 + max(0,p.combo-3)*0.01)
        progress*=1+cb; xp*=1+cb; bonuses.append(("Combo Core",f"+{round(cb*100)}% Combo Bonus"))
    if "lucky_finder" in active and random.random()<0.12:
        coins+=15; bonuses.append(("Lucky Finder","+15 Coins"))
    if "rare_hunter" in active and random.random()<0.10:
        from database.models import AvatarItem, UserAvatarItem
        owned_ids={x.item_id for x in UserAvatarItem.query.filter_by(user_id=user_id).all()}
        rare_items=[x for x in AvatarItem.query.filter(AvatarItem.slot.in_(('species','skill_item'))).all()
                    if x.id not in owned_ids and x.rarity in ("rare","epic","legendary")
                    and (x.slot != "skill_item" or x.asset_key in ALLOWED_SKILL_ITEM_KEYS)]
        if rare_items:
            reward_item=random.choice(rare_items)
            db.session.add(UserAvatarItem(user_id=user_id,item_id=reward_item.id))
            bonuses.append(("Rare Hunter",f"Unlocked {reward_item.name}"))
        else:
            coins+=10; bonuses.append(("Rare Hunter","+10 Coins (all rare items owned)"))
    if "mission_hunter" in active:
        bonuses.append(("Mission Hunter","+8% Special Mission discovery"))
    if "explorer_compass" in active:
        bonuses.append(("Explorer Compass","Discovery expanded"))
    if "skill_analyzer" in active:
        bonuses.append(("Skill Analyzer","Skill analytics updated"))
    if "career_compass" in active:
        bonuses.append(("Career Compass","Career context updated"))
    coach=""
    if "vbuddy_coach" in active:
        bonuses.append(("V-Buddy Coach","Post-activity coaching ready"))
        if p.combo>=3:
            coach="คุณกำลังสร้าง Momentum ได้ดี — รักษา Combo และลองสลับหมวด Mission เพื่อพัฒนา Skill ให้กว้างขึ้น"
        else:
            coach="Mission นี้ถูกบันทึกเป็นหลักฐานการพัฒนาของคุณแล้ว ลองทำ Mission อีกหมวดเพื่อขยาย Skill Profile"

    # Achievement bonus is granted only when a NEW achievement was created by
    # the calling flow. The flag is added later by award_achievement_bonus().
    final_progress=round(progress,1); final_xp=round(xp)
    p.progress_points=round((p.progress_points or 0)+final_progress,1)
    p.xp=(p.xp or 0)+final_xp
    p.coins=(p.coins or 0)+coins
    p.last_activity_at=now; p.last_activity_day=today
    log=SkillRewardLog(user_id=user_id,activity_type="mission",activity_id=attempt_id,
                       base_xp=base_xp,final_xp=final_xp,base_progress=base_progress,
                       final_progress=final_progress,coins=coins,
                       bonus_json=json.dumps([{"skill":a,"bonus":b} for a,b in bonuses],ensure_ascii=False))
    db.session.add(log); db.session.commit()
    return {"xp":final_xp,"progress":final_progress,"coins":coins,"total_coins":p.coins,"combo":p.combo,
            "streak":p.mission_streak,"bonuses":bonuses,"coach":coach}

def award_achievement_bonus(user_id, achievement_id):
    if "achievement_magnet" not in equipped(user_id): return 0
    log=SkillRewardLog.query.filter_by(user_id=user_id).order_by(SkillRewardLog.id.desc()).first()
    if not log or log.activity_type!="mission": return 0
    bonus=round(max(1,log.final_progress*0.10),1)
    p=_progress(user_id); p.progress_points=round((p.progress_points or 0)+bonus,1)
    data=json.loads(log.bonus_json or "[]")
    data.append({"skill":"Achievement Magnet","bonus":f"+{bonus} Progress"})
    log.bonus_json=json.dumps(data,ensure_ascii=False)
    db.session.commit()
    return bonus

def skill_overview(user_id):
    rows=[]
    for ss in SkillScore.query.filter_by(user_id=user_id).all():
        sk=db.session.get(Skill,ss.skill_id)
        if sk: rows.append({"name":sk.name,"score":round(ss.score,1),"evidence":ss.evidence_count})
    rows.sort(key=lambda x:-x["score"])
    return rows

def dashboard_data(user_id):
    ensure_catalog(); unlock_available(user_id)
    p=_progress(user_id)
    perks={x.skill_id:x for x in SkillPerk.query.filter_by(active=True).all()}
    owned={x.skill_id:x for x in UserSkillPerk.query.filter_by(user_id=user_id).all()}
    cards=[]
    item_map={}
    for item in curated_items():
        sid=skill_id_for_item(item.asset_key)
        if sid and sid not in item_map: item_map[sid]=item.name
    active=set(equipped_from_items(user_id))
    for k in PERKS:
        r=perks[k["skill_id"]]; u=owned.get(k["skill_id"])
        cards.append({"id":r.skill_id,"name":r.skill_name,"category":r.category,"rarity":r.rarity,
                      "icon":r.icon,"description":r.description,"effect_type":r.effect_type,
                      "effect_value":r.effect_value,"unlock_requirement":r.unlock_requirement,
                      "linked_item":item_map.get(r.skill_id,"ยังไม่มีไอเทม"),
                      "unlocked":bool(u),"equipped":r.skill_id in active})
    return {"progress":p,"cards":cards,"active_ids":[c["id"] for c in cards if c["equipped"]],
            "overview":skill_overview(user_id)}
