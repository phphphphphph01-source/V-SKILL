(() => {
  'use strict';
  const BASE='/static/img/avatar_assets/';
  const GIF='/static/img/avatar_gifs/';
  const speciesNames={fox:'Explorer Fox',cat:'Smart Cat',rabbit:'Builder Rabbit',panda:'Tech Panda',penguin:'Cyber Penguin',tiger:'Engineer Tiger',owl:'AI Owl',wolf:'Cyber Wolf',dragon:'V-Dragon',unicorn:'V-Unicorn'};
  const file=(key)=>`${BASE}${key.startsWith('avatar_')?key:'avatar_'+key}.png`;
  const gif=(species,state='idle')=>`${GIF}${species}_${state}.gif?v=20260917c`;
  const esc=(s)=>String(s||'').replace(/[&<>"']/g,c=>({'&':'&amp;','<':'&lt;','>':'&gt;','"':'&quot;',"'":'&#39;'}[c]));
  function render(target){
    const isItem=target.dataset.previewItem;
    if(isItem){
      const key=target.dataset.previewItem;
      target.innerHTML=`<img class="asset-preview avatar-asset" src="${gif(key)}" onerror="this.onerror=null;this.src='${file(key)}'" alt="${esc(speciesNames[key]||key)}" draggable="false" loading="lazy">`;
      return;
    }
    const species=target.dataset.species||'fox';
    target.innerHTML=`<img class="avatar-gif" src="${gif(species,'idle')}" onerror="this.onerror=null;this.src='${file(species)}'" alt="${esc(speciesNames[species]||'Buddy')}" draggable="false" loading="eager">`;
  }
  function playState(target,state='idle'){
    if(!target)return;
    const species=target.dataset.species||'fox';
    const img=target.querySelector('.avatar-gif'); if(!img)return;
    img.src=gif(species,state); img.dataset.gifState=state;
    img.onerror=()=>{img.onerror=null;img.src=file(species)};
    if(state!=='idle') setTimeout(()=>{img.src=gif(species,'idle');img.dataset.gifState='idle'}, state==='level_up'?2200:1500);
  }
  function init(){
    document.querySelectorAll('.buddy-avatar,.avatar-2d-main,.avatar-mini-2d').forEach(render);
    const main=document.querySelector('.buddy-avatar');
    if(main){main.addEventListener('click',()=>{playState(main,'click');});}
    document.querySelectorAll('.rarity-filter-btn').forEach(btn=>btn.addEventListener('click',()=>{
      document.querySelectorAll('.rarity-filter-btn').forEach(b=>b.classList.remove('active')); btn.classList.add('active');
      const r=btn.dataset.rarity;
      document.querySelectorAll('.buddy-card,.skill-item-card').forEach(card=>card.hidden=r!=='all'&&card.dataset.rarity!==r);
    }));
    window.VSkillAvatar={playState:(state)=>playState(document.querySelector('.buddy-avatar'),state)};
  }
  if(document.readyState==='loading') document.addEventListener('DOMContentLoaded',init); else init();
})();
