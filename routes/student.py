from flask import Blueprint, render_template, request, redirect, url_for, jsonify, abort, session
from flask_login import login_required,current_user
from database.database import db
from database.models import *
from core.scoring import score_attempt
from core.skill_engine import profile,rebuild_user_skills
from core.skill_perks import dashboard_data as skill_lab_data, apply_mission_completion, award_achievement_bonus, sync_skill_perks_from_items
from core.career_engine import career_fit,department_fit
from core.discovery_engine import recommended_discovery, selected_department, NEW_DEPARTMENTS
from core.recommendation import learning_plan_data
from core.quiz_bank import make_session, make_from_ids
import uuid,datetime,random,json,secrets
from core.avatar_items import ensure_catalog as ensure_avatar_item_catalog, curated_items as curated_avatar_items, skill_id_for_item
student_bp=Blueprint("student",__name__)

def _require_department():
    """Return the student's active department or None.
    Legacy department records are intentionally ignored so users can migrate
    into the new department-selection catalog without losing their account.
    """
    return selected_department(current_user)

def _ensure_department_selected():
    dep=_require_department()
    if not dep:
        return redirect(url_for("student.department_select"))
    return None

@student_bp.get("/")
@login_required
def dashboard():
    if current_user.role!="student": abort(403)
    gate=_ensure_department_selected()
    if gate: return gate
    prof=profile(current_user.id)
    progress=UserProgress.query.filter_by(user_id=current_user.id).first()
    return render_template("student/dashboard.html", profile=prof, careers=career_fit(current_user.id)[:5],
        departments=department_fit(current_user.id)[:8], missions=recommended_discovery(current_user.id),
        progress=progress)

@student_bp.route("/department", methods=["GET","POST"])
@login_required
def department_select():
    if current_user.role!="student": abort(403)
    from database.models import Department
    from core.department_missions import DEPARTMENT_CATALOG
    departments=Department.query.filter(Department.name.in_(list(NEW_DEPARTMENTS))).order_by(Department.name).all()
    current=_require_department()
    if request.method=="POST":
        try:
            dep_id=int(request.form.get("department_id",""))
        except (TypeError,ValueError):
            return render_template("student/department_select.html",departments=departments,current=current,error="กรุณาเลือกสายการเรียน")
        dep=db.session.get(Department,dep_id)
        if not dep or dep.name not in DEPARTMENT_CATALOG:
            return render_template("student/department_select.html",departments=departments,current=current,error="ไม่พบสายการเรียนที่เลือก")
        # Exactly one active department. Historical skill evidence is retained.
        current_user.departments=[dep]
        db.session.commit()
        return redirect(url_for("student.dashboard"))
    return render_template("student/department_select.html",departments=departments,current=current)

@student_bp.get("/discovery")
@login_required
def discovery():
    if current_user.role!="student": abort(403)
    gate=_ensure_department_selected()
    if gate: return gate
    from core.skill_perks import equipped as equipped_perks
    active=set(equipped_perks(current_user.id))
    missions=recommended_discovery(current_user.id)
    random.shuffle(missions)
    # Exploration perks may widen the number of recommended missions, but never
    # alter questions, correct answers, score, or skill evidence.
    if "explorer_compass" not in active:
        missions=missions[:6]
    elif "mission_hunter" in active:
        missions=missions[:10]
    return render_template("student/discovery.html",missions=missions,exploration_perks=active)

@student_bp.get("/mission/<int:mission_id>")
@login_required
def mission(mission_id):
    if current_user.role!="student": abort(403)
    gate=_ensure_department_selected()
    if gate: return gate
    dep=_require_department()
    m=Mission.query.get_or_404(mission_id)
    if m.department_id != dep.id:
        abort(403)
    # Runtime guard: old deployed databases may still contain 3-step missions.
    # Repair before rendering so a learner can never enter a partial assessment.
    from core.question_engine import ensure_mission_has_ten_questions
    ensure_mission_has_ten_questions(m.id, dep.id)
    db.session.refresh(m)
    if len(m.steps) != 10:
        return jsonify({"ok":False,"error":"Mission นี้ยังมีข้อสอบไม่ครบ 10 ข้อ กรุณาลองใหม่"}), 500
    # A completed mission is not replayed as a scored mission. Users receive a
    # fresh mission from the same department instead.
    if MissionAttempt.query.filter_by(user_id=current_user.id,mission_id=m.id).filter(MissionAttempt.completed_at.isnot(None)).first():
        return redirect(url_for("student.discovery"))
    # Create/reuse a server-side session so timer and hints cannot be forged.
    now=datetime.datetime.utcnow()
    active=MissionSession.query.filter_by(user_id=current_user.id,mission_id=m.id,completed_at=None).order_by(MissionSession.id.desc()).first()
    if not active or active.expires_at <= now:
        if active:
            active.completed_at=now
        active=MissionSession(user_id=current_user.id,mission_id=m.id,started_at=now,
                              expires_at=now+datetime.timedelta(seconds=max(30,m.time_limit)))
        db.session.add(active); db.session.commit()
    choice_map={step.id:list(step.choices) for step in m.steps}
    for choices in choice_map.values():
        random.shuffle(choices)
    return render_template("student/mission.html",mission=m,choice_map=choice_map,
                           avatar=_ensure_avatar(current_user.id),mission_session=active)

@student_bp.post("/mission/<int:mission_id>/submit")
@login_required
def submit(mission_id):
    if current_user.role!="student": abort(403)
    dep=_require_department()
    if not dep: return jsonify({"ok":False,"error":"กรุณาเลือกสายการเรียนก่อน"}),400
    m=Mission.query.get_or_404(mission_id)
    if m.department_id != dep.id:
        return jsonify({"ok":False,"error":"Mission นี้ไม่อยู่ในสายการเรียนปัจจุบันของคุณ"}),403

    # One scored attempt per mission. This prevents farming the same question.
    if MissionAttempt.query.filter_by(user_id=current_user.id,mission_id=m.id).filter(MissionAttempt.completed_at.isnot(None)).first():
        return jsonify({"ok":False,"error":"Mission นี้ถูกทำไปแล้ว ระบบจะส่ง Mission ใหม่ให้คุณ"}),409

    active=MissionSession.query.filter_by(
        user_id=current_user.id, mission_id=m.id, completed_at=None
    ).order_by(MissionSession.id.desc()).first()
    if not active:
        return jsonify({"ok":False,"error":"ไม่พบ Mission session กรุณาเปิด Mission ใหม่"}),409

    now=datetime.datetime.utcnow()
    actual_elapsed=max(0.0,(now-active.started_at).total_seconds())
    # Time is server-authoritative. Going over the limit is allowed to submit,
    # but receives no time bonus rather than blocking evidence.
    elapsed=min(actual_elapsed, float(max(m.time_limit,1)))

    data=request.get_json(silent=True) or {}
    decisions=data.get("decisions",[])
    # Client may only submit step_id/choice_id. Hint usage is read from session.
    clean=[]
    for d in decisions:
        if not isinstance(d,dict): continue
        clean.append({"step_id":d.get("step_id"),"choice_id":d.get("choice_id")})

    try:
        score,accuracy,validated=score_attempt(m,clean,elapsed)
    except (ValueError,TypeError,KeyError):
        return jsonify({"ok":False,"error":"ข้อมูลการตัดสินใจของ Mission ไม่ถูกต้องหรือไม่ครบทุกขั้น"}),400

    hints=int(active.hints_used or 0)
    # Remove client-controlled hint level from validated evidence.
    for d in validated:
        d["hint_level"]=0

    a=MissionAttempt(user_id=current_user.id,mission_id=m.id,started_at=active.started_at,
                     completed_at=now,score=score,accuracy=accuracy,time_used=actual_elapsed,
                     hints_used=hints)
    db.session.add(a); db.session.flush()
    for d in validated:
        db.session.add(AttemptDecision(attempt_id=a.id,step_id=d["step_id"],choice_id=d["choice_id"],
                                       points=d["points"],hint_level=0))
    active.completed_at=now
    db.session.commit()
    rebuild_user_skills(current_user.id)

    # Use the single achievement engine so duplicate logic cannot drift.
    from core.full_engine import achievements
    before={x.achievement_id for x in UserAchievement.query.filter_by(user_id=current_user.id).all()}
    achievements(current_user.id)
    after={x.achievement_id for x in UserAchievement.query.filter_by(user_id=current_user.id).all()}
    new_achievement_ids=list(after-before)

    reward=apply_mission_completion(current_user.id,a.id,base_progress=100,base_xp=50)
    achievement_bonus=0
    if new_achievement_ids:
        achievement_bonus=award_achievement_bonus(current_user.id,new_achievement_ids[-1])
    reward["achievement_bonus"]=achievement_bonus

    return jsonify({"ok":True,"attempt_id":a.id,"score":score,"accuracy":accuracy,
                    "time_used":round(actual_elapsed,1),"hints_used":hints,
                    "decisions":validated,"reward":reward})

@student_bp.post("/mission/<int:mission_id>/hint")
@login_required
def mission_hint(mission_id):
    if current_user.role!="student": abort(403)
    dep=_require_department()
    m=Mission.query.get_or_404(mission_id)
    if not dep or m.department_id!=dep.id:
        return jsonify({"ok":False,"error":"ไม่สามารถใช้ Hint ของ Mission นี้ได้"}),403
    active=MissionSession.query.filter_by(user_id=current_user.id,mission_id=m.id,completed_at=None).order_by(MissionSession.id.desc()).first()
    if not active:
        return jsonify({"ok":False,"error":"Mission session หมดอายุ กรุณาเปิด Mission ใหม่"}),409
    if active.expires_at <= datetime.datetime.utcnow():
        return jsonify({"ok":False,"error":"หมดเวลา Mission แล้ว"}),409
    level=int(active.hints_used or 0)+1
    if level>3:
        return jsonify({"ok":False,"error":"ใช้คำใบ้ครบ 3 ครั้งแล้ว"}),409
    step_id=request.get_json(silent=True).get("step_id") if request.is_json else request.form.get("step_id")
    try: step_id=int(step_id)
    except (TypeError,ValueError): return jsonify({"ok":False,"error":"ไม่พบขั้นตอน"}),400
    step=db.session.get(MissionStep,step_id)
    if not step or step.mission_id!=m.id:
        return jsonify({"ok":False,"error":"ขั้นตอนไม่ถูกต้อง"}),400
    active.hints_used=level
    db.session.commit()
    hint=[step.hint1,step.hint2,step.hint3][level-1] or "ลองเริ่มจากข้อมูลที่ตรวจสอบได้ก่อน"
    return jsonify({"ok":True,"level":level,"hint":hint})

@student_bp.post("/feedback")
@login_required
def feedback():
    data=request.get_json()
    db.session.add(InterestFeedback(user_id=current_user.id,mission_id=int(data["mission_id"]),
                                    enjoyment=int(data["enjoyment"]),repeat_interest=bool(data["repeat_interest"])))
    db.session.commit(); return jsonify({"ok":True})


@student_bp.route("/quiz", methods=["GET","POST"])
@login_required
def quiz_arena():
    if current_user.role != "student":
        abort(403)
    gate=_ensure_department_selected()
    if gate:
        return gate
    dep=_require_department()
    if request.method == "POST":
        payload=request.get_json(silent=True) or {}
        quiz_state=session.get("vskill_quiz")
        if not quiz_state:
            return jsonify({"ok":False,"error":"รอบข้อสอบหมดอายุ กรุณาเริ่มรอบใหม่"}),400
        dep=_require_department()
        if not dep:
            return jsonify({"ok":False,"error":"กรุณาเลือกสายการเรียนก่อน"}),400
        if int(quiz_state.get("department_id", dep.id)) != int(dep.id):
            session.pop("vskill_quiz",None)
            return jsonify({"ok":False,"error":"มีการเปลี่ยนสายการเรียน กรุณาเริ่มรอบข้อสอบใหม่"}),409
        questions=make_from_ids(quiz_state["ids"], quiz_state["seed"], department_name=dep.name)
        if len(questions) != len(quiz_state.get("ids", [])):
            session.pop("vskill_quiz",None)
            return jsonify({"ok":False,"error":"คลังข้อสอบของสายนี้มีการเปลี่ยนแปลง กรุณาเริ่มรอบใหม่"}),409
        answers=payload.get("answers",{})
        correct=0
        results=[]
        for q in questions:
            chosen=answers.get(q["id"])
            is_correct=(chosen is not None and int(chosen)==int(q["correct_position"]))
            correct += int(is_correct)
            results.append({"id":q["id"],"correct":is_correct,"correct_position":q["correct_position"]})
        total=len(questions)
        score=round(correct/total*100,1) if total else 0
        # Store lightweight session history for the user's current browser session.
        history=session.get("vskill_quiz_history",[])
        history.insert(0,{"score":score,"correct":correct,"total":total})
        session["vskill_quiz_history"]=history[:5]
        session.pop("vskill_quiz",None)
        return jsonify({"ok":True,"score":score,"correct":correct,"total":total,"results":results})
    import secrets
    seed=secrets.randbits(63)
    questions=make_session(10, seed=seed, department_name=dep.name)
    if len(questions) != 10:
        return jsonify({"ok":False,"error":"คลังข้อสอบของสายนี้ยังไม่พร้อม 10 ข้อ กรุณาเรียกใหม่"}),500
    session["vskill_quiz"]={"ids":[q["id"] for q in questions],"seed":seed,"department_id":dep.id}
    return render_template("student/quiz.html",questions=questions,
                           history=session.get("vskill_quiz_history",[]))

# ---------------- SKILL LAB ----------------
@student_bp.get("/skills")
@login_required
def skills_page():
    if current_user.role!="student": abort(403)
    gate=_ensure_department_selected()
    if gate: return gate
    prof=profile(current_user.id)
    # Show every available skill, including unmeasured skills at 0, so the
    # profile is useful from the first day.
    measured={x["skill_id"]:x for x in prof}
    all_skills=Skill.query.order_by(Skill.name).all()
    rows=[]
    for s in all_skills:
        rows.append(measured.get(s.id,{"skill":s.name,"skill_id":s.id,"score":0,"evidence":0,
                    "qualified":False,"confidence":"ยังไม่มีหลักฐาน","confidence_score":0}))
    rows.sort(key=lambda x:(-x["score"],x["skill"]))
    return render_template("student/skills.html",profile=rows)

@student_bp.post("/skills/<skill_id>/equip")
@login_required
def skill_equip(skill_id):
    if current_user.role!="student": abort(403)
    # Kept only as a compatibility endpoint. Skills cannot be equipped here.
    sync_skill_perks_from_items(current_user.id)
    payload={"ok":False,"message":"Skill Lab ใช้ดูความสามารถเท่านั้น — กรุณาใส่ไอเทมประจำ Skill ใน Buddy Studio","active_ids":skill_lab_data(current_user.id)["active_ids"]}
    return jsonify(payload),409

@student_bp.get("/careers")
@login_required
def careers():
    rows=career_fit(current_user.id)
    compass="career_compass" in __import__("core.skill_perks",fromlist=["equipped"]).equipped(current_user.id)
    if compass:
        prof=sorted(profile(current_user.id), key=lambda x:x.get("score",0), reverse=True)
        top=[x["skill"] for x in prof[:2] if x.get("score",0)>0]
        for row in rows:
            row["recommendation_reason"] = ("คุณมี Progress ในหมวด " + " และ ".join(top) + " สูง และมีหลักฐานจาก Mission จริง"
                                         if top else "ระบบจะแนะนำจากหลักฐาน Mission ที่คุณทำจริง")
    return render_template("student/careers.html",careers=rows,career_compass=compass)
@student_bp.get("/learning")
@login_required
def learning(): return render_template("student/learning.html",topics=learning_plan_data(current_user.id))
@student_bp.get("/portfolio")
@login_required
def portfolio():
    prof=profile(current_user.id)
    return render_template("student/portfolio.html",user=current_user,profile=prof,attempts=current_user.attempts,avatar=_ensure_avatar(current_user.id))


@student_bp.get("/skill-dna")
@login_required
def skill_dna_page():
    from core.full_engine import skill_dna
    return render_template("student/skill_dna.html", dna=skill_dna(current_user.id))

@student_bp.get("/report")
@login_required
def discovery_report_page():
    from core.full_engine import discovery_report
    return render_template("student/report.html", report=discovery_report(current_user.id))

@student_bp.get("/achievements")
@login_required
def achievements_page():
    from core.full_engine import achievements
    return render_template("student/achievements.html", achievements=achievements(current_user.id), avatar=_ensure_avatar(current_user.id))

@student_bp.get("/certificate")
@login_required
def certificate_page():
    from core.full_engine import certificate_for_top_skill
    return render_template("student/certificate.html", certificate=certificate_for_top_skill(current_user.id))

@student_bp.get("/portfolio/full")
@login_required
def full_portfolio():
    from core.full_engine import portfolio_data
    return render_template("student/portfolio_full.html", data=portfolio_data(current_user.id), user=current_user)

@student_bp.route("/interview", methods=["GET","POST"])
@login_required
def interview():
    from core.full_engine import interview_score
    result=None
    if request.method=="POST":
        answer=request.form.get("answer","")
        score,feedback=interview_score(answer)
        i=Interview(user_id=current_user.id)
        db.session.add(i); db.session.flush()
        db.session.add(InterviewResult(interview_id=i.id,question=request.form.get("question","เล่าสถานการณ์ที่คุณแก้ปัญหายากที่สุด"),answer=answer,score=score,feedback=feedback))
        db.session.commit()
        result={"score":score,"feedback":feedback}
    return render_template("student/interview.html",result=result)

@student_bp.get("/growth")
@login_required
def growth():
    from core.skill_engine import rebuild_user_skills
    rebuild_user_skills(current_user.id)
    rows=[]
    for h in SkillHistory.query.filter_by(user_id=current_user.id).order_by(SkillHistory.skill_id,SkillHistory.id).all():
        skill=db.session.get(Skill,h.skill_id)
        if skill:
            rows.append({"skill":skill.name,"score":h.score,"attempt":h.source_attempt_id,"at":h.created_at.strftime("%Y-%m-%d %H:%M")})
    return render_template("student/growth.html",rows=rows)


# ---------------- LIVE COMPETITION ----------------
def _competition_code():
    alphabet='ABCDEFGHJKLMNPQRSTUVWXYZ23456789'
    while True:
        code=''.join(secrets.choice(alphabet) for _ in range(6))
        if not Competition.query.filter_by(code=code).first():
            return code

def _get_competition(code):
    return Competition.query.filter_by(code=code.upper()).first_or_404()

def _participant(comp, user_id):
    return CompetitionParticipant.query.filter_by(competition_id=comp.id,user_id=user_id).first()

def _competition_department_name(comp):
    """Return the active department used by the competition host.

    Competition questions are department-isolated, so every room must build
    its question set from the host's selected vocational department.
    """
    host=db.session.get(User, comp.host_user_id)
    dep=selected_department(host) if host else None
    return dep.name if dep else None

def _ensure_competition_questions(comp):
    """Repair legacy/partially-created rooms that have no question rows.

    Older rooms could be created while the question bank was temporarily
    unavailable. The room must never crash the live-state endpoint in that
    case. Waiting rooms are safely re-seeded; running rooms are left unchanged
    so their timer/answer integrity cannot be altered mid-match.
    """
    if len(comp.questions) >= comp.total_questions:
        return True
    if comp.status != 'waiting':
        return False
    seed=secrets.randbits(63)
    department_name=_competition_department_name(comp)
    questions=make_session(
        comp.total_questions,
        seed=seed,
        department_name=department_name
    )
    if not questions or len(questions) < comp.total_questions:
        return False
    for old in list(comp.questions):
        db.session.delete(old)
    for idx,q in enumerate(questions,1):
        db.session.add(CompetitionQuestion(
            competition_id=comp.id, order_index=idx,
            question_text=q['question'],
            category=f"{q['category']} · {q['sub']}",
            choices_json=json.dumps(q['choices'],ensure_ascii=False),
            correct_index=q['correct_position']))
    db.session.commit()
    db.session.refresh(comp)
    return len(comp.questions) >= comp.total_questions

def _sync_comp_status(comp):
    if comp.status=='running' and comp.started_at:
        elapsed=(datetime.datetime.utcnow()-comp.started_at).total_seconds()
        total=comp.question_seconds*comp.total_questions
        if elapsed >= total:
            comp.status='finished'
            comp.finished_at=datetime.datetime.utcnow()
            db.session.commit()
    return comp

def _competition_buddy_payload(user_id):
    av=_ensure_avatar(user_id)
    species=av.species or 'fox'
    species_item=AvatarItem.query.filter_by(slot='species',asset_key=species).first()
    try:
        equipped=json.loads(av.equipped_items or '{}')
    except Exception:
        equipped={}
    skill_keys=equipped.get('skill_items',[]) if isinstance(equipped,dict) else []
    if not isinstance(skill_keys,list):
        skill_keys=[skill_keys] if skill_keys else []
    return {
        'species':species,
        'name':species_item.name if species_item else {'fox':'Explorer Fox','cat':'Smart Cat','rabbit':'Builder Rabbit','panda':'Tech Panda','penguin':'Cyber Penguin','tiger':'Engineer Tiger','owl':'AI Owl','wolf':'Cyber Wolf','dragon':'V-Dragon','unicorn':'V-Unicorn'}.get(species,'Buddy'),
        'rarity':species_item.rarity if species_item else 'common',
        'image':f'/static/img/avatar_assets/avatar_{species}.png',
        'level':1 + MissionAttempt.query.filter_by(user_id=user_id).filter(MissionAttempt.completed_at.isnot(None)).count(),
        'items':[{'key':k,'image':f'/static/img/avatar_assets/item_{k}.png'} for k in skill_keys[:3]]
    }

@student_bp.get('/competition')
@login_required
def competition_home():
    if current_user.role!='student': abort(403)
    recent=CompetitionParticipant.query.filter_by(user_id=current_user.id).order_by(CompetitionParticipant.joined_at.desc()).limit(5).all()
    return render_template('student/competition.html', recent=recent)

@student_bp.post('/competition/create')
@login_required
def competition_create():
    if current_user.role!='student': abort(403)
    title=(request.form.get('title') or 'V-SKILL LIVE DUEL').strip()[:180]
    comp=Competition(code=_competition_code(),title=title,host_user_id=current_user.id,status='waiting',question_seconds=15,total_questions=8)
    db.session.add(comp); db.session.flush()
    dep=_require_department()
    if not dep:
        db.session.rollback()
        return redirect(url_for('student.department_select'))
    seed=secrets.randbits(63)
    questions=make_session(
        comp.total_questions,
        seed=seed,
        department_name=dep.name
    )
    if len(questions) < comp.total_questions:
        db.session.rollback()
        return redirect(url_for('student.competition_home', error='คลังคำถามของสายการเรียนยังไม่พร้อม'))
    for idx,q in enumerate(questions,1):
        db.session.add(CompetitionQuestion(competition_id=comp.id,order_index=idx,question_text=q['question'],
            category=f"{q['category']} · {q['sub']}",choices_json=json.dumps(q['choices'],ensure_ascii=False),correct_index=q['correct_position']))
    db.session.add(CompetitionParticipant(competition_id=comp.id,user_id=current_user.id))
    db.session.commit()
    return redirect(url_for('student.competition_room',code=comp.code))

@student_bp.post('/competition/join')
@login_required
def competition_join():
    if current_user.role!='student': abort(403)
    code=(request.form.get('code') or '').strip().upper()
    comp=Competition.query.filter_by(code=code).first()
    if not comp:
        return redirect(url_for('student.competition_home',error='ไม่พบห้องแข่งขัน'))
    if comp.status=='finished':
        return redirect(url_for('student.competition_room',code=comp.code))
    p=_participant(comp,current_user.id)
    if not p:
        if len(comp.participants)>=30:
            return redirect(url_for('student.competition_home',error='ห้องนี้เต็มแล้ว (สูงสุด 30 คน)'))
        p=CompetitionParticipant(competition_id=comp.id,user_id=current_user.id); db.session.add(p); db.session.commit()
    return redirect(url_for('student.competition_room',code=comp.code))

@student_bp.get('/competition/<code>')
@login_required
def competition_room(code):
    if current_user.role!='student': abort(403)
    comp=_get_competition(code); p=_participant(comp,current_user.id)
    if not p:
        return redirect(url_for('student.competition_home'))
    _sync_comp_status(comp)
    return render_template('student/competition_room.html',competition=comp,participant=p,is_host=(comp.host_user_id==current_user.id))

@student_bp.post('/competition/<code>/start')
@login_required
def competition_start(code):
    comp=_get_competition(code)
    if comp.host_user_id!=current_user.id:
        return jsonify({'ok':False,'error':'เฉพาะเจ้าของห้องเท่านั้นที่เริ่มการแข่งขันได้'}),403
    if comp.status!='waiting':
        return jsonify({'ok':False,'error':'การแข่งขันเริ่มหรือจบไปแล้ว'}),400
    if not _ensure_competition_questions(comp):
        return jsonify({'ok':False,'error':'คลังคำถามยังไม่พร้อม ไม่สามารถเริ่มการแข่งขันได้'}),503
    if len(comp.participants)<2:
        return jsonify({'ok':False,'error':'ต้องมีผู้เข้าแข่งขันอย่างน้อย 2 คน'}),400
    comp.status='running'; comp.started_at=datetime.datetime.utcnow(); db.session.commit()
    return jsonify({'ok':True})

@student_bp.get('/competition/<code>/state')
@login_required
def competition_state(code):
    comp=_get_competition(code); p=_participant(comp,current_user.id)
    if not p: return jsonify({'ok':False,'error':'คุณยังไม่ได้เข้าห้องนี้'}),403
    _sync_comp_status(comp)
    now=datetime.datetime.utcnow()
    if comp.status=='waiting':
        _ensure_competition_questions(comp)
    elapsed=max(0,(now-comp.started_at).total_seconds()) if comp.started_at else 0
    current_index=min(max(0,comp.total_questions-1),max(0,int(elapsed//max(comp.question_seconds,1))))
    q=comp.questions[current_index] if comp.questions and current_index < len(comp.questions) else None
    answered=bool(q and CompetitionAnswer.query.filter_by(participant_id=p.id,question_id=q.id).first())
    remaining=max(0,comp.question_seconds-(elapsed%max(comp.question_seconds,1))) if comp.status=='running' else 0
    if comp.status=='finished' or q is None:
        q_payload=None
    else:
        q_payload={'number':current_index+1,'total':comp.total_questions,'id':q.id,'category':q.category,'question':q.question_text,'choices':json.loads(q.choices_json),'answered':answered}
    participants=[]
    for x in sorted(comp.participants,key=lambda z:(-(z.score or 0),z.joined_at or datetime.datetime.min)):
        u=db.session.get(User,x.user_id)
        buddy=_competition_buddy_payload(x.user_id)
        participants.append({'name':u.name if u else 'ผู้เล่น','score':round(x.score or 0,1),'correct':x.correct_count or 0,'species':buddy['species'],'buddy':buddy,'me':x.user_id==current_user.id,'last_seen':x.last_seen.isoformat() if x.last_seen else None})
    p.last_seen=now; db.session.commit()
    if comp.status=='waiting' and q is None:
        return jsonify({'ok':False,'status':'waiting','error':'ยังโหลดคลังคำถามไม่สำเร็จ กรุณาลองใหม่อีกครั้ง','players':participants}),503
    return jsonify({'ok':True,'status':comp.status,'title':comp.title,'code':comp.code,'elapsed':elapsed,'remaining':round(remaining,1),'question':q_payload,'you':{'score':round(p.score or 0,1),'correct':p.correct_count or 0},'players':participants})

@student_bp.post('/competition/<code>/answer')
@login_required
def competition_answer(code):
    comp=_get_competition(code); p=_participant(comp,current_user.id)
    if not p: return jsonify({'ok':False,'error':'คุณยังไม่ได้เข้าห้องนี้'}),403
    _sync_comp_status(comp)
    if comp.status!='running' or not comp.started_at:
        return jsonify({'ok':False,'error':'ตอนนี้ยังไม่อยู่ในช่วงตอบคำถาม'}),400
    data=request.get_json(silent=True) or {}
    try: qid=int(data.get('question_id')); choice=int(data.get('choice_index'))
    except (TypeError,ValueError):
        return jsonify({'ok':False,'error':'ข้อมูลคำตอบไม่ถูกต้อง'}),400
    q=db.session.get(CompetitionQuestion,qid)
    if not q or q.competition_id!=comp.id:
        return jsonify({'ok':False,'error':'ไม่พบคำถามนี้'}),404
    elapsed=(datetime.datetime.utcnow()-comp.started_at).total_seconds()
    current_index=int(elapsed//comp.question_seconds)
    if current_index>=comp.total_questions or q.order_index-1!=current_index:
        return jsonify({'ok':False,'error':'หมดเวลาข้อนี้แล้ว'}),409
    if CompetitionAnswer.query.filter_by(participant_id=p.id,question_id=q.id).first():
        return jsonify({'ok':False,'error':'ข้อนี้คุณตอบไปแล้ว'}),409
    choices=json.loads(q.choices_json)
    if choice<0 or choice>=len(choices):
        return jsonify({'ok':False,'error':'ตัวเลือกไม่ถูกต้อง'}),400
    response_seconds=max(0,elapsed-(current_index*comp.question_seconds))
    correct=choice==q.correct_index
    points=round(100+max(0,comp.question_seconds-response_seconds)*4,1) if correct else 0
    ans=CompetitionAnswer(participant_id=p.id,question_id=q.id,choice_index=choice,correct=correct,points=points,response_seconds=response_seconds)
    db.session.add(ans); p.score=(p.score or 0)+points; p.correct_count=(p.correct_count or 0)+int(correct); p.last_seen=datetime.datetime.utcnow(); db.session.commit()
    return jsonify({'ok':True,'correct':correct,'points':points,'score':round(p.score,1)})

@student_bp.post('/competition/<code>/leave')
@login_required
def competition_leave(code):
    comp=_get_competition(code); p=_participant(comp,current_user.id)
    if p and comp.status=='waiting' and comp.host_user_id!=current_user.id:
        db.session.delete(p); db.session.commit()
    return redirect(url_for('student.competition_home'))

# ---------------- AVATAR WARDROBE ----------------
def _ensure_avatar(user_id):
    av=UserAvatar.query.filter_by(user_id=user_id).first()
    if not av:
        av=UserAvatar(user_id=user_id); db.session.add(av); db.session.commit()
    # The old Bear asset was a composite screenshot, so never use it as the
    # active avatar. Fall back to the clean starter model.
    if av.species == 'bear':
        av.species='fox'; db.session.commit()
    return av

def _ensure_avatar_catalog():
    """Create the curated visual item catalog without deleting old DB records."""
    ensure_avatar_item_catalog()
    return True

def _unlock_avatar_items(user_id):
    _ensure_avatar(user_id)
    _ensure_avatar_catalog()
    missions=MissionAttempt.query.filter_by(user_id=user_id).count()
    perfect=MissionAttempt.query.filter_by(user_id=user_id).filter(MissionAttempt.score>=99.99).count()
    achievements=UserAchievement.query.filter_by(user_id=user_id).count()
    values={'missions':missions,'perfect':perfect,'achievements':achievements}
    allowed_species={"fox","cat","rabbit","panda","penguin","tiger","owl","wolf","dragon","unicorn"}
    allowed_item_keys={x.asset_key for x in curated_avatar_items()}
    for item in AvatarItem.query.all():
        # Only award clean species assets and curated standalone items.
        if item.slot=='species' and item.asset_key not in allowed_species: continue
        if item.slot=='skill_item' and item.asset_key not in allowed_item_keys: continue
        if item.slot not in ('species','skill_item'): continue
        if item.unlock_type not in values: continue
        if values[item.unlock_type] >= item.unlock_value and not UserAvatarItem.query.filter_by(user_id=user_id,item_id=item.id).first():
            db.session.add(UserAvatarItem(user_id=user_id,item_id=item.id))
    db.session.commit()
    return values

@student_bp.route('/avatar',methods=['GET','POST'])
@login_required
def avatar_page():
    if current_user.role!='student': abort(403)
    av=_ensure_avatar(current_user.id); progress=_unlock_avatar_items(current_user.id)
    if request.method=='POST':
        item_id=request.form.get('item_id')
        if item_id:
            try: item_id_int=int(item_id)
            except (TypeError,ValueError): return redirect(url_for('student.avatar_page'))
            item=db.session.get(AvatarItem,item_id_int)
            allowed_keys={x.asset_key for x in curated_avatar_items()}
            owned=UserAvatarItem.query.filter_by(user_id=current_user.id,item_id=item_id_int).first() if item else None
            if not item or not owned or (item.slot=='skill_item' and item.asset_key not in allowed_keys) or item.slot not in ('species','skill_item'):
                return redirect(url_for('student.avatar_page'))
            try: equipped=json.loads(av.equipped_items or '{}')
            except Exception: equipped={}
            if item.slot=='species':
                av.species=item.asset_key
            else:
                # Cosmetic/visual loadout only. Actual Skill Perk effects remain in Skill Lab.
                items=equipped.get('skill_items',[])
                if not isinstance(items,list): items=[items] if items else []
                if item.asset_key in items: items.remove(item.asset_key)
                else:
                    if len(items)>=3: return redirect(url_for('student.avatar_page', error='ใส่ Skill Item ได้สูงสุด 3 ชิ้น'))
                    items.append(item.asset_key)
                equipped['skill_items']=items
            av.equipped_items=json.dumps(equipped, ensure_ascii=False)
            db.session.commit()
            if item.slot=='skill_item':
                sync_skill_perks_from_items(current_user.id)
            if request.headers.get('X-Requested-With')=='XMLHttpRequest' or 'application/json' in request.headers.get('Accept',''):
                return jsonify({'ok':True,'avatar':{'species':av.species,'equipped':equipped}})
        return redirect(url_for('student.avatar_page'))

    owned_ids={x.item_id for x in UserAvatarItem.query.filter_by(user_id=current_user.id).all()}
    rarity_order={'common':0,'rare':1,'epic':2,'legendary':3}
    species_rows=AvatarItem.query.filter(AvatarItem.slot=='species', AvatarItem.asset_key.in_(['fox','cat','rabbit','panda','penguin','tiger','owl','wolf','dragon','unicorn'])).order_by(AvatarItem.id).all()
    species_by_key={}
    for row in species_rows:
        species_by_key.setdefault(row.asset_key,row)
    species=sorted(species_by_key.values(), key=lambda i:(rarity_order.get(i.rarity,9), i.unlock_value, i.id))
    skill_items=sorted(curated_avatar_items(), key=lambda i:(rarity_order.get(i.rarity,9), i.unlock_value, i.id))
    current_avatar_item=next((x for x in species if x.asset_key==av.species), None)
    try: equipped_items=json.loads(av.equipped_items or '{}')
    except Exception: equipped_items={}
    equipped_skill_keys=equipped_items.get('skill_items',[]) if isinstance(equipped_items.get('skill_items',[]),list) else []
    skill_item_skill_map={i.asset_key:skill_id_for_item(i.asset_key) for i in skill_items}
    return render_template('student/avatar.html',avatar=av,items=species,skill_items=skill_items,
                           item_by_id={i.id:i for i in species+skill_items},owned_ids=owned_ids,
                           equipped_items=equipped_items,equipped_skill_keys=equipped_skill_keys,
                           skill_item_skill_map=skill_item_skill_map,progress=progress,
                           current_avatar_item=current_avatar_item)
