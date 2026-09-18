from datetime import datetime
from math import exp
from database.database import db
from database.models import Skill, SkillScore, SkillHistory, MissionAttempt, Mission

MIN_EVIDENCE = 2

def _attempt_value(a):
    """Convert one server-validated mission result into a 0-100 skill evidence value."""
    # Mission score already combines accuracy and time. Difficulty slightly increases
    # the evidence weight without allowing one hard mission to dominate.
    difficulty_weight=0.85 + min(max(a.mission.difficulty or 1,1),4)*0.05
    # Recent evidence is more useful than very old evidence, but old work never vanishes.
    age_days=max(0,(datetime.utcnow()-(a.completed_at or a.started_at)).total_seconds()/86400)
    recency_weight=0.65 + 0.35*exp(-age_days/90)
    hint_penalty=max(0.0,1.0-min(int(a.hints_used or 0),3)*0.08)
    return max(0.0,min(100.0,float(a.score)*recency_weight*hint_penalty)), difficulty_weight

def rebuild_user_skills(user_id):
    skills=Skill.query.all()
    for skill in skills:
        attempts=(MissionAttempt.query.join(Mission, MissionAttempt.mission_id==Mission.id)
                   .filter(MissionAttempt.user_id==user_id,
                           MissionAttempt.completed_at.isnot(None),
                           Mission.skills.any(id=skill.id))
                   .order_by(MissionAttempt.completed_at.asc()).all())
        if not attempts:
            continue
        pairs=[_attempt_value(a) for a in attempts]
        values=[x[0] for x in pairs]
        weights=[x[1] for x in pairs]
        # Harder missions contribute slightly more evidence without increasing their
        # raw score beyond 100.
        score=round(sum(v*w for v,w in zip(values,weights))/sum(weights),2)
        row=SkillScore.query.filter_by(user_id=user_id,skill_id=skill.id).first()
        if not row:
            row=SkillScore(user_id=user_id,skill_id=skill.id)
            db.session.add(row)
        row.score=min(100,score)
        row.evidence_count=len(attempts)
        latest=attempts[-1]
        last_history=SkillHistory.query.filter_by(user_id=user_id,skill_id=skill.id).order_by(SkillHistory.id.desc()).first()
        if not last_history or last_history.source_attempt_id!=latest.id:
            db.session.add(SkillHistory(user_id=user_id,skill_id=skill.id,score=row.score,source_attempt_id=latest.id))
    db.session.commit()
    return SkillScore.query.filter_by(user_id=user_id).all()

def profile(user_id):
    rows=rebuild_user_skills(user_id)
    result=[]
    for r in rows:
        skill=db.session.get(Skill,r.skill_id)
        if not skill: continue
        confidence=min(100, round((r.evidence_count/5)*100,1))
        result.append({
            "skill":skill.name,"skill_id":skill.id,"score":round(r.score,1),
            "evidence":r.evidence_count,
            "qualified":r.evidence_count>=MIN_EVIDENCE,
            "confidence":("ยืนยันจากหลักฐานหลายครั้ง" if r.evidence_count>=5 else
                          "มีหลักฐานเพียงพอ" if r.evidence_count>=MIN_EVIDENCE else
                          "ต้องการหลักฐานเพิ่ม"),
            "confidence_score":confidence
        })
    return sorted(result,key=lambda x:x["score"],reverse=True)
