# V-SKILL Department & Skill System Upgrade

## Main changes
- Registration no longer asks for a department.
- New students choose a department after login.
- Students can change their department at any time.
- The active department is stored using the existing user_department relationship; historical Skill evidence is preserved.
- Discovery/Mission recommendations are filtered to the active department.
- Mission difficulty adapts per department: Level 1 -> 2 -> 3 -> 4 based on completed missions in that department.
- Completed missions are not offered again, preventing simple repeat farming.
- Added 11 practical departments and 88 unique missions (8 per department, levels 1-4):
  - เทคโนโลยีคอมพิวเตอร์
  - ไฟฟ้า
  - อิเล็กทรอนิกส์/เมคคาทรอนิกส์
  - ช่างยนต์
  - เทคนิคการผลิต
  - บริหารธุรกิจ
  - ดิจิทัล/กราฟิก
  - อาหาร/คหกรรม
  - ก่อสร้าง
  - โลจิสติกส์
  - การโรงแรมและท่องเที่ยว
- Added domain-specific Skills and Careers.
- Reworked Skill Profile to use evidence from real Mission attempts, with difficulty, recency, and hint considerations plus confidence/evidence count.
- Added server-side MissionSession for authoritative Mission timing.
- Hint usage is recorded server-side and cannot be spoofed in the submit payload.
- Mission scoring remains server-side; client-supplied points/time/hint values are not trusted.
- Simplified the student-facing Skill Lab into an evidence-based Skill Profile and removed Avatar dependency from the main Mission experience.
- Added department JSON API endpoints for future/mobile UI use.
- Fixed the old `current_user.username` template reference to `current_user.name`.
- Student navigation is now separated from Teacher/Admin navigation.

## QA performed
- Python compileall: PASS.
- Department catalog syntax/AST validation: PASS.
- Department count: 11.
- Mission count: 88.
- Mission title uniqueness: 88/88 unique.
- Full Flask integration tests could not be executed in this environment because Flask dependencies are not installed in the execution environment.

## Important runtime behavior
The existing SQLite database is preserved. `db.create_all()` creates the new `mission_session` table and the seed process adds the new department/mission catalog without deleting legacy records.

Existing users who only have an old/legacy department will be asked to choose one of the new department paths. Their previous Mission/Skill evidence is retained.

## Remaining production hardening
The existing project still contains legacy Avatar/Perk code for compatibility. It is no longer part of the primary student flow. If the Avatar system is not needed, it can be removed in a separate cleanup pass after confirming no other feature depends on it.
