from database.database import db
from database.models import (
    User, Department, Skill, Mission, MissionStep, MissionChoice,
    Career, Achievement, LearningTopic, AvatarItem
)


DEPARTMENTS = [
    ("Computer Technology", "งานคอมพิวเตอร์และการแก้ปัญหาระบบ"),
    ("Information Technology", "เครือข่าย ระบบสารสนเทศ และงาน IT"),
    ("Electrical", "ระบบไฟฟ้า การวัด และความปลอดภัย"),
    ("Electronics", "วงจร เซนเซอร์ และระบบอิเล็กทรอนิกส์"),
    ("Automotive", "การวิเคราะห์และซ่อมระบบยานยนต์"),
    ("Mechanical", "เครื่องจักร การผลิต และการบำรุงรักษา"),
    ("Accounting", "ข้อมูลทางบัญชี การตรวจสอบ และความถูกต้อง"),
    ("Business / Marketing", "การตลาด การวางแผน และการตัดสินใจทางธุรกิจ"),
]

SKILLS = [
    ("Problem Solving", "แยกปัญหา หาสาเหตุ และเลือกวิธีแก้"),
    ("Logical Thinking", "คิดเป็นลำดับและเชื่อมโยงเหตุผล"),
    ("Analytical Thinking", "วิเคราะห์ข้อมูลและหลักฐานก่อนสรุป"),
    ("Technical Skill", "ประยุกต์ใช้ความรู้เชิงเทคนิคกับงานจริง"),
    ("Decision Making", "ตัดสินใจภายใต้ข้อมูล เวลา และทรัพยากรจำกัด"),
    ("Creativity", "สร้างทางเลือกหรือวิธีใหม่ที่เหมาะกับสถานการณ์"),
    ("Communication", "สื่อสารข้อมูลและเหตุผลอย่างชัดเจน"),
    ("Teamwork", "แบ่งงาน รับฟัง และประสานงานกับผู้อื่น"),
    ("Planning", "วางลำดับงานและจัดสรรทรัพยากร"),
    ("Time Management", "จัดการเวลาและลำดับความเร่งด่วน"),
    ("Attention to Detail", "ตรวจรายละเอียดและความผิดปกติ"),
    ("Adaptability", "ปรับแผนเมื่อเงื่อนไขเปลี่ยน"),
    ("Technology Skill", "เลือกและใช้เทคโนโลยีได้เหมาะสม"),
]

def _get_or_create(model, name, **kwargs):
    row = model.query.filter_by(name=name).first()
    if not row:
        row = model(name=name, **kwargs)
        db.session.add(row)
        db.session.flush()
    return row

def _add_step(mission, order, prompt, choices):
    step = MissionStep(
        order_index=order,
        prompt=prompt,
        hint1="เริ่มจากข้อมูลที่ตรวจสอบได้ก่อนตัดสินใจ",
        hint2="เลือกการตรวจสอบที่ลดความเสี่ยงและใช้ทรัพยากรอย่างคุ้มค่า",
        hint3="คิดถึงผลกระทบของทางเลือกถัดไปและหลักฐานที่ยังขาด",
    )
    step.choices = [
        MissionChoice(text=text, points=points, consequence=consequence, is_correct=correct)
        for text, points, consequence, correct in choices
    ]
    mission.steps.append(step)

def _mission_exists(title):
    return Mission.query.filter_by(title=title).first() is not None

def _add_advanced_missions(D, S):
    specs = [
        ("Wi-Fi Dead Zone", "ผู้ใช้ในห้องเรียนหนึ่งโซนเชื่อมต่อ Wi-Fi ไม่ได้ แต่โซนอื่นยังใช้งานได้",
         "Information Technology", ["Problem Solving","Analytical Thinking","Technical Skill","Planning"], 2, 240, 1200,
         [
             ("ตรวจ Access Point และดูสถานะ/สัญญาณก่อน", [("ดู log และระดับสัญญาณ",10,"ได้หลักฐานโดยไม่เปลี่ยนระบบ",True),("รีสตาร์ตทุกตัวทันที",3,"กระทบผู้ใช้โซนอื่น",False),("เปลี่ยน Router ใหม่",1,"ใช้งบโดยยังไม่รู้สาเหตุ",False)]),
             ("พบว่า AP ตัวเดียวมีสัญญาณผิดปกติ คุณทำอะไรต่อ?", [("ทดสอบสายและ PoE ของ AP ตัวนั้น",10,"แยกปัญหาได้เป็นระบบ",True),("เพิ่มกำลังส่งทันที",4,"อาจกลบปัญหาเดิม",False),("แจ้งว่าระบบล่มทั้งอาคาร",1,"สรุปเกินหลักฐาน",False)]),
             ("สาย PoE หลวมและงบจำกัด คุณเลือกอย่างไร?", [("จัดลำดับซ่อมจุดที่กระทบผู้ใช้มากสุดและทดสอบซ้ำ",10,"ใช้ทรัพยากรตรงจุด",True),("ซื้ออุปกรณ์สำรองทั้งหมด",4,"ใช้งบสูงเกินจำเป็น",False),("ปล่อยไว้ก่อน",1,"ปัญหายังไม่ถูกแก้",False)])
         ]),
        ("Bug in Inventory App", "แอปสต็อกแสดงจำนวนชิ้นส่วนติดลบหลังบันทึกการเบิก",
         "Computer Technology", ["Logical Thinking","Problem Solving","Technical Skill","Attention to Detail"], 2, 270, 900,
         [
             ("ตรวจข้อมูลตัวอย่างและขั้นตอนที่ทำให้ค่าติดลบ", [("ทำซ้ำด้วยข้อมูลจำลองและตรวจลำดับการคำนวณ",10,"ได้หลักฐานสำหรับหาจุดผิด",True),("แก้ฐานข้อมูลด้วยการเพิ่มเลข",2,"อาจทำให้ข้อมูลเพี้ยน",False),("ลบรายการที่ติดลบ",3,"ทำลายหลักฐาน",False)]),
             ("พบว่าการตรวจจำนวนคงเหลือทำหลังการหัก คุณทำอะไร?", [("ย้าย validation ให้อยู่ก่อน commit และเขียน test",10,"ป้องกันปัญหาซ้ำ",True),("ซ่อนค่าติดลบด้วย CSS",1,"แก้เฉพาะการแสดงผล",False),("ปิดระบบเบิกทั้งหมด",4,"ลดความเสี่ยงแต่กระทบงาน",False)]),
             ("ก่อน deploy คุณจะยืนยันอย่างไร?", [("ทดสอบกรณีปกติ ศูนย์ และเบิกเกินพร้อมตรวจ log",10,"ครอบคลุม edge cases",True),("ทดสอบแค่ข้อมูลเดิม",4,"หลักฐานไม่พอ",False),("deploy ทันทีเพื่อดูผลจริง",1,"เสี่ยงต่อข้อมูลจริง",False)])
         ]),
        ("Circuit Overheat", "แผงวงจรควบคุมร้อนผิดปกติหลังเปิดเครื่อง 10 นาที",
         "Electronics", ["Analytical Thinking","Technical Skill","Attention to Detail","Decision Making"], 3, 300, 1500,
         [
             ("การตรวจแรกที่ปลอดภัยที่สุดคืออะไร?", [("ตัดไฟและตรวจจุดร้อน/กระแสตามขั้นตอน",10,"ลดความเสี่ยงและเก็บหลักฐาน",True),("จับชิ้นส่วนด้วยมือ",1,"เสี่ยงอันตราย",False),("เปลี่ยน IC ทันที",3,"ยังไม่มีหลักฐาน",False)]),
             ("พบกระแสสูงกว่าค่าปกติ คุณจะตรวจอะไร?", [("ตรวจโหลดและจุดลัดวงจรตามแผนผัง",10,"จำกัดสมมติฐาน",True),("เพิ่มฟิวส์ให้ใหญ่ขึ้น",2,"เพิ่มความเสี่ยง",False),("ลดแรงดันแบบสุ่ม",4,"อาจเปลี่ยนเงื่อนไขการวิเคราะห์",False)]),
             ("แก้ไขแล้ว อะไรคือหลักฐานว่าพร้อมใช้งาน?", [("ทดสอบภายใต้โหลดและเฝ้าดูอุณหภูมิ/กระแส",10,"ยืนยันด้วยข้อมูล",True),("เปิดเครื่อง 1 นาทีแล้วจบ",4,"เวลาทดสอบสั้น",False),("ดูว่าไฟติดก็พอ",1,"ยังไม่ยืนยันความเสถียร",False)])
         ]),
        ("PLC Sensor Mismatch", "เซนเซอร์นับชิ้นงานมากกว่าจำนวนจริงเป็นบางช่วง",
         "Electrical", ["Analytical Thinking","Technical Skill","Attention to Detail","Logical Thinking"], 3, 330, 1800,
         [
             ("คุณจะเริ่มหาสาเหตุจากอะไร?", [("เทียบสัญญาณ sensor กับจังหวะจริงและดู noise",10,"สร้าง baseline",True),("เปลี่ยน PLC",2,"ราคาแพงและยังไม่รู้สาเหตุ",False),("เพิ่มตัวนับอีกตัวโดยไม่ตรวจ",3,"เพิ่มความซับซ้อน",False)]),
             ("พบสัญญาณเด้งหลายครั้งเมื่อชิ้นงานผ่าน คุณทำอะไร?", [("ตรวจ debounce/filter และตำแหน่ง sensor",10,"แก้ที่สาเหตุและเงื่อนไข",True),("เพิ่มความเร็วสายพาน",1,"อาจทำให้แย่ลง",False),("ปิด alarm",2,"ซ่อนปัญหา",False)]),
             ("หลังปรับค่าแล้วควรทำอย่างไร?", [("เก็บผลหลายรอบและเทียบ false count ก่อน/หลัง",10,"วัดผลจริง",True),("ทดสอบเพียงหนึ่งชิ้น",4,"หลักฐานน้อย",False),("ถือว่าเสร็จทันที",1,"ยังไม่ยืนยัน",False)])
         ]),
        ("Car Starting Failure", "รถทดลองสตาร์ตไม่ติดและมีไฟเตือนเครื่องยนต์",
         "Automotive", ["Problem Solving","Technical Skill","Decision Making","Attention to Detail"], 2, 300, 2500,
         [
             ("ขั้นแรกที่เหมาะสมคืออะไร?", [("ตรวจแบตเตอรี่ ขั้วต่อ และอ่านอาการตามขั้นตอน",10,"เริ่มจากสาเหตุพื้นฐาน",True),("เปลี่ยนหัวเทียนทันที",4,"ยังไม่มีหลักฐาน",False),("เปลี่ยน ECU",1,"ใช้งบสูงมาก",False)]),
             ("แบตเตอรี่ปกติแต่มี code เกี่ยวกับ sensor คุณทำอะไร?", [("ตรวจสาย/connector และค่าจาก sensor",10,"ตรวจทั้งวงจร",True),("ลบ code แล้วจบ",2,"ลบหลักฐาน",False),("เปลี่ยน sensor โดยไม่วัด",4,"มีโอกาสเปลืองอะไหล่",False)]),
             ("หลังซ่อม คุณจะยืนยันผลอย่างไร?", [("ลบสาเหตุแล้วทดสอบ start และตรวจ code ซ้ำ",10,"ยืนยันครบขั้นตอน",True),("สตาร์ตติดครั้งเดียว",5,"ยังไม่พอ",False),("ส่งรถทันที",1,"ขาดการตรวจซ้ำ",False)])
         ]),
        ("Machine Vibration", "เครื่องจักรสั่นมากขึ้นและมีเวลาซ่อมเพียง 30 นาที",
         "Mechanical", ["Problem Solving","Planning","Time Management","Technical Skill"], 3, 180, 2000,
         [
             ("เมื่อเวลาจำกัด คุณจะทำอย่างไร?", [("จัดลำดับความเสี่ยงและตรวจจุดยึด/การสั่นก่อน",10,"ลด downtime อย่างมีระบบ",True),("ถอดเครื่องทั้งหมด",2,"ใช้เวลาเกิน",False),("เดินเครื่องต่อเต็มกำลัง",1,"เสี่ยงเสียหาย",False)]),
             ("พบจุดยึดหลวม คุณเลือกอย่างไร?", [("หยุดเครื่องตามความปลอดภัย ขันตาม torque และตรวจซ้ำ",10,"แก้ตรงสาเหตุ",True),("ขันให้แน่นที่สุด",4,"อาจเกิน torque",False),("เพิ่มน้ำมันหล่อลื่น",2,"ไม่ตรงอาการ",False)]),
             ("เหลือเวลา 5 นาที คุณทำอะไร?", [("ทดสอบเดินเครื่องและบันทึกค่า vibration ก่อนส่งมอบ",10,"มีหลักฐานการซ่อม",True),("ข้ามการทดสอบ",2,"เสี่ยง",False),("ส่งมอบโดยแจ้งว่าเดี๋ยวค่อยตรวจ",1,"ยังไม่ยืนยัน",False)])
         ]),
        ("Invoice Anomaly", "พบใบแจ้งหนี้ 2 รายการที่ยอดและเลขอ้างอิงผิดปกติ",
         "Accounting", ["Analytical Thinking","Attention to Detail","Decision Making","Communication"], 2, 240, 800,
         [
             ("คุณจะตรวจอะไรเป็นอันดับแรก?", [("เทียบเลขอ้างอิง ยอด ภาษี และเอกสารต้นทาง",10,"ตรวจ cross-check",True),("อนุมัติรายการที่ดูปกติ",3,"อาจพลาดความผิดปกติ",False),("ลบรายการผิดปกติ",1,"ทำลายหลักฐาน",False)]),
             ("พบยอดซ้ำแต่ vendor ต่างกัน คุณทำอะไร?", [("พักรายการและขอหลักฐานจากผู้เกี่ยวข้อง",10,"ลดความเสี่ยงก่อนจ่าย",True),("จ่ายไปก่อน",1,"เสี่ยงจ่ายซ้ำ",False),("สรุปว่าเป็นทุจริตทันที",3,"ยังไม่มีหลักฐานพอ",False)]),
             ("การสื่อสารผลควรเป็นแบบใด?", [("รายงานข้อเท็จจริง หลักฐาน และสิ่งที่ต้องตรวจเพิ่ม",10,"ชัดเจนและตรวจสอบได้",True),("ส่งข้อความสั้นว่า 'มีปัญหา'",3,"ข้อมูลไม่พอ",False),("กล่าวหาบุคคลในทีม",1,"ไม่เหมาะสมและไม่มีหลักฐาน",False)])
         ]),
        ("Campaign Recovery", "แคมเปญออนไลน์ใช้เงินไป 60% แต่ยอด conversion ต่ำกว่าเป้า",
         "Business / Marketing", ["Analytical Thinking","Creativity","Planning","Decision Making"], 2, 270, 5000,
         [
             ("ก่อนเพิ่มงบ คุณควรดูอะไร?", [("แยก funnel และดู conversion ของแต่ละขั้น",10,"รู้ว่าคอขวดอยู่ตรงไหน",True),("เพิ่มงบอีกเท่าตัว",2,"เพิ่มความเสี่ยง",False),("หยุดทุกช่องทาง",3,"ตัดข้อมูลที่อาจมีประโยชน์",False)]),
             ("พบว่า landing page มี conversion ต่ำ คุณทำอะไร?", [("ทดสอบข้อความ/CTA แบบ A-B ด้วยงบจำกัด",10,"ทดลองอย่างวัดผลได้",True),("เปลี่ยนทุกอย่างพร้อมกัน",4,"แยกผลไม่ได้",False),("เพิ่มงบโฆษณา",2,"ไม่แก้คอขวด",False)]),
             ("ผลทดสอบดีขึ้นเล็กน้อย คุณวางแผนอย่างไร?", [("ขยายเฉพาะ variant ที่มีหลักฐานและติดตาม KPI",10,"ควบคุมความเสี่ยง",True),("เทงบทั้งหมดทันที",3,"เสี่ยงเกินข้อมูล",False),("เลิก campaign",1,"อาจเร็วเกินไป",False)])
         ]),
        ("Team Project Triage", "ทีม 4 คนมีงานด่วน 3 งานและเวลาจำกัด",
         "Computer Technology", ["Planning","Teamwork","Communication","Time Management"], 2, 240, 1000,
         [
             ("เริ่มต้นอย่างไร?", [("จัดลำดับงานตามผลกระทบและ deadline แล้วแบ่งเจ้าของงาน",10,"ทีมเห็นภาพเดียวกัน",True),("ให้ทุกคนทำทุกงาน",3,"งานซ้ำและไม่ชัดเจน",False),("เลือกงานที่ง่ายที่สุดก่อน",2,"ไม่คำนึงผลกระทบ",False)]),
             ("สมาชิกหนึ่งคนติดปัญหา คุณทำอะไร?", [("ขอข้อมูลสั้น ๆ แล้วจับคู่คนช่วยโดยไม่หยุดงานส่วนอื่น",10,"ใช้ทีมแก้ bottleneck",True),("ตำหนิว่าไม่เก่ง",1,"ทำลายการสื่อสาร",False),("ให้คนเดียวรับทั้งหมด",3,"เพิ่มคอขวด",False)]),
             ("ก่อนส่งงาน คุณทำอะไร?", [("checklist จุดสำคัญและสื่อสารสถานะ/ความเสี่ยง",10,"ลดความผิดพลาด",True),("ส่งทันทีเมื่อเสร็จบางส่วน",3,"เสี่ยงตกหล่น",False),("รอให้หัวหน้าตรวจทุกอย่าง",4,"เพิ่มคอขวด",False)])
         ]),
        ("Network Security Incident", "พบเครื่องหนึ่งส่ง traffic ผิดปกติแต่ระบบหลักยังทำงานได้",
         "Information Technology", ["Analytical Thinking","Decision Making","Technical Skill","Adaptability"], 4, 300, 3000,
         [
             ("การตอบสนองแรกที่เหมาะสม?", [("เก็บหลักฐานและจำกัดผลกระทบตาม incident procedure",10,"รักษาหลักฐานและลดความเสี่ยง",True),("ปิดเซิร์ฟเวอร์ทั้งหมด",3,"กระทบระบบมาก",False),("ลบ log",1,"ทำลายหลักฐาน",False)]),
             ("ข้อมูลใหม่บอกว่า traffic มาจาก service ที่ถูกต้องแต่ตั้งค่าผิด คุณทำอะไร?", [("ปรับ containment ตามหลักฐานและตรวจ configuration",10,"ปรับแผนตามข้อมูล",True),("ยืนยันว่าเป็นการโจมตี",2,"สรุปเร็วเกินไป",False),("ยกเลิก incident",4,"ยังต้องตรวจให้ครบ",False)]),
             ("หลังแก้ไขควรสรุปอะไร?", [("timeline, evidence, root cause, action และ prevention",10,"เรียนรู้จากเหตุการณ์",True),("แค่บอกว่าแก้แล้ว",3,"ไม่มีบทเรียน",False),("โทษคนตั้งค่า",1,"ไม่ช่วยป้องกันซ้ำ",False)])
         ]),
        ("Warehouse Stock Mismatch", "สต็อกจริงกับระบบต่างกัน 18 ชิ้นในรายการหนึ่ง",
         "Accounting", ["Attention to Detail","Analytical Thinking","Planning","Problem Solving"], 2, 300, 1200,
         [
             ("คุณจะเริ่มจากอะไร?", [("นับซ้ำและเทียบ movement ย้อนหลัง",10,"สร้างหลักฐานสองทาง",True),("ปรับยอดในระบบทันที",2,"แก้โดยไม่รู้สาเหตุ",False),("สั่งของเพิ่ม",1,"เพิ่มปัญหา",False)]),
             ("พบ movement หนึ่งรายการไม่มีเอกสาร คุณทำอะไร?", [("พักการปรับยอดและตามหาเอกสาร/ผู้รับผิดชอบ",10,"รักษาความถูกต้อง",True),("ลบทิ้ง",1,"ทำลายหลักฐาน",False),("เดาว่าเป็นของเสีย",3,"ยังไม่มีหลักฐาน",False)]),
             ("หลังพบสาเหตุ คุณทำอะไร?", [("ปรับยอดพร้อมบันทึกเหตุผลและเพิ่มจุดควบคุม",10,"แก้และป้องกันซ้ำ",True),("ปรับยอดอย่างเดียว",5,"แก้เฉพาะหน้า",False),("ไม่ต้องบันทึก",1,"ตรวจสอบย้อนหลังไม่ได้",False)])
         ]),
    ]
    for title, scenario, dep, skill_names, difficulty, limit, budget, steps in specs:
        if _mission_exists(title):
            continue
        m = Mission(
            title=title, scenario=scenario, department=D[dep],
            difficulty=difficulty, time_limit=limit, budget=budget, discovery=True
        )
        m.skills=[S[n] for n in skill_names]
        db.session.add(m)
        db.session.flush()
        for idx,(prompt,choices) in enumerate(steps,1):
            _add_step(m, idx, prompt, choices)

def seed_database():
    # Upgrade-safe seeding: existing installations receive missing Phase 2 data.
    D = {name: _get_or_create(Department, name, description=desc) for name,desc in DEPARTMENTS}
    S = {name: _get_or_create(Skill, name, description=desc) for name,desc in SKILLS}

    # Keep the original foundation missions if present, and add richer multi-step missions.
    if Mission.query.count() == 0:
        basic = [
            ("Network Outage","ห้องปฏิบัติการต่อ Internet ไม่ได้","Information Technology",["Problem Solving","Analytical Thinking","Technical Skill","Decision Making"]),
            ("Debug the Program","โปรแกรมคำนวณยอดขายให้ผลผิด","Computer Technology",["Logical Thinking","Problem Solving","Technical Skill"]),
            ("Power Failure","อุปกรณ์ในห้องไม่จ่ายไฟ","Electrical",["Problem Solving","Technical Skill","Attention to Detail"]),
            ("Sensor Fault","Sensor ให้ค่าสัญญาณผิดปกติ","Electronics",["Analytical Thinking","Technical Skill","Decision Making"]),
            ("Car Won't Start","รถสตาร์ทไม่ติด","Automotive",["Problem Solving","Technical Skill","Planning"]),
            ("Production Delay","สายการผลิตหยุดชะงัก","Mechanical",["Planning","Problem Solving","Decision Making"]),
            ("Expense Audit","ตรวจหาความผิดปกติในค่าใช้จ่าย","Accounting",["Analytical Thinking","Attention to Detail","Decision Making"]),
            ("Campaign Rescue","ยอดขาย Campaign ต่ำกว่าคาด","Business / Marketing",["Analytical Thinking","Creativity","Planning"]),
        ]
        for title,scenario,dep,skill_names in basic:
            m=Mission(title=title,scenario=scenario,department=D[dep],difficulty=1,time_limit=240,budget=1000,discovery=True)
            m.skills=[S[x] for x in skill_names]
            db.session.add(m); db.session.flush()
            _add_step(m,1,"คุณควรเริ่มจากอะไร?",[
                ("เก็บข้อมูลและตรวจสาเหตุพื้นฐานก่อน",10,"ได้ข้อมูลเพิ่ม",True),
                ("เปลี่ยนอุปกรณ์ทันที",4,"อาจเสียทรัพยากร",False),
                ("เดาสาเหตุจากอาการอย่างเดียว",1,"ข้อมูลไม่พอ",False),
            ])

    _add_advanced_missions(D,S)

    careers = [
        ("Network Technician","ดูแลและแก้ปัญหาเครือข่าย","Information Technology",["Problem Solving","Technical Skill","Analytical Thinking"]),
        ("Software Developer","ออกแบบและพัฒนาซอฟต์แวร์","Computer Technology",["Logical Thinking","Problem Solving","Technical Skill"]),
        ("Electrical Technician","ติดตั้งและแก้ปัญหาระบบไฟฟ้า","Electrical",["Technical Skill","Attention to Detail","Problem Solving"]),
        ("Electronics Technician","วิเคราะห์วงจรและอุปกรณ์อิเล็กทรอนิกส์","Electronics",["Technical Skill","Analytical Thinking","Attention to Detail"]),
        ("Automotive Technician","วิเคราะห์และซ่อมระบบรถยนต์","Automotive",["Technical Skill","Problem Solving","Planning"]),
        ("Maintenance Technician","ดูแลเครื่องจักรและการบำรุงรักษา","Mechanical",["Problem Solving","Technical Skill","Planning"]),
        ("Accounting Officer","จัดการและวิเคราะห์ข้อมูลทางบัญชี","Accounting",["Analytical Thinking","Attention to Detail","Planning"]),
        ("Marketing Specialist","วิเคราะห์ตลาดและวางแผน Campaign","Business / Marketing",["Analytical Thinking","Creativity","Communication"]),
        ("QA / Test Engineer","ออกแบบการทดสอบและวิเคราะห์ defect","Computer Technology",["Attention to Detail","Analytical Thinking","Logical Thinking"]),
        ("Automation Technician","ดูแลระบบควบคุมและ automation","Electrical",["Technical Skill","Logical Thinking","Problem Solving"]),
        ("Data Analyst","วิเคราะห์ข้อมูลเพื่อสนับสนุนการตัดสินใจ","Information Technology",["Analytical Thinking","Logical Thinking","Attention to Detail"]),
        ("Operations Planner","วางแผนทรัพยากรและงานปฏิบัติการ","Business / Marketing",["Planning","Time Management","Decision Making"]),
    ]
    for name,desc,dep,skill_names in careers:
        c=Career.query.filter_by(name=name).first()
        if not c:
            c=Career(name=name,description=desc,department=D[dep],skills=[S[x] for x in skill_names])
            db.session.add(c)

    achievement_names = [
        ("First Mission",1),("10 Missions",10),("No Hint",1),("Fast Solver",1),
        ("Perfect Score",1),("Problem Solver",3),("Team Player",1),("Explorer",5),
        ("Skill Master",5),("Discovery Complete",10),
    ]
    for name,threshold in achievement_names:
        a=Achievement.query.filter_by(name=name).first()
        if not a:
            db.session.add(Achievement(name=name,description=f"Achievement: {name}",threshold=threshold))

    for s in S.values():
        for level in (1,2,3):
            title=f"{s.name}: Level {level}"
            if not LearningTopic.query.filter_by(title=title).first():
                db.session.add(LearningTopic(title=title,skill_id=s.id,level=level,
                    description=f"แบบฝึก {s.name} ระดับ {level} จากหลักฐาน Mission"))

    demo = [
        ("student@example.com","Student123!","student","Demo Student"),
        ("teacher@example.com","Teacher123!","teacher","Demo Teacher"),
        ("admin@example.com","Admin123!","admin","Demo Admin"),
    ]
    for email,pw,role,name in demo:
        if not User.query.filter_by(email=email).first():
            u=User(email=email,name=name,role=role); u.set_password(pw)
            if role=="student": u.departments=[D["Information Technology"]]
            db.session.add(u)
    avatar_items = [
        ("จิ้งจอกนักสำรวจ", "สัตว์คู่หูเริ่มต้นของ V-SKILL", "species", "fox", "common", "missions", 0),
        ("แมวนักคิด", "ปลดล็อกเมื่อทำ Mission ครบ 2 ครั้ง", "species", "cat", "common", "missions", 2),
        ("กระต่ายสายสปีด", "ปลดล็อกเมื่อทำ Mission ครบ 4 ครั้ง", "species", "rabbit", "rare", "missions", 4),
        ("แพนด้านักวางแผน", "ปลดล็อกเมื่อทำ Mission ครบ 6 ครั้ง", "species", "panda", "rare", "missions", 6),
        ("หมีผู้พิทักษ์", "ปลดล็อกเมื่อทำ Mission ครบ 8 ครั้ง", "species", "bear", "epic", "missions", 8),
        ("เพนกวินโปร", "ปลดล็อกเมื่อทำ Mission ครบ 10 ครั้ง", "species", "penguin", "epic", "missions", 10),
        ("หมวกดาวรุ่ง", "หมวกสำหรับคนที่เริ่มเก็บผลงาน", "hat", "star_hat", "common", "missions", 1),
        ("หูฟัง Neon", "เพิ่มสไตล์ให้คู่หู", "hat", "headphones", "rare", "missions", 3),
        ("ผ้าพันคอผู้กล้า", "ปลดล็อกจากภารกิจที่ทำได้ดี", "accessory", "scarf", "rare", "perfect", 1),
        ("ประกายแชมป์", "ตราพิเศษสำหรับผู้ทำภารกิจคะแนนเต็ม", "badge", "spark_badge", "epic", "perfect", 2),
        ("มงกุฎ Explorer", "สำหรับผู้ที่ปลดล็อก Achievement หลายรายการ", "hat", "crown", "legendary", "achievements", 5),
    ]
    for name,desc,slot,key,rarity,ut,uv in avatar_items:
        if not AvatarItem.query.filter_by(name=name).first():
            db.session.add(AvatarItem(name=name,description=desc,slot=slot,asset_key=key,rarity=rarity,unlock_type=ut,unlock_value=uv))

    # Curated standalone Skill Items supplied for Avatar Studio.
    from core.avatar_items import SKILL_ITEMS
    for name,desc,slot,key,rarity,ut,uv,_skill_id in SKILL_ITEMS:
        if not AvatarItem.query.filter_by(name=name).first():
            db.session.add(AvatarItem(name=name,description=desc,slot=slot,asset_key=key,rarity=rarity.lower(),unlock_type=ut,unlock_value=uv))

    db.session.commit()

    # New department-selection system. Registration no longer chooses a department;
    # students choose/change it after login. The catalog is upgrade-safe.
    from core.department_missions import DEPARTMENT_CATALOG, ensure_department_missions
    D, S = ensure_department_missions(D, S)

    # Replace the legacy 3-step repetitive bank with 10-question exam-style banks.
    from core.question_engine import upgrade_all_department_missions
    upgrade_all_department_missions()

    # Migrate only the bundled demo account to the new catalog. Real users with
    # legacy departments are asked to choose their new path instead of being changed silently.
    demo_student=User.query.filter_by(email="student@example.com").first()
    if demo_student and not any(d.name in DEPARTMENT_CATALOG for d in (demo_student.departments or [])):
        demo_student.departments=[D["เทคโนโลยีคอมพิวเตอร์"]]
    db.session.commit()

    # Add useful department-specific careers without deleting legacy careers.
    extra_careers = [
        ("Python Developer","พัฒนาโปรแกรมและระบบด้วย Python","เทคโนโลยีคอมพิวเตอร์",["Programming","Logical Thinking","Problem Solving"]),
        ("Network Administrator","ดูแลเครือข่ายและระบบโครงสร้างพื้นฐาน","เทคโนโลยีคอมพิวเตอร์",["Network","Technical Skill","Problem Solving"]),
        ("PLC Technician","ติดตั้งและแก้ปัญหาระบบ PLC และระบบควบคุม","ไฟฟ้า",["PLC","Motor Control","Problem Solving"]),
        ("EV Technician","ตรวจวิเคราะห์และบำรุงรักษาระบบรถไฟฟ้า","ช่างยนต์",["EV Systems","Automotive Electronics","Technical Skill"]),
        ("CNC Technician","ควบคุมเครื่องจักร CNC และตรวจคุณภาพชิ้นงาน","เทคนิคการผลิต",["CNC","Metrology","Quality"]),
        ("UI/UX Designer","ออกแบบประสบการณ์และส่วนติดต่อผู้ใช้","ดิจิทัล/กราฟิก",["UI/UX","User Research","Visual Design"]),
        ("Graphic Designer","สร้างงานภาพและระบบแบรนด์สำหรับสื่อดิจิทัล","ดิจิทัล/กราฟิก",["Graphic Design","Branding","Creative Thinking"]),
        ("Chef / Kitchen Supervisor","จัดการครัว ต้นทุน คุณภาพ และความปลอดภัยอาหาร","อาหาร/คหกรรม",["Food Safety","Kitchen Management","Costing"]),
        ("Site Supervisor","ควบคุมงานก่อสร้าง คุณภาพ และความปลอดภัย","ก่อสร้าง",["Construction","Site Safety","Planning"]),
        ("Logistics Planner","วางแผนคลังสินค้า เส้นทาง และซัพพลายเชน","โลจิสติกส์",["Logistics","Route Planning","Supply Chain"]),
        ("Hotel Operations","จัดการงานบริการและประสบการณ์ลูกค้า","การโรงแรมและท่องเที่ยว",["Hospitality","Customer Service","Planning"]),
    ]
    for name,desc,dep,skill_names in extra_careers:
        c=Career.query.filter_by(name=name).first()
        if not c:
            c=Career(name=name,description=desc,department=D[dep],skills=[S[x] for x in skill_names])
            db.session.add(c)
    db.session.commit()

    # Upgrade-safe Skill Perks catalog; independent from legacy AvatarItem skills.
    from core.skill_perks import ensure_catalog
    ensure_catalog()
