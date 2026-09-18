import json, uuid, hashlib
from datetime import datetime
from database.database import db
from database.models import *
from core.skill_engine import rebuild_user_skills, MIN_EVIDENCE

def skill_dna(user_id):
    rebuild_user_skills(user_id)
    rows=SkillScore.query.filter_by(user_id=user_id).all()
    data=[]
    for r in rows:
        s=db.session.get(Skill,r.skill_id)
        if s and r.evidence_count>=MIN_EVIDENCE:
            data.append({"skill":s.name,"skill_id":s.id,"score":round(r.score,1),"evidence":r.evidence_count})
    data.sort(key=lambda x:x["score"],reverse=True)
    top=data[:3]
    dna={"top_strengths":top,"all_evidence":data,"label":"Skill DNA จากหลักฐานภารกิจจริง"}
    row=SkillDNA.query.filter_by(user_id=user_id).first()
    if not row: row=SkillDNA(user_id=user_id,dna_json=json.dumps(dna,ensure_ascii=False)); db.session.add(row)
    else: row.dna_json=json.dumps(dna,ensure_ascii=False); row.updated_at=datetime.utcnow()
    row.evidence_count=sum(x["evidence"] for x in data); db.session.commit()
    return dna

def discovery_report(user_id):
    dna=skill_dna(user_id)
    attempts=MissionAttempt.query.filter_by(user_id=user_id).order_by(MissionAttempt.completed_at.asc()).all()
    return {"attempts":len(attempts),"average_score":round(sum(a.score for a in attempts)/len(attempts),1) if attempts else 0,
            "top_strengths":dna["top_strengths"],"message":"แนวโน้มจากผลงานจริง ไม่ใช่คำตัดสินความสามารถถาวร"}

def achievements(user_id):
    rebuild_user_skills(user_id)
    attempts=MissionAttempt.query.filter_by(user_id=user_id).all()
    earned=UserAchievement.query.filter_by(user_id=user_id).all()
    earned_ids={x.achievement_id for x in earned}
    for ach in Achievement.query.all():
        qualifies=False
        if ach.name=="First Mission": qualifies=len(attempts)>=1
        elif ach.name=="10 Missions": qualifies=len(attempts)>=10
        elif ach.name=="Explorer": qualifies=len({a.mission_id for a in attempts})>=5
        elif ach.name=="Perfect Score": qualifies=any(a.score>=99.99 for a in attempts)
        elif ach.name=="No Hint": qualifies=any(a.hints_used==0 for a in attempts)
        elif ach.name=="Discovery Complete": qualifies=len(attempts)>=10
        else: qualifies=len(attempts)>=ach.threshold
        if qualifies and ach.id not in earned_ids:
            db.session.add(UserAchievement(user_id=user_id,achievement_id=ach.id)); db.session.commit()
    return UserAchievement.query.filter_by(user_id=user_id).all()

def certificate_for_top_skill(user_id):
    dna=skill_dna(user_id)
    if not dna["top_strengths"]: return None
    top=dna["top_strengths"][0]
    existing=Certificate.query.filter_by(user_id=user_id,skill_id=top["skill_id"]).first()
    if existing: return existing
    cid="VSKILL-"+uuid.uuid4().hex[:10].upper()
    c=Certificate(user_id=user_id,skill_id=top["skill_id"],certificate_id=cid,score=top["score"])
    db.session.add(c); db.session.commit(); return c

def portfolio_data(user_id):
    prof=skill_dna(user_id)
    attempts=MissionAttempt.query.filter_by(user_id=user_id).all()
    projects=[]
    for a in attempts[-5:]:
        projects.append({"title":a.mission.title,"evidence":f"ทำ Mission ได้คะแนน {a.score:.1f}/100, accuracy {a.accuracy:.1f}%","skills":", ".join(s.name for s in a.mission.skills)})
    return {"summary":"Portfolio ที่สร้างจากหลักฐานการทำ Mission จริง","strengths":prof["top_strengths"],"projects":projects}

def interview_score(answer, career_name=""): 
    text=(answer or "").strip(); n=len(text.split())
    evidence=sum(k in text.lower() for k in ["เพราะ","ข้อมูล","ปัญหา","แผน","ทีม","ทดสอบ","เหตุผล"])
    score=min(100, round(35+min(n,80)*0.55+evidence*7,1))
    return score, "ควรตอบให้เห็นสถานการณ์ วิธีคิด การลงมือทำ และผลลัพธ์ที่ตรวจสอบได้" if score<70 else "คำตอบมีโครงสร้างและหลักฐานที่ดีขึ้น ควรเสริมผลลัพธ์ที่วัดได้"
