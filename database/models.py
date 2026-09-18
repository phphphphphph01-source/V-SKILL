from datetime import datetime
from flask_login import UserMixin
from werkzeug.security import generate_password_hash, check_password_hash
from database.database import db

user_department = db.Table(
    "user_department",
    db.Column("user_id", db.Integer, db.ForeignKey("user.id"), primary_key=True),
    db.Column("department_id", db.Integer, db.ForeignKey("department.id"), primary_key=True),
)
mission_skill = db.Table(
    "mission_skill",
    db.Column("mission_id", db.Integer, db.ForeignKey("mission.id"), primary_key=True),
    db.Column("skill_id", db.Integer, db.ForeignKey("skill.id"), primary_key=True),
)
career_skill = db.Table(
    "career_skill",
    db.Column("career_id", db.Integer, db.ForeignKey("career.id"), primary_key=True),
    db.Column("skill_id", db.Integer, db.ForeignKey("skill.id"), primary_key=True),
)

class User(UserMixin, db.Model):
    id=db.Column(db.Integer, primary_key=True)
    name=db.Column(db.String(120), nullable=False)
    email=db.Column(db.String(255), unique=True, nullable=False, index=True)
    password_hash=db.Column(db.String(255), nullable=False)
    role=db.Column(db.String(20), nullable=False, default="student")
    created_at=db.Column(db.DateTime, default=datetime.utcnow)
    departments=db.relationship("Department", secondary=user_department, back_populates="users")
    attempts=db.relationship("MissionAttempt", back_populates="user", cascade="all, delete-orphan")
    achievements=db.relationship("UserAchievement", back_populates="user", cascade="all, delete-orphan")
    def set_password(self,p): self.password_hash=generate_password_hash(p)
    def check_password(self,p): return check_password_hash(self.password_hash,p)

class Department(db.Model):
    id=db.Column(db.Integer, primary_key=True)
    name=db.Column(db.String(120), unique=True, nullable=False)
    description=db.Column(db.Text, default="")
    users=db.relationship("User", secondary=user_department, back_populates="departments")
    missions=db.relationship("Mission", back_populates="department")
    careers=db.relationship("Career", back_populates="department")

class Skill(db.Model):
    id=db.Column(db.Integer, primary_key=True)
    name=db.Column(db.String(120), unique=True, nullable=False)
    description=db.Column(db.Text, default="")
    mission_weight=db.Column(db.Float, default=1.0)
    missions=db.relationship("Mission", secondary=mission_skill, back_populates="skills")
    careers=db.relationship("Career", secondary=career_skill, back_populates="skills")

class Mission(db.Model):
    id=db.Column(db.Integer, primary_key=True)
    title=db.Column(db.String(180), nullable=False)
    scenario=db.Column(db.Text, nullable=False)
    difficulty=db.Column(db.Integer, default=1)
    time_limit=db.Column(db.Integer, default=300)
    budget=db.Column(db.Float, default=0)
    discovery=db.Column(db.Boolean, default=False)
    department_id=db.Column(db.Integer, db.ForeignKey("department.id"))
    department=db.relationship("Department", back_populates="missions")
    skills=db.relationship("Skill", secondary=mission_skill, back_populates="missions")
    steps=db.relationship("MissionStep", back_populates="mission", cascade="all, delete-orphan", order_by="MissionStep.order_index")
    attempts=db.relationship("MissionAttempt", back_populates="mission")

class MissionStep(db.Model):
    id=db.Column(db.Integer, primary_key=True)
    mission_id=db.Column(db.Integer, db.ForeignKey("mission.id"), nullable=False)
    # Explicit question-bank metadata. Keeping these fields on the step makes
    # department ownership and validation inspectable without relying only on
    # the parent Mission row. JSON fields are stored as TEXT for SQLite/Postgres portability.
    question_id=db.Column(db.String(80), index=True)
    department_id=db.Column(db.Integer, index=True)
    department_name=db.Column(db.String(120))
    category=db.Column(db.String(160))
    sub_category=db.Column(db.String(160))
    difficulty=db.Column(db.String(20))
    question_type=db.Column(db.String(60))
    scenario=db.Column(db.Text)
    source_topic=db.Column(db.String(180))
    uniqueness_key=db.Column(db.String(255), index=True)
    skills_json=db.Column(db.Text)
    skill_weights_json=db.Column(db.Text)
    order_index=db.Column(db.Integer, nullable=False)
    prompt=db.Column(db.Text, nullable=False)
    hint1=db.Column(db.Text, default="")
    hint2=db.Column(db.Text, default="")
    hint3=db.Column(db.Text, default="")
    mission=db.relationship("Mission", back_populates="steps")
    choices=db.relationship("MissionChoice", back_populates="step", cascade="all, delete-orphan", order_by="MissionChoice.id")

class MissionChoice(db.Model):
    id=db.Column(db.Integer, primary_key=True)
    step_id=db.Column(db.Integer, db.ForeignKey("mission_step.id"), nullable=False)
    text=db.Column(db.Text, nullable=False)
    points=db.Column(db.Float, default=0)
    consequence=db.Column(db.Text, default="")
    is_correct=db.Column(db.Boolean, default=False)
    step=db.relationship("MissionStep", back_populates="choices")

class MissionSession(db.Model):
    """Server-side active Mission session. Prevents client-controlled timer/hints."""
    id=db.Column(db.Integer, primary_key=True)
    user_id=db.Column(db.Integer, db.ForeignKey("user.id"), nullable=False, index=True)
    mission_id=db.Column(db.Integer, db.ForeignKey("mission.id"), nullable=False, index=True)
    started_at=db.Column(db.DateTime, default=datetime.utcnow, nullable=False)
    expires_at=db.Column(db.DateTime, nullable=False)
    completed_at=db.Column(db.DateTime)
    hints_used=db.Column(db.Integer, default=0, nullable=False)
    __table_args__=(db.Index("ix_mission_session_active","user_id","mission_id","completed_at"),)

class MissionAttempt(db.Model):
    id=db.Column(db.Integer, primary_key=True)
    user_id=db.Column(db.Integer, db.ForeignKey("user.id"), nullable=False)
    mission_id=db.Column(db.Integer, db.ForeignKey("mission.id"), nullable=False)
    started_at=db.Column(db.DateTime, default=datetime.utcnow)
    completed_at=db.Column(db.DateTime)
    score=db.Column(db.Float, default=0)
    accuracy=db.Column(db.Float, default=0)
    time_used=db.Column(db.Float, default=0)
    hints_used=db.Column(db.Integer, default=0)
    user=db.relationship("User", back_populates="attempts")
    mission=db.relationship("Mission", back_populates="attempts")
    decisions=db.relationship("AttemptDecision", back_populates="attempt", cascade="all, delete-orphan")

class AttemptDecision(db.Model):
    id=db.Column(db.Integer, primary_key=True)
    attempt_id=db.Column(db.Integer, db.ForeignKey("mission_attempt.id"), nullable=False)
    step_id=db.Column(db.Integer, nullable=False)
    choice_id=db.Column(db.Integer, nullable=False)
    points=db.Column(db.Float, default=0)
    hint_level=db.Column(db.Integer, default=0)
    attempt=db.relationship("MissionAttempt", back_populates="decisions")

class SkillScore(db.Model):
    id=db.Column(db.Integer, primary_key=True)
    user_id=db.Column(db.Integer, db.ForeignKey("user.id"), nullable=False)
    skill_id=db.Column(db.Integer, db.ForeignKey("skill.id"), nullable=False)
    score=db.Column(db.Float, default=0)
    evidence_count=db.Column(db.Integer, default=0)
    updated_at=db.Column(db.DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)
    __table_args__=(db.UniqueConstraint("user_id","skill_id"),)

class SkillHistory(db.Model):
    id=db.Column(db.Integer, primary_key=True)
    user_id=db.Column(db.Integer, nullable=False)
    skill_id=db.Column(db.Integer, nullable=False)
    score=db.Column(db.Float, nullable=False)
    source_attempt_id=db.Column(db.Integer, nullable=False)
    created_at=db.Column(db.DateTime, default=datetime.utcnow)

class InterestFeedback(db.Model):
    id=db.Column(db.Integer, primary_key=True)
    user_id=db.Column(db.Integer, nullable=False)
    mission_id=db.Column(db.Integer, nullable=False)
    enjoyment=db.Column(db.Integer, nullable=False)
    repeat_interest=db.Column(db.Boolean, nullable=False)

class Career(db.Model):
    id=db.Column(db.Integer, primary_key=True)
    name=db.Column(db.String(160), unique=True, nullable=False)
    description=db.Column(db.Text, default="")
    department_id=db.Column(db.Integer, db.ForeignKey("department.id"))
    department=db.relationship("Department", back_populates="careers")
    skills=db.relationship("Skill", secondary=career_skill, back_populates="careers")

class Achievement(db.Model):
    id=db.Column(db.Integer, primary_key=True)
    name=db.Column(db.String(120), unique=True, nullable=False)
    description=db.Column(db.Text, default="")
    threshold=db.Column(db.Integer, default=1)
class UserAchievement(db.Model):
    id=db.Column(db.Integer, primary_key=True)
    user_id=db.Column(db.Integer, db.ForeignKey("user.id"), nullable=False)
    achievement_id=db.Column(db.Integer, db.ForeignKey("achievement.id"), nullable=False)
    created_at=db.Column(db.DateTime, default=datetime.utcnow)
    user=db.relationship("User", back_populates="achievements")
    achievement=db.relationship("Achievement")

class LearningTopic(db.Model):
    id=db.Column(db.Integer, primary_key=True)
    title=db.Column(db.String(180), nullable=False)
    skill_id=db.Column(db.Integer, db.ForeignKey("skill.id"), nullable=False)
    level=db.Column(db.Integer, default=1)
    description=db.Column(db.Text, default="")
class LearningPlan(db.Model):
    id=db.Column(db.Integer, primary_key=True)
    user_id=db.Column(db.Integer, nullable=False)
    created_at=db.Column(db.DateTime, default=datetime.utcnow)
    items=db.relationship("LearningPlanItem", back_populates="plan", cascade="all, delete-orphan")
class LearningPlanItem(db.Model):
    id=db.Column(db.Integer, primary_key=True)
    plan_id=db.Column(db.Integer, db.ForeignKey("learning_plan.id"), nullable=False)
    day=db.Column(db.Integer, nullable=False)
    topic_id=db.Column(db.Integer, db.ForeignKey("learning_topic.id"), nullable=False)
    completed=db.Column(db.Boolean, default=False)
    plan=db.relationship("LearningPlan", back_populates="items")
    topic=db.relationship("LearningTopic")

class Portfolio(db.Model):
    id=db.Column(db.Integer, primary_key=True)
    user_id=db.Column(db.Integer, unique=True, nullable=False)
    summary=db.Column(db.Text, default="")
class Certificate(db.Model):
    id=db.Column(db.Integer, primary_key=True)
    user_id=db.Column(db.Integer, nullable=False)
    skill_id=db.Column(db.Integer, nullable=False)
    certificate_id=db.Column(db.String(80), unique=True, nullable=False)
    score=db.Column(db.Float, nullable=False)
    issued_at=db.Column(db.DateTime, default=datetime.utcnow)
class Notification(db.Model):
    id=db.Column(db.Integer, primary_key=True)
    user_id=db.Column(db.Integer, nullable=False)
    title=db.Column(db.String(180), nullable=False)
    message=db.Column(db.Text, nullable=False)
    read=db.Column(db.Boolean, default=False)
    created_at=db.Column(db.DateTime, default=datetime.utcnow)


# Full-release extension tables (kept separate so existing SQLite databases can upgrade safely)
class DiscoverySession(db.Model):
    id=db.Column(db.Integer, primary_key=True)
    user_id=db.Column(db.Integer, nullable=False)
    status=db.Column(db.String(20), default="active")
    created_at=db.Column(db.DateTime, default=datetime.utcnow)
    completed_at=db.Column(db.DateTime)

class DiscoveryResult(db.Model):
    id=db.Column(db.Integer, primary_key=True)
    session_id=db.Column(db.Integer, nullable=False)
    user_id=db.Column(db.Integer, nullable=False)
    summary=db.Column(db.Text, default="")
    created_at=db.Column(db.DateTime, default=datetime.utcnow)

class SkillDNA(db.Model):
    id=db.Column(db.Integer, primary_key=True)
    user_id=db.Column(db.Integer, nullable=False)
    dna_json=db.Column(db.Text, nullable=False)
    evidence_count=db.Column(db.Integer, default=0)
    updated_at=db.Column(db.DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)
    __table_args__=(db.UniqueConstraint("user_id"),)

class CareerFit(db.Model):
    id=db.Column(db.Integer, primary_key=True)
    user_id=db.Column(db.Integer, nullable=False)
    career_id=db.Column(db.Integer, nullable=False)
    fit=db.Column(db.Float, default=0)
    evidence_count=db.Column(db.Integer, default=0)
    updated_at=db.Column(db.DateTime, default=datetime.utcnow)

class Team(db.Model):
    id=db.Column(db.Integer, primary_key=True)
    name=db.Column(db.String(160), nullable=False)
    owner_id=db.Column(db.Integer, nullable=False)
    created_at=db.Column(db.DateTime, default=datetime.utcnow)
class TeamMember(db.Model):
    id=db.Column(db.Integer, primary_key=True)
    team_id=db.Column(db.Integer, nullable=False)
    user_id=db.Column(db.Integer, nullable=False)
    role=db.Column(db.String(80), default="member")
class TeamMission(db.Model):
    id=db.Column(db.Integer, primary_key=True)
    team_id=db.Column(db.Integer, nullable=False)
    mission_id=db.Column(db.Integer, nullable=False)
    status=db.Column(db.String(30), default="assigned")

class Interview(db.Model):
    id=db.Column(db.Integer, primary_key=True)
    user_id=db.Column(db.Integer, nullable=False)
    career_id=db.Column(db.Integer)
    created_at=db.Column(db.DateTime, default=datetime.utcnow)
class InterviewResult(db.Model):
    id=db.Column(db.Integer, primary_key=True)
    interview_id=db.Column(db.Integer, nullable=False)
    question=db.Column(db.Text, nullable=False)
    answer=db.Column(db.Text, default="")
    score=db.Column(db.Float, default=0)
    feedback=db.Column(db.Text, default="")

class PortfolioProject(db.Model):
    id=db.Column(db.Integer, primary_key=True)
    portfolio_id=db.Column(db.Integer, nullable=False)
    title=db.Column(db.String(180), nullable=False)
    evidence=db.Column(db.Text, default="")
    skills=db.Column(db.Text, default="")



# ---------------- V-SKILL SKILL PERKS ----------------
class SkillPerk(db.Model):
    __tablename__ = "skill_perk"
    id=db.Column(db.Integer, primary_key=True)
    skill_id=db.Column(db.String(80), unique=True, nullable=False, index=True)
    skill_name=db.Column(db.String(120), nullable=False)
    category=db.Column(db.String(40), nullable=False)
    rarity=db.Column(db.String(20), nullable=False, default="COMMON")
    icon=db.Column(db.String(20), default="✨")
    description=db.Column(db.Text, default="")
    effect_type=db.Column(db.String(50), nullable=False)
    effect_value=db.Column(db.Float, default=0)
    unlock_requirement=db.Column(db.String(255), default="")
    active=db.Column(db.Boolean, default=True)
    created_at=db.Column(db.DateTime, default=datetime.utcnow)

class UserSkillPerk(db.Model):
    __tablename__ = "user_skill_perk"
    id=db.Column(db.Integer, primary_key=True)
    user_id=db.Column(db.Integer, db.ForeignKey("user.id"), nullable=False)
    skill_id=db.Column(db.String(80), db.ForeignKey("skill_perk.skill_id"), nullable=False)
    equipped=db.Column(db.Boolean, default=False)
    unlocked_at=db.Column(db.DateTime, default=datetime.utcnow)
    __table_args__=(db.UniqueConstraint("user_id","skill_id"),)

class UserProgress(db.Model):
    __tablename__ = "user_progress"
    id=db.Column(db.Integer, primary_key=True)
    user_id=db.Column(db.Integer, db.ForeignKey("user.id"), unique=True, nullable=False)
    xp=db.Column(db.Integer, default=0)
    coins=db.Column(db.Integer, default=0)
    progress_points=db.Column(db.Float, default=0)
    combo=db.Column(db.Integer, default=0)
    mission_streak=db.Column(db.Integer, default=0)
    last_activity_at=db.Column(db.DateTime)
    last_activity_day=db.Column(db.Date)
    updated_at=db.Column(db.DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)

class SkillRewardLog(db.Model):
    __tablename__ = "skill_reward_log"
    id=db.Column(db.Integer, primary_key=True)
    user_id=db.Column(db.Integer, db.ForeignKey("user.id"), nullable=False)
    activity_type=db.Column(db.String(40), nullable=False, default="mission")
    activity_id=db.Column(db.Integer)
    base_xp=db.Column(db.Float, default=0)
    final_xp=db.Column(db.Float, default=0)
    base_progress=db.Column(db.Float, default=0)
    final_progress=db.Column(db.Float, default=0)
    coins=db.Column(db.Integer, default=0)
    bonus_json=db.Column(db.Text, default="{}")
    created_at=db.Column(db.DateTime, default=datetime.utcnow)

# V-SKILL Arena + Avatar system
class AvatarItem(db.Model):
    id=db.Column(db.Integer, primary_key=True)
    name=db.Column(db.String(120), nullable=False, unique=True)
    description=db.Column(db.Text, default='')
    slot=db.Column(db.String(30), nullable=False, default='accessory')
    asset_key=db.Column(db.String(80), nullable=False, default='spark')
    rarity=db.Column(db.String(30), default='common')
    unlock_type=db.Column(db.String(30), default='missions')
    unlock_value=db.Column(db.Integer, default=1)

class UserAvatar(db.Model):
    id=db.Column(db.Integer, primary_key=True)
    user_id=db.Column(db.Integer, unique=True, nullable=False)
    species=db.Column(db.String(40), default='fox')
    body_color=db.Column(db.String(30), default='violet')
    equipped_hat=db.Column(db.Integer, nullable=True)
    equipped_accessory=db.Column(db.Integer, nullable=True)
    equipped_badge=db.Column(db.Integer, nullable=True)
    equipped_items=db.Column(db.Text, default='{}')
    updated_at=db.Column(db.DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)

class UserAvatarItem(db.Model):
    id=db.Column(db.Integer, primary_key=True)
    user_id=db.Column(db.Integer, nullable=False)
    item_id=db.Column(db.Integer, nullable=False)
    unlocked_at=db.Column(db.DateTime, default=datetime.utcnow)
    __table_args__=(db.UniqueConstraint('user_id','item_id'),)

class Competition(db.Model):
    id=db.Column(db.Integer, primary_key=True)
    code=db.Column(db.String(12), unique=True, nullable=False, index=True)
    title=db.Column(db.String(180), nullable=False)
    host_user_id=db.Column(db.Integer, nullable=False)
    status=db.Column(db.String(20), default='waiting')
    question_seconds=db.Column(db.Integer, default=15)
    total_questions=db.Column(db.Integer, default=8)
    started_at=db.Column(db.DateTime)
    finished_at=db.Column(db.DateTime)
    created_at=db.Column(db.DateTime, default=datetime.utcnow)
    questions=db.relationship('CompetitionQuestion', back_populates='competition', cascade='all, delete-orphan', order_by='CompetitionQuestion.order_index')
    participants=db.relationship('CompetitionParticipant', back_populates='competition', cascade='all, delete-orphan')

class CompetitionQuestion(db.Model):
    id=db.Column(db.Integer, primary_key=True)
    competition_id=db.Column(db.Integer, db.ForeignKey('competition.id'), nullable=False)
    order_index=db.Column(db.Integer, nullable=False)
    question_text=db.Column(db.Text, nullable=False)
    category=db.Column(db.String(100), default='ทักษะทั่วไป')
    choices_json=db.Column(db.Text, nullable=False)
    correct_index=db.Column(db.Integer, nullable=False)
    competition=db.relationship('Competition', back_populates='questions')
    answers=db.relationship('CompetitionAnswer', back_populates='question', cascade='all, delete-orphan')

class CompetitionParticipant(db.Model):
    id=db.Column(db.Integer, primary_key=True)
    competition_id=db.Column(db.Integer, db.ForeignKey('competition.id'), nullable=False)
    user_id=db.Column(db.Integer, nullable=False)
    score=db.Column(db.Float, default=0)
    correct_count=db.Column(db.Integer, default=0)
    joined_at=db.Column(db.DateTime, default=datetime.utcnow)
    last_seen=db.Column(db.DateTime, default=datetime.utcnow)
    competition=db.relationship('Competition', back_populates='participants')
    answers=db.relationship('CompetitionAnswer', back_populates='participant', cascade='all, delete-orphan')
    __table_args__=(db.UniqueConstraint('competition_id','user_id'),)

class CompetitionAnswer(db.Model):
    id=db.Column(db.Integer, primary_key=True)
    participant_id=db.Column(db.Integer, db.ForeignKey('competition_participant.id'), nullable=False)
    question_id=db.Column(db.Integer, db.ForeignKey('competition_question.id'), nullable=False)
    choice_index=db.Column(db.Integer, nullable=False)
    correct=db.Column(db.Boolean, default=False)
    points=db.Column(db.Float, default=0)
    answered_at=db.Column(db.DateTime, default=datetime.utcnow)
    response_seconds=db.Column(db.Float, default=0)
    participant=db.relationship('CompetitionParticipant', back_populates='answers')
    question=db.relationship('CompetitionQuestion', back_populates='answers')
    __table_args__=(db.UniqueConstraint('participant_id','question_id'),)
