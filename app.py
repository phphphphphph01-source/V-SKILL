import os
from flask import Flask, render_template
from config import Config
from database.database import db
from auth.routes import auth_bp
from routes.main import main_bp
from routes.student import student_bp
from routes.teacher import teacher_bp
from routes.admin import admin_bp
from routes.api import api_bp
from database.seed import seed_database
from sqlalchemy import text

def migrate_question_bank_schema():
    """Add Question Bank metadata columns to older SQLite deployments safely."""
    columns = {
        "question_id": "VARCHAR(80)",
        "department_id": "INTEGER",
        "department_name": "VARCHAR(120)",
        "category": "VARCHAR(160)",
        "sub_category": "VARCHAR(160)",
        "difficulty": "VARCHAR(20)",
        "question_type": "VARCHAR(60)",
        "scenario": "TEXT",
        "source_topic": "VARCHAR(180)",
        "uniqueness_key": "VARCHAR(255)",
        "skills_json": "TEXT",
        "skill_weights_json": "TEXT",
    }
    try:
        existing={row[1] for row in db.session.execute(text("PRAGMA table_info(mission_step)"))}
        for name,sql_type in columns.items():
            if name not in existing:
                db.session.execute(text(f"ALTER TABLE mission_step ADD COLUMN {name} {sql_type}"))
        db.session.commit()
    except Exception:
        db.session.rollback()

def migrate_avatar_schema():
    """Lightweight SQLite-safe migration for the 2D Avatar Studio equipment state."""
    try:
        cols = {row[1] for row in db.session.execute(text("PRAGMA table_info(user_avatar)"))}
        if "equipped_items" not in cols:
            db.session.execute(text("ALTER TABLE user_avatar ADD COLUMN equipped_items TEXT DEFAULT '{}'"))
            db.session.commit()
    except Exception:
        db.session.rollback()

def create_app():
    app = Flask(__name__)
    app.config.from_object(Config)
    db.init_app(app)

    from flask_login import LoginManager
    login_manager = LoginManager()
    login_manager.login_view = "auth.login"
    login_manager.init_app(app)

    from database.models import User
    @login_manager.user_loader
    def load_user(user_id):
        return db.session.get(User, int(user_id))

    app.register_blueprint(auth_bp)
    app.register_blueprint(main_bp)
    app.register_blueprint(student_bp, url_prefix="/student")
    app.register_blueprint(teacher_bp, url_prefix="/teacher")
    app.register_blueprint(admin_bp, url_prefix="/admin")
    app.register_blueprint(api_bp, url_prefix="/api")

    @app.context_processor
    def inject_app():
        return {"app_name": "V-SKILL"}

    with app.app_context():
        db.create_all()
        migrate_avatar_schema()
        migrate_question_bank_schema()
        seed_database()

    return app

app = create_app()

if __name__ == "__main__":
    app.run(host="0.0.0.0", port=int(os.getenv("PORT", 5000)), debug=True)
