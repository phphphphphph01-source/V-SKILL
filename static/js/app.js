(() => {
  document.documentElement.classList.add('js-ready');

  const progress = document.createElement('div');
  progress.className = 'scroll-progress';
  progress.innerHTML = '<span></span>';
  document.body.prepend(progress);
  const bar = progress.firstElementChild;
  const update = () => {
    const max = document.documentElement.scrollHeight - window.innerHeight;
    bar.style.transform = `scaleX(${max > 0 ? window.scrollY / max : 0})`;
  };
  window.addEventListener('scroll', update, {passive:true}); update();

  const glow = document.querySelector('.cursor-glow');
  window.addEventListener('pointermove', e => {
    if (glow) { glow.style.left = `${e.clientX}px`; glow.style.top = `${e.clientY}px`; }
  }, {passive:true});

  document.querySelectorAll('.btn,.choice').forEach(el => {
    el.addEventListener('pointerdown', e => {
      const r = el.getBoundingClientRect(), ripple = document.createElement('i');
      ripple.className='ripple'; ripple.style.left=`${e.clientX-r.left}px`; ripple.style.top=`${e.clientY-r.top}px`;
      el.appendChild(ripple); setTimeout(()=>ripple.remove(),700);
    });
  });

  const observer = new IntersectionObserver(entries => entries.forEach(entry => {
    if(entry.isIntersecting){ entry.target.classList.add('is-visible'); observer.unobserve(entry.target); }
  }), {threshold:.08});
  document.querySelectorAll('.card,.mission,.step,.hero,.page-head,.section-title,.quiz-card').forEach((el,i)=>{
    el.style.setProperty('--delay',`${Math.min(i,12)*55}ms`); el.classList.add('reveal'); observer.observe(el);
  });

  // Gentle pointer tilt for selected cards: movement, not click-only animation.
  if(!window.matchMedia('(prefers-reduced-motion: reduce)').matches){
    document.querySelectorAll('[data-tilt]').forEach(card=>{
      card.addEventListener('pointermove', e=>{
        const r=card.getBoundingClientRect(), x=(e.clientX-r.left)/r.width-.5, y=(e.clientY-r.top)/r.height-.5;
        card.style.transform=`perspective(900px) rotateX(${(-y*3).toFixed(2)}deg) rotateY(${(x*4).toFixed(2)}deg) translateY(-4px)`;
      });
      card.addEventListener('pointerleave',()=>card.style.transform='');
    });
  }

  // Count-up numbers
  const counters=document.querySelectorAll('[data-count]');
  const countObserver=new IntersectionObserver(entries=>entries.forEach(entry=>{
    if(!entry.isIntersecting) return;
    const el=entry.target, target=parseFloat(el.dataset.count||0), decimals=String(target).includes('.')?1:0;
    let start=null;
    const tick=t=>{if(start===null)start=t;const p=Math.min((t-start)/900,1);const eased=1-Math.pow(1-p,3);el.textContent=(target*eased).toFixed(decimals);if(p<1)requestAnimationFrame(tick)};
    requestAnimationFrame(tick);countObserver.unobserve(el);
  }),{threshold:.5});
  counters.forEach(x=>countObserver.observe(x));
})();