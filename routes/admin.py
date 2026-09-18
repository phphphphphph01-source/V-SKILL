from flask import Blueprint,render_template,abort
from flask_login import login_required,current_user
from database.models import *
admin_bp=Blueprint("admin",__name__)
@admin_bp.get("/")
@login_required
def dashboard():
    if current_user.role!="admin": abort(403)
    return render_template("admin/dashboard.html",users=User.query.count(),missions=Mission.query.count(),
                           departments=Department.query.count(),skills=Skill.query.count())
