# V-SKILL Audit Report — Companion Skill / Avatar UI Fix

Date: 2026-09-14
Base: `vvv(8).zip`

## Scope

This revision keeps the existing V-SKILL architecture and data model intact while fixing the Avatar Studio companion catalog failure and moving companion Skill details into the animal cards.

## 1. Bugs Found

| Severity | Bug | File | Cause | Fix |
|---|---|---|---|---|
| 🔴 Critical | `/student/avatar` returned HTTP 500 with `UNIQUE constraint failed: avatar_item.name` | `core/avatar_items.py` | Legacy/new catalog synchronization could assign a display name while another `AvatarItem` row already owned that unique name; pending ORM rows made the previous conflict check unreliable | Reworked `ensure_catalog()` into an idempotent reconciliation flow: consolidate duplicate species rows, transfer ownership, free conflicting legacy names first, create missing rows with temporary unique names, then assign canonical names |
| 🟠 High | Multiple animals reused the same Skill ID | `core/avatar_items.py`, `core/skill_perks.py` | Several animals pointed to the same generic perk (`skill_analyzer`, `explorer_compass`, etc.) | Added 20 unique companion Skill IDs and 20 corresponding Skill definitions |
| 🟠 High | Companion Skill identity was mixed with the standalone Skill Lab UI | `templates/base.html`, `templates/student/dashboard.html`, `templates/student/avatar.html`, `static/js/mission.js` | The UI exposed a separate Skill Lab even though the selected animal is now the Skill identity | Removed Skill Lab from student-facing navigation/dashboard actions; retained the old route for backward compatibility |
| 🟡 Medium | Animal portraits looked visually cramped/touching in the collection grid | `static/css/avatar2d.css` | Small grid gap and nearly edge-to-edge image sizing | Increased grid gap, image container padding, and portrait breathing room without changing source artwork |
| 🟡 Medium | Variety bonus did not actually enforce a 7-day window | `core/skill_perks.py` | Query used `LIMIT 12` instead of a date cutoff | Changed to `completed_at >= now - 7 days` |
| 🟡 Medium | Navbar referenced `current_user.username` although User uses `name` | `templates/base.html` | Template/model naming mismatch | Changed student navbar references to `current_user.name` |

## 2. Security / Integrity Changes in This Revision

- Avatar selection continues to require ownership of the selected `AvatarItem`.
- Only `slot='species'` and allow-listed animal keys can be selected.
- Companion Skills remain post-activity/progression abilities; they do not modify Mission questions, choices, correctness, or stored assessment score.
- The unique catalog synchronization avoids destructive database reset and preserves ownership when duplicate species rows are consolidated.

## 3. Database Changes

No destructive schema migration was introduced.

The existing `SkillPerk` and `UserSkillPerk` tables are reused. Missing unique companion Skill rows are created through the existing catalog initialization path.

Existing legacy `AvatarItem` records remain supported. Duplicate species records are consolidated safely and ownership is moved to the canonical species row before deletion.

## 4. Feature Improvements

### Companion Skills

- 20 animals now map to 20 unique Skill IDs.
- Skill tiers follow:
  - Common = Tier 1
  - Rare = Tier 2
  - Epic = Tier 3
  - Legendary = Tier 4
- Higher rarity receives stronger progression/reward-oriented effects.
- Skill details are shown directly from the animal card via a modal.
- The modal shows animal, Skill name, description, what it does, category, unlock requirement, and power tier.

### Avatar Collection UI

- More space between cards.
- More internal portrait padding.
- Existing supplied animal artwork is preserved; no new animal faces were generated.
- Skill Lab is no longer presented as a required separate destination.

## 5. Tests / Verification

### Passed in the available static verification environment

- Python syntax compilation for modified Python modules.
- Jinja2 template compilation for:
  - `templates/base.html`
  - `templates/student/dashboard.html`
  - `templates/student/avatar.html`
- JavaScript syntax check with Node for:
  - `static/js/avatar2d.js`
  - `static/js/mission.js`
- Verified 20 animal keys.
- Verified 20 unique animal Skill IDs.
- Verified all 20 animal image assets exist.
- Verified the student dashboard/avatar templates no longer expose `/student/skills` or `SKILL LAB` as visible UI.

### Not run here

Full Flask integration tests could not be executed in this isolated environment because Flask is not installed and external package installation is unavailable. The project already contains `tests/test_app.py`; additional regression tests were added for avatar catalog idempotency, unique companion Skills/assets, and removal of Skill Lab from student navigation. Run the normal project test command in the user's `.venv` to execute them.

## 6. Remaining Issues

- The full production security hardening requested in the broader V-SKILL specification (server-authoritative Mission timer/hint persistence, global CSRF enforcement, environment-only production secrets, rate limiting, and complete competition anti-cheat coverage) was not rewritten as part of this focused Avatar/Companion revision.
- Full browser-level responsive/console QA still needs to be run in the user's local browser after replacing the project files.

## Changed Files

1. `core/avatar_items.py`
2. `core/skill_perks.py`
3. `routes/student.py`
4. `templates/base.html`
5. `templates/student/dashboard.html`
6. `templates/student/avatar.html`
7. `static/css/avatar2d.css`
8. `static/js/avatar2d.js`
9. `static/js/mission.js`
10. `tests/test_app.py`
11. `AUDIT_REPORT.md`
