from flask import Blueprint,jsonify,request
from flask_login import login_required,current_user
from database.database import db
from database.models import Skill,Career,Department
from core.skill_engine import profile
from core.career_engine import career_fit,department_fit
from ai.tutor import tutor
api_bp=Blueprint("api",__name__)
@api_bp.get("/me")
@login_required
def me(): return jsonify({"id":current_user.id,"name":current_user.name,"role":current_user.role})
@api_bp.get("/skills")
def skills(): return jsonify([{"id":s.id,"name":s.name,"description":s.description} for s in Skill.query.all()])
@api_bp.get("/careers")
def careers(): return jsonify([{"id":c.id,"name":c.name,"description":c.description} for c in Career.query.all()])
@api_bp.get("/student/skill-profile")
@login_required
def skill_profile(): return jsonify(profile(current_user.id))
@api_bp.get("/student/career-fit")
@login_required
def fit(): return jsonify({"careers":career_fit(current_user.id),"departments":department_fit(current_user.id)})
@api_bp.post("/student/tutor")
@login_required
def ai_tutor():
    d=request.get_json() or {}; return jsonify(tutor(d.get("message",""),d.get("context","")))

@api_bp.get("/student/skill-dna")
@login_required
def skill_dna_api():
    from core.full_engine import skill_dna
    return jsonify(skill_dna(current_user.id))

@api_bp.get("/student/report")
@login_required
def report_api():
    from core.full_engine import discovery_report
    return jsonify(discovery_report(current_user.id))

@api_bp.get("/student/achievements")
@login_required
def achievements_api():
    from core.full_engine import achievements
    return jsonify([{"name":x.achievement.name,"description":x.achievement.description} for x in achievements(current_user.id)])

@api_bp.get("/student/portfolio")
@login_required
def portfolio_api():
    from core.full_engine import portfolio_data
    return jsonify(portfolio_data(current_user.id))

@api_bp.get("/student/certificate")
@login_required
def certificate_api():
    from core.full_engine import certificate_for_top_skill
    c=certificate_for_top_skill(current_user.id)
    return jsonify(None if not c else {"certificate_id":c.certificate_id,"skill_id":c.skill_id,"score":c.score,"issued_at":c.issued_at.isoformat()})

@api_bp.get("/student/departments")
@login_required
def student_departments():
    from core.discovery_engine import NEW_DEPARTMENTS
    return jsonify([{"id":d.id,"name":d.name,"description":d.description} for d in Department.query.filter(Department.name.in_(list(NEW_DEPARTMENTS))).order_by(Department.name).all()])

@api_bp.get("/student/department")
@login_required
def student_department():
    from core.discovery_engine import selected_department
    d=selected_department(current_user)
    return jsonify(None if not d else {"id":d.id,"name":d.name,"description":d.description})

@api_bp.post("/student/department")
@login_required
def set_student_department():
    if current_user.role!="student": return jsonify({"ok":False,"error":"เฉพาะนักเรียน"}),403
    from core.discovery_engine import NEW_DEPARTMENTS
    try: dep_id=int((request.get_json(silent=True) or {}).get("department_id"))
    except (TypeError,ValueError): return jsonify({"ok":False,"error":"department_id ไม่ถูกต้อง"}),400
    d=db.session.get(Department,dep_id)
    if not d or d.name not in NEW_DEPARTMENTS: return jsonify({"ok":False,"error":"ไม่พบสายการเรียน"}),404
    current_user.departments=[d]; db.session.commit()
    return jsonify({"ok":True,"department":{"id":d.id,"name":d.name,"description":d.description}})
