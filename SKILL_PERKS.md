# V-SKILL Skill Perks System

## Architecture
`SkillPerk` and `UserSkillPerk` are independent from `AvatarItem`. Avatar/Cosmetic remains visual identity; Skill Lab remains ability/progression.

### Post-activity rule
Mission:
1. Validate and score the Mission server-side.
2. Persist `MissionAttempt` and decisions.
3. Rebuild evidence-based Skill Profile.
4. Apply Skill Perk reward modifiers.
5. Update XP / Progress / Combo / Mission Streak.
6. Check Achievement.
7. Apply Achievement Magnet only when a new Achievement is actually earned.
8. Return reward animation data.

Quiz:
- No Skill Perk integration.
- No Skill Perk script is loaded on `/student/quiz`.
- Skill Perks cannot change questions, choices, difficulty, hints, score, or assessment result.

## Skill Lab
Route: `/student/skills`

12 independent perks:
- XP Spark
- Combo Core
- Skill Accelerator
- Explorer Compass
- Mission Hunter
- Rare Hunter
- Lucky Finder
- Skill Analyzer
- Career Compass
- V-Buddy Coach
- Achievement Magnet

Equip limit: 3.

## Database
New upgrade-safe tables:
- `skill_perk`
- `user_skill_perk`
- `user_progress`
- `skill_reward_log`

Existing tables are preserved. `db.create_all()` creates the new tables on an existing SQLite database without dropping legacy data.

## Animated Avatar
Real looping GIF assets are stored under:
`static/img/avatar_gifs/`

For each supported species there are real GIF files for:
`idle`, `happy`, `excited`, `level_up`, `achievement`, `click`

The web UI loads the selected GIF first and falls back to the existing PNG asset if the GIF cannot load.

Cosmetics remain separate from Skill Perks. Current Avatar Studio uses the animated GIF as the base character and existing transparent cosmetic assets as overlays. A future layered-frame compositor can be added without changing the Skill architecture.

## Validation performed
- Python `compileall`: passed.
- JavaScript syntax checks for Skill Lab, Mission, and Avatar scripts: passed.
- Full Flask runtime/pytest was not executed in this build environment because Flask is not installed there. Run `pip install -r requirements.txt` and `pytest` locally.
