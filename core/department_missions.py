"""
V-SKILL Department Mission Catalog
Real-world, department-specific mission templates. 8 unique missions per department,
difficulty 1-4, designed to be seeded into the existing Mission/MissionStep schema.
"""
from database.database import db
from database.models import Department, Skill, Mission, MissionStep, MissionChoice

DEPARTMENT_CATALOG = {
    "เทคโนโลยีคอมพิวเตอร์": {
        "desc":"Python, Network, Hardware, Database, Logic และงานพัฒนาระบบ",
        "skills":["Programming","Network","Hardware","Database","Logical Thinking","Problem Solving","Analytical Thinking","Technical Skill"],
        "missions":[
            ("Python Debugging Lab","โปรแกรม Python คำนวณยอดขายถูกในข้อมูลทั่วไป แต่ผิดเมื่อมีรายการคืนสินค้าและส่วนลดซ้อนกัน",1,
             ["Programming","Logical Thinking","Problem Solving"],
             ["ตรวจ test case แยกกรณีคืนสินค้าและส่วนลดก่อนแก้เงื่อนไข","เขียน test ที่ครอบคลุมกรณีปกติ ศูนย์ และค่าติดลบ","ทดสอบด้วยข้อมูลใหม่หลายชุดและตรวจผลกับค่าที่คาด"]),
            ("API Failure Investigation","ระบบเว็บเรียก API สำเร็จเป็นส่วนใหญ่ แต่บางคำขอได้ 500 เมื่อมีข้อมูลจำนวนมาก",2,
             ["Programming","Analytical Thinking","Problem Solving"],
             ["ดู server log และ request ที่ล้มเหลวก่อนแก้โค้ด","จำลอง payload ขนาดใหญ่เพื่อหาขอบเขตที่ทำให้เกิดปัญหา","เพิ่ม validation และทดสอบทั้งข้อมูลเล็กและใหญ่"]),
            ("Database Query Bottleneck","หน้ารายงานช้าลงเมื่อข้อมูลเพิ่มจากหลักพันเป็นหลักล้านแถว",2,
             ["Database","Analytical Thinking","Technical Skill"],
             ["ดู execution plan และจำนวนแถวที่ query อ่านจริง","ตรวจ index และเงื่อนไข filter ที่ใช้บ่อยก่อนเพิ่ม index","ทดสอบ query เดิมกับข้อมูลจำลองขนาดใกล้ production"]),
            ("Network Dead Zone","ห้องปฏิบัติการบางจุดหลุด Wi-Fi เฉพาะช่วงพักที่มีผู้ใช้หนาแน่น",2,
             ["Network","Problem Solving","Analytical Thinking"],
             ["เทียบจำนวน client, channel utilization และ signal ในช่วงเกิดปัญหา","ตรวจ AP, uplink และ DHCP log แยกตามช่วงเวลา","ปรับ configuration ทีละจุดแล้ววัดผลก่อน-หลัง"]),
            ("PC Hardware Diagnosis","คอมพิวเตอร์ดับเองเมื่อรันงานหนัก แต่เปิดเอกสารทั่วไปได้ปกติ",3,
             ["Hardware","Technical Skill","Analytical Thinking"],
             ["เก็บอุณหภูมิ CPU/GPU และแรงดันขณะโหลดก่อนเปลี่ยนชิ้นส่วน","ทดสอบโหลด CPU/GPU แยกกันเพื่อแยกสาเหตุ","ตรวจ PSU, การระบายความร้อน และ event log แล้วทดสอบซ้ำ"]),
            ("Authentication Bug Hunt","ผู้ใช้บางรายหลุดออกจากระบบหลังเปิดหลายแท็บพร้อมกัน",3,
             ["Programming","Logical Thinking","Attention to Detail"],
             ["ตรวจ session/cookie และลำดับ request ของกรณีที่เกิดปัญหา","จำลองหลายแท็บและ concurrent request ก่อนแก้ state","เพิ่ม test สำหรับ login, refresh, logout และ session expiry"]),
            ("Inventory Race Condition","ระบบสต็อกติดลบเมื่อผู้ใช้สองคนเบิกชิ้นส่วนเดียวกันเกือบพร้อมกัน",4,
             ["Database","Programming","Problem Solving","Attention to Detail"],
             ["จำลอง concurrent transaction เพื่อยืนยัน race condition","ใช้ transaction/locking หรือ atomic update พร้อมตรวจ stock ก่อน commit","ทดสอบพร้อมกันหลายคำขอและยืนยันว่า stock ไม่ติดลบ"]),
            ("Network Segmentation Design","ห้องเรียนต้องแยกเครือข่ายนักเรียน ครู และอุปกรณ์ IoT โดยยังให้บริการที่จำเป็นร่วมกัน",4,
             ["Network","Logical Thinking","Planning","Technical Skill"],
             ["กำหนด VLAN และสิทธิ์การสื่อสารตามความต้องการจริง","เขียน access rule แบบ least privilege และกำหนดจุดตรวจสอบ","ทดสอบทั้ง allowed/blocked traffic และแผน fallback"]),
        ],
    },
    "ไฟฟ้า": {
        "desc":"วงจรไฟฟ้า การคำนวณ PLC Motor ระบบควบคุม และความปลอดภัย",
        "skills":["Electrical Calculation","Circuit","PLC","Motor Control","Safety","Technical Skill","Problem Solving","Attention to Detail"],
        "missions":[
            ("ตู้ควบคุมเบรกเกอร์ตัด","ตู้ควบคุมตัดวงจรเมื่อโหลดทำงานพร้อมกันหลายตัว",1,["Electrical Calculation","Safety","Problem Solving"],["ตัดแหล่งจ่ายและยืนยันสถานะปลอดภัยก่อนตรวจ","วัดกระแสแต่ละโหลดและเทียบกับพิกัดอุปกรณ์","คำนวณโหลดรวมและทดสอบภายใต้เงื่อนไขที่ควบคุมได้"]),
            ("Motor Starting Current","มอเตอร์กินกระแสสูงมากช่วงสตาร์ตและทำให้แรงดันตก",2,["Motor Control","Electrical Calculation","Analytical Thinking"],["วัดกระแสสตาร์ตและแรงดันตกโดยใช้เครื่องมือที่เหมาะสม","เทียบวิธีสตาร์ตและขนาดสาย/อุปกรณ์กับโหลด","เลือกวิธีควบคุมที่ลดผลกระทบและทดสอบก่อนใช้งานจริง"]),
            ("PLC Input Mismatch","PLC รับสัญญาณ sensor เป็น 1 ทั้งที่ชิ้นงานยังไม่ผ่านจุดตรวจ",2,["PLC","Problem Solving","Attention to Detail"],["ตรวจ wiring และสถานะ input พร้อมเทียบกับสัญญาณจริง","ตรวจ noise, debounce และ logic ของ input","ทดสอบหลายรอบและบันทึก false trigger ก่อนสรุป"]),
            ("Three-Phase Imbalance","มอเตอร์สามเฟสมีอุณหภูมิสูงขึ้นและกระแสแต่ละเฟสไม่เท่ากัน",3,["Electrical Calculation","Motor Control","Analytical Thinking"],["วัดแรงดันและกระแสทั้งสามเฟสตามขั้นตอนความปลอดภัย","เปรียบเทียบ imbalance กับค่าที่ผู้ผลิตกำหนด","แก้ต้นเหตุแล้วทดสอบภายใต้โหลดและบันทึกค่าก่อนส่งมอบ"]),
            ("Control Circuit Failure","คอนแทคเตอร์ทำงานมือได้แต่ไม่ทำงานเมื่อกด Start",3,["Circuit","PLC","Problem Solving"],["ไล่สัญญาณจากปุ่ม Start ผ่าน interlock ถึง coil","ตรวจ auxiliary contact และเงื่อนไข interlock","ทดสอบลำดับ start/stop และ emergency stop หลังแก้"]),
            ("Power Factor Improvement","โรงงานมีค่า power factor ต่ำและต้องการลด reactive power โดยไม่กระทบโหลด",3,["Electrical Calculation","Analytical Thinking","Planning"],["เก็บค่า kW, kVAR และ power factor ตามช่วงโหลด","คำนวณขนาดการชดเชยจากข้อมูลจริง ไม่เลือกจากการเดา","ทดสอบการชดเชยและเฝ้าดูความเสี่ยง resonance/overcompensation"]),
            ("PLC Sequence Race","เครื่องจักรทำงานผิดลำดับเมื่อ operator กดคำสั่งเร็วต่อเนื่อง",4,["PLC","Logical Thinking","Problem Solving"],["บันทึก timestamp และ state transition ของ sequence","กำหนด interlock/state machine ให้คำสั่งที่ไม่ถูกจังหวะไม่ทำงาน","ทดสอบ rapid input และ recovery หลังหยุดฉุกเฉิน"]),
            ("Motor Protection Coordination","ต้องตั้ง protection ของมอเตอร์หลายตัวให้แยกตัดเมื่อเกิด fault",4,["Motor Control","Electrical Calculation","Safety"],["รวบรวมกระแสพิกัดและลักษณะโหลดของแต่ละมอเตอร์","จัดลำดับ protection ให้จุดใกล้ fault ตัดก่อน","ทดสอบ coordination ตามข้อกำหนดโดยไม่เพิ่มพิกัดอุปกรณ์แบบสุ่ม"]),
        ],
    },
    "อิเล็กทรอนิกส์/เมคคาทรอนิกส์": {
        "desc":"วงจร เซนเซอร์ไมโครคอนโทรลเลอร์ ระบบอัตโนมัติ และการควบคุม",
        "skills":["Electronics","Sensors","Microcontroller","Control Systems","Technical Skill","Problem Solving","Analytical Thinking"],
        "missions":[
            ("Sensor Calibration","เซนเซอร์วัดระยะมี error เพิ่มขึ้นเมื่ออุณหภูมิเปลี่ยน",1,["Sensors","Analytical Thinking","Technical Skill"],["เก็บค่าจริงเทียบ reference หลายอุณหภูมิ","แยก error จาก sensor และสภาพแวดล้อมก่อนสร้าง calibration","ทดสอบ calibration กับข้อมูลที่ไม่ใช้ตอนปรับค่า"]),
            ("Arduino Brownout","บอร์ดไมโครคอนโทรลเลอร์รีเซตเมื่อ servo เริ่มหมุน",1,["Microcontroller","Electronics","Problem Solving"],["วัดแรงดันตกช่วง servo start และตรวจแหล่งจ่าย","แยก power path ของโหลดและ controller ตามสเปก","ทดสอบการทำงานซ้ำหลายรอบและตรวจ log reset"]),
            ("Noise Filter","สัญญาณ digital เด้งหลายครั้งจากสวิตช์กลไก",2,["Electronics","Sensors","Logical Thinking"],["ดู waveform เพื่อยืนยัน bounce ก่อนเลือกวิธีแก้","เลือก debounce ที่เหมาะกับเวลาตอบสนองของระบบ","ทดสอบจำนวน false trigger ก่อนและหลังปรับ"]),
            ("PID Temperature Control","ระบบควบคุมอุณหภูมิ overshoot สูงและใช้เวลานานกว่าจะนิ่ง",2,["Control Systems","Analytical Thinking","Technical Skill"],["เก็บ response ของระบบก่อนปรับ PID","ปรับ gain ทีละส่วนและวัด overshoot/settling time","ทดสอบ setpoint หลายค่าและตรวจ stability"]),
            ("Motor Encoder Fault","ค่ารอบจาก encoder ขาดเป็นช่วง ๆ เมื่อสายเคเบิลขยับ",3,["Sensors","Control Systems","Problem Solving"],["ตรวจสัญญาณและ connector ระหว่างขยับสายอย่างปลอดภัย","แยกปัญหาสายสัญญาณ, noise และ input circuit","ทดสอบหลายตำแหน่งและบันทึก error rate"]),
            ("PLC Conveyor Cell","เซนเซอร์สองตัวบนสายพานให้ลำดับสัญญาณไม่สอดคล้องกับตำแหน่งชิ้นงาน",3,["Control Systems","Sensors","Logical Thinking"],["วัด timestamp ของ sensor ทั้งสองตัวเทียบกับระยะจริง","ตรวจ state transition และเงื่อนไข timeout","ทดสอบชิ้นงานหลายความเร็วและตรวจกรณี sensor ค้าง"]),
            ("Robotic Interlock","แขนกลต้องหยุดเมื่อประตูนิรภัยเปิด แม้มีคำสั่งเคลื่อนที่ค้าง",4,["Control Systems","Safety","Logical Thinking"],["กำหนด safety interlock เป็นเงื่อนไขที่ตัด motion ได้ทันที","ทดสอบ door open ระหว่างทุก state ของ motion","ตรวจ recovery ไม่ให้แขนเริ่มเองเมื่อประตูปิด"]),
            ("Multi-Sensor Fusion","ต้องรวมข้อมูล sensor 3 ตัวที่มี noise ต่างกันเพื่อประเมินตำแหน่ง",4,["Sensors","Analytical Thinking","Control Systems"],["ประเมินความคลาดเคลื่อนและความถี่ของแต่ละ sensor","เลือกวิธีกรอง/ให้น้ำหนักตามคุณภาพข้อมูล","ทดสอบกับข้อมูลจริงและกรณี sensor ตัวหนึ่งหาย"]),
        ],
    },
    "ช่างยนต์": {
        "desc":"เครื่องยนต์ EV ระบบเบรก diagnostics และการบำรุงรักษา",
        "skills":["Engine Diagnostics","EV Systems","Brake Systems","Automotive Electronics","Technical Skill","Problem Solving","Attention to Detail"],
        "missions":[
            ("Cold Start Diagnosis","รถสตาร์ตยากเฉพาะตอนเครื่องเย็น",1,["Engine Diagnostics","Problem Solving","Attention to Detail"],["เก็บอาการและตรวจแบตเตอรี่/ระบบพื้นฐานก่อน","เปรียบเทียบ sensor และแรงดันช่วงเย็นกับช่วงร้อน","ทดสอบซ้ำตามเงื่อนไขเดิมและยืนยันสาเหตุก่อนเปลี่ยนอะไหล่"]),
            ("Brake Pulling","รถดึงไปด้านหนึ่งขณะเบรก",1,["Brake Systems","Technical Skill","Safety"],["ตรวจความปลอดภัยและสภาพระบบเบรกทั้งสองข้าง","เปรียบเทียบแรงเบรกและสภาพผ้าเบรก/คาลิเปอร์","ทดสอบเบรกในพื้นที่ปลอดภัยและตรวจผลหลังแก้"]),
            ("OBD Sensor Anomaly","ค่า sensor OBD แกว่งผิดปกติแต่รถยังขับได้",2,["Automotive Electronics","Engine Diagnostics","Analytical Thinking"],["อ่าน code และข้อมูล live data ก่อนสรุป","เทียบ sensor ที่เกี่ยวข้องและ wiring/connector","ทดสอบภายใต้เงื่อนไขที่ทำให้เกิดอาการและยืนยัน root cause"]),
            ("EV Range Estimate","ระยะทางคงเหลือของ EV แกว่งหลังเปลี่ยนรูปแบบการขับ",2,["EV Systems","Analytical Thinking","Technical Skill"],["แยกค่าประมาณ range จากพลังงานที่ใช้จริง","ดูข้อมูลย้อนหลังหลายรอบและเงื่อนไขการขับ","สรุปจากแนวโน้ม ไม่ตัดสินแบตจากตัวเลขครั้งเดียว"]),
            ("Cooling System Fault","อุณหภูมิเครื่องสูงขึ้นเฉพาะรถติดนาน",3,["Engine Diagnostics","Technical Skill","Problem Solving"],["ตรวจระดับน้ำหล่อเย็น การไหล และพัดลมตามขั้นตอน","เทียบอุณหภูมิช่วงรถวิ่งกับช่วงจอด","ทดสอบภายใต้เงื่อนไขจริงและตรวจรอยรั่วหลังแก้"]),
            ("EV Isolation Alert","รถ EV แจ้งเตือน isolation fault หลังล้างรถ",3,["EV Systems","Automotive Electronics","Safety"],["ปฏิบัติตามขั้นตอนความปลอดภัยแรงดันสูงก่อนตรวจ","แยกวงจรและตรวจความชื้น/ฉนวนด้วยวิธีที่ผู้ผลิตกำหนด","ยืนยันค่า isolation กลับสู่เกณฑ์ก่อนคืนรถ"]),
            ("Intermittent No-Start","รถบางครั้งสตาร์ตไม่ติดและกลับมาติดได้เอง",4,["Engine Diagnostics","Automotive Electronics","Problem Solving"],["บันทึกเงื่อนไขตอนเกิดอาการแทนการเปลี่ยนอะไหล่ทันที","ตรวจ signal ระหว่าง fault และทำ wiggle/heat test อย่างเหมาะสม","สร้างหลักฐานซ้ำได้ก่อนยืนยันชิ้นส่วนเสีย"]),
            ("ADAS Calibration","เปลี่ยนชิ้นส่วนหน้ารถแล้วระบบช่วยเบรกเตือนผิดปกติ",4,["Automotive Electronics","Technical Skill","Attention to Detail"],["ตรวจ alignment และเงื่อนไข calibration ตามผู้ผลิต","ทำ calibration ด้วยขั้นตอนและ target ที่ถูกต้อง","ทดสอบบนพื้นที่ควบคุมและตรวจ error code ก่อนส่งมอบ"]),
        ],
    },
    "เทคนิคการผลิต": {
        "desc":"CNC การผลิต วัสดุ การวัด CAD และคุณภาพ",
        "skills":["CNC","Manufacturing","Metrology","CAD","Materials","Quality","Planning","Technical Skill"],
        "missions":[
            ("CNC Tool Wear","ขนาดชิ้นงานเริ่มคลาดเมื่อผลิตต่อเนื่องหลายชั่วโมง",1,["CNC","Quality","Metrology"],["เก็บขนาดชิ้นงานตามรอบและตรวจสภาพ tool","แยกแนวโน้ม tool wear จากความคลาดอื่น","กำหนดจุดเปลี่ยน tool จากข้อมูลและทดสอบชิ้นแรก"]),
            ("Material Selection","ต้องเลือกวัสดุสำหรับชิ้นส่วนที่รับแรงและต้องควบคุมต้นทุน",1,["Materials","Analytical Thinking","Decision Making"],["ระบุโหลด สภาพแวดล้อม และข้อกำหนดก่อนเลือกวัสดุ","เปรียบเทียบ strength, machinability และต้นทุน","ทำ prototype/test ตามเกณฑ์ก่อนผลิตจำนวนมาก"]),
            ("Measurement Error","ชิ้นงานสองเครื่องวัดให้ค่าไม่เท่ากัน",2,["Metrology","Quality","Attention to Detail"],["ตรวจ calibration และวิธีจับชิ้นงานของเครื่องมือ","ทำ repeatability/reproducibility test","กำหนดวิธีวัดมาตรฐานและบันทึก uncertainty ที่เหมาะสม"]),
            ("CAD Revision Control","ช่างผลิตใช้แบบ CAD คนละ revision ทำให้รูเจาะผิดตำแหน่ง",2,["CAD","Quality","Attention to Detail"],["ตรวจ revision และ drawing release ก่อนเริ่มผลิต","กำหนด single source of truth และ traceability","ทดสอบการควบคุมเอกสารด้วยการเปลี่ยน revision จำลอง"]),
            ("Production Bottleneck","ไลน์ผลิตทำงานไม่ทันเป้าแต่เครื่องส่วนใหญ่มีเวลาว่าง",3,["Manufacturing","Planning","Analytical Thinking"],["เก็บ cycle time และ queue time แยกแต่ละขั้น","ระบุ bottleneck จากข้อมูลจริงก่อนเพิ่มคน/เครื่อง","ทดลองปรับลำดับงานและวัด throughput ก่อน-หลัง"]),
            ("Surface Finish Issue","ผิวชิ้นงานหยาบขึ้นเฉพาะบางล็อต",3,["CNC","Materials","Quality"],["แยกข้อมูลตาม tool, material, speed และช่วงเวลา","ตรวจ parameter และสภาพ tool ก่อนปรับ","ทำชิ้นทดสอบและยืนยันค่า roughness ตามเกณฑ์"]),
            ("Statistical Process Control","ค่าเส้นผ่านศูนย์กลางยังอยู่ใน spec แต่ control chart เริ่มมี trend",4,["Quality","Metrology","Analytical Thinking"],["ดู trend และ control limit ไม่ดูแค่ค่าเฉลี่ย","ตรวจปัจจัยที่เปลี่ยนตามเวลา เช่น tool และอุณหภูมิ","วาง preventive action ก่อนหลุด spec และติดตามผล"]),
            ("Flexible Production Plan","มี order ด่วนแทรกและวัตถุดิบหลักส่งล่าช้า",4,["Planning","Manufacturing","Decision Making"],["จัดลำดับงานตาม deadline, setup และวัตถุดิบที่มีจริง","สร้างแผนสำรองและคำนวณผลกระทบของแต่ละทางเลือก","สื่อสาร trade-off และติดตามแผนด้วย milestone"]),
        ],
    },
    "บริหารธุรกิจ": {
        "desc":"การขาย บัญชี การตลาด การจัดการ และการวิเคราะห์ธุรกิจ",
        "skills":["Sales","Accounting","Marketing","Business Analytics","Decision Making","Communication","Planning","Customer Focus"],
        "missions":[
            ("Sales Conversion Drop","จำนวนผู้สนใจเท่าเดิมแต่ conversion ลดลง",1,["Sales","Business Analytics","Problem Solving"],["แยก funnel ตั้งแต่ lead ถึงปิดการขาย","ดูว่าขั้นตอนไหนมี drop-off และตรวจกลุ่มลูกค้า","ทดลองปรับจุดคอขวดและวัดผลด้วย KPI เดิม"]),
            ("Invoice Reconciliation","ยอดรวมตรงแต่รายการย่อยบางรายการไม่ตรงกับเอกสาร",1,["Accounting","Attention to Detail","Analytical Thinking"],["กระทบยอดระดับรายการและตรวจเอกสารต้นทาง","แยกส่วนต่างตามสาเหตุและช่วงเวลา","แก้รายการพร้อมบันทึกหลักฐานและตรวจซ้ำ"]),
            ("Customer Complaint Triage","ลูกค้าร้องเรียนเรื่องส่งของช้าและทีมมีข้อมูลหลายระบบ",2,["Customer Focus","Communication","Analytical Thinking"],["รวบรวม timeline จากข้อมูลที่ตรวจสอบได้","แยกสาเหตุที่ควบคุมได้และ dependency ภายนอก","สื่อสารแนวทางแก้และติดตาม SLA หลังแก้"]),
            ("Budget Forecast","โครงการใช้เงิน 70% ทั้งที่เวลาเพิ่งผ่าน 45%",2,["Accounting","Planning","Business Analytics"],["แยก actual, committed และค่าใช้จ่ายที่ยังไม่เกิด","ทำ forecast ค่าใช้จ่ายที่เหลือหลายกรณี","เลือก action จาก forecast และความเสี่ยง ไม่ดู % เดียว"]),
            ("Campaign Experiment","ต้องเลือกระหว่างข้อความโฆษณา 2 แบบด้วยงบจำกัด",3,["Marketing","Business Analytics","Planning"],["กำหนด metric และกลุ่มทดลองให้เทียบกันได้","รัน A/B test โดยควบคุมตัวแปรสำคัญ","ตัดสินจากผลและความไม่แน่นอนก่อนขยายงบ"]),
            ("Pricing Decision","ยอดขายเพิ่มหลังลดราคาแต่กำไรต่อหน่วยลดลงมาก",3,["Business Analytics","Decision Making","Accounting"],["ดู contribution margin และ volume แยกตามสินค้า","จำลองหลายราคาและผลต่อกำไร","เลือก price strategy จากกำไรและเป้าหมายระยะยาว"]),
            ("Demand Forecast Shock","ยอดสั่งซื้อพุ่งกะทันหันและคลังมีของไม่พอ",4,["Business Analytics","Planning","Decision Making"],["แยก demand spike จากข้อมูลผิดหรือโปรโมชั่น","จัดลำดับลูกค้า/สินค้าและคำนวณ stockout impact","วาง replenishment plan พร้อม scenario และ trigger"]),
            ("Business Risk Review","ทางเลือกหนึ่งกำไรคาดการณ์สูงกว่าแต่ข้อมูลไม่แน่นอน",4,["Decision Making","Business Analytics","Risk Management"],["ระบุ assumption และช่วงความไม่แน่นอน","เปรียบเทียบ expected outcome กับ downside","กำหนดเงื่อนไขหยุด/ทบทวนก่อนตัดสินใจ"]),
        ],
    },
    "ดิจิทัล/กราฟิก": {
        "desc":"Design, UI/UX, Branding, Creative และงานสื่อดิจิทัล",
        "skills":["UI/UX","Graphic Design","Branding","Creative Thinking","User Research","Communication","Visual Design","Problem Solving"],
        "missions":[
            ("UI Navigation Test","ผู้ใช้บอกว่าหน้าจอสวยแต่หาฟังก์ชันสำคัญไม่เจอ",1,["UI/UX","User Research","Problem Solving"],["ทดสอบ task จริงและสังเกตจุดที่ผู้ใช้ติด","จัดลำดับปัญหาตามผลกระทบก่อนแก้","ทำ prototype และทดสอบซ้ำกับผู้ใช้กลุ่มเดิม/ใหม่"]),
            ("Brand Consistency","ทีมใช้สีและโลโก้ต่างกันในสื่อหลายช่องทาง",1,["Branding","Visual Design","Attention to Detail"],["รวบรวม asset และระบุ inconsistency","สร้าง brand guideline ที่กำหนดสี typography และการใช้โลโก้","ตรวจงานตัวอย่างหลายขนาดก่อนเผยแพร่"]),
            ("Poster Hierarchy","โปสเตอร์มีข้อมูลครบแต่คนอ่านไม่รู้ว่าควรดูอะไรเป็นอันดับแรก",2,["Graphic Design","Visual Design","Creative Thinking"],["กำหนด primary message และลำดับข้อมูล","ปรับ hierarchy ด้วยขนาด น้ำหนัก และพื้นที่ว่าง","ทดสอบเวลาในการหา message สำคัญกับผู้ใช้"]),
            ("Mobile UX Friction","ฟอร์มสมัครบนมือถือมีคนเริ่มกรอกมากแต่ส่งสำเร็จน้อย",2,["UI/UX","User Research","Analytical Thinking"],["วิเคราะห์ funnel และ device-specific drop-off","ทดสอบ field, keyboard, validation และ error message","ปรับจุด friction แล้ววัด completion rate ใหม่"]),
            ("Campaign Creative Test","ภาพโฆษณา A ได้ click สูงแต่ conversion ต่ำกว่า B",3,["Creative Thinking","Marketing","Business Analytics"],["แยก click metric จาก conversion metric","กำหนด test ที่ควบคุม audience และ placement","เลือก creative จากเป้าหมายธุรกิจ ไม่ใช่ metric เดียว"]),
            ("Accessibility Review","หน้าเว็บมี contrast ต่ำและใช้สีอย่างเดียวเพื่อบอกสถานะ",3,["UI/UX","Visual Design","Attention to Detail"],["ตรวจ contrast และสถานะที่ไม่ควรพึ่งสีเพียงอย่างเดียว","เพิ่ม text/icon/focus state ที่สื่อความหมายได้","ทดสอบ keyboard และ screen reader-friendly structure"]),
            ("Design System Scale","หลายหน้ามี component เดียวกันแต่ spacing และ state ไม่เหมือนกัน",4,["UI/UX","Visual Design","Planning"],["ทำ inventory component และ variant ที่มีอยู่","กำหนด token และ state กลางก่อนแก้ทีละหน้า","ตรวจ regression ทุกหน้าหลังรวม component"]),
            ("Brand Repositioning","แบรนด์ต้องเปลี่ยนภาพลักษณ์จากนักเรียนเป็นมืออาชีพโดยยังจำง่าย",4,["Branding","Creative Thinking","User Research"],["เก็บ perception ปัจจุบันและกลุ่มเป้าหมายก่อนออกแบบ","สร้าง concept หลายทางและประเมินตาม brand attributes","ทดสอบ concept กับกลุ่มเป้าหมายและเลือกจากหลักฐาน"]),
        ],
    },
    "อาหาร/คหกรรม": {
        "desc":"วัตถุดิบ การจัดการครัว ต้นทุน สุขอนามัย และการออกแบบเมนู",
        "skills":["Food Safety","Kitchen Management","Costing","Menu Design","Inventory","Quality","Planning","Creativity"],
        "missions":[
            ("Cold Storage Check","วัตถุดิบแช่เย็นบางรายการมีอุณหภูมิสูงกว่าปกติ",1,["Food Safety","Quality","Attention to Detail"],["แยกวัตถุดิบที่เสี่ยงและตรวจอุณหภูมิตามขั้นตอน","ตรวจเวลาและเงื่อนไขการเก็บก่อนตัดสินใจใช้","บันทึก corrective action และตรวจอุณหภูมิซ้ำ"]),
            ("Recipe Costing","เมนูใหม่ขายดีแต่กำไรต่อจานต่ำกว่าที่คาด",1,["Costing","Menu Design","Business Analytics"],["แยกต้นทุนวัตถุดิบต่อ portion และ waste","คำนวณต้นทุนจริงรวมบรรจุภัณฑ์/แรงงานที่เกี่ยวข้อง","ปรับ portion หรือราคาโดยตรวจผลต่อคุณภาพและกำไร"]),
            ("Kitchen Workflow","ช่วง lunch ครัวส่งอาหารช้าแม้วัตถุดิบพร้อม",2,["Kitchen Management","Planning","Time Management"],["จับเวลาขั้นตอนและหา bottleneck","จัด prep และ station ให้ลดงานรอ","ทดลอง workflow ใหม่และวัด ticket time"]),
            ("Cross Contamination","พบเขียงและอุปกรณ์ถูกใช้กับวัตถุดิบดิบและอาหารพร้อมกิน",2,["Food Safety","Kitchen Management","Attention to Detail"],["หยุดการใช้ร่วมและแยกอุปกรณ์ตามความเสี่ยง","กำหนด cleaning/sanitizing และ flow ที่ชัดเจน","ตรวจการปฏิบัติจริงและบันทึก corrective action"]),
            ("Waste Reduction","วัตถุดิบเหลือทิ้งเพิ่มขึ้นจากเมนูที่ขายไม่แน่นอน",3,["Inventory","Costing","Analytical Thinking"],["แยก waste ตามสาเหตุและเมนู","ใช้ยอดขายย้อนหลังและ shelf life เพื่อวาง par level","ทดลองปรับการสั่งซื้อและติดตาม waste rate"]),
            ("Menu Engineering","ต้องเลือกเมนูเด่นจากข้อมูลยอดขายและกำไรหลายเดือน",3,["Menu Design","Business Analytics","Creativity"],["จัดกลุ่มเมนูตาม popularity และ contribution margin","ตรวจฤดูกาลและข้อจำกัดครัวก่อนตัดสินใจ","ทดสอบการจัดวางเมนูและติดตามผล"]),
            ("Allergen Control","ลูกค้าแจ้งแพ้อาหารและครัวมีความเสี่ยงจากอุปกรณ์ร่วม",4,["Food Safety","Kitchen Management","Communication"],["ยืนยัน allergen และแยกวัตถุดิบ/อุปกรณ์ตามขั้นตอน","สื่อสารคำสั่งกับทุก station และบันทึกการตรวจ","ตรวจ traceability ก่อนส่งจานให้ลูกค้า"]),
            ("Production Scaling","ต้องเพิ่มการผลิตจาก 50 เป็น 300 portions โดยรักษาคุณภาพ",4,["Kitchen Management","Planning","Quality"],["คำนวณวัตถุดิบและ capacity พร้อมเผื่อ loss","กำหนด batch size, checkpoint และวิธีเก็บรักษา","ทำ pilot batch และตรวจคุณภาพก่อนขยายเต็มกำลัง"]),
        ],
    },
    "ก่อสร้าง": {
        "desc":"งานก่อสร้าง การอ่านแบบ วัสดุ ความปลอดภัย และการควบคุมงาน",
        "skills":["Construction","Blueprint Reading","Site Safety","Materials","Quantity Survey","Planning","Quality","Problem Solving"],
        "missions":[
            ("Drawing Revision Check","หน้างานพบแบบพิมพ์ที่ revision ไม่ตรงกับเอกสารล่าสุด",1,["Blueprint Reading","Quality","Attention to Detail"],["หยุดงานที่ได้รับผลกระทบและตรวจ revision ล่าสุด","เทียบแบบกับ document control ก่อนดำเนินการ","บันทึกการเปลี่ยนแปลงและตรวจพื้นที่ก่อนเริ่มต่อ"]),
            ("Site Safety Walk","พบทางเดินมีวัสดุกีดขวางและไม่มีป้ายเตือน",1,["Site Safety","Planning","Communication"],["กั้นพื้นที่/แก้ hazard ตามขั้นตอนทันที","ตรวจความเสี่ยงอื่นในเส้นทางและบันทึก corrective action","ยืนยันว่าพื้นที่ปลอดภัยก่อนเปิดใช้งาน"]),
            ("Material Quantity Check","วัสดุส่งเข้าหน้างานน้อยกว่าที่ใบสั่งซื้อระบุ",2,["Materials","Quantity Survey","Attention to Detail"],["ตรวจนับและเทียบ delivery note กับ purchase order","แยกของขาด/ของเสียและแจ้งหลักฐาน","ปรับแผนงานเฉพาะส่วนที่ไม่ติดวัสดุและติดตามการส่งเพิ่ม"]),
            ("Concrete Quality","ผลทดสอบคอนกรีตบางชุดต่ำกว่าเกณฑ์",2,["Construction","Quality","Materials"],["กักงาน/ล็อตที่เกี่ยวข้องและตรวจข้อมูล batch","ตรวจสัดส่วน วัสดุ การเก็บตัวอย่าง และเงื่อนไข curing","วาง corrective action และทดสอบยืนยันก่อนเดินงานต่อ"]),
            ("Schedule Slippage","งานโครงสร้างช้ากว่าแผน 5 วันและมีงานต่อเนื่องหลายส่วน",3,["Planning","Construction","Time Management"],["วิเคราะห์ critical path และ dependency","จัดลำดับ recovery ที่ไม่เพิ่มความเสี่ยงเกินควบคุม","ทำ baseline ใหม่พร้อม milestone และ owner"]),
            ("Quantity Variation","ปริมาณงานจริงต่างจาก BOQ ในบางรายการ",3,["Quantity Survey","Materials","Analytical Thinking"],["ตรวจ measurement sheet และ drawing revision","แยก variation ที่เกิดจากแบบกับหน้างาน","จัดทำหลักฐานก่อนเสนอ change/claim"]),
            ("Structural Defect Triage","พบรอยร้าวที่องค์ประกอบโครงสร้างและยังไม่ทราบสาเหตุ",4,["Construction","Site Safety","Problem Solving"],["จำกัดพื้นที่และประเมินความปลอดภัยก่อนตรวจละเอียด","บันทึกตำแหน่ง รูปแบบ และแนวโน้มรอยร้าว","ส่งต่อวิศวกร/ผู้มีอำนาจตามเกณฑ์และติดตามผลตรวจ"]),
            ("Resource Optimization","มีแรงงานจำกัดแต่ต้องเร่งงานหลายพื้นที่พร้อมกัน",4,["Planning","Construction","Decision Making"],["จัดลำดับพื้นที่ตาม critical path และความเสี่ยง","วาง resource allocation พร้อม contingency","ติดตาม productivity และปรับแผนจากข้อมูลจริง"]),
        ],
    },
    "โลจิสติกส์": {
        "desc":"คลังสินค้า การขนส่ง สต็อก เส้นทาง และการวางแผนซัพพลายเชน",
        "skills":["Logistics","Inventory","Route Planning","Supply Chain","Data Analytics","Planning","Problem Solving","Customer Focus"],
        "missions":[
            ("Stock Count Variance","ยอดสต็อกจริงต่างจากระบบ 18 ชิ้นใน SKU เดียว",1,["Inventory","Attention to Detail","Problem Solving"],["นับซ้ำและตรวจ movement ย้อนหลัง","แยก receiving, picking และ adjustment ที่เกี่ยวข้อง","ปรับยอดพร้อมเหตุผลและเพิ่ม control point"]),
            ("Delivery Delay","รถส่งของล่าช้าหลายเที่ยวในช่วงเวลาเดียวกัน",1,["Logistics","Data Analytics","Problem Solving"],["แยก delay ตาม route, driver และช่วงเวลา","ตรวจ bottleneck ที่ depot/traffic/loading","ปรับแผนและติดตาม on-time rate หลังแก้"]),
            ("Warehouse Layout","พนักงานเดินไกลมากสำหรับ SKU ที่หยิบบ่อย",2,["Inventory","Planning","Logistics"],["วิเคราะห์ pick frequency และระยะทาง","จัด slotting โดยคำนึงถึงความถี่ น้ำหนัก และความปลอดภัย","ทดลอง layout และวัด pick time ก่อน-หลัง"]),
            ("Reorder Point","วัตถุดิบขาดบ่อยทั้งที่ยอดเฉลี่ยไม่ได้เพิ่มมาก",2,["Inventory","Supply Chain","Data Analytics"],["ดู lead time variability และ demand distribution","กำหนด reorder point/safety stock จากข้อมูล","back-test policy กับข้อมูลย้อนหลัง"]),
            ("Route Optimization","ต้องส่ง 12 จุดด้วยรถ 2 คันและมีเวลาส่งต่างกัน",3,["Route Planning","Planning","Data Analytics"],["รวบรวม time window และข้อจำกัดรถก่อนจัด route","เปรียบเทียบ route ตามระยะเวลาและ SLA","ตรวจแผนกับข้อจำกัดจริงและทำ contingency"]),
            ("Cold Chain Excursion","สินค้าควบคุมอุณหภูมิเกินช่วงระหว่างขนส่ง",3,["Logistics","Quality","Problem Solving"],["กัก shipment และตรวจ temperature log","หาจุดที่อุณหภูมิหลุดจาก timeline","ประเมิน disposition ตามเกณฑ์และแก้ process ที่ต้นเหตุ"]),
            ("Demand Spike","คำสั่งซื้อเพิ่มขึ้น 40% ในสัปดาห์เดียว",4,["Supply Chain","Data Analytics","Planning"],["ตรวจว่า spike มาจาก campaign หรือข้อมูลผิด","คำนวณ capacity, stock และ supplier lead time","ทำ scenario plan พร้อม trigger เมื่อ demand กลับปกติ/เพิ่มต่อ"]),
            ("Multi-Warehouse Allocation","มีสินค้าจำกัดและลูกค้าหลายพื้นที่มี SLA ต่างกัน",4,["Supply Chain","Decision Making","Data Analytics"],["จัด priority จาก SLA และผลกระทบ stockout","จำลอง allocation หลายแบบและดู service level","เลือกแผนที่สมดุล service level กับต้นทุนขนส่ง"]),
        ],
    },
    "การโรงแรมและท่องเที่ยว": {
        "desc":"งานบริการ การจัดการโรงแรม การท่องเที่ยว และประสบการณ์ลูกค้า",
        "skills":["Hospitality","Customer Service","Event Planning","Revenue Management","Communication","Problem Solving","Planning","Service Quality"],
        "missions":[
            ("Check-in Queue","แขกจำนวนมากมาถึงพร้อมกันและแถวยาวผิดปกติ",1,["Hospitality","Customer Service","Planning"],["แยกขั้นตอน check-in และหาจุดคอขวด","จัดคนตามช่วง demand และเตรียมข้อมูลล่วงหน้า","วัด waiting time และปรับ staffing จากข้อมูล"]),
            ("Room Complaint","แขกแจ้งว่าห้องไม่พร้อมตามเวลาที่สัญญา",1,["Customer Service","Communication","Service Quality"],["ยืนยันสถานะจริงและเสนอทางเลือกที่เหมาะสม","สื่อสารเวลาและผู้รับผิดชอบอย่างชัดเจน","ติดตามจนปิดเคสและบันทึกสาเหตุ"]),
            ("Booking Overlap","ระบบจองห้องพบรายการซ้อนในช่วงเดียวกัน",2,["Revenue Management","Problem Solving","Attention to Detail"],["ตรวจ source ของ booking และ timestamp","ยืนยัน inventory จริงก่อนแก้ reservation","ปรับระบบ/ขั้นตอนและทดสอบกรณี concurrent booking"]),
            ("Event Capacity","งานอีเวนต์มีผู้เข้าร่วมเกินจำนวนที่วางแผน",2,["Event Planning","Hospitality","Safety"],["ตรวจ capacity และข้อกำหนดความปลอดภัยก่อนรับเพิ่ม","จัด flow ทางเข้า/ที่นั่งและ resource","สื่อสาร contingency plan และติดตาม occupancy"]),
            ("Service Recovery","รีวิวเชิงลบเพิ่มขึ้นหลังเปลี่ยนขั้นตอนบริการ",3,["Service Quality","Customer Service","Data Analytics"],["แยกรีวิวตาม touchpoint และช่วงเวลา","ตรวจว่าปัญหาเกิดจากขั้นตอนไหนก่อนแก้ทั้งหมด","ทดลอง service recovery และติดตามคะแนน/complaint rate"]),
            ("Room Pricing","อัตราเข้าพักสูงแต่รายได้ต่อห้องต่ำกว่าช่วงใกล้เคียง",3,["Revenue Management","Data Analytics","Decision Making"],["แยก occupancy, ADR และ channel mix","วิเคราะห์ราคาเทียบ demand และข้อจำกัดห้อง","ทดลอง pricing rule และติดตามรายได้จริง"]),
            ("Tour Disruption","ฝนหนักทำให้แผนท่องเที่ยวบางจุดใช้งานไม่ได้",4,["Event Planning","Problem Solving","Communication"],["ประเมินความปลอดภัยและยกเลิกกิจกรรมเสี่ยงก่อน","จัด route สำรองตามเวลาและความต้องการลูกค้า","สื่อสารทางเลือกและติดตามการเปลี่ยนแปลงหน้างาน"]),
            ("Service Capacity Planning","โรงแรมต้องรองรับกรุ๊ปใหญ่พร้อมแขกทั่วไปโดยคุณภาพไม่ตก",4,["Planning","Hospitality","Service Quality"],["ทำ capacity plan แยก housekeeping, front desk และอาหาร","กำหนด peak staffing และ service checkpoint","ทดสอบแผนด้วย scenario และปรับจากข้อมูลจริง"]),
        ],
    },
}

def ensure_department_missions(D, S):
    """Seed the new department-specific mission catalog without deleting legacy data."""
    for dep_name, spec in DEPARTMENT_CATALOG.items():
        dep = D.get(dep_name) or Department.query.filter_by(name=dep_name).first()
        if not dep:
            dep = Department(name=dep_name, description=spec["desc"])
            db.session.add(dep)
            db.session.flush()
        elif not dep.description:
            dep.description = spec["desc"]
        D[dep_name]=dep

        # Ensure every skill referenced by this department AND its missions exists.
        # Mission catalogs may contain supporting/cross-cutting skills that are not
        # repeated in spec["skills"]. Never assume the department-level list is
        # exhaustive: resolving all mission skill names here prevents KeyError during seed.
        all_skill_names = set(spec["skills"])
        for _title, _scenario, _difficulty, _mission_skill_names, _stages in spec["missions"]:
            all_skill_names.update(_mission_skill_names)

        for skill_name in sorted(all_skill_names):
            if skill_name not in S:
                skill = Skill.query.filter_by(name=skill_name).first()
                if not skill:
                    skill = Skill(name=skill_name, description=f"ทักษะสำหรับงาน {dep_name}")
                    db.session.add(skill)
                    db.session.flush()
                S[skill_name] = skill

        for title, scenario, difficulty, skill_names, stages in spec["missions"]:
            if Mission.query.filter_by(title=title).first():
                continue
            m = Mission(
                title=title, scenario=scenario, department=dep,
                difficulty=difficulty, time_limit={1:240,2:300,3:360,4:420}[difficulty],
                budget={1:500,2:1000,3:2000,4:5000}[difficulty], discovery=True
            )
            m.skills=[S[x] for x in skill_names]
            db.session.add(m)
            db.session.flush()
            for order, prompt in enumerate(stages, 1):
                # Correct response is intentionally first; scoring reads DB choice IDs,
                # so the presentation layer can safely shuffle choices.
                question_templates={
                    1:"เมื่อพบสถานการณ์นี้ คุณควรเริ่มต้นอย่างไร?",
                    2:"เมื่อได้ข้อมูลเบื้องต้นแล้ว คุณควรดำเนินการขั้นต่อไปอย่างไร?",
                    3:"ก่อนสรุปผลหรือส่งมอบงาน คุณควรยืนยันอะไร?"
                }
                choices = [
                    (prompt, 10, "ได้หลักฐานและลดความเสี่ยงก่อนตัดสินใจ", True),
                    ("รีบเปลี่ยนหรือแก้ทุกอย่างทันทีโดยไม่เก็บข้อมูลเพิ่ม", 3, "อาจเสียทรัพยากรและทำให้หาสาเหตุยากขึ้น", False),
                    ("สรุปสาเหตุจากอาการเดียวแล้วดำเนินการทันที", 2, "หลักฐานยังไม่เพียงพอสำหรับข้อสรุป", False),
                    ("เลื่อนปัญหาออกไปโดยไม่กำหนดจุดติดตามผล", 1, "ปัญหาอาจกระทบงานต่อเนื่อง", False),
                ]
                step = MissionStep(
                    order_index=order, prompt=f"ขั้นที่ {order}: {question_templates[order]}",
                    hint1="เริ่มจากข้อมูลและเงื่อนไขที่ตรวจสอบได้",
                    hint2="เลือกวิธีที่ลดความเสี่ยงและสามารถวัดผลได้",
                    hint3="ก่อนสรุป ให้คิดถึงหลักฐานที่ยังขาดและผลกระทบของทางเลือก"
                )
                step.choices=[MissionChoice(text=t,points=p,consequence=c,is_correct=ok) for t,p,c,ok in choices]
                m.steps.append(step)
    db.session.commit()
    return D, S
