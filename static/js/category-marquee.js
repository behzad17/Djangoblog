/* Adapted interaction model from kevingirelli's 21st.dev Marquee.
   Native scroll positions keep links, touch inertia and keyboard focus usable in RTL. */
(() => {
 document.querySelectorAll('[data-category-marquee]').forEach(root=>{
  const items=[...root.children];
  if(items.length<2)return;
  const controls=document.createElement('div');controls.className='pv-marquee-controls';
  const button=(label)=>{const b=document.createElement('button');b.type='button';b.textContent=label;return b;};
  const prev=button('قبلی'),pause=button('توقف حرکت'),next=button('بعدی');
  pause.setAttribute('aria-pressed','false');controls.append(prev,pause,next);
  const viewport=document.createElement('div');viewport.className='pv-marquee-viewport';
  viewport.setAttribute('role','region');viewport.setAttribute('aria-label',root.getAttribute('data-category-marquee-label')||'دسته‌بندی مطالب کاربران؛ نوار افقی');viewport.tabIndex=0;
  const track=document.createElement('div');track.className='pv-marquee-track';
  const group=document.createElement('div');group.className='pv-marquee-group';
  items.forEach(item=>group.append(item));track.append(group);viewport.append(track);root.append(controls,viewport);
  root.classList.add('pv-category-marquee');
  let copy=null,period=0,raf=0,last=0,position=0,visible=false,paused=false,hover=false,focus=false,touchInteraction=false,pressed=false,drag=null,suppressClick=false,manualUntil=0;
  const mod=(n,d)=>((n%d)+d)%d;
  const stop=()=>{cancelAnimationFrame(raf);raf=0;last=0;};
  const mayRun=()=>visible&&!document.hidden&&!paused&&!hover&&!focus&&!pressed&&period>viewport.clientWidth;
  const tick=time=>{
   raf=0;
   if(!mayRun()){last=0;return;}
   if(time>=manualUntil){
    // Preserve fractional pixels: some browsers round scrollLeft on every write.
    if(last){
     position=mod(position+Math.min(time-last,50)*.0288,period);
     viewport.scrollLeft=position;
    }else position=viewport.scrollLeft;
    last=time;
   }else last=0;
   raf=requestAnimationFrame(tick);
  };
  const wake=()=>{if(mayRun()&&!raf)raf=requestAnimationFrame(tick);else if(!mayRun())stop();};
  const syncCopy=()=>{
   if(!copy){
    copy=group.cloneNode(true);copy.setAttribute('aria-hidden','true');
    copy.querySelectorAll('[id]').forEach(e=>e.removeAttribute('id'));
    copy.querySelectorAll('a,button,[tabindex]').forEach(e=>e.tabIndex=-1);
    // Keep real hrefs on the visual copy: inert would disable mouse/touch visits.
    track.append(copy);
   }
   pause.disabled=false;
   pause.setAttribute('aria-pressed',String(paused));
   pause.textContent=paused?'ادامهٔ حرکت':'توقف حرکت';
  };
  const resize=()=>{
   stop();
   if(!viewport.clientWidth){visible=false;stop();return;}
   const count=parseFloat(getComputedStyle(root).getPropertyValue('--pv-card-count'))||5;
   const gap=parseFloat(getComputedStyle(root).getPropertyValue('--pv-marquee-gap'))||12;
   const oldPeriod=period,progress=oldPeriod?viewport.scrollLeft/oldPeriod:0;
   root.style.setProperty('--pv-marquee-card-width',Math.max(110,(viewport.clientWidth-gap*(count-1))/count)+'px');
   syncCopy();period=group.getBoundingClientRect().width;
   viewport.scrollLeft=oldPeriod?progress*period:Math.max(0,period-viewport.clientWidth);
   wake();
  };
  pause.addEventListener('click',()=>{
   paused=!paused;
   resize();
  });
  const step=direction=>{stop();manualUntil=performance.now()+2500;viewport.scrollLeft=mod(viewport.scrollLeft+direction*viewport.clientWidth*.8,period);wake();};
  prev.addEventListener('click',()=>step(-1));next.addEventListener('click',()=>step(1));
  viewport.addEventListener('pointerenter',e=>{if(e.pointerType==='mouse'){hover=true;wake();}});
  viewport.addEventListener('pointerleave',()=>{hover=false;wake();});
  viewport.addEventListener('focusin',()=>{focus=!touchInteraction;wake();});
  viewport.addEventListener('focusout',()=>{queueMicrotask(()=>{focus=!touchInteraction&&viewport.contains(document.activeElement);wake();});});
  viewport.addEventListener('keydown',e=>{
   touchInteraction=false;focus=true;wake();
   if(e.target!==viewport)return;
   if(e.key==='ArrowLeft'||e.key==='ArrowRight'){e.preventDefault();step(e.key==='ArrowRight'?1:-1);}
  });
  viewport.addEventListener('pointerdown',e=>{
   suppressClick=false;if(e.button!==0)return;
   // Touch focus can persist after a swipe; only keyboard/mouse focus pauses.
   touchInteraction=e.pointerType==='touch';
   if(touchInteraction){focus=false;hover=false;}
   pressed=true;stop();
   if(e.pointerType!=='touch')drag={id:e.pointerId,x:e.clientX,y:e.clientY,start:viewport.scrollLeft,moving:false};
  });
  viewport.addEventListener('pointermove',e=>{
   if(!drag||e.pointerId!==drag.id)return;
   const dx=e.clientX-drag.x;
   if(!drag.moving){
    if(Math.abs(dx)<5||Math.abs(dx)<Math.abs(e.clientY-drag.y))return;
    drag.moving=true;viewport.setPointerCapture(e.pointerId);viewport.classList.add('is-dragging');
    if(viewport.contains(document.activeElement))document.activeElement.blur();
   }
   e.preventDefault();viewport.scrollLeft=mod(drag.start-dx,period);suppressClick=true;
  });
  const release=e=>{
   if(!pressed)return;pressed=false;
   if(drag&&viewport.hasPointerCapture(drag.id))viewport.releasePointerCapture(drag.id);
   drag=null;viewport.classList.remove('is-dragging');manualUntil=performance.now()+1500;wake();
  };
  window.addEventListener('pointerup',release);window.addEventListener('pointercancel',release);
  viewport.addEventListener('click',e=>{if(suppressClick){e.preventDefault();e.stopPropagation();suppressClick=false;}},true);
  viewport.addEventListener('dragstart',e=>e.preventDefault());
  document.addEventListener('visibilitychange',wake);
  new ResizeObserver(resize).observe(viewport);
  if('IntersectionObserver' in window)new IntersectionObserver(([entry])=>{visible=entry.isIntersecting;wake();},{rootMargin:'80px'}).observe(viewport);
  else visible=true;
  resize();
 });
})();
