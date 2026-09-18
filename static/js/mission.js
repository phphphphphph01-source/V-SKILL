const box=document.querySelector('#mission');
const submit=document.querySelector('#submit');
const selected=new Map();
let submitted=false;
let hintBusy=false;
const serverStartedAt=Date.now(); // synchronized to server on page load via data; display is UX only

function selectChoice(btn){
  const stepEl=btn.closest('.step');
  const step=stepEl.dataset.step;
  stepEl.querySelectorAll('.choice').forEach(x=>x.classList.remove('selected'));
  btn.classList.add('selected');
  selected.set(step,{step_id:Number(step),choice_id:Number(btn.dataset.choice)});
  const con=stepEl.querySelector('.consequence');
  if(con){con.textContent='✓ เลือกแล้ว — คะแนนจะถูกคำนวณจากข้อมูลฝั่งเซิร์ฟเวอร์';con.classList.add('show');}
  stepEl.classList.add('answered');
}
document.querySelectorAll('.choice').forEach(btn=>btn.addEventListener('click',()=>selectChoice(btn)));

async function requestHint(stepEl,hint){
  if(hintBusy)return;
  hintBusy=true; hint.disabled=true;
  try{
    const r=await fetch(`/student/mission/${box.dataset.id}/hint`,{
      method:'POST',headers:{'Content-Type':'application/json'},
      body:JSON.stringify({step_id:Number(stepEl.dataset.step)})
    });
    const d=await r.json();
    if(!r.ok||!d.ok)throw new Error(d.error||'ขอคำใบ้ไม่สำเร็จ');
    let boxHint=stepEl.querySelector('.hint-text');
    if(!boxHint){boxHint=document.createElement('p');boxHint.className='hint-text';stepEl.appendChild(boxHint);}
    boxHint.textContent=`Hint ${d.level}: ${d.hint}`;
    boxHint.classList.add('hint-pop');
    hint.textContent=d.level>=3?'💡 ใช้คำใบ้ครบแล้ว':`💡 ขอคำใบ้ (${d.level}/3)`;
    if(d.level>=3)hint.disabled=true;
  }catch(e){
    hint.disabled=false;
    const msg=document.createElement('p');msg.className='flash';msg.textContent=e.message;stepEl.appendChild(msg);
  }finally{hintBusy=false;}
}

document.querySelectorAll('.step').forEach((step,index)=>{
  step.style.animation=`fadeUp .65s cubic-bezier(.2,.8,.2,1) ${index*90}ms both`;
  const hint=document.createElement('button');
  hint.type='button'; hint.className='btn hint'; hint.textContent='💡 ขอคำใบ้ (0/3)';
  hint.addEventListener('click',()=>requestHint(step,hint));
  step.appendChild(hint);
  step.style.setProperty('--step-delay',`${index*70}ms`);
});

const timer=document.createElement('div');
timer.className='card mission-timer'; timer.id='mission-timer';
timer.innerHTML='<span>⏱️ <b>เวลาที่ใช้</b></span><strong></strong>';
document.querySelector('.mission-shell').insertBefore(timer,box);
const timerValue=timer.querySelector('strong');
const started=Date.now();
function tick(){
  const sec=Math.floor((Date.now()-started)/1000), limit=Number(box.dataset.limit||0);
  timerValue.textContent=limit?`${sec}s / ${limit}s`:`${sec}s`;
  timer.classList.toggle('danger',limit>0&&sec>=limit*.8);
}
tick(); const timerId=setInterval(tick,1000);

function celebrate(){
  if(window.matchMedia('(prefers-reduced-motion: reduce)').matches)return;
  const layer=document.createElement('div'); layer.style.cssText='position:fixed;inset:0;pointer-events:none;z-index:99999;overflow:hidden';
  for(let i=0;i<70;i++){
    const p=document.createElement('i'); const size=5+Math.random()*8;
    p.style.cssText=`position:absolute;left:${50+Math.random()*8-4}%;top:45%;width:${size}px;height:${size*1.5}px;border-radius:3px;background:hsl(${Math.random()*360} 85% 68%);transform:rotate(${Math.random()*360}deg);animation:confettiFall ${.9+Math.random()*1.3}s ease-out forwards`;
    layer.appendChild(p);
  }
  document.body.appendChild(layer); setTimeout(()=>layer.remove(),2300);
}
submit.addEventListener('click',async()=>{
  if(submitted)return;
  const steps=[...document.querySelectorAll('.step')];
  if(selected.size!==steps.length){
    document.querySelector('#result').innerHTML='<div class="flash">⚠️ กรุณาเลือกคำตอบให้ครบทุกขั้นก่อนส่ง Mission</div>';
    const first=steps.find(s=>!selected.has(s.dataset.step));
    first?.scrollIntoView({behavior:'smooth',block:'center'}); return;
  }
  submitted=true; submit.disabled=true; submit.textContent='กำลังวิเคราะห์ผลจาก Server...';
  try{
    const r=await fetch(`/student/mission/${box.dataset.id}/submit`,{
      method:'POST',headers:{'Content-Type':'application/json'},
      body:JSON.stringify({decisions:[...selected.values()]})
    });
    const d=await r.json(); if(!r.ok||!d.ok)throw new Error(d.error||'ส่ง Mission ไม่สำเร็จ');
    clearInterval(timerId);
    const score=Number(d.score||0), rw=d.reward||{};
    const bonus=(rw.bonuses||[]).map(x=>`<span>${x[0]} <b>${x[1]}</b></span>`).join('');
    document.querySelector('#result').innerHTML=`<div class="result-card card"><div class="result-badge">MISSION COMPLETE</div><h2>ภารกิจสำเร็จ 🎉</h2><div class="result-score">${score}<small>/100</small></div><div class="result-stats"><span>Accuracy <b>${d.accuracy}%</b></span><span>Time <b>${Math.round(d.time_used||0)}s</b></span><span>Hints <b>${d.hints_used}</b></span></div><div class="reward-panel"><span>⚡ +${rw.xp||0} XP</span><span>📈 +${rw.progress||0} Progress</span><span>🪙 +${rw.coins||0} Coins</span><span>🔥 Combo ${rw.combo||0}</span><span>⚡ Streak ${rw.streak||0}</span></div>${bonus?`<div class="reward-bonuses">${bonus}</div>`:''}${rw.achievement_bonus?`<div class="achievement-reward">🏆 Achievement Magnet +${rw.achievement_bonus} Progress</div>`:''}${rw.coach?`<div class="coach-reward">🤖 <b>V-SKILL Coach</b> ${rw.coach}</div>`:''}<p>คะแนน เวลา และการใช้ Hint ถูกตรวจสอบและคำนวณจาก Server เพื่อป้องกันการแก้ค่าจาก Browser</p><div class="result-actions"><a class="btn" href="/student/skills">✨ ดู Skill Profile</a><a class="btn secondary" href="/student/discovery">ทำภารกิจต่อ</a></div></div>`;
    document.querySelector('#missionAvatar')?.classList.add('celebrate');
    if(window.VSkillAvatar) window.VSkillAvatar.playState('happy');
    celebrate(); document.querySelector('#result').scrollIntoView({behavior:'smooth',block:'center'});
    submit.style.display='none';
  }catch(e){submitted=false;submit.disabled=false;submit.textContent='ส่ง Mission';document.querySelector('#result').innerHTML=`<div class="flash">${e.message}</div>`;}
});
