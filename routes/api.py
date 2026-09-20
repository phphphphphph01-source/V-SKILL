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

# Knowledge Library API: the same source is used by the HTML reader and future clients.
@api_bp.get("/student/library")
@login_required
def library_index_api():
    from core.library import rank_library_articles
    from database.models import LibraryArticle, LibraryCategory, LibraryProgress
    from core.discovery_engine import selected_department
    department_id = request.args.get("department_id", type=int) or (selected_department(current_user).id if selected_department(current_user) else None)
    q = (request.args.get("q") or "").strip()
    category_id = request.args.get("category_id", type=int)
    difficulty = (request.args.get("difficulty") or "").strip()
    query = LibraryArticle.query.filter_by(status="published")
    if department_id:
        query = query.filter_by(department_id=department_id)
    if category_id:
        query = query.filter_by(category_id=category_id)
    if difficulty:
        query = query.filter_by(difficulty=difficulty)
    rows = rank_library_articles(query.all(), q)
    progress = {p.article_id: p for p in LibraryProgress.query.filter_by(user_id=current_user.id).all()}
    return jsonify({"ok": True, "articles": [{
        "id": a.id, "title": a.title, "slug": a.slug, "summary": a.summary,
        "department_id": a.department_id, "category_id": a.category_id,
        "difficulty": a.difficulty, "estimated_minutes": a.estimated_minutes,
        "cover_image": a.cover_image, "progress": (progress[a.id].progress if a.id in progress else 0),
        "completed": (progress[a.id].completed if a.id in progress else False),
    } for a in rows]})


@api_bp.get("/student/library/<slug>")
@login_required
def library_detail_api(slug):
    from database.models import LibraryArticle, LibraryProgress
    article = LibraryArticle.query.filter_by(slug=slug, status="published").first()
    if not article:
        return jsonify({"ok": False, "error": "ไม่พบบทความ"}), 404
    progress = LibraryProgress.query.filter_by(user_id=current_user.id, article_id=article.id).first()
    return jsonify({"ok": True, "article": {
        "id": article.id, "title": article.title, "slug": article.slug,
        "summary": article.summary, "content": article.content,
        "learning_objectives": article.learning_objectives,
        "practical_example": article.practical_example,
        "real_world_scenario": article.real_world_scenario,
        "common_mistakes": article.common_mistakes,
        "safety_notes": article.safety_notes, "checklist": article.checklist,
        "mini_challenge": article.mini_challenge,
        "skills": [{"id": s.id, "name": s.name} for s in article.skills],
        "missions": [{"id": m.id, "title": m.title} for m in article.missions],
        "progress": progress.progress if progress else 0,
        "completed": progress.completed if progress else False,
    }})

@api_bp.post("/student/library/<slug>/progress")
@login_required
def library_progress_api(slug):
    from database.models import LibraryArticle, LibraryProgress
    article = LibraryArticle.query.filter_by(slug=slug, status="published").first()
    if not article:
        return jsonify({"ok": False, "error": "ไม่พบบทความ"}), 404
    payload = request.get_json(silent=True) or {}
    try:
        raw = int(payload.get("progress", 0))
        last_position = int(payload.get("last_position", raw))
    except (TypeError, ValueError):
        return jsonify({"ok": False, "error": "progress ต้องเป็นตัวเลข"}), 400
    raw = max(0, min(100, raw))
    value = min((0, 25, 50, 75, 100), key=lambda point: abs(point - raw))
    row = LibraryProgress.query.filter_by(user_id=current_user.id, article_id=article.id).first()
    if not row:
        row = LibraryProgress(user_id=current_user.id, article_id=article.id)
        db.session.add(row)
    now = __import__("datetime").datetime.utcnow()
    row.progress = value
    row.last_position = max(0, min(100, last_position))
    row.completed = value >= 100
    row.last_read_at = now
    row.completed_at = row.completed_at or now if row.completed else None
    db.session.commit()
    return jsonify({"ok": True, "progress": row.progress, "completed": row.completed, "last_position": row.last_position})
