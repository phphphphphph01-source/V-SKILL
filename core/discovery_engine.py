from datetime import datetime, timedelta
from database.models import Mission, MissionAttempt, InterestFeedback, Department

NEW_DEPARTMENTS = {
    "เทคโนโลยีคอมพิวเตอร์","ไฟฟ้า","อิเล็กทรอนิกส์/เมคคาทรอนิกส์","ช่างยนต์",
    "เทคนิคการผลิต","บริหารธุรกิจ","ดิจิทัล/กราฟิก","อาหาร/คหกรรม",
    "ก่อสร้าง","โลจิสติกส์","การโรงแรมและท่องเที่ยว"
}

def selected_department(user):
    deps=[d for d in (user.departments or []) if d.name in NEW_DEPARTMENTS]
    return deps[0] if deps else None

def recommended_discovery(user_id):
    from database.models import User
    user=User.query.get(user_id)
    dep=selected_department(user) if user else None
    if not dep:
        return []
    dept_attempts=(MissionAttempt.query.join(Mission, MissionAttempt.mission_id==Mission.id)
                   .filter(MissionAttempt.user_id==user_id, Mission.department_id==dep.id,
                           MissionAttempt.completed_at.isnot(None)).all())
    done={a.mission_id for a in dept_attempts}
    candidates=[m for m in Mission.query.filter_by(department_id=dep.id, discovery=True).all() if m.id not in done]
    # Adaptive difficulty is tracked per department, so switching departments
    # gives the learner a fair starting point in the new domain.
    completed=len(done)
    target=1 if completed < 2 else 2 if completed < 5 else 3 if completed < 9 else 4
    def key(m):
        return (abs((m.difficulty or 1)-target), -(m.difficulty or 1), m.id)
    candidates.sort(key=key)
    # Shuffle among equally suitable missions so the next question is not predictable.
    import random
    groups={}
    for m in candidates:
        groups.setdefault((abs((m.difficulty or 1)-target), m.difficulty or 1), []).append(m)
    result=[]
    for group in groups.values():
        random.shuffle(group)
        result.extend(group)
    return result[:8]

def discovery_summary(user_id):
    attempts=MissionAttempt.query.filter_by(user_id=user_id).all()
    feedback=InterestFeedback.query.filter_by(user_id=user_id).all()
    return {"missions_completed":len(attempts),"feedback_count":len(feedback)}
