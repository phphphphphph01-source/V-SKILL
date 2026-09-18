# V-SKILL Question Bank Validation

## Final status

**PASS**

- Active vocational departments: **11**
- Discovery missions per active department: **8**
- Questions per mission: **10 exactly**
- Total active questions: **880**
- Incomplete active missions: **0**
- Duplicate question IDs: **0**
- Duplicate uniqueness keys: **0**
- Duplicate questions: **0**
- Cross-department exact choice duplicates: **0**
- Cross-department semantic token similarity gate: **PASS** (maximum observed 0.545, threshold 0.75)
- Schema metadata coverage: **100%**
- Exactly one correct choice per question: **PASS**
- Four unique choices per question: **PASS**
- Skill mapping: **1–3 skills/question**
- Skill weights: **sum = 1.0**

## Department isolation

The active student catalog is restricted to the new vocational departments. Legacy English-named missions remain only as historical database data and are marked `discovery=0` when their assessment is incomplete, so they cannot be recommended to students.

The Mission route also contains a runtime guard: if an old deployed database presents a selected-department mission with fewer than 10 valid questions, the mission is rebuilt before rendering.

## Question metadata

Each active MissionStep now stores:

- `question_id`
- `department_id`
- `department_name`
- `category`
- `sub_category`
- `difficulty`
- `question_type`
- `scenario`
- `source_topic`
- `uniqueness_key`
- `skills_json`
- `skill_weights_json`

## Runtime quiz isolation

Quiz Arena now loads only questions belonging to the learner's active department. The selected department ID is stored with the quiz session and verified again on submission.

## Important deployment behavior

Do **not** delete existing MissionAttempt records during upgrades. The question rebuild only replaces assessment steps/choices. Historical attempt rows remain intact.
