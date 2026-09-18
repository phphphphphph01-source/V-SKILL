from flask import Blueprint, render_template, request, redirect, url_for, flash
from flask_login import login_user, logout_user
from database.database import db
from database.models import User, Department
auth_bp=Blueprint("auth",__name__)
@auth_bp.route("/register",methods=["GET","POST"])
def register():
    if request.method=="POST":
        name=request.form["name"].strip(); email=request.form["email"].strip().lower(); pw=request.form["password"]
        if User.query.filter_by(email=email).first(): flash("Email นี้ถูกใช้แล้ว"); return render_template("register.html")
        u=User(name=name,email=email,role="student"); u.set_password(pw)
        db.session.add(u); db.session.commit(); login_user(u)
        return redirect(url_for("student.dashboard"))
    return render_template("register.html",departments=Department.query.all())
@auth_bp.route("/login",methods=["GET","POST"])
def login():
    if request.method=="POST":
        u=User.query.filter_by(email=request.form["email"].strip().lower()).first()
        if u and u.check_password(request.form["password"]):
            login_user(u)
            return redirect(url_for({"student":"student.dashboard","teacher":"teacher.dashboard","admin":"admin.dashboard"}[u.role]))
        flash("อีเมลหรือรหัสผ่านไม่ถูกต้อง")
    return render_template("login.html")
@auth_bp.get("/logout")
def logout():
    logout_user(); return redirect(url_for("main.index"))
