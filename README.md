# V-SKILL Full Release

V-SKILL is a Flask-based AI Career & Real-World Skill Discovery platform. This package is built from the supplied V-SKILL Phase 2 project and extends it without replacing the existing architecture.

## Included

- Student / Teacher / Admin roles
- Real-world multi-step Discovery Missions
- Server-side scoring validation
- Skill scoring and evidence history
- Skill Map, Skill DNA, Top 3 Strengths
- Evidence threshold (2 missions)
- Department Fit and Career Fit
- Career Explorer and Learning Plan
- AI Tutor with Gemini/local fallback
- Achievements
- Evidence-based Portfolio
- V-SKILL-only certificate IDs
- Skill Growth history
- Job Interview practice and scoring
- REST API endpoints for skills, careers, profile, fit, DNA, report, achievements, portfolio and certificate
- Teacher mission creation/deletion
- Admin dashboard
- SQLite development / PostgreSQL production configuration
- Gunicorn / Procfile
- Seed data and tests

## Windows

```cmd
python -m venv .venv
.venv\Scripts\activate.bat
pip install -r requirements.txt
python app.py
```

Open http://127.0.0.1:5000

If PowerShell blocks Activate.ps1, use Command Prompt and `activate.bat` as shown above.

## Demo accounts

- Student: student@example.com / Student123!
- Teacher: teacher@example.com / Teacher123!
- Admin: admin@example.com / Admin123!

Change demo passwords before production use.

## Gemini

Set `GEMINI_API_KEY` in `.env` to enable Gemini. The tutor falls back to local rules when Gemini is unavailable.

## Important

This release is substantially expanded from the supplied Phase 2 code. Python syntax was compiled successfully for all Python files in the build environment. The build environment used for packaging did not contain Flask/SQLAlchemy, so a full runtime/pytest execution could not be honestly claimed here. Run `pip install -r requirements.txt` and `pytest` in your local environment before treating the release as production-certified.

No claim of 100% production certification is made until the full acceptance flow is executed on the target environment.


## Competition UI / Quiz Upgrade

This release adds:
- Game-like animated UI with ambient motion, floating illustrations, reveal animations and pointer tilt.
- Local SVG illustrations for the hero, discovery, quiz and career sections.
- `Quiz Arena`: 60-question competency bank (15 categories x 4 variants), 10 questions sampled per run.
- Answer choices are shuffled per session; a new run generates a different combination.
- Mission answer choices are also shuffled on each visit while scoring remains server-side by choice ID.
- Mission completion celebration animation and smoother step transitions.
- Responsive/mobile presentation and reduced-motion accessibility support.

### Quiz Arena
After login, open **Quiz Arena** from the navigation or `/student/quiz`.
Each run samples 10 questions from the larger bank and stores only a small signed session state (question IDs + seed), avoiding oversized browser sessions.
