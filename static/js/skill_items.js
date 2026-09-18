(() => {
  'use strict';
  const INFO = {
    holographic_scanner:{name:'Hint Scanner',icon:'🔍',rarity:'COMMON',text:'สแกนโจทย์เพื่อชี้ “จุดที่ควรตรวจ” โดยไม่บอกคำตอบ'},
    smart_tablet:{name:'Knowledge Tablet',icon:'📚',rarity:'COMMON',text:'เปิดกรอบความรู้ที่เกี่ยวข้อง เช่น หลักการ สูตร หน่วย หรือขั้นตอน'},
    digital_toolkit:{name:'Logic Toolkit',icon:'🧩',rarity:'RARE',text:'แตกโจทย์เป็น ข้อมูล → เงื่อนไข → สิ่งที่ต้องพิสูจน์ ก่อนเลือกคำตอบ'},
    explorer_goggles:{name:'Mission Compass',icon:'🧭',rarity:'RARE',text:'ช่วยจัดลำดับงานและชี้สิ่งที่ควรทำก่อนเมื่อมีหลายทางเลือก'},
    smart_glasses:{name:'AI Thinking Lens',icon:'🧠',rarity:'RARE',text:'แยกข้อเท็จจริง สมมติฐาน และข้อมูลที่ยังขาด เพื่อกันการเดา'},
    tech_headset:{name:'Precision Lens',icon:'🎧',rarity:'EPIC',text:'ตรวจคำสำคัญ หน่วย เงื่อนไข ข้อยกเว้น และรายละเอียดที่มักพลาด'},
    v_core:{name:'Time Booster',icon:'⚡',rarity:'EPIC',text:'ขยายเวลาคิดของ Mission 20% เพื่อให้ตรวจเหตุผลก่อนส่ง'},
    skill_aura:{name:'Focus Shield',icon:'🛡️',rarity:'EPIC',text:'ทำเครื่องหมายข้อที่ยังไม่มั่นใจ เพื่อกลับมาตรวจอย่างเป็นระบบ'},
    vbuddy_assistant:{name:'V-Buddy Assistant',icon:'🤖',rarity:'LEGENDARY',text:'ตั้งคำถามนำเพื่อให้คุณคิดเอง ไม่เปิดเฉลย'},
    master_analyzer:{name:'Master Analyzer',icon:'✨',rarity:'LEGENDARY',text:'ตรวจขั้นสุดท้าย: หลักการถูกไหม? หลักฐานครบไหม? ผลลัพธ์สมเหตุสมผลไหม?'}
  };
  const el=document.querySelector('[data-skill-items]');
  let keys=[]; try{keys=el?JSON.parse(el.dataset.skillItems||'[]'):[]}catch(e){}
  const has=k=>keys.includes(k), getInfo=k=>INFO[k]||{name:k,icon:'🧰',rarity:'COMMON',text:'เครื่องมือช่วยคิด ไม่เฉลย'};

  function getQuestion(target){
    if(!target) return '';
    return (target.querySelector('h2')?.textContent||target.dataset.prompt||'').trim();
  }
  function getContext(target){
    const text=(getQuestion(target)+' '+(document.querySelector('.scenario')?.textContent||'')).toLowerCase();
    return text;
  }
  function showPanel(host, title, body, tone='cyan'){
    let p=host.querySelector('.skill-context-panel');
    if(!p){p=document.createElement('div');p.className='skill-context-panel';host.appendChild(p);}
    p.dataset.tone=tone;
    p.innerHTML=`<div class="skill-panel-head"><span>AI SUPPORT</span><b>${title}</b></div><div class="skill-panel-body">${body}</div>`;
    p.classList.remove('skill-panel-pop'); void p.offsetWidth; p.classList.add('skill-panel-pop');
  }
  function contextFor(k,target){
    const q=getContext(target);
    const technical=/wifi|network|sensor|plc|วงจร|ไฟฟ้า|แรงดัน|กระแส|แบต|รถ|เครื่องจักร|โค้ด|โปรแกรม|database|ฐานข้อมูล|server|traffic|poe|สาย/.test(q);
    const numbers=/\d|บาท|เปอร์เซ็นต์|%|วินาที|นาที|volt|amp|ohm/.test(q);
    const decision=/เลือก|ตัดสินใจ|ควรทำ|อันดับแรก|ก่อน|หลังจาก|ปัญหา|ผิดปกติ/.test(q);
    if(k==='holographic_scanner') return technical?'🔍 <b>สแกนจุด:</b> หา “ตัวแปรที่ผิดปกติ” และหลักฐานที่ยืนยันอาการก่อนเลือกวิธีแก้':'🔍 <b>สแกนจุด:</b> ขีดเส้นใต้ข้อมูลที่โจทย์ให้มา แล้วดูว่าข้อมูลใดเปลี่ยนการตัดสินใจได้จริง';
    if(k==='smart_tablet') return technical?'📚 <b>ความรู้ที่ควรนึกถึง:</b> หลักการของระบบ + ขั้นตอนตรวจจากง่ายไปยาก + ความปลอดภัย/ข้อจำกัดที่เกี่ยวข้อง':numbers?'📚 <b>เช็กก่อนคำนวณ:</b> หน่วย, ค่าที่โจทย์ให้, สูตร/ความสัมพันธ์ และเงื่อนไขของโจทย์':'📚 <b>กรอบความรู้:</b> นิยามปัญหา → หลักการที่เกี่ยวข้อง → เกณฑ์ที่ใช้ตัดสิน';
    if(k==='digital_toolkit') return `🧩 <b>แตกโจทย์:</b><ol><li>เรารู้อะไรแล้ว?</li><li>ยังขาดข้อมูลอะไร?</li><li>ทางเลือกไหนพิสูจน์ได้จากหลักฐาน?</li></ol>`;
    if(k==='explorer_goggles') return decision?'🧭 <b>ลำดับแนะนำ:</b> ความปลอดภัย/ผลกระทบ → หลักฐาน → ทางเลือก → ทดสอบผล':'🧭 <b>ลำดับแนะนำ:</b> เป้าหมาย → ข้อจำกัด → ทรัพยากร → ตรวจผลลัพธ์';
    if(k==='smart_glasses') return `🧠 <b>แยกการคิด:</b><ul><li><b>Fact:</b> สิ่งที่โจทย์ยืนยัน</li><li><b>Assumption:</b> สิ่งที่เรากำลังคาด</li><li><b>Missing:</b> สิ่งที่ควรตรวจเพิ่ม</li></ul>`;
    if(k==='tech_headset') return numbers?'🎧 <b>Precision Check:</b> ตรวจหน่วย ค่าขอบเขต เครื่องหมาย และคำว่า “อย่างน้อย/ไม่เกิน/เฉพาะ/ก่อน”':'🎧 <b>Precision Check:</b> ตรวจคำปฏิเสธ เงื่อนไข ข้อยกเว้น และรายละเอียดที่ทำให้ตัวเลือกคล้ายกันแต่ไม่เท่ากัน';
    if(k==='vbuddy_assistant') return `🤖 <b>คำถามจาก V-Buddy:</b> “ถ้าต้องอธิบายเหตุผลให้คนอื่นตรวจสอบได้ คุณจะอ้างหลักฐานข้อไหน?”`;
    if(k==='master_analyzer') return '✨ <b>Final Check:</b> ถ้าคำตอบนี้ถูกจริง หลักฐานจากโจทย์ต้องรองรับอะไร? มีเงื่อนไขไหนที่ยังไม่ได้ตรวจ? และผลกระทบหลังเลือกคืออะไร?';
    return getInfo(k).text;
  }
  function selectTarget(mode){
    return mode==='quiz' ? document.querySelector('.quiz-question.selected-for-skill')||document.querySelector('.quiz-question:not(.skill-review)') : document.querySelector('.step.selected-for-skill')||document.querySelector('.step:not(.answered)')||document.querySelector('.step');
  }
  function relevance(k,target){
    const skills=((target?.dataset.skills||'')+' '+getContext(target)).toLowerCase();
    const map={
      holographic_scanner:/technical|problem solving|troubleshooting|sensor|network|diagnostic|ตรวจ|ปัญหา/,
      smart_tablet:/technical|logical|สูตร|วงจร|ไฟฟ้า|program|database|automotive|electronics/,
      digital_toolkit:/logical|analytical|problem solving|decision|algorithm|ข้อมูล|เงื่อนไข/,
      explorer_goggles:/planning|time|decision|mission|ลำดับ|deadline|ทรัพยากร/,
      smart_glasses:/analytical|logical|adaptability|risk|หลักฐาน|สมมติฐาน/,
      tech_headset:/attention|quality|precision|หน่วย|เงื่อนไข|ขอบเขต|detail/,
      vbuddy_assistant:/problem solving|learning|communication|teamwork|decision|คิด|เหตุผล/,
      master_analyzer:/analytical|quality|decision|problem solving|ตรวจ|หลักฐาน/
    };
    if(k==='v_core'||k==='skill_aura') return true;
    return map[k]?map[k].test(skills):true;
  }
  function addBar(shell,mode){
    if(!shell||shell.querySelector('.skill-tools-bar')) return;
    const bar=document.createElement('section'); bar.className='skill-tools-bar';
    bar.innerHTML='<div class="skill-tools-title"><div><span class="eyebrow">EQUIPPED SUPPORT</span><b>🧰 เครื่องมือช่วยคิด</b></div><small>ใช้เพื่อวิเคราะห์ ไม่ใช่เฉลย</small></div><div class="skill-tools-buttons"></div><div class="skill-tool-status">เลือกโจทย์ที่ต้องการช่วย แล้วเลือกเครื่องมือ</div>';
    shell.insertBefore(bar, mode==='quiz'?shell.querySelector('#quizForm'):shell.querySelector('#mission'));
    const buttons=bar.querySelector('.skill-tools-buttons');
    keys.forEach(k=>{
      const info=getInfo(k), btn=document.createElement('button'); btn.type='button'; btn.className='skill-tool-btn';
      btn.innerHTML=`<span class="skill-tool-icon">${info.icon}</span><span class="skill-tool-copy"><b>${info.name}</b><small>${info.rarity}</small></span><span class="skill-tool-arrow">›</span>`;
      btn.addEventListener('click',()=>{
        const target=selectTarget(mode); if(!target){bar.querySelector('.skill-tool-status').textContent='เลือกโจทย์ก่อนใช้ไอเทม';return;}
        if(k==='v_core'){bar.querySelector('.skill-tool-status').textContent='⚡ Time Booster ทำงานกับเวลาของ Mission แล้ว';return;}
        if(!relevance(k,target)){
          bar.querySelector('.skill-tool-status').textContent=`${info.icon} ${info.name} ไม่ใช่เครื่องมือที่เหมาะที่สุดกับโจทย์นี้ — ลองใช้ไอเทมอื่นที่ตรงทักษะกว่า`;
          btn.classList.add('skill-not-fit'); setTimeout(()=>btn.classList.remove('skill-not-fit'),650); return;
        }
        if(k==='skill_aura'){target.classList.toggle('skill-review');bar.querySelector('.skill-tool-status').textContent=target.classList.contains('skill-review')?'🛡️ เพิ่มไว้ในรายการทบทวนแล้ว':'🛡️ นำออกจากรายการทบทวนแล้ว';return;}
        showPanel(target,info.name,contextFor(k,target));
        bar.querySelector('.skill-tool-status').textContent=`${info.icon} ${info.name} ถูกใช้กับโจทย์นี้แล้ว`;
        btn.classList.add('used'); setTimeout(()=>btn.classList.remove('used'),500);
      }); buttons.appendChild(btn);
    });
    return bar;
  }
  function setup(mode){
    const shell=document.querySelector(mode==='quiz'?'.quiz-shell':'.mission-shell'); if(!shell||!keys.length)return;
    const bar=addBar(shell,mode);
    document.querySelectorAll(mode==='quiz'?'.quiz-question':'.step').forEach(q=>q.addEventListener('click',()=>{
      document.querySelectorAll(mode==='quiz'?'.quiz-question':'.step').forEach(x=>x.classList.remove('selected-for-skill'));
      q.classList.add('selected-for-skill');
      bar?.querySelector('.skill-tool-status')?.replaceChildren(document.createTextNode('โจทย์นี้พร้อมรับการช่วยคิดแล้ว'));
    }));
  }
  if(document.readyState==='loading') document.addEventListener('DOMContentLoaded',()=>{setup('mission');setup('quiz')}); else {setup('mission');setup('quiz')}
})();
