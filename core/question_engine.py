"""V-SKILL Question Bank V2 runtime.

The bundled JSON bank is the source of truth for assessment content.  Runtime
validation rejects banks that expose answer-length, answer-position, or schema
clues.  Rebuilding replaces only MissionStep/MissionChoice rows; MissionAttempt
history is preserved.
"""
import json, os, re
from database.database import db
from database.models import Mission, MissionStep, MissionChoice, Department
from core.department_missions import DEPARTMENT_CATALOG

QUESTION_COUNT=10
BANK_PATH=os.path.join(os.path.dirname(os.path.dirname(__file__)), 'data', 'question_bank_v2.json')
DEPARTMENT_CODES={"เทคโนโลยีคอมพิวเตอร์":"CT","ไฟฟ้า":"ELEC","อิเล็กทรอนิกส์/เมคคาทรอนิกส์":"EM","ช่างยนต์":"AUTO","เทคนิคการผลิต":"MFG","บริหารธุรกิจ":"BIZ","ดิจิทัล/กราฟิก":"DG","อาหาร/คหกรรม":"FOOD","ก่อสร้าง":"CONST","โลจิสติกส์":"LOG","การโรงแรมและท่องเที่ยว":"HOSP"}

def _clean(text): return ' '.join((text or '').split()).strip()
def _words(text): return re.findall(r'[\wก-๙]+', text or '', flags=re.UNICODE)

def _load_bank():
    with open(BANK_PATH, encoding='utf-8') as f: return json.load(f)

def _bank_for_mission(mission_id):
    return [q for q in _load_bank() if q['question_id'].split('-')[1] == f'{int(mission_id):03d}']

def build_question_data(mission, department_name, source_stages=None):
    rows=_bank_for_mission(mission.id)
    if len(rows)!=QUESTION_COUNT or any(q['department_id']!=mission.department_id or q['department_name']!=department_name for q in rows):
        raise ValueError(f'No V2 question bank found for mission {mission.id}')
    return rows

def _step_is_valid(step, mission):
    texts=[_clean(c.text) for c in step.choices]
    if len(texts)!=4 or len(set(texts))!=4 or sum(bool(c.is_correct) for c in step.choices)!=1: return False
    chars=[len(x) for x in texts]; words=[len(_words(x)) for x in texts]; cp=next(i for i,c in enumerate(step.choices) if c.is_correct)
    if max(chars)/max(1,min(chars))>1.50 or max(words)/max(1,min(words))>1.50: return False
    if len(texts[cp])>=max(chars): return False
    required=("question_id","department_id","department_name","category","sub_category","difficulty","question_type","scenario","source_topic","uniqueness_key","skills_json","skill_weights_json")
    if any(getattr(step,n,None) in (None,'') for n in required): return False
    if step.department_id!=mission.department_id or step.department_name!=mission.department.name: return False
    try:
        weights=json.loads(step.skill_weights_json)
        if not isinstance(weights,dict) or abs(sum(float(v) for v in weights.values())-1.0)>0.01: return False
    except Exception: return False
    if any(x in ' '.join(texts) for x in ['เสมอ','แน่นอน','เท่านั้น']): return False
    return True

def _is_valid_bank(mission):
    steps=sorted(mission.steps,key=lambda x:x.order_index)
    if len(steps)!=QUESTION_COUNT or len({_clean(s.prompt) for s in steps})!=QUESTION_COUNT: return False
    if not all(_step_is_valid(s,mission) for s in steps): return False
    qids=[s.question_id for s in steps]; keys=[s.uniqueness_key for s in steps]
    if len(set(qids))!=QUESTION_COUNT or len(set(keys))!=QUESTION_COUNT: return False
    return True

def _rebuild_mission(mission, dep_name):
    rows=build_question_data(mission,dep_name)
    for step in list(mission.steps): db.session.delete(step)
    db.session.flush()
    for order,q in enumerate(sorted(rows,key=lambda x:x['question_id']),1):
        step=MissionStep(mission_id=mission.id,order_index=order,prompt=q['question'],hint1='เริ่มจากข้อมูลที่วัดได้จริงก่อนตั้งสมมติฐาน',hint2='เปรียบเทียบเงื่อนไขเดียวกันและเปลี่ยนทีละตัวแปร',hint3='ก่อนสรุปให้ตรวจผลซ้ำและผลกระทบของทางเลือกถัดไป',question_id=q['question_id'],department_id=q['department_id'],department_name=q['department_name'],category=q['category'],sub_category=q['sub_category'],difficulty=q['difficulty'],question_type=q['question_type'],scenario=q['scenario'],source_topic=q['source_topic'],uniqueness_key=q['uniqueness_key'],skills_json=json.dumps(q['skills'],ensure_ascii=False),skill_weights_json=json.dumps(q['skill_weights'],ensure_ascii=False))
        cp=ord(q['correct_answer'])-65
        choices=[]
        for j,ch in enumerate(q['choices'].values()):
            choices.append(MissionChoice(text=ch,points=10 if j==cp else 2,consequence=q['explanation'] if j==cp else 'ตัวเลือกนี้มีหลักคิดที่ใช้ได้บางกรณี แต่ไม่ตรงกับเงื่อนไขของสถานการณ์นี้',is_correct=j==cp))
        step.choices=choices; mission.steps.append(step)

def upgrade_all_department_missions(force=False):
    changed=0
    for dep_name in DEPARTMENT_CATALOG:
        dep=Department.query.filter_by(name=dep_name).first()
        if not dep: continue
        for mission in Mission.query.filter_by(department_id=dep.id,discovery=True).all():
            if force or not _is_valid_bank(mission):
                _rebuild_mission(mission,dep_name); changed+=1
    if changed: db.session.commit()
    return changed

def ensure_mission_has_ten_questions(mission_id, department_id):
    dep=Department.query.get(department_id); mission=Mission.query.get(mission_id)
    if not dep or not mission or mission.department_id!=department_id or dep.name not in DEPARTMENT_CATALOG: return False
    if not _is_valid_bank(mission): _rebuild_mission(mission,dep.name); db.session.commit(); return True
    return False
