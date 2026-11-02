const fs=require('fs'),vm=require('vm'),assert=require('node:assert/strict');
class Node {
 constructor(tag='div'){this.tag=tag;this.children=[];this.attrs={};this.events={};this.className='';this.clientWidth=800;this._scrollLeft=0;this.style={setProperty:(k,v)=>this.attrs[k]=v};this.classList={add:()=>{},remove:()=>{}};}
 get scrollLeft(){return this._scrollLeft;}
 set scrollLeft(value){this._scrollLeft=Math.round(value);}
 append(...nodes){for(const n of nodes){if(n.parent)n.remove();this.children.push(n);n.parent=this;}}
 remove(){if(this.parent)this.parent.children=this.parent.children.filter(n=>n!==this);this.parent=null;}
 setAttribute(k,v){this.attrs[k]=v;} removeAttribute(k){delete this.attrs[k];}
 addEventListener(k,fn){(this.events[k]??=[]).push(fn);}
 emit(k,e={}){for(const fn of this.events[k]||[])fn({target:this,button:0,pointerId:1,pointerType:'mouse',clientX:100,clientY:0,preventDefault(){this.prevented=true;},stopPropagation(){},...e});}
 contains(n){return n===this||this.children.some(c=>c.contains(n));}
 getBoundingClientRect(){return {width:this.className==='pv-marquee-group'?2400:800};}
 setPointerCapture(id){this.capture=id;}hasPointerCapture(id){return this.capture===id;}releasePointerCapture(){this.capture=null;}
 querySelectorAll(selector){const all=this.children.flatMap(c=>[c,...c.querySelectorAll('*')]);if(selector==='[id]')return all.filter(c=>c.attrs.id);if(selector==='a,button,[tabindex]')return all.filter(c=>c.tag==='a'||c.tag==='button'||c.attrs.tabindex);return all;}
 cloneNode(){const n=new Node(this.tag);n.className=this.className;n.attrs={...this.attrs};this.children.forEach(c=>n.append(c.cloneNode()));return n;}
 blur(){doc.activeElement=null;}
}
const root=new Node();for(let i=0;i<14;i++){const a=new Node('a');a.attrs.href='/category/'+i;root.append(a);}
const doc=new Node();doc.querySelectorAll=()=>[root];doc.createElement=t=>new Node(t);doc.hidden=false;
const win=new Node();win.IntersectionObserver=true;const reduced=new Node();reduced.matches=false;
let callback,now=0,visibleCallback;const frames=new Map();let frameId=0;
vm.runInNewContext(fs.readFileSync(require('path').join(__dirname,'../static/js/category-marquee.js'),'utf8'),{document:doc,window:win,matchMedia:()=>reduced,getComputedStyle:()=>({getPropertyValue:k=>k==='--pv-card-count'?'5':'12'}),requestAnimationFrame:fn=>{frames.set(++frameId,fn);return frameId;},cancelAnimationFrame:id=>frames.delete(id),performance:{now:()=>now},queueMicrotask:fn=>fn(),ResizeObserver:class{constructor(fn){this.fn=fn;}observe(){}},IntersectionObserver:class{constructor(fn){visibleCallback=fn;}observe(){} }});
const controls=root.children[0],view=root.children[1],track=view.children[0],group=track.children[0];
assert.equal(group.children.length,14);assert.equal(track.children.length,2);
assert.equal(track.children[1].attrs['aria-hidden'],'true');
assert.equal(track.children[1].children[0].tabIndex,-1);
assert.equal(track.children[1].children[0].attrs.href,'/category/0');
visibleCallback([{isIntersecting:true}]);assert.equal(frames.size,1);
function frame(t){const [id,fn]=frames.entries().next().value;frames.delete(id);fn(t);}
frame(100);const before=view.scrollLeft;for(let i=1;i<=120;i++)frame(100+i*1000/60);assert.ok(Math.abs(view.scrollLeft-before-48)<=1,'60Hz autoplay must retain subpixel movement on integer scroll positions');
view.emit('pointerenter');assert.equal(frames.size,0);
view.emit('pointerleave');assert.equal(frames.size,1);
controls.children[1].emit('click');assert.equal(controls.children[1].attrs['aria-pressed'],'true');assert.equal(frames.size,0);
controls.children[1].emit('click');assert.equal(frames.size,1);
let prevented=false;view.emit('pointerdown');view.emit('pointermove',{clientX:102});win.emit('pointerup');view.emit('click',{preventDefault:()=>prevented=true});assert.equal(prevented,false,'small moves must preserve links');
view.emit('pointerdown');view.emit('pointermove',{clientX:140});win.emit('pointerup');view.emit('click',{preventDefault:()=>prevented=true});assert.equal(prevented,true,'drag must suppress accidental navigation');
// A touch focuses the scroll region in mobile browsers; it must not latch pause.
view.emit('pointerleave');
view.emit('pointerdown',{pointerType:'touch'});doc.activeElement=view;
view.emit('focusin');win.emit('pointerup',{pointerType:'touch'});
assert.equal(frames.size,1,'touch focus must resume autoplay after release');
now=4000;frame(now);const touchStart=view.scrollLeft;
for(let i=1;i<=120;i++)frame(now+i*1000/60);
assert.ok(view.scrollLeft>touchStart,'autoplay must resume after touch focus');
view.emit('keydown',{key:'Tab'});
assert.equal(frames.size,0,'keyboard focus must still pause autoplay');
doc.activeElement=null;view.emit('focusout');
assert.equal(frames.size,1,'leaving keyboard focus must resume autoplay');
reduced.matches=true;reduced.emit('change');assert.equal(track.children.length,1);assert.equal(frames.size,0);
assert.equal(controls.children[1].disabled,false,'reduced motion must offer an explicit start');
assert.equal(controls.children[1].textContent,'شروع حرکت');
assert.equal(controls.children[1].attrs['aria-pressed'],'true');
controls.children[1].emit('click');
assert.equal(track.children.length,2,'explicit start must restore the seamless loop');
assert.equal(frames.size,1,'explicit start must allow motion with reduced motion enabled');
frame(7000);const optedStart=view.scrollLeft;
for(let i=1;i<=120;i++)frame(7000+i*1000/60);
assert.ok(Math.abs(view.scrollLeft-optedStart-48)<=1,'explicitly enabled motion must advance at 60Hz');
controls.children[1].emit('click');assert.equal(frames.size,0);
controls.children[1].emit('click');assert.equal(frames.size,1);
reduced.emit('change');
assert.equal(frames.size,0,'system preference changes must reset the override');
assert.equal(track.children.length,1);
console.log('Passed: preserved links, accessible clones, leftward motion, hover/pause, drag threshold, touch focus recovery, keyboard focus, reduced motion');
