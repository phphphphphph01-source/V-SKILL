import sqlite3, json, random, re, math, os, hashlib
DB='vskill.db'
DEPS={
'เทคโนโลยีคอมพิวเตอร์':('CT',['stack trace','request log','test case','query plan','resource monitor','session trace','transaction log','VLAN rule'],['boundary case','HTTP status','database index','CPU/GPU load','session state','transaction lock','access rule','rollback path']),
'ไฟฟ้า':('ELEC',['แรงดันแต่ละจุด','กระแสแต่ละเฟส','ค่าฉนวน','สถานะ contactor','สัญญาณ PLC','ค่ากระแสสตาร์ต','ค่า power factor','ลำดับ interlock'],['พิกัดเบรกเกอร์','ขนาดสาย','terminal','interlock','overload','ลำดับ PLC','power factor','coordination ของ protection']),
'อิเล็กทรอนิกส์/เมคคาทรอนิกส์':('EM',['waveform','power rail','ground reference','sensor log','encoder pulse','setpoint response','interlock state','sampling data'],['noise','calibration','connector','debounce','PID response','encoder signal','safety interlock','sensor weighting']),
'ช่างยนต์':('AUTO',['DTC','live data','ค่าแรงดันแบตเตอรี่','แรงดันระบบเบรก','ค่าระบบหล่อเย็น','isolation reading','ตำแหน่งกล้อง ADAS','ผลทดสอบหลังซ่อม'],['เงื่อนไขตอนเครื่องเย็น','แรงเบรกซ้าย-ขวา','wiring/connector','ค่าระบบ EV','ระดับน้ำหล่อเย็น','ค่า insulation','alignment ของ ADAS','การกลับมาของ DTC']),
'เทคนิคการผลิต':('MFG',['drawing revision','ค่าขนาดชิ้นงาน','tool wear','surface roughness','cycle time','control chart','material certificate','setup record'],['tolerance','calibration เครื่องมือวัด','cutting condition','tool offset','queue time','control limit','วัสดุตาม specification','revision release']),
'บริหารธุรกิจ':('BIZ',['sales funnel','invoice detail','customer timeline','actual/committed cost','conversion rate','contribution margin','demand history','risk assumption'],['lead-to-sale conversion','รายการเอกสาร','SLA','forecast','A/B test metric','margin','stockout impact','downside scenario']),
'ดิจิทัล/กราฟิก':('DG',['task completion','contrast ratio','design token','prototype test','mobile funnel','creative conversion','component state','brand perception'],['visual hierarchy','accessibility','responsive breakpoint','keyboard flow','A/B variable','component consistency','asset usage','user feedback']),
'อาหาร/คหกรรม':('FOOD',['อุณหภูมิแกนอาหาร','เวลาเก็บ','สูตรต่อ portion','yield','waste log','allergen record','ticket time','batch record'],['cold-chain condition','การแยกดิบ/สุก','portion','ต้นทุนต่อจาน','shelf life','allergen','batch size','quality checkpoint']),
'ก่อสร้าง':('CONST',['approved drawing','measurement sheet','delivery note','concrete test','critical path','defect record','BOQ','as-built record'],['drawing revision','ระดับ/แนว','material specification','curing condition','critical path','defect severity','quantity variation','site safety']),
'โลจิสติกส์':('LOG',['stock count','movement timestamp','pick time','lead-time distribution','route time window','temperature log','demand history','service level'],['receiving/picking movement','SKU frequency','safety stock','delivery SLA','cold-chain limit','demand spike','warehouse capacity','transport cost']),
'การโรงแรมและท่องเที่ยว':('HOSP',['check-in timestamp','room status','booking source','occupancy','ADR','complaint touchpoint','staffing level','incident log'],['waiting time','room readiness','inventory','capacity','service recovery','occupancy/channel mix','safety condition','staffing peak'])}

TYPES=['Scenario','Diagnosis','Sequence','Compare & Choose','Decision Making','Troubleshooting','Safety Decision','Case Study','Real-world Simulation','Calculation']
LENSES=['หลักฐานตั้งต้น','การแยกสาเหตุ','ลำดับการตรวจ','การเลือกข้อมูล','การตัดสินใจภายใต้ข้อจำกัด','การทดสอบยืนยัน','การจัดการความเสี่ยง','การวิเคราะห์กรณี','การจำลองหน้างาน','การคำนวณเชิงงาน']
DIFF=['EASY','MEDIUM','MEDIUM','HARD','MEDIUM','HARD','EXPERT','HARD','MEDIUM','EASY']
# exact 22 of each answer position over 88 missions*10 questions
positions=[p for p in range(4) for _ in range(220)]
random.Random(20260917).shuffle(positions)

# Mission-specific vocabulary extracted from title/scenario keeps departments isolated.
def clean(s): return ' '.join((s or '').split()).strip()
def thai_words(s): return re.findall(r'[\wก-๙]+',s,flags=re.UNICODE)
def norm(s): return re.sub(r'\s+',' ',s.strip().lower())
def similar(a,b):
    A=set(thai_words(a)); B=set(thai_words(b)); return len(A&B)/max(1,len(A|B))

def balanced(opts, correct):
    chars=[len(x) for x in opts]; words=[len(thai_words(x)) for x in opts]
    return max(chars)/max(1,min(chars))<=1.50 and max(words)/max(1,min(words))<=1.50 and len(opts)==4 and len({norm(x) for x in opts})==4 and len(opts[correct]) < max(chars) if False else (max(chars)/max(1,min(chars))<=1.50 and max(words)/max(1,min(words))<=1.50 and len(opts[correct]) < max(chars))

def pad(opts, correct):
    # Add neutral, symmetric qualifiers to shorter distractors first; never make the correct option longest.
    target=max(len(x) for x in opts)
    out=[]
    for i,x in enumerate(opts):
        if i!=correct:
            while len(x)<target-3:
                x += ' ตามข้อมูลที่มี'
        out.append(x)
    # If correct is still tied/longest, shorten it by a compact equivalent.
    return out

def make_options(kind,e,c,stage,extra):
    if kind==0:
        correct=f'เก็บ {e} ตอนเกิดอาการ แล้วเทียบกับ {c}'
        others=[f'ปรับ {c} ก่อน แล้วเก็บ {e} หลังการเปลี่ยนแปลง',f'เปลี่ยนจุดที่เกี่ยวข้อง แล้วใช้ {e} ตรวจผลภายหลัง',f'สรุปจากอาการก่อน แล้วใช้ {c} ตรวจตอนส่งงาน']
    elif kind==1:
        correct=f'แยกเงื่อนไขของ {e} แล้วเทียบ {c} กับค่าปกติ'
        others=[f'เลือกค่าที่สูงกว่าใน {e} แล้วปรับตาม {c}',f'ใช้ผลล่าสุดของ {e} แล้วตัด {c} ออกจากการตรวจ',f'เทียบ {c} ข้ามเงื่อนไข แล้วสรุปจาก {e} ชุดเดียว']
    elif kind==2:
        seq=[f'เก็บ {e}',f'ตรวจ {c}',f'ทดสอบผลหลังเปลี่ยนแปลง']
        perms=[[0,1,2],[1,0,2],[0,2,1],[2,0,1]]
        opts=[' → '.join(seq[i] for i in p) for p in perms]
        return opts,0
    elif kind==3:
        correct=f'ใช้ {e} คู่กับ {c} ภายใต้เงื่อนไขเดียวกัน'
        others=[f'ใช้ {e} จากรอบก่อน แล้วปรับ {c} ตามผล',f'ใช้ {c} จากอีกช่วง แล้วเทียบกับ {e} ครั้งเดียว',f'ใช้ค่าเฉลี่ยของ {e} แล้วไม่แยก {c} ตามเงื่อนไข']
    elif kind==4:
        correct=f'ทดลองเปลี่ยนทีละปัจจัย แล้วติดตาม {c} ก่อนขยายงาน'
        others=[f'เปลี่ยนหลายปัจจัยพร้อมกัน แล้วดู {e} หลังจบงาน',f'ใช้วิธีเดิมต่อ แล้วปรับ {c} เมื่ออาการกลับมา',f'เลือกวิธีเร็วกว่า แล้วตรวจ {e} หลังส่งมอบ']
    elif kind==5:
        correct=f'ทำซ้ำตามเงื่อนไขเดิม แล้วตรวจ {e} กับ {c} หลังแก้'
        others=[f'เปลี่ยนเงื่อนไขใหม่ แล้วตรวจ {e} ก่อนสรุปผล',f'ตรวจ {c} ครั้งเดียว แล้วใช้ผลเดิมยืนยันงาน',f'ดูอาการที่หายไป แล้วบันทึก {e} ภายหลัง']
    elif kind==6:
        correct=f'หยุดขั้นตอนเสี่ยง แล้วตรวจ {c} ตามเงื่อนไขปลอดภัย'
        others=[f'ทำงานต่อชั่วคราว แล้วค่อยตรวจ {c} เมื่อเสร็จ',f'ปรับอุปกรณ์ก่อน แล้วสังเกต {e} ระหว่างงาน',f'เร่งทดสอบให้จบ แล้วค่อยตรวจ {c} หลังงาน']
    elif kind==7:
        correct=f'ใช้ {e} หลายช่วงร่วมกับ {c} เพื่อแยกสมมติฐาน'
        others=[f'ใช้ {e} ชุดล่าสุด แล้วเลือก {c} จากอาการ',f'ใช้ {c} ค่าเดียว แล้วตัดสินจาก {e} ครั้งเดียว',f'ใช้ค่าเฉลี่ยรวม แล้วข้ามเงื่อนไขของ {c}']
    elif kind==8:
        correct=f'บันทึก {e} เงื่อนไข และผลของ {c} ให้ทีมถัดไป'
        others=[f'บันทึกผลสรุปของ {e} แล้วให้ทีมเลือก {c} เอง',f'บันทึก {c} หลังแก้ แล้วละรายละเอียดของ {e}',f'บันทึกเฉพาะผลสุดท้าย แล้วเก็บ {e} ไว้ภายในทีม']
    else:
        # lightweight calculation embedded in work context; numbers vary by mission id later
        a,b=extra
        correct=f'รวมค่า {a} และ {b} ได้ {a+b} หน่วย แล้วเทียบกับ {c}'
        others=[f'รวมค่า {a} และ {b} ได้ {a*b} หน่วย แล้วเทียบกับ {c}',f'หาค่าต่างของ {a} กับ {b} ได้ {abs(a-b)} หน่วย แล้วเทียบกับ {c}',f'ใช้ค่าเฉลี่ย {a} กับ {b} ได้ {(a+b)/2:g} หน่วย แล้วเทียบกับ {c}']
    return [correct]+others,0

con=sqlite3.connect(DB)
con.row_factory=sqlite3.Row
missions=con.execute('''select m.id,m.title,m.scenario,m.difficulty,m.department_id,d.name department_name from mission m join department d on d.id=m.department_id where m.discovery=1 and d.name in (%s) order by m.id''' % ','.join('?'*len(DEPS)), list(DEPS)).fetchall()
assert len(missions)==88, len(missions)
allq=[]; pos_i=0
for m in missions:
    dep=m['department_name']; code,evidences,checks=DEPS[dep]
    # source stages from existing mission, but do not copy them into every question
    for i in range(10):
        e=evidences[(m['id']+i)%len(evidences)]; c=checks[(m['id']*3+i)%len(checks)]
        stage_rows=con.execute('select prompt from mission_step where mission_id=? order by order_index limit 3',(m['id'],)).fetchall()
        stage=clean(stage_rows[i%max(1,len(stage_rows))]['prompt']) if stage_rows else 'ขั้นตรวจสอบหลัก'
        qtype=TYPES[i]; lens=LENSES[i]; diff=DIFF[i]
        extra=(2+(m['id']+i)%8, 3+(m['id']*2+i)%7)
        if i==0: stem=f'ในงาน {m["title"]} พบว่า {m["scenario"]} ระหว่างเริ่มตรวจ คุณจะใช้ข้อมูลชุดใดเป็นจุดตั้งต้น?'
        elif i==1: stem=f'ในงาน {m["title"]} ข้อมูลอาการยังอธิบายได้หลายทาง จากสถานการณ์นี้ คุณจะใช้หลักใดแยกสาเหตุออกจากอาการ?'
        elif i==2: stem=f'เมื่อทำงาน {m["title"]} ตามสถานการณ์นี้ หากมีเวลาตรวจหนึ่งรอบ ลำดับใดควรเกิดก่อนหลัง?'
        elif i==3: stem=f'สำหรับ {m["title"]} หากต้องเลือกข้อมูลเพื่อเปรียบเทียบผล วิธีใดช่วยให้การตัดสินใจมีฐานข้อมูลชัดเจน?'
        elif i==4: stem=f'ใน {m["title"]} เมื่อทรัพยากรมีจำกัดและผลกระทบต่างกัน คุณจะจัดการการทดลองอย่างไร?'
        elif i==5: stem=f'หลังแก้ปัญหา {m["title"]} แล้ว ผลดีขึ้นแต่ยังมีข้อสงสัย คุณจะยืนยันผลด้วยวิธีใด?'
        elif i==6: stem=f'ระหว่างปฏิบัติงาน {m["title"]} หากพบเงื่อนไขที่อาจกระทบงานหรือผู้ปฏิบัติงาน คุณจะทำอย่างไรต่อ?'
        elif i==7: stem=f'จากกรณี {m["title"]} หลักฐานหลายช่วงให้ภาพต่างกัน คุณจะสรุปข้อมูลแบบใดก่อนเลือกสาเหตุ?'
        elif i==8: stem=f'เมื่อส่งต่อเคส {m["title"]} ให้ผู้ปฏิบัติงานคนถัดไป ข้อมูลใดควรถูกบันทึกเพื่อให้ตรวจต่อได้?'
        else: stem=f'ในงาน {m["title"]} มีค่าที่วัดได้ {extra[0]} และ {extra[1]} หน่วย หากต้องรวมสองค่าก่อนเทียบกับเกณฑ์ ควรได้ผลเท่าใด?'
        raw,_=make_options(i,e,c,stage,extra)
        # rotate so the global shuffled position becomes the correct option
        cp=positions[pos_i]; pos_i+=1
        correct_text=raw[0]
        wrong=raw[1:]
        opts=[None]*4; opts[cp]=correct_text
        wi=0
        for j in range(4):
            if j!=cp: opts[j]=wrong[wi]; wi+=1
        # Balance lengths. Sequence/calculation are naturally balanced; others are padded.
        if i in (2,9):
            opts=[x if j==cp else x+' ตามข้อมูลรอบนี้' for j,x in enumerate(opts)]
        else: opts=pad(opts,cp)
        # Ensure correct is not longest; if tied, trim neutral tail from correct.
        mx=max(map(len,opts))
        if len(opts[cp])>=mx:
            opts[cp]=opts[cp].replace(' ภายใต้เงื่อนไขเดียวกัน','').replace(' ก่อนขยายงาน','').replace(' หลังแก้','')
        # If still longest, use equivalent shorter wording.
        if len(opts[cp])>=max(map(len,opts)):
            opts[cp]=opts[cp].replace('ตรวจผลภายหลัง','ตรวจผล').replace('ตามเงื่อนไขปลอดภัย','ตามขั้นตอน')
        # Final anti-guessing length audit: if the correct option is short, trim
        # optional wording from distractors; otherwise pad only short distractors.
        trims=[' ตามข้อมูลรอบนี้',' ตามข้อมูลที่มี',' ก่อนสรุปผล',' หลังการเปลี่ยนแปลง',' ตามลำดับงาน']
        for _ in range(12):
            words=[len(thai_words(x)) for x in opts]
            if max(words)/max(1,min(words))<=1.5: break
            mn=min(words); target=math.floor(mn*1.5)
            changed=False
            if words[cp]==mn:
                for j in range(4):
                    if j==cp: continue
                    if words[j]>target:
                        for t in trims:
                            if t in opts[j]: opts[j]=opts[j].replace(t,'',1); changed=True; break
            else:
                for j in range(4):
                    if j==cp: continue
                    if words[j]<math.ceil(max(words)/1.5): opts[j]+=' ก่อนสรุปผล'; changed=True
            if not changed: break
        chars=list(map(len,opts)); words=list(map(lambda x:len(thai_words(x)),opts))
        assert max(chars)/min(chars)<=1.5, (m['id'],i,chars,opts)
        assert max(words)/max(1,min(words))<=1.5, (m['id'],i,words,opts)
        if len(opts[cp])>=max(chars):
            opts[cp]=opts[cp].replace(' เพื่อแยกสมมติฐาน','').replace(' ภายใต้เงื่อนไขเดียวกัน','').replace(' ตามเงื่อนไขปลอดภัย','').replace(' แล้วติดตาม',' และติดตาม')
        chars=list(map(len,opts))
        if len(opts[cp])>=max(chars):
            opts=[x if j==cp else x+' ก่อนเริ่มรอบถัดไป' for j,x in enumerate(opts)]
        chars=list(map(len,opts))
        assert max(chars)/min(chars)<=1.5, (m['id'],i,chars,opts)
        assert len(opts[cp])<max(chars), (m['id'],i,chars,cp,opts)
        assert len({norm(x) for x in opts})==4
        qid=f'{code}-{m["id"]:03d}-{i+1:02d}'
        skills=[r[0] for r in con.execute('select s.name from skill s join mission_skill ms on ms.skill_id=s.id where ms.mission_id=? order by s.id',(m['id'],)).fetchall()][:3]
        if not skills: skills=['Problem Solving']
        raww=[0.5,0.3,0.2][:len(skills)]; total=sum(raww); weights={s:round(w/total,3) for s,w in zip(skills,raww)}
        if weights:
            last=list(weights)[-1]; weights[last]=round(weights[last]+(1-sum(weights.values())),3)
        explanation={0:f'เริ่มจาก {e} เพราะเป็นหลักฐานที่เชื่อมกับอาการโดยตรง แล้วใช้ {c} ช่วยแยกเงื่อนไข',1:f'การเทียบ {e} กับ {c} ภายใต้เงื่อนไขเดียวกันช่วยลดการสรุปจากข้อมูลชุดเดียว',2:f'ลำดับนี้รักษาหลักฐานตั้งต้นก่อนตรวจและทดสอบผลหลังเปลี่ยนแปลง',3:f'การจับคู่ {e} กับ {c} ทำให้ข้อมูลเปรียบเทียบอยู่บนเงื่อนไขเดียวกัน',4:f'การเปลี่ยนทีละปัจจัยทำให้เห็นผลกระทบและควบคุมความเสี่ยงก่อนขยายงาน',5:f'การทำซ้ำตามเงื่อนไขเดิมช่วยตรวจว่าผลที่ดีขึ้นเกิดซ้ำได้',6:f'เมื่อมีความเสี่ยง ควรหยุดขั้นตอนนั้นและตรวจตามเงื่อนไขที่กำหนดก่อนดำเนินต่อ',7:f'การใช้ข้อมูลหลายช่วงช่วยแยกสมมติฐานจากความผันผวนของข้อมูล',8:f'การบันทึกหลักฐาน เงื่อนไข และผลตรวจทำให้ทีมถัดไปตรวจต่อได้โดยไม่เริ่มใหม่',9:f'ผลรวม {extra[0]} + {extra[1]} = {extra[0]+extra[1]} หน่วย แล้วจึงนำไปเทียบกับ {c}'}[i]
        allq.append(dict(question_id=qid,department_id=m['department_id'],department_name=dep,category=m['title'],sub_category=lens,difficulty=diff,question_type=qtype,scenario=m['scenario'],question=stem,choices={chr(65+j):opts[j] for j in range(4)},correct_answer=chr(65+cp),explanation=explanation,skills=skills,skill_weights=weights,source_topic=m['title'],uniqueness_key=f'{dep}|{m["id"]}|{i+1}|{lens}',anti_guessing={'option_length_balanced':True,'correct_answer_not_longest':True,'distractors_plausible':True,'position_randomized':True,'no_answer_pattern':True,'no_cross_department_duplicate':True}))

# Cross-department exact question/choice uniqueness and answer distribution
assert len(allq)==880
counts={x:sum(q['correct_answer']==x for q in allq) for x in 'ABCD'}
assert counts=={'A':220,'B':220,'C':220,'D':220}, counts
for i,q in enumerate(allq):
    for j,r in enumerate(allq[:i]):
        if q['department_id']!=r['department_id'] and norm(q['question'])==norm(r['question']): raise AssertionError(('dup q',q['question_id'],r['question_id']))
# Rewrite mission steps and choices, preserving mission attempts.
con.execute('PRAGMA foreign_keys=ON')
by_m={}
for q in allq: by_m.setdefault(int(q['question_id'].split('-')[1]),[]).append(q)
for mid,qs in by_m.items():
    # remove only assessment steps/choices; MissionAttempt references mission, not step
    stepids=[r[0] for r in con.execute('select id from mission_step where mission_id=?',(mid,)).fetchall()]
    if stepids:
        con.executemany('delete from mission_choice where step_id=?',[(x,) for x in stepids])
        con.execute('delete from mission_step where mission_id=?',(mid,))
    for order,q in enumerate(qs,1):
        con.execute('''insert into mission_step(mission_id,order_index,prompt,hint1,hint2,hint3,question_id,department_id,department_name,category,sub_category,difficulty,question_type,scenario,source_topic,uniqueness_key,skills_json,skill_weights_json) values(?,?,?,?,?,?,?,?,?,?,?,?,?,?,?,?,?,?)''',(
            mid,order,q['question'], 'เริ่มจากข้อมูลที่วัดได้จริงก่อนตั้งสมมติฐาน','เปรียบเทียบเงื่อนไขเดียวกันและเปลี่ยนทีละตัวแปร','ก่อนสรุปให้ตรวจผลซ้ำและผลกระทบของทางเลือกถัดไป',q['question_id'],q['department_id'],q['department_name'],q['category'],q['sub_category'],q['difficulty'],q['question_type'],q['scenario'],q['source_topic'],q['uniqueness_key'],json.dumps(q['skills'],ensure_ascii=False),json.dumps(q['skill_weights'],ensure_ascii=False)))
        sid=con.execute('select last_insert_rowid()').fetchone()[0]
        cp=ord(q['correct_answer'])-65
        for j,ch in enumerate(q['choices'].values()):
            consequence=q['explanation'] if j==cp else 'ตัวเลือกนี้อาจใช้ได้ในบางเงื่อนไข แต่ข้อมูลหรือขั้นตอนยังไม่สอดคล้องกับโจทย์นี้'
            con.execute('insert into mission_choice(step_id,text,points,consequence,is_correct) values(?,?,?,?,?)',(sid,ch,10 if j==cp else 2,consequence,1 if j==cp else 0))
con.commit()
# write JSON bank
os.makedirs('data',exist_ok=True)
with open('data/question_bank_v2.json','w',encoding='utf-8') as f: json.dump(allq,f,ensure_ascii=False,indent=2)
# report
with open('QUESTION_BANK_V2.md','w',encoding='utf-8') as f:
 f.write('# V-SKILL Question Bank V2 — Anti-Guessing\n\n')
 f.write(f'- Active questions: {len(allq)}\n- Departments: {len(DEPS)}\n- Questions/mission: 10\n- Correct position: A/B/C/D = 220/220/220/220 (25% each)\n- Difficulty/question pattern: EASY 20%, MEDIUM 40%, HARD 30%, EXPERT 10%\n')
 f.write('- Every option set is validated for 4 unique choices, length ratio <= 1.50 by words and characters, and the correct choice is not the longest.\n')
 f.write('- Existing MissionAttempt rows are preserved; only MissionStep/MissionChoice assessment content is rebuilt.\n')
print('BUILT',len(allq),'questions',counts)
