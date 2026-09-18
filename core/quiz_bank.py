"""Department-isolated Quiz Arena question bank.

The old bank contained generic questions with categories such as "Business",
"Data" and "Learning" and could randomly mix them for every learner.  The
production bank is now sourced from the same validated ten-question Mission
banks, filtered by the learner's active vocational department.
"""
import random
from database.models import Department, Mission


def _question_rows(department_name):
    if not department_name:
        return []
    missions=(Mission.query.join(Department)
              .filter(Department.name==department_name, Mission.discovery.is_(True))
              .order_by(Mission.id).all())
    rows=[]
    for mission in missions:
        steps=sorted(mission.steps,key=lambda x:x.order_index)
        if len(steps)!=10:
            continue
        for step in steps:
            choices=sorted(list(step.choices),key=lambda c:c.id)
            if len(choices)!=4 or sum(bool(c.is_correct) for c in choices)!=1:
                continue
            rows.append({
                "id":f"M{mission.id}S{step.id}",
                "department_id":mission.department_id,
                "department_name":department_name,
                "mission_id":mission.id,
                "mission_title":mission.title,
                "category":mission.title,
                "sub":f"Question {step.order_index}",
                "question":step.prompt,
                "scenario":mission.scenario,
                "difficulty":mission.difficulty,
                "choices":[c.text for c in choices],
                "correct":next(i for i,c in enumerate(choices) if c.is_correct),
                "skills":[s.name for s in mission.skills],
                "source_topic":step.source_topic or mission.title,
                "question_type":step.question_type or "Scenario",
                "uniqueness_key":step.uniqueness_key or f"{department_name}|{mission.id}|{step.order_index}",
            })
    return rows


def get_questions(ids, department_name=None):
    rows=_question_rows(department_name) if department_name else []
    by_id={q["id"]:q for q in rows}
    return [by_id[i] for i in ids if i in by_id]


def make_session(count=10, seed=None, department_name=None):
    """Create a quiz session using only the active department's bank."""
    rng=random.Random(seed)
    bank=_question_rows(department_name)
    if not bank:
        return []

    # Prefer broad mission coverage so ten questions do not all come from one
    # failure mode. Each mission contributes at most one question in the first
    # pass; a second pass fills the remainder only when necessary.
    by_mission={}
    for q in bank:
        by_mission.setdefault(q["mission_id"],[]).append(q)
    mission_ids=list(by_mission)
    rng.shuffle(mission_ids)
    selected=[]
    for mid in mission_ids:
        pool=by_mission[mid]
        selected.append(rng.choice(pool))
        if len(selected)>=count:
            break
    if len(selected)<count:
        remaining=[q for q in bank if q["id"] not in {x["id"] for x in selected}]
        rng.shuffle(remaining)
        selected.extend(remaining[:count-len(selected)])

    prepared=[]
    for q in selected[:count]:
        pairs=list(enumerate(q["choices"]))
        rng.shuffle(pairs)
        prepared.append({
            "id":q["id"],"category":q["category"],"sub":q["sub"],
            "question":q["question"],"scenario":q["scenario"],
            "mission_title":q["mission_title"],"difficulty":q["difficulty"],
            "choices":[text for _,text in pairs],
            "correct_position":next(pos for pos,(orig,_) in enumerate(pairs) if orig==q["correct"]),
            "skills":q["skills"],"department_name":q["department_name"],
            "source_topic":q["source_topic"],"question_type":q["question_type"],
            "uniqueness_key":q["uniqueness_key"],
        })
    return prepared


def make_from_ids(ids, seed, department_name=None):
    rng=random.Random(seed)
    bank=_question_rows(department_name)
    by_id={q["id"]:q for q in bank}
    prepared=[]
    for qid in ids:
        q=by_id.get(qid)
        if not q:
            continue
        pairs=list(enumerate(q["choices"]))
        rng.shuffle(pairs)
        prepared.append({
            "id":q["id"],"category":q["category"],"sub":q["sub"],
            "question":q["question"],"scenario":q["scenario"],
            "mission_title":q["mission_title"],"difficulty":q["difficulty"],
            "choices":[text for _,text in pairs],
            "correct_position":next(pos for pos,(orig,_) in enumerate(pairs) if orig==q["correct"]),
            "skills":q["skills"],"department_name":q["department_name"],
            "source_topic":q["source_topic"],"question_type":q["question_type"],
            "uniqueness_key":q["uniqueness_key"],
        })
    return prepared
