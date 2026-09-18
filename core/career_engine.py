from database.models import Career, SkillScore, Department
from core.discovery_engine import NEW_DEPARTMENTS

def _selected_department(user_id):
    from database.models import User
    u=User.query.get(user_id)
    return next((d for d in (u.departments or []) if d.name in NEW_DEPARTMENTS), None) if u else None

def career_fit(user_id):
    scores={x.skill_id:x.score for x in SkillScore.query.filter_by(user_id=user_id)}
    selected=_selected_department(user_id)
    out=[]
    for c in Career.query.all():
        if not c.skills: continue
        vals=[scores.get(s.id,0) for s in c.skills]
        fit=sum(vals)/len(vals)
        if selected and c.department_id==selected.id:
            fit=min(100,fit+8)
        gaps=sorted([(s.name,round(scores.get(s.id,0),1)) for s in c.skills],key=lambda x:x[1])
        out.append({"career":c.name,"fit":round(fit,1),"department":c.department.name if c.department else None,
                    "gaps":gaps[:3],"selected":bool(selected and c.department_id==selected.id)})
    return sorted(out,key=lambda x:(-x["fit"],x["career"]))

def department_fit(user_id):
    scores={x.skill_id:x.score for x in SkillScore.query.filter_by(user_id=user_id)}
    selected=_selected_department(user_id)
    out=[]
    for d in Department.query.filter(Department.name.in_(list(NEW_DEPARTMENTS))).all():
        ms=[]
        for m in d.missions: ms.extend(m.skills)
        uniq={s.id:s for s in ms}.values()
        vals=[scores.get(s.id,0) for s in uniq]
        fit=(sum(vals)/len(vals)) if vals else 0
        if selected and d.id==selected.id: fit=min(100,fit+8)
        out.append({"department":d.name,"fit":round(fit,1),"selected":bool(selected and d.id==selected.id)})
    return sorted(out,key=lambda x:(not x["selected"],-x["fit"]))
