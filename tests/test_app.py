import os, tempfile, pytest

from app import create_app
from database.database import db
from database.models import Mission, MissionAttempt, SkillScore, SkillHistory, User

@pytest.fixture
def client():
    fd,path=tempfile.mkstemp(suffix=".db"); os.close(fd)
    app=create_app()
    app.config.update(TESTING=True,SQLALCHEMY_DATABASE_URI="sqlite:///"+path,SECRET_KEY="test")
    with app.app_context():
        db.drop_all(); db.create_all()
        from database.seed import seed_database
        seed_database()
        yield app.test_client()
        db.session.remove()
    os.unlink(path)

def login(client,email="student@example.com",password="Student123!"):
    return client.post("/login",data={"email":email,"password":password},follow_redirects=False)

def test_register_login(client):
    r=client.post("/register",data={"name":"A","email":"a@test.com","password":"password123"},follow_redirects=True)
    assert r.status_code==200
    assert client.get("/logout").status_code==302
    assert client.post("/login",data={"email":"a@test.com","password":"password123"}).status_code==302

def test_seed_has_phase2_core_data(client):
    with client.application.app_context():
        from database.models import Department, Skill, Career, LearningTopic
        assert Department.query.count() >= 8
        assert Skill.query.count() >= 10
        assert Mission.query.count() >= 20
        assert Career.query.count() >= 10
        assert LearningTopic.query.count() >= 20
        assert Mission.query.filter(Mission.steps.any()).count() >= 20

def test_discovery_requires_login(client):
    assert client.get("/student/discovery").status_code==302

def test_api_skills(client):
    r=client.get("/api/skills")
    assert r.status_code==200 and len(r.json)>=10

def test_student_flow(client):
    assert login(client).status_code==302
    r=client.get("/student/discovery")
    assert r.status_code==200

def test_server_does_not_trust_client_points(client):
    login(client)
    with client.application.app_context():
        m=Mission.query.filter(Mission.steps.any()).first()
        step=m.steps[0]
        choice=step.choices[0]
        payload={"elapsed":10,"decisions":[{"step_id":step.id,"choice_id":choice.id,"points":999999}]}
    r=client.post(f"/student/mission/{m.id}/submit",json=payload)
    # Multi-step missions require all steps; this must not accept forged/incomplete scoring.
    assert r.status_code==400

def test_real_mission_submission_creates_evidence(client):
    login(client)
    with client.application.app_context():
        m=Mission.query.filter(Mission.steps.any()).first()
        payload={"elapsed":10,"decisions":[
            {"step_id":s.id,"choice_id":s.choices[0].id,"points":0,"hint_level":0}
            for s in m.steps
        ]}
    r=client.post(f"/student/mission/{m.id}/submit",json=payload)
    assert r.status_code==200 and r.json["ok"] is True
    with client.application.app_context():
        assert MissionAttempt.query.count()==1
        assert SkillScore.query.count()>0
        assert SkillHistory.query.count()>0

def test_duplicate_history_is_not_created_by_profile_refresh(client):
    login(client)
    with client.application.app_context():
        m=Mission.query.filter(Mission.steps.any()).first()
        payload={"elapsed":10,"decisions":[{"step_id":s.id,"choice_id":s.choices[0].id,"hint_level":0} for s in m.steps]}
    assert client.post(f"/student/mission/{m.id}/submit",json=payload).status_code==200
    with client.application.app_context():
        before=SkillHistory.query.count()
        client.get("/student/")
        client.get("/student/")
        after=SkillHistory.query.count()
        assert after==before
