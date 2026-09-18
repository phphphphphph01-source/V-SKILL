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
