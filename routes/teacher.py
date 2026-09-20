from flask import Blueprint,render_template,request,redirect,url_for,abort,flash
from flask_login import login_required,current_user
from database.database import db
from database.models import *
teacher_bp=Blueprint("teacher",__name__)
def teacher_only():
    if current_user.role!="teacher": abort(403)
@teacher_bp.get("/")
@login_required
def dashboard():
    teacher_only()
    students=User.query.filter_by(role="student").all()
    return render_template("teacher/dashboard.html",students=students,missions=Mission.query.count())
@teacher_bp.route("/missions",methods=["GET","POST"])
@login_required
def missions():
    teacher_only()
    if request.method=="POST":
        m=Mission(title=request.form["title"],scenario=request.form["scenario"],difficulty=int(request.form["difficulty"]),
                  time_limit=int(request.form["time_limit"]),department_id=int(request.form["department_id"]))
        skill_ids=[int(x) for x in request.form.getlist("skills")]
        m.skills=Skill.query.filter(Skill.id.in_(skill_ids)).all()
        db.session.add(m); db.session.commit(); flash("สร้าง Mission แล้ว")
        return redirect(url_for("teacher.missions"))
    return render_template("teacher/missions.html",missions=Mission.query.all(),departments=Department.query.all(),skills=Skill.query.all())
@teacher_bp.post("/missions/<int:mid>/delete")
@login_required
def delete_mission(mid):
    teacher_only(); m=Mission.query.get_or_404(mid); db.session.delete(m); db.session.commit(); return redirect(url_for("teacher.missions"))

# Library content management is restricted to teacher/admin roles and never exposed
# through the student routes.
@teacher_bp.route("/library", methods=["GET", "POST"])
@login_required
def library_manager():
    if current_user.role not in {"teacher", "admin"}:
        abort(403)
    if request.method == "POST":
        title = (request.form.get("title") or "").strip()
        summary = (request.form.get("summary") or "").strip()
        content = (request.form.get("content") or "").strip()
        try:
            department_id = int(request.form.get("department_id"))
            category_id = int(request.form.get("category_id"))
            estimated_minutes = max(1, min(180, int(request.form.get("estimated_minutes") or 5)))
        except (TypeError, ValueError):
            abort(400, description="ข้อมูลหมวดหมู่/เวลาอ่านไม่ถูกต้อง")
        if len(title) < 5 or len(title) > 220 or len(content) < 120:
            abort(400, description="หัวข้อต้องยาว 5-220 ตัวอักษร และเนื้อหาต้องมีอย่างน้อย 120 ตัวอักษร")
        department = db.session.get(Department, department_id)
        category = db.session.get(LibraryCategory, category_id)
        if not department or not category or category.department_id != department.id:
            abort(400, description="Department และ Category ไม่สัมพันธ์กัน")
        from core.library import _slug
        slug = _slug(f"{department.name}-{title}")
        if LibraryArticle.query.filter_by(slug=slug).first():
            abort(409, description="บทความ slug นี้มีอยู่แล้ว")
        cover_image = (request.form.get("cover_image") or "").strip()
        if cover_image and not (cover_image.startswith("/static/") or cover_image.startswith("https://")):
            abort(400, description="cover image ต้องเป็น /static/ หรือ https://")
        article = LibraryArticle(
            department_id=department.id, category_id=category.id, title=title,
            slug=slug, summary=summary, content=content,
            difficulty=request.form.get("difficulty") or "พื้นฐาน",
            estimated_minutes=estimated_minutes, cover_image=cover_image,
            tags=(request.form.get("tags") or "").strip(), status="published",
            learning_objectives=(request.form.get("learning_objectives") or "").strip(),
            safety_notes=(request.form.get("safety_notes") or "").strip(),
            mini_challenge=(request.form.get("mini_challenge") or "").strip(),
        )
        article.skills = Skill.query.filter(Skill.id.in_([int(x) for x in request.form.getlist("skill_ids") if x.isdigit()])).all()
        article.missions = Mission.query.filter(Mission.id.in_([int(x) for x in request.form.getlist("mission_ids") if x.isdigit()]), Mission.department_id == department.id).all()
        db.session.add(article)
        db.session.commit()
        return redirect(url_for("teacher.library_manager"))
    return render_template("teacher/library.html", articles=LibraryArticle.query.order_by(LibraryArticle.updated_at.desc()).all(), departments=Department.query.order_by(Department.name).all(), categories=LibraryCategory.query.order_by(LibraryCategory.name).all(), skills=Skill.query.order_by(Skill.name).all(), missions=Mission.query.filter_by(discovery=True).order_by(Mission.title).all())

@teacher_bp.route("/library/<int:article_id>/edit", methods=["GET", "POST"])
@login_required
def library_edit(article_id):
    if current_user.role not in {"teacher", "admin"}:
        abort(403)
    article = LibraryArticle.query.get_or_404(article_id)
    if request.method == "POST":
        title = (request.form.get("title") or "").strip()
        content = (request.form.get("content") or "").strip()
        try:
            department_id = int(request.form.get("department_id"))
            category_id = int(request.form.get("category_id"))
            minutes = max(1, min(180, int(request.form.get("estimated_minutes") or 5)))
        except (TypeError, ValueError):
            abort(400, description="ข้อมูลบทความไม่ถูกต้อง")
        department = db.session.get(Department, department_id)
        category = db.session.get(LibraryCategory, category_id)
        if not department or not category or category.department_id != department.id or len(title) < 5 or len(content) < 120:
            abort(400, description="ตรวจสอบชื่อ เนื้อหา Department และ Category")
        from core.library import _slug
        new_slug = _slug(f"{department.name}-{title}")
        conflict = LibraryArticle.query.filter(LibraryArticle.slug == new_slug, LibraryArticle.id != article.id).first()
        if conflict:
            abort(409, description="slug ใหม่ซ้ำกับบทความอื่น")
        article.title = title
        article.slug = new_slug
        article.summary = (request.form.get("summary") or "").strip()
        article.content = content
        article.department_id = department.id
        article.category_id = category.id
        article.difficulty = request.form.get("difficulty") or "พื้นฐาน"
        article.estimated_minutes = minutes
        article.tags = (request.form.get("tags") or "").strip()
        article.cover_image = (request.form.get("cover_image") or "").strip()
        article.learning_objectives = (request.form.get("learning_objectives") or "").strip()
        article.safety_notes = (request.form.get("safety_notes") or "").strip()
        article.mini_challenge = (request.form.get("mini_challenge") or "").strip()
        article.skills = Skill.query.filter(Skill.id.in_([int(x) for x in request.form.getlist("skill_ids") if x.isdigit()])).all()
        article.missions = Mission.query.filter(Mission.id.in_([int(x) for x in request.form.getlist("mission_ids") if x.isdigit()]), Mission.department_id == department.id).all()
        db.session.commit()
        return redirect(url_for("teacher.library_manager"))
    return render_template("teacher/library_edit.html", article=article, departments=Department.query.order_by(Department.name).all(), categories=LibraryCategory.query.order_by(LibraryCategory.name).all(), skills=Skill.query.order_by(Skill.name).all(), missions=Mission.query.filter_by(discovery=True).order_by(Mission.title).all())


@teacher_bp.post("/library/<int:article_id>/archive")
@login_required
def library_archive(article_id):
    if current_user.role not in {"teacher", "admin"}:
        abort(403)
    article = LibraryArticle.query.get_or_404(article_id)
    article.status = "archived"
    db.session.commit()
    return redirect(url_for("teacher.library_manager"))
