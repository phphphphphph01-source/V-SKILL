import json, re, sqlite3, sys
DB='vskill.db'
BANK='data/question_bank_v2.json'

def words(s): return re.findall(r'[\wก-๙]+',s or '',flags=re.UNICODE)
def main():
    bank=json.load(open(BANK,encoding='utf-8')); con=sqlite3.connect(DB)
    active=con.execute('''select m.id,d.name from mission m join department d on d.id=m.department_id where m.discovery=1 and d.name in (?,?,?,?,?,?,?,?,?,?,?)''',('เทคโนโลยีคอมพิวเตอร์','ไฟฟ้า','อิเล็กทรอนิกส์/เมคคาทรอนิกส์','ช่างยนต์','เทคนิคการผลิต','บริหารธุรกิจ','ดิจิทัล/กราฟิก','อาหาร/คหกรรม','ก่อสร้าง','โลจิสติกส์','การโรงแรมและท่องเที่ยว')).fetchall()
    errors=[]
    if len(bank)!=880: errors.append(f'bank count={len(bank)}, expected 880')
    ids=set(); keys=set(); pos={x:0 for x in 'ABCD'}
    for q in bank:
        if q['question_id'] in ids: errors.append('duplicate question_id'); break
        ids.add(q['question_id']); keys.add(q['uniqueness_key']); pos[q['correct_answer']]+=1
        opts=list(q['choices'].values()); cp=ord(q['correct_answer'])-65; chars=[len(x) for x in opts]; ws=[len(words(x)) for x in opts]
        if len(opts)!=4 or len(set(opts))!=4: errors.append(q['question_id']+': choices not unique')
        if max(chars)/min(chars)>1.5 or max(ws)/max(1,min(ws))>1.5: errors.append(q['question_id']+': option length imbalance')
        if len(opts[cp])>=max(chars): errors.append(q['question_id']+': correct is longest/tied longest')
        if any(x in ' '.join(opts) for x in ['เสมอ','แน่นอน','เท่านั้น']): errors.append(q['question_id']+': absolute wording in choices')
        aa=q['anti_guessing']
        if not all(aa.values()): errors.append(q['question_id']+': anti_guessing flag false')
    if len(keys)!=len(bank): errors.append('duplicate uniqueness_key')
    if any(v!=220 for v in pos.values()): errors.append(f'answer position distribution={pos}')
    # Active DB shape and metadata.
    for mid,dep in active:
        n=con.execute('select count(*) from mission_step where mission_id=?',(mid,)).fetchone()[0]
        if n!=10: errors.append(f'mission {mid} has {n} steps')
    print('V-SKILL QUESTION BANK V2 VALIDATION')
    print('Active missions:',len(active)); print('Questions:',len(bank)); print('Answer positions:',pos)
    print('Difficulty:',{d:sum(q['difficulty']==d for q in bank) for d in ['EASY','MEDIUM','HARD','EXPERT']})
    print('Errors:',len(errors))
    if errors: print('\n'.join(errors[:50])); return 1
    print('RESULT: PASS'); return 0
if __name__=='__main__': sys.exit(main())
