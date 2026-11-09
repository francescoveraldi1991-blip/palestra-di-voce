"""Componenti "live": accordatore e pratica con microfono in tempo reale.

Girano nel browser (JavaScript) dentro st.components.v1.html, così il
microfono funziona in diretta anche su Streamlit Community Cloud.
"""
import json

import streamlit.components.v1 as components

_BASE = r"""
<link rel="stylesheet" href="https://fonts.googleapis.com/css2?family=Bricolage+Grotesque:opsz,wght@12..96,800&family=IBM+Plex+Sans:wght@400;500;600&family=IBM+Plex+Mono:wght@400;500&display=swap">
<script>const TH='__THEME__';if(TH==='dark'||TH==='light')document.documentElement.setAttribute('data-theme',TH);</script>
<style>
:root{--bg:#FFFFFF;--lane:#F6F8FB;--ink:#141B26;--muted:#5A6577;--line:#D8DEE7;--accent:#2B45D4;--soft:#E6EAFB;--good:#1C9764;--warm:#D9702A;--bad:#CC3F37;--on:#FFFFFF;
 --f-display:"Bricolage Grotesque","Avenir Next",system-ui,sans-serif;--f-body:"IBM Plex Sans","Segoe UI",system-ui,sans-serif;--f-mono:"IBM Plex Mono",ui-monospace,Menlo,monospace}
@media (prefers-color-scheme: dark){:root:not([data-theme="light"]){--bg:#161D28;--lane:#111823;--ink:#E7EBF1;--muted:#95A1B4;--line:#273244;--accent:#7D90FF;--soft:#1E2747;--good:#3CC48A;--warm:#F09B5C;--bad:#F06A62;--on:#0E131B;color-scheme:dark}}
:root[data-theme="dark"]{--bg:#161D28;--lane:#111823;--ink:#E7EBF1;--muted:#95A1B4;--line:#273244;--accent:#7D90FF;--soft:#1E2747;--good:#3CC48A;--warm:#F09B5C;--bad:#F06A62;--on:#0E131B;color-scheme:dark}
*{box-sizing:border-box}
[hidden]{display:none!important}
html,body{background:transparent}
body{margin:0;padding:1px;font-family:var(--f-body);color:var(--ink);font-size:15px;line-height:1.45}
.card{background:var(--bg);border:1px solid var(--line);border-radius:16px;padding:18px 20px;display:flex;flex-direction:column;gap:14px;position:relative;overflow:hidden}
.card::before{content:"";position:absolute;inset:0 auto 0 0;width:4px;background:var(--accent)}
.head{display:flex;justify-content:space-between;align-items:center;gap:10px;flex-wrap:wrap}
.eyebrow{font:500 11px var(--f-mono);letter-spacing:.14em;text-transform:uppercase;color:var(--muted)}
.row{display:flex;gap:8px;flex-wrap:wrap;align-items:center}
.btn{appearance:none;border:1px solid var(--line);background:var(--bg);color:var(--ink);font:600 14px var(--f-body);padding:8px 16px;border-radius:8px;cursor:pointer;transition:border-color .15s,background .15s}
.btn:hover:not(:disabled){border-color:var(--accent)}
.btn:focus-visible,input:focus-visible{outline:2px solid var(--accent);outline-offset:2px}
.btn.primary{background:var(--accent);border-color:var(--accent);color:var(--on)}
.btn.primary:hover:not(:disabled){filter:brightness(1.08)}
.btn:disabled{opacity:.4;cursor:not-allowed}
.pill{font:500 11px var(--f-mono);letter-spacing:.04em;padding:5px 11px;border-radius:999px;border:1px solid var(--line);color:var(--muted);display:inline-flex;align-items:center;gap:7px}
.pill::before{content:"";width:7px;height:7px;border-radius:50%;background:currentColor;opacity:.7}
.pill.on{color:var(--good);border-color:var(--good)} .pill.on::before{animation:pulse 1.6s ease-in-out infinite;opacity:1}
.pill.err{color:var(--bad);border-color:var(--bad)}
@keyframes pulse{50%{transform:scale(.55);opacity:.4}}
@media (prefers-reduced-motion:reduce){.pill.on::before{animation:none}.btn{transition:none}}
.mono{font-family:var(--f-mono);font-variant-numeric:tabular-nums}
.muted{color:var(--muted)}
canvas{display:block;width:100%;border:1px solid var(--line);border-radius:10px;background:var(--lane)}
label{display:flex;gap:7px;align-items:center;font-weight:500;font-size:14px;cursor:pointer;color:var(--ink)}
label input{width:16px;height:16px;accent-color:var(--accent)}
.chips{display:flex;flex-wrap:wrap;gap:5px}
.chip{font:12px var(--f-mono);padding:3px 7px;border-radius:6px;border:1px solid var(--line)}
.chip.g{color:var(--good);border-color:var(--good)} .chip.m{color:var(--warm);border-color:var(--warm)} .chip.b{color:var(--bad);border-color:var(--bad)}
#micHelp{background:var(--soft);color:var(--ink);border-radius:10px;padding:10px 12px}
</style>
<script>
const NAMES=['Do','Do♯','Re','Re♯','Mi','Fa','Fa♯','Sol','Sol♯','La','La♯','Si'];
const nameOf=m=>{m=Math.round(m);return NAMES[((m%12)+12)%12]+(Math.floor(m/12)-1)};
const f2m=f=>69+12*Math.log2(f/440), m2f=m=>440*Math.pow(2,(m-69)/12);
const fold=(v,t)=>((v-t)%12+18)%12-6;
const C=()=>{const s=getComputedStyle(document.documentElement);const g=n=>s.getPropertyValue(n).trim();return{lane:g('--lane'),line:g('--line'),ink:g('--ink'),muted:g('--muted'),accent:g('--accent'),soft:g('--soft'),good:g('--good'),warm:g('--warm'),on:g('--on')}};
let ctx=null,an=null,buf=null,micOn=false,hist=[],cur=null;const voices=[];
function audio(){if(!ctx)ctx=new(window.AudioContext||window.webkitAudioContext)();if(ctx.state==='suspended')ctx.resume();return ctx}
function detect(b,sr){let r=0;for(let i=0;i<b.length;i++)r+=b[i]*b[i];if(Math.sqrt(r/b.length)<0.012)return -1;
 let a=0,e=b.length-1;for(let i=0;i<b.length/2;i++)if(Math.abs(b[i])<.2){a=i;break}for(let i=1;i<b.length/2;i++)if(Math.abs(b[b.length-i])<.2){e=b.length-i;break}
 const x=b.slice(a,e),n=x.length;if(n<256)return -1;const c=new Float32Array(n),L=Math.min(n-1,Math.floor(sr/65));
 for(let l=0;l<=L;l++){let s=0;for(let i=0;i<n-l;i++)s+=x[i]*x[i+l];c[l]=s}
 let d=0;while(d<L&&c[d]>c[d+1])d++;let mx=-1,p=-1;for(let i=d;i<=L;i++)if(c[i]>mx){mx=c[i];p=i}
 if(p<=0||mx<c[0]*.35)return -1;const x1=c[p-1],x2=c[p],x3=c[p+1]||x2,A=(x1+x3-2*x2)/2,B=(x3-x1)/2,T=A?p-B/(2*A):p,f=sr/T;return(f>65&&f<1200)?f:-1}
let micStream=null,micSrc=null;
async function startMic(pill,btn){try{const st=await navigator.mediaDevices.getUserMedia({audio:{echoCancellation:false,noiseSuppression:false,autoGainControl:false}});
 const c=audio();an=c.createAnalyser();an.fftSize=2048;micSrc=c.createMediaStreamSource(st);micSrc.connect(an);micStream=st;buf=new Float32Array(2048);micOn=true;
 pill.className='pill on';pill.textContent='Microfono attivo';btn.textContent='Spegni microfono';btn.classList.remove('primary')}
 catch(e){pill.className='pill err';pill.textContent='Microfono bloccato';
  const m=document.getElementById('micHelp');if(m)m.hidden=false}}
// spegne davvero il microfono: il browser toglie anche l'indicatore di registrazione
function stopMic(pill,btn){if(micStream)micStream.getTracks().forEach(t=>t.stop());if(micSrc)try{micSrc.disconnect()}catch(e){}
 micStream=null;micSrc=null;an=null;micOn=false;cur=null;hist=[];
 pill.className='pill';pill.textContent='Microfono spento';btn.textContent='Attiva microfono';btn.classList.add('primary')}
const toggleMic=(pill,btn)=>micOn?stopMic(pill,btn):startMic(pill,btn);
function readMic(){if(!micOn||!an){cur=null;return}an.getFloatTimeDomainData(buf);const f=detect(buf,ctx.sampleRate);
 if(f>0){hist.push(f2m(f));if(hist.length>5)hist.shift();const s=[...hist].sort((a,b)=>a-b);cur=s[s.length>>1]}else{hist=[];cur=null}}
function tone(m,w,d,v=.18){const c=audio(),o=c.createOscillator(),o2=c.createOscillator(),g=c.createGain(),g2=c.createGain();o.type='triangle';o.frequency.value=m2f(m);o2.frequency.value=m2f(m)*2;g2.gain.value=.25;
 o.connect(g);o2.connect(g2);g2.connect(g);g.connect(c.destination);const e=w+Math.max(.12,d-.04);
 g.gain.setValueAtTime(0,w);g.gain.linearRampToValueAtTime(v,w+.025);g.gain.setTargetAtTime(v*.7,w+.05,.15);g.gain.setTargetAtTime(0,e,.04);
 o.start(w);o2.start(w);o.stop(e+.3);o2.stop(e+.3);voices.push(o,o2)}
function click(w,acc){const c=audio(),o=c.createOscillator(),g=c.createGain();o.frequency.value=acc?1500:1000;o.connect(g);g.connect(c.destination);
 g.gain.setValueAtTime(.25,w);g.gain.exponentialRampToValueAtTime(.001,w+.06);o.start(w);o.stop(w+.08);voices.push(o)}
function silence(){while(voices.length){try{voices.pop().stop()}catch(e){}}}
function sizeCanvas(cv){const d=devicePixelRatio||1,W=cv.clientWidth,H=cv.clientHeight;if(cv.width!==Math.round(W*d)||cv.height!==Math.round(H*d)){cv.width=Math.round(W*d);cv.height=Math.round(H*d)}const g=cv.getContext('2d');g.setTransform(d,0,0,d,0,0);return[g,W,H]}
</script>
<p id="micHelp" class="muted" style="font-size:13px;margin:0 0 8px" hidden>
Il browser ha bloccato il microfono. Clicca l'icona a sinistra dell'indirizzo (lucchetto o impostazioni),
imposta <b>Microfono: Consenti</b> e ricarica la pagina.</p>
"""

_TUNER = r"""
<div class="card">
  <div class="head">
    <span class="eyebrow">Accordatore in diretta</span>
    <div class="row"><span class="pill" id="pill">Microfono spento</span><button class="btn primary" id="go">Attiva microfono</button></div>
  </div>
  <div class="row" style="align-items:flex-end;gap:24px">
    <div id="note" style="font-family:var(--f-display);font-size:76px;font-weight:800;line-height:.95;letter-spacing:-.04em;min-width:3.2ch">—</div>
    <div class="mono muted"><div id="hz">0 Hz</div><div id="ct">± 0 cents</div></div>
  </div>
  <div style="position:relative;height:36px;border:1px solid var(--line);border-radius:8px;background:var(--lane);overflow:hidden">
    <div style="position:absolute;left:40%;width:20%;top:0;bottom:0;background:color-mix(in srgb,var(--good) 18%,transparent)"></div>
    <div style="position:absolute;left:50%;top:0;bottom:0;width:2px;background:var(--good)"></div>
    <div id="needle" style="position:absolute;top:5px;bottom:5px;width:6px;border-radius:3px;background:var(--ink);left:50%;transform:translateX(-50%);transition:left .08s linear"></div>
  </div>
  <div class="row mono muted" style="justify-content:space-between;font-size:12px"><span>−50 calante</span><span>crescente +50</span></div>
  <canvas id="cv" style="height:150px"></canvas>
</div>
<script>
const pill=document.getElementById('pill'),go=document.getElementById('go'),cv=document.getElementById('cv');
go.onclick=()=>toggleMic(pill,go);
const trail=[];let last=0;
function loop(){readMic();const now=performance.now()/1000;trail.push({t:now,m:cur});while(trail.length&&trail[0].t<now-8)trail.shift();
 if(cur!==null){last=now;const r=Math.round(cur),c=Math.round((cur-r)*100);
  document.getElementById('note').textContent=nameOf(r);document.getElementById('hz').textContent=m2f(cur).toFixed(1)+' Hz';
  document.getElementById('ct').textContent=(c>0?'+':c<0?'−':'± ')+Math.abs(c)+' cents';
  const n=document.getElementById('needle');n.style.left=(50+c)+'%';n.style.background=Math.abs(c)<=10?'var(--good)':'var(--ink)'}
 const[g,W,H]=sizeCanvas(cv),k=C();g.fillStyle=k.lane;g.fillRect(0,0,W,H);
 const ms=trail.filter(p=>p.m!==null).map(p=>p.m);const mid=ms.length?ms[ms.length-1]:60,lo=Math.round(mid)-7,hi=Math.round(mid)+7,y=m=>6+(hi-m)/(hi-lo)*(H-12);
 g.font='11px "IBM Plex Mono",ui-monospace,monospace';g.textBaseline='middle';
 for(let m=lo;m<=hi;m++){const nat=[0,2,4,5,7,9,11].includes(((m%12)+12)%12);g.strokeStyle=k.line;g.globalAlpha=nat?1:.35;g.beginPath();g.moveTo(44,y(m));g.lineTo(W,y(m));g.stroke();g.globalAlpha=1;if(nat){g.fillStyle=k.muted;g.fillText(nameOf(m),4,y(m))}}
 g.lineWidth=3;g.lineCap='round';let pr=null;
 for(const p of trail){if(p.m===null){pr=null;continue}const x=44+(p.t-(now-8))/8*(W-48),yy=y(Math.max(lo,Math.min(hi,p.m)));
  if(pr){g.strokeStyle=Math.abs(p.m-Math.round(p.m))<.1?k.good:k.accent;g.beginPath();g.moveTo(pr[0],pr[1]);g.lineTo(x,yy);g.stroke()}pr=[x,yy]}
 requestAnimationFrame(loop)}
requestAnimationFrame(loop);
</script>
"""

_PRACTICE = r"""
<style>
.coach{border:1px solid var(--line);border-radius:12px;padding:14px 16px;background:var(--lane);display:flex;flex-direction:column;gap:10px}
.steps{display:flex;gap:6px;flex-wrap:wrap;align-items:center}
.stp{font:600 12px var(--f-body);padding:4px 11px;border-radius:999px;border:1px solid var(--line);color:var(--muted);background:var(--bg)}
.stp.on{background:var(--accent);border-color:var(--accent);color:var(--on)}
.stp.done{color:var(--good);border-color:var(--good)}
.stp.done::before{content:"✓ "}
.ctitle{font:800 20px/1.2 var(--f-display);letter-spacing:-.01em}
#cTips{margin:0;padding-left:1.2em;display:flex;flex-direction:column;gap:4px}
.cue{position:absolute;top:10px;right:12px;font:800 20px var(--f-display);padding:4px 12px;border-radius:10px;background:var(--bg);border:2px solid currentColor}
.cue.up,.cue.down{color:var(--warm)} .cue.ok{color:var(--good)}
.delta{font:600 14px var(--f-body)} .delta.pos{color:var(--good)} .delta.neg{color:var(--warm)}
#lyr .s{color:var(--muted);transition:color .1s}#lyr .s.done{color:var(--accent)}#lyr .s.now{color:var(--accent);text-decoration:underline;text-decoration-thickness:3px;text-underline-offset:5px}
</style>
<div class="card">
  <div class="head">
    <span class="eyebrow" id="eyeb">Pratica in diretta</span>
    <div class="row"><span class="pill" id="pill">Microfono spento</span><button class="btn primary" id="micBtn">Attiva microfono</button></div>
  </div>
  <div class="coach" id="coachBox" hidden>
    <div class="steps"><span class="stp" id="s1">1 · Ascolta</span><span class="stp" id="s2">2 · Con la guida</span><span class="stp" id="s3">3 · Da solo</span>
      <span class="mono muted" id="lvl" style="margin-left:auto;font-size:12px"></span></div>
    <div class="ctitle" id="cTitle"></div>
    <div id="cText"></div>
    <ul id="cTips" hidden></ul>
    <div class="row" id="cActs"></div>
  </div>
  <div style="position:relative"><canvas id="cv" style="height:260px"></canvas><div class="cue" id="cue" hidden></div></div>
  <div id="lyr" style="font-family:var(--f-display);font-size:22px;min-height:1.4em;font-weight:800;letter-spacing:-.01em"></div>
  <div class="row" id="ctrl">
    <button class="btn primary" id="sing">Canta</button>
    <button class="btn" id="listen">Solo ascolto</button>
    <button class="btn" id="stop" disabled>Ferma</button>
    <label><input type="checkbox" id="guide" checked> Suona la guida</label>
    <label><input type="checkbox" id="loop"> Ripeti</label>
    <button class="btn" id="toCoach" hidden>Torna al percorso guidato</button>
  </div>
  <div class="row" id="ctrlCoach" hidden>
    <button class="btn" id="stop2" disabled>Ferma</button>
    <button class="btn" id="toFree">Modalità libera</button>
  </div>
  <div class="mono muted" id="status" style="font-size:13px">Attiva il microfono, poi premi Canta: partono 4 colpi di metronomo.</div>
  <div id="res" hidden style="border-top:1px solid var(--line);padding-top:10px;display:flex;flex-direction:column;gap:8px"></div>
</div>
<script>
const P=__PLAN__;
const LS={get(k,d){try{const v=localStorage.getItem(k);return v?JSON.parse(v):d}catch(e){return d}},set(k,v){try{localStorage.setItem(k,JSON.stringify(v))}catch(e){}}};
const $=id=>document.getElementById(id),cv=$('cv'),st=$('status');
const KEY=(P.kind||'song')+':'+(P.id||P.name||'');
let run=false,sing=false,t0=0,voice=[],full=false,spd=1,shift=0,useGuide=true,coachOn=!!P.coach,step=1,fails=0;
let N=[],lo=0,hi=0,t=P.lead;
function build(){N=P.notes.map(n=>Object.assign({},n,{midi:n.midi+shift}));lo=Math.min(...N.map(n=>n.midi))-2;hi=Math.max(...N.map(n=>n.midi))+2;
 if(hi-lo<12){const p=12-(hi-lo);lo-=Math.floor(p/2);hi+=Math.ceil(p/2)}}
build();
const target=tt=>N.find(n=>tt>=n.start&&tt<n.start+n.dur);
const spb=()=>60/P.bpm;
$('micBtn').onclick=()=>{if(micOn&&run)stop(true);toggleMic($('pill'),$('micBtn'))};

function setRunUI(r){$('stop').disabled=$('stop2').disabled=!r;$('sing').disabled=$('listen').disabled=r;
 for(const b of $('cActs').querySelectorAll('button'))b.disabled=r;$('toFree').disabled=r;$('toCoach').disabled=r}
async function start(s,guide,ref){if(s&&!micOn)await startMic($('pill'),$('micBtn'));const c=audio();silence();
 sing=s&&micOn;voice=[];full=false;useGuide=guide;$('res').hidden=true;$('cTips').hidden=true;
 let pre=.15;if(ref){tone(N[0].midi,c.currentTime+.1,1.1);pre=1.5}
 t0=c.currentTime+pre;const b=spb()/spd;for(let i=0;i<4;i++)click(t0+i*b,i===0);
 if(guide)for(const n of N)tone(n.midi,t0+n.start/spd,n.dur/spd);
 run=true;setRunUI(true);
 st.textContent=s?(micOn?(ref?'Ascolta la prima nota, poi al quarto colpo canta.':'Al quarto colpo inizia a cantare.'):'Microfono non attivo: ascolta senza punteggio.'):'Ascolta la melodia.'}
function stop(user){silence();run=false;setRunUI(false);$('cue').hidden=true;
 if(user){st.textContent='Fermato.';if(!coachOn&&sing&&voice.length)finish()}}
$('sing').onclick=()=>start(true,$('guide').checked);$('listen').onclick=()=>start(false,true);
$('stop').onclick=$('stop2').onclick=()=>stop(true);

// ---------- analisi del tentativo ----------
function analyze(){
 const per=N.map(n=>{const a=n.start+Math.min(.12,n.dur*.25),b=n.start+n.dur,fr=voice.filter(v=>v.t>=a&&v.t<b),vo=fr.filter(v=>v.m!==null);
  const dev=vo.map(v=>fold(v.m,n.midi)),ok=dev.filter(d=>Math.abs(d)<.5).length,avg=dev.length?dev.reduce((s,d)=>s+d,0)/dev.length:null;
  const sd=dev.length>3?Math.sqrt(dev.reduce((s,d)=>s+(d-avg)*(d-avg),0)/dev.length):null;
  const hit=voice.find(v=>v.t>=n.start&&v.t<b&&v.m!==null&&Math.abs(fold(v.m,n.midi))<.5);
  return{n,p:fr.length?ok/fr.length:0,avg,sd,att:hit?(hit.t-n.start)*1/spd:null,fr:fr.length,vo:vo.length}});
 const tot=per.reduce((s,x)=>s+x.n.dur,0),pct=Math.round(per.reduce((s,x)=>s+x.p*x.n.dur,0)/tot*100);
 const frames=per.reduce((s,x)=>s+x.fr,0),voiced=per.reduce((s,x)=>s+x.vo,0);
 const tips=[];
 const fl=per.filter(x=>x.avg!==null&&x.avg<-.3).length,sh=per.filter(x=>x.avg!==null&&x.avg>.3).length;
 if(fl>sh+1)tips.push('Tendi a calare: sostieni il fiato fino alla fine di ogni nota e pensa il suono «in alto».');
 else if(sh>fl+1)tips.push('Tendi a crescere: rilassa collo e mascella, non spingere il suono.');
 const atts=per.map(x=>x.att).filter(a=>a!==null).sort((a,b)=>a-b);
 if(atts.length>2&&atts[atts.length>>1]>.3)tips.push('Arrivi sulla nota in ritardo: immagina la nota prima di cantarla e attaccala decisa.');
 const sds=per.map(x=>x.sd).filter(x=>x!==null);
 if(sds.length&&sds.reduce((a,b)=>a+b,0)/sds.length>.35)tips.push('La voce oscilla dentro la nota: tieni il fiato costante, come un filo teso.');
 const worst=per.filter(x=>x.p<.5).sort((a,b)=>a.p-b.p).slice(0,2);
 if(worst.length){const names=[...new Set(worst.map(x=>nameOf(x.n.midi)))].join(' e ');
  const top=Math.max(...N.map(n=>n.midi)),bot=Math.min(...N.map(n=>n.midi));
  if(worst.every(x=>x.n.midi===top))tips.push('La nota più acuta ('+names+') è la più difficile: non spingere, lascia il suono leggero e «in avanti», sul viso.');
  else if(worst.every(x=>x.n.midi===bot))tips.push('La nota più grave ('+names+') è la più difficile: rilassa la gola e non abbassare il mento.');
  else tips.push('Le note più difficili: '+names+'. Cantale lentamente da sole con l\'accordatore.')}
 if(!tips.length&&pct>=80)tips.push('Note centrate e stabili: ottimo lavoro.');
 return{per,pct,silent:frames>0&&voiced/frames<.25,tips}}

function finish(){
 const r=analyze(),R=$('res');R.replaceChildren();
 if(r.silent){const p=document.createElement('div');p.textContent='Non ti ho sentito abbastanza: avvicinati al microfono o canta un po\' più forte, poi riprova.';
  R.append(p);R.hidden=false;st.textContent='Nessun punteggio.';full=true;return r}
 const best=LS.get('pdv.best',{}),prev=best[KEY];
 const h=document.createElement('div');h.innerHTML='<b style="font-family:var(--f-display);font-size:40px;font-weight:800;letter-spacing:-.03em">'+r.pct+'%</b> ';
 const sp=document.createElement('span');sp.textContent='di note giuste';h.append(sp);
 if(typeof prev==='number'){const d=document.createElement('span');const diff=r.pct-prev;
  d.className='delta '+(diff>0?'pos':diff<0?'neg':'');d.textContent=diff>0?'  · nuovo record! +'+diff+' rispetto al '+prev+'%':'  · il tuo record: '+prev+'%';h.append(d)}
 best[KEY]=Math.max(prev||0,r.pct);LS.set('pdv.best',best);
 const ch=document.createElement('div');ch.className='chips';r.per.slice(0,80).forEach(x=>{const c=document.createElement('span');c.className='chip '+(x.p>=.7?'g':x.p>=.35?'m':'b');c.textContent=nameOf(x.n.midi)+' '+Math.round(x.p*100)+'%';ch.append(c)});
 R.append(h,ch);
 if(!coachOn){const ul=document.createElement('ul');ul.style.margin='0';ul.style.paddingLeft='1.2em';r.tips.forEach(x=>{const li=document.createElement('li');li.textContent=x;ul.append(li)});R.append(ul)}
 const note=document.createElement('div');note.className='muted';note.style.fontSize='13px';note.textContent='Vale anche cantare un\'ottava sopra o sotto la guida.';R.append(note);
 R.hidden=false;st.textContent='Fatto.';full=true;
 // salva il tentativo per la pagina dei progressi
 const log=LS.get('pdv.progress',[]);
 log.push({d:Date.now(),k:P.kind||'song',id:P.id||P.name||'',name:P.name||'',root:N[0].midi,bpm:Math.round(P.bpm*spd),guide:useGuide,pct:r.pct});
 LS.set('pdv.progress',log.slice(-2000));
 if(!useGuide&&r.pct>=80&&P.kind==='ex'){const lv=LS.get('pdv.levels',{});lv[P.id]=Math.max(lv[P.id]||0,N[0].midi);LS.set('pdv.levels',lv)}
 return r}

// ---------- percorso guidato ----------
function btn(label,fn,primary){const b=document.createElement('button');b.className='btn'+(primary?' primary':'');b.textContent=label;b.onclick=fn;return b}
function coachUI(title,text,acts,tips){
 [1,2,3].forEach(i=>{const e=$('s'+i);e.className='stp'+(i===step?' on':i<step?' done':'')});
 const lv=LS.get('pdv.levels',{})[P.id],rec=LS.get('pdv.best',{})[KEY];
 $('lvl').textContent='Partenza '+nameOf(N[0].midi)+' · velocità '+Math.round(spd*100)+'%'+(typeof rec==='number'?' · record '+rec+'%':'')+(lv?' · livello '+nameOf(lv):'');
 $('cTitle').textContent=title;$('cText').textContent=text;$('cActs').replaceChildren(...acts);
 const ul=$('cTips');ul.replaceChildren();(tips||[]).forEach(x=>{const li=document.createElement('li');li.textContent=x;ul.append(li)});ul.hidden=!(tips&&tips.length)}
function prompt(){
 const c=P.coach,syl=c.syll?'«'+c.syll+'»':'una vocale aperta';
 if(step===1)coachUI('Passo 1 · Ascolta',(c.prep?c.prep+' ':'')+'Ascolta l\'esercizio una volta, senza cantare. Canterai su '+syl+'.',
  [btn('Ascolta',()=>start(false,true),true),btn('Salta, canto subito',()=>{step=2;prompt()})]);
 else if(step===2)coachUI('Passo 2 · Canta con la guida','Canta insieme alla guida, su '+syl+'. '+(c.focus||''),
  [btn('Canta con la guida',()=>start(true,true),true),btn('Riascolta',()=>start(false,true))]);
 else coachUI('Passo 3 · Canta da solo','Senti solo la prima nota, poi i 4 colpi: canta senza aiuto. Per superare l\'esercizio serve almeno l\'80%.',
  [btn('Canta da solo',()=>start(true,false,true),true),btn('Torna con la guida',()=>{step=2;prompt()})])}
function after(r){
 if(r.silent){prompt();return}
 const p=r.pct;
 if(step===2){
  if(p>=70){fails=0;coachUI('Bene, '+p+'%!','Hai seguito la guida con sicurezza. Ora prova da solo: sentirai solo la prima nota.',
    [btn('Avanti: canta da solo',()=>{step=3;prompt()},true),btn('Ripeti con la guida',()=>start(true,true))],r.tips)}
  else{fails++;const acts=[btn('Riprova con la guida',()=>start(true,true),true)];
   if(fails>=2&&spd>.65)acts.push(btn('Rallenta e riprova',()=>{spd=Math.round((spd-.15)*100)/100;start(true,true)}));
   acts.push(btn('Riascolta',()=>start(false,true)));
   coachUI(p>=50?p+'%: ci sei quasi':p+'%: andiamo con calma','Appoggiati al suono della guida e canta le note tenendole ferme.'+(fails>=2&&spd>.65?' Se vuoi, rallentiamo un po\'.':''),acts,r.tips)}}
 else{
  if(p>=80){const acts=[btn('Sali di mezzo tono',()=>{shift++;build();step=2;fails=0;prompt()},true)];
   if(spd<1)acts.push(btn('Prova a velocità piena',()=>{spd=1;prompt()}));
   acts.push(btn('Riprova da solo',()=>start(true,false,true)));
   coachUI('Esercizio superato!','Hai cantato da solo con il '+p+'% di note giuste partendo da '+nameOf(N[0].midi)+'. Il livello è salvato nei tuoi progressi.',acts,r.tips)}
  else if(p>=60)coachUI('Quasi! '+p+'%','Ti manca poco: ripeti da solo, oppure torna un momento con la guida.',
   [btn('Riprova da solo',()=>start(true,false,true),true),btn('Torna con la guida',()=>{step=2;prompt()})],r.tips);
  else coachUI(p+'%: torniamo con la guida','Senza guida è ancora difficile: rinforziamo le note con la guida e poi riproviamo.',
   [btn('Canta con la guida',()=>{step=2;start(true,true)},true),btn('Riprova da solo',()=>start(true,false,true))],r.tips)}}
function setCoach(on){coachOn=on&&!!P.coach;$('coachBox').hidden=!coachOn;$('ctrlCoach').hidden=!coachOn;$('ctrl').hidden=coachOn;
 $('toCoach').hidden=!P.coach||coachOn;$('eyeb').textContent=coachOn?'Percorso guidato':'Pratica in diretta';if(coachOn)prompt()}
$('toFree').onclick=()=>setCoach(false);$('toCoach').onclick=()=>setCoach(true);
setCoach(true);

function draw(){const[g,W,H]=sizeCanvas(cv),k=C();g.fillStyle=k.lane;g.fillRect(0,0,W,H);const lw=44,py=12,y=m=>py+(hi-m)/(hi-lo)*(H-2*py);
 let x;if(full){const a=Math.max(0,P.lead-.6),b=P.total+.3;x=tt=>lw+(tt-a)/(b-a)*(W-lw-8)}else{const pps=(W-lw)*.72/5,ph=lw+(W-lw)*.26;x=tt=>ph+(tt-t)*pps}
 g.font='11px "IBM Plex Mono",ui-monospace,monospace';g.textBaseline='middle';
 for(let m=lo;m<=hi;m++){const nat=[0,2,4,5,7,9,11].includes(((m%12)+12)%12);g.strokeStyle=k.line;g.globalAlpha=nat?1:.35;g.beginPath();g.moveTo(lw,y(m));g.lineTo(W,y(m));g.stroke();g.globalAlpha=1;if(nat&&(hi-lo<=20||m%12===0||m%12===7)){g.fillStyle=k.muted;g.fillText(nameOf(m),4,y(m))}}
 const rh=Math.max(6,(H-2*py)/(hi-lo)*.8);
 for(const n of N){const x0=x(n.start),x1=x(n.start+n.dur);if(x1<lw||x0>W)continue;const act=!full&&t>=n.start&&t<n.start+n.dur;
  g.fillStyle=act?k.accent:k.soft;g.strokeStyle=k.accent;g.lineWidth=1.5;const xx=Math.max(x0+1,lw),ww=Math.max(2,x1-2-xx);g.beginPath();g.rect(xx,y(n.midi)-rh/2,ww,rh);g.fill();g.stroke();
  if(ww>34&&rh>=10){g.fillStyle=act?k.on:k.accent;g.fillText(nameOf(n.midi),xx+5,y(n.midi))}
  if(n.syl){g.save();g.font=(act?'700 ':'600 ')+'13px "IBM Plex Sans",system-ui,sans-serif';g.fillStyle=act?k.accent:k.ink;g.textBaseline='top';g.fillText(n.syl,xx+1,y(n.midi)+rh/2+4);g.restore()}}
 g.lineWidth=3;g.lineCap='round';let pr=null;
 for(const v of voice){if(v.m===null){pr=null;continue}const tg=target(v.t);let m=v.m;if(tg)m=tg.midi+fold(v.m,tg.midi);else{while(m>hi+1)m-=12;while(m<lo-1)m+=12}
  const px=x(v.t),yy=y(Math.max(lo,Math.min(hi,m)));if(pr&&px>=lw&&px-pr[0]<30){g.strokeStyle=tg&&Math.abs(m-tg.midi)<.5?k.good:k.warm;g.beginPath();g.moveTo(pr[0],pr[1]);g.lineTo(px,yy);g.stroke()}pr=[px,yy]}
 if(!full){const px=x(t);g.strokeStyle=k.ink;g.globalAlpha=.5;g.lineWidth=1.5;g.beginPath();g.moveTo(px,0);g.lineTo(px,H);g.stroke();g.globalAlpha=1;
  if(run&&sing&&cur!==null){const tg=target(t);let m=tg?tg.midi+fold(cur,tg.midi):cur;m=Math.max(lo,Math.min(hi,m));g.fillStyle=tg&&Math.abs(m-tg.midi)<.5?k.good:k.warm;g.beginPath();g.arc(px,y(m),6,0,7);g.fill()}}}
// testo della frase: ogni sillaba si colora quando arriva la sua nota
let lyrP=-2,lyrS=[];
function renderLyr(p){lyrP=p;const L=$('lyr');L.replaceChildren();lyrS=[];
 const ns=N.filter(n=>n.phrase===p),has=ns.some(n=>n.syl);
 if(!has){L.textContent=(P.lyrics&&P.lyrics[p])||'';return}
 for(const n of ns){if(!n.syl)continue;const s=document.createElement('span');s.className='s';s.textContent=n.syl;L.append(s);lyrS.push({s,n});if(n.we)L.append(' ')}}
function updLyr(tt){for(const o of lyrS){o.s.classList.toggle('done',tt>=o.n.start+o.n.dur);o.s.classList.toggle('now',tt>=o.n.start&&tt<o.n.start+o.n.dur)}}
if(N.length)renderLyr(N[0].phrase);
function cue(){const c=$('cue');const tg=run&&sing&&t>=P.lead?target(t):null;
 if(!tg||cur===null){c.hidden=true;return}const d=fold(cur,tg.midi);c.hidden=false;
 if(Math.abs(d)<.5){c.className='cue ok';c.textContent='✓ giusto'}else if(d<0){c.className='cue up';c.textContent='↑ più su'}else{c.className='cue down';c.textContent='↓ più giù'}}
function loop(){readMic();
 if(run){t=(ctx.currentTime-t0)*spd;if(sing)voice.push({t,m:cur});const n=target(t);
  if(n&&n.phrase!==lyrP)renderLyr(n.phrase);updLyr(t);cue();
  if(t<0)st.textContent='Ascolta la prima nota…';
  else if(t<P.lead)st.textContent='Attacco tra '+Math.ceil((P.lead-t)/spb())+'…';
  else if(n)st.textContent='Nota: '+nameOf(n.midi)+(sing&&cur!==null?'   ·   tu: '+nameOf(cur):'');
  if(t>P.total+.4){stop(false);
   if(sing){const r=finish();if(coachOn)after(r)}
   else{st.textContent='Fine. Ora prova a cantarla.';if(coachOn&&step===1){step=2;prompt()}}
   if(!coachOn&&$('loop').checked)setTimeout(()=>start(sing,$('guide').checked),900);else if(micOn)stopMic($('pill'),$('micBtn'))}}
 draw();requestAnimationFrame(loop)}
requestAnimationFrame(loop);
</script>
"""

_PROGRESS = r"""
<style>
.tiles{display:grid;grid-template-columns:repeat(auto-fit,minmax(150px,1fr));gap:10px}
.tile{border:1px solid var(--line);border-radius:12px;padding:12px 14px;background:var(--bg)}
.tile b{display:block;font:800 30px/1.1 var(--f-display);letter-spacing:-.02em;font-variant-numeric:tabular-nums}
.tile span{font-size:13px;color:var(--muted)}
.tile .delta{font:600 13px var(--f-body)} .pos{color:var(--good)} .neg{color:var(--warm)}
.days{display:grid;grid-template-columns:repeat(28,minmax(0,1fr));gap:3px}
.days i{display:block;aspect-ratio:1;border-radius:3px;background:var(--lane);border:1px solid var(--line)}
.days i.l1{background:color-mix(in srgb,var(--good) 35%,var(--bg));border-color:transparent}
.days i.l2{background:color-mix(in srgb,var(--good) 65%,var(--bg));border-color:transparent}
.days i.l3{background:var(--good);border-color:transparent}
.tbl{width:100%;border-collapse:collapse;font-size:14px}
.tbl th{text-align:left;font:500 11px var(--f-mono);letter-spacing:.08em;text-transform:uppercase;color:var(--muted);padding:6px 8px;border-bottom:1px solid var(--line)}
.tbl td{padding:8px;border-bottom:1px solid var(--line);font-variant-numeric:tabular-nums}
.wrapx{overflow-x:auto}
select{font:600 14px var(--f-body);background:var(--bg);color:var(--ink);border:1px solid var(--line);border-radius:8px;padding:6px 8px}
.sec{display:flex;flex-direction:column;gap:8px}
.h{font:800 18px var(--f-display)}
</style>
<div class="card" id="root">
  <div class="head"><span class="eyebrow">I tuoi progressi</span><span class="muted" style="font-size:13px">Salvati in questo browser</span></div>
  <div id="empty" hidden class="sec">
    <div class="h">Ancora nessun risultato</div>
    <div class="muted">Fai un esercizio nella scheda Esercizi (o canta una canzone) e torna qui: ogni tentativo viene registrato e vedrai come migliori giorno per giorno.</div>
  </div>
  <div id="full" class="sec" style="gap:18px">
    <div class="tiles">
      <div class="tile"><b id="tStreak">0</b><span>giorni di fila</span></div>
      <div class="tile"><b id="tWeek">0</b><span>tentativi negli ultimi 7 giorni</span></div>
      <div class="tile"><b id="tAvg">—</b><span>media ultimi 7 giorni</span><div class="delta" id="tDelta"></div></div>
      <div class="tile"><b id="tLevels">0</b><span>esercizi superati da solo</span></div>
    </div>
    <div class="sec"><div class="h">Ultimi 28 giorni</div><div class="days" id="days"></div></div>
    <div class="sec">
      <div class="row" style="justify-content:space-between"><div class="h">Andamento del punteggio</div><select id="filt" aria-label="Cosa mostrare"></select></div>
      <canvas id="ch" style="height:230px;background:var(--bg)"></canvas>
      <div class="muted" style="font-size:13px">Ogni punto è un tentativo. La linea unisce il risultato migliore di ogni giorno. La riga tratteggiata è l'obiettivo dell'80%.</div>
    </div>
    <div class="sec"><div class="h">Esercizi e canzoni</div><div class="wrapx"><table class="tbl"><thead><tr><th>Esercizio</th><th>Tentativi</th><th>Record</th><th>Ultimo</th><th>Livello</th><th>Tendenza</th></tr></thead><tbody id="rows"></tbody></table></div></div>
    <div class="row"><button class="btn" id="reset">Azzera i progressi</button><span id="confirm" hidden class="row"><span>Cancellare tutti i risultati?</span><button class="btn primary" id="yes">Sì, azzera</button><button class="btn" id="no">Annulla</button></span></div>
  </div>
</div>
<script>
const LS={get(k,d){try{const v=localStorage.getItem(k);return v?JSON.parse(v):d}catch(e){return d}},set(k,v){try{localStorage.setItem(k,JSON.stringify(v))}catch(e){}}};
const $=id=>document.getElementById(id);
const DAY=86400000,dayKey=ts=>{const d=new Date(ts);d.setHours(0,0,0,0);return d.getTime()};
const KIND={ex:'',song:'Canzone · ',karaoke:'Karaoke · ',lesson:'Lezione · '};
let log=[];
function render(){log=LS.get('pdv.progress',[]);const empty=!log.length;$('empty').hidden=!empty;$('full').hidden=empty;if(empty)return;
 const today=dayKey(Date.now()),days=new Set(log.map(r=>dayKey(r.d)));
 let s=0,d=days.has(today)?today:today-DAY;while(days.has(d)){s++;d-=DAY}$('tStreak').textContent=s;
 const w=log.filter(r=>r.d>=today-6*DAY),pw=log.filter(r=>r.d>=today-13*DAY&&r.d<today-6*DAY);
 $('tWeek').textContent=w.length;const avg=a=>a.length?Math.round(a.reduce((x,r)=>x+r.pct,0)/a.length):null;
 const A=avg(w),B=avg(pw);$('tAvg').textContent=A===null?'—':A+'%';const dl=$('tDelta');
 if(A!==null&&B!==null){const df=A-B;dl.className='delta '+(df>0?'pos':df<0?'neg':'');dl.textContent=(df>0?'+':'')+df+' rispetto alla settimana prima'}else dl.textContent='';
 const lv=LS.get('pdv.levels',{});$('tLevels').textContent=Object.keys(lv).length;
 const D=$('days');D.replaceChildren();for(let i=27;i>=0;i--){const k=today-i*DAY,c=log.filter(r=>dayKey(r.d)===k).length,e=document.createElement('i');
  e.className=c>=8?'l3':c>=4?'l2':c>=1?'l1':'';e.title=new Date(k).toLocaleDateString('it-IT')+': '+c+' tentativi';D.append(e)}
 // filtro
 const groups={};for(const r of log){const g=r.k+':'+r.id;(groups[g]=groups[g]||{k:r.k,id:r.id,name:r.name,items:[]}).items.push(r)}
 const F=$('filt'),cur=F.value;F.replaceChildren(new Option('Tutto','all'));
 Object.entries(groups).forEach(([g,o])=>F.append(new Option(KIND[o.k]+o.name,g)));F.value=[...F.options].some(o=>o.value===cur)?cur:'all';
 drawChart(F.value==='all'?log:groups[F.value].items);
 // tabella
 const R=$('rows');R.replaceChildren();
 Object.values(groups).sort((a,b)=>b.items[b.items.length-1].d-a.items[a.items.length-1].d).forEach(o=>{
  const it=o.items,best=Math.max(...it.map(r=>r.pct)),last=it[it.length-1].pct;
  const f3=avg(it.slice(0,3)),l3=avg(it.slice(-3));let tr='—';if(it.length>=4){const df=l3-f3;tr=(df>0?'↑ +':df<0?'↓ ':'= ')+df+' punti'}
  const tr_=document.createElement('tr');
  [KIND[o.k]+o.name,it.length,best+'%',last+'%',o.k==='ex'&&lv[o.id]?'superato da '+nameOf(lv[o.id]):o.k==='ex'?'non ancora':'—',tr].forEach((v,i)=>{
   const td=document.createElement('td');td.textContent=v;if(i===5&&String(v).startsWith('↑'))td.className='pos';if(i===5&&String(v).startsWith('↓'))td.className='neg';tr_.append(td)});R.append(tr_)})}
function drawChart(items){const cv=$('ch'),[g,W,H]=sizeCanvas(cv),k=C();g.clearRect(0,0,W,H);
 const today=dayKey(Date.now()),first=Math.min(today-6*DAY,dayKey(Math.min(...items.map(r=>r.d)))),last=today+DAY;
 const L=36,Rr=10,T=10,Bt=26,x=ts=>L+(ts-first)/(last-first)*(W-L-Rr),y=p=>T+(100-p)/100*(H-T-Bt);
 g.font='11px "IBM Plex Mono",monospace';g.fillStyle=k.muted;g.textBaseline='middle';
 for(const p of [0,50,100]){g.strokeStyle=k.line;g.lineWidth=1;g.beginPath();g.moveTo(L,y(p));g.lineTo(W-Rr,y(p));g.stroke();g.fillText(p+'%',2,y(p))}
 g.setLineDash([5,4]);g.strokeStyle=k.good;g.beginPath();g.moveTo(L,y(80));g.lineTo(W-Rr,y(80));g.stroke();g.setLineDash([]);g.fillStyle=k.good;g.fillText('80%',2,y(80));
 const span=(last-first)/DAY,step=Math.max(1,Math.ceil(span/6));g.fillStyle=k.muted;g.textBaseline='top';
 for(let d=first;d<last;d+=step*DAY){const dt=new Date(d);g.fillText(dt.getDate()+'/'+(dt.getMonth()+1),x(d)-10,H-Bt+8)}
 g.fillStyle=k.accent;g.globalAlpha=.35;for(const r of items){g.beginPath();g.arc(x(r.d),y(r.pct),3.5,0,7);g.fill()}g.globalAlpha=1;
 const byDay={};for(const r of items){const d=dayKey(r.d);byDay[d]=Math.max(byDay[d]||0,r.pct)}
 const pts=Object.keys(byDay).map(Number).sort((a,b)=>a-b).map(d=>[x(d+DAY/2),y(byDay[d])]);
 g.strokeStyle=k.accent;g.lineWidth=2.5;g.beginPath();pts.forEach(([a,b],i)=>i?g.lineTo(a,b):g.moveTo(a,b));g.stroke();
 g.fillStyle=k.accent;for(const [a,b] of pts){g.beginPath();g.arc(a,b,4.5,0,7);g.fill()}}
$('filt').onchange=render;
$('reset').onclick=()=>{$('confirm').hidden=false;$('reset').hidden=true};
$('no').onclick=()=>{$('confirm').hidden=true;$('reset').hidden=false};
$('yes').onclick=()=>{LS.set('pdv.progress',[]);LS.set('pdv.levels',{});LS.set('pdv.best',{});$('confirm').hidden=true;$('reset').hidden=false;render()};
window.addEventListener('storage',e=>{if(!e.key||e.key.startsWith('pdv.'))render()});
document.addEventListener('visibilitychange',()=>{if(!document.hidden)render()});
setInterval(render,5000);
render();new ResizeObserver(render).observe($('ch'));
</script>
"""


_LESSON = r"""
<style>
.lsteps{display:flex;gap:6px;flex-wrap:wrap}
.lst{appearance:none;font:600 12px var(--f-body);padding:5px 11px;border-radius:999px;border:1px solid var(--line);color:var(--muted);background:var(--bg);cursor:pointer}
.lst.on{background:var(--accent);border-color:var(--accent);color:var(--on)}
.lst.done{color:var(--good);border-color:var(--good)} .lst.done::before{content:"✓ "}
.lst.on.done{color:var(--on)}
.atitle{font:800 22px/1.2 var(--f-display);letter-spacing:-.01em}
.box{border:1px solid var(--line);border-radius:12px;padding:12px 14px;background:var(--lane);display:flex;flex-direction:column;gap:6px}
.box h4{margin:0;font:500 11px var(--f-mono);letter-spacing:.12em;text-transform:uppercase;color:var(--muted)}
.box p{margin:0;max-width:70ch}
.stage{display:flex;flex-direction:column;gap:10px;align-items:stretch}
.big{font:800 30px/1.1 var(--f-display);text-align:center;letter-spacing:-.02em;min-height:1.2em}
.sub{text-align:center;color:var(--muted);min-height:1.3em}
.cells{display:flex;gap:4px;justify-content:center;flex-wrap:wrap}
.cells i{width:30px;height:30px;border-radius:7px;border:1px solid var(--line);background:var(--bg);display:flex;align-items:center;justify-content:center;font:600 12px var(--f-mono);font-style:normal;color:var(--muted)}
.cells i.now{border-color:var(--accent);color:var(--accent)}
.cells i.g{background:var(--good);border-color:var(--good);color:var(--on)}
.cells i.m{background:var(--warm);border-color:var(--warm);color:var(--on)}
.cells i.b{background:var(--line)}
.meter{position:relative;height:18px;border-radius:9px;background:var(--bg);border:1px solid var(--line);overflow:hidden}
.meter .band{position:absolute;top:0;bottom:0;background:color-mix(in srgb,var(--good) 20%,transparent)}
.meter .lvl{position:absolute;left:0;top:0;bottom:0;background:var(--accent);transition:width .08s linear}
.result{border-top:1px solid var(--line);padding-top:10px;display:flex;flex-direction:column;gap:6px}
.result b.sc{font:800 30px var(--f-display)}
.result ul{margin:0;padding-left:1.2em;display:flex;flex-direction:column;gap:4px}
.check{display:flex;flex-direction:column;gap:8px}
.item{display:flex;gap:10px;align-items:flex-start;border:1px solid var(--line);border-radius:10px;padding:10px 12px;background:var(--bg)}
.item.ok{border-color:var(--good)}
.item .tx{flex:1;min-width:0}
.item .mk{width:22px;height:22px;border-radius:50%;border:2px solid var(--line);flex:none;display:flex;align-items:center;justify-content:center;color:var(--on);font-size:13px}
.item.ok .mk{background:var(--good);border-color:var(--good)}
.done-all{font:800 20px var(--f-display);color:var(--good)}
</style>
<div class="card">
  <div class="head">
    <div><div class="eyebrow" id="lEye"></div><div class="atitle" id="lTitle" style="font-size:16px;font-weight:600;font-family:var(--f-body)"></div></div>
    <div class="row"><span class="pill" id="pill">Microfono spento</span><button class="btn primary" id="micBtn">Attiva microfono</button></div>
  </div>
  <div class="lsteps" id="lsteps"></div>
  <div class="atitle" id="aTitle"></div>
  <div class="box" id="howBox"><h4>Cosa fare</h4><p id="aHow"></p></div>
  <div class="box" id="chkBox"><h4>Come capisci se va bene</h4><p id="aChk"></p></div>
  <div id="area" class="stage"></div>
  <div class="row" id="acts"></div>
  <div class="result" id="res" hidden></div>
</div>
<script>
const L=__LESSON__;
const LS={get(k,d){try{const v=localStorage.getItem(k);return v?JSON.parse(v):d}catch(e){return d}},set(k,v){try{localStorage.setItem(k,JSON.stringify(v))}catch(e){}}};
const $=id=>document.getElementById(id);
const el=(tag,cls,txt)=>{const e=document.createElement(tag);if(cls)e.className=cls;if(txt!==undefined)e.textContent=txt;return e};
const now=()=>performance.now()/1000;
$('micBtn').onclick=()=>{if(task)endTask(true);toggleMic($('pill'),$('micBtn'))};
let ai=0,task=null,rms=0,zcr=0;
const doneKey='pdv.lesson.'+L.id;let done=new Set(LS.get(doneKey,[]));
function readLevels(){if(!micOn||!an||!buf){rms=0;zcr=0;return}let s=0,z=0;for(let i=0;i<buf.length;i++){s+=buf[i]*buf[i];if(i&&(buf[i]>=0)!==(buf[i-1]>=0))z++}rms=Math.sqrt(s/buf.length);zcr=z/buf.length}
const med=a=>{if(!a.length)return 0;const s=[...a].sort((x,y)=>x-y);return s[s.length>>1]};
const mean=a=>a.length?a.reduce((x,y)=>x+y,0)/a.length:0;
const sdev=a=>{const m=mean(a);return Math.sqrt(mean(a.map(x=>(x-m)*(x-m))))};

function header(){$('lEye').textContent='Lezione '+L.n+' · '+L.title;$('lTitle').textContent='Attività '+(ai+1)+' di '+L.acts.length;
 const S=$('lsteps');S.replaceChildren();L.acts.forEach((a,i)=>{const b=el('button','lst'+(i===ai?' on':'')+(done.has(i)?' done':''),(i+1)+' · '+a.short);b.onclick=()=>{if(task)endTask(true);ai=i;show()};S.append(b)})}
function markDone(){done.add(ai);LS.set(doneKey,[...done]);header()}
function log(pct,label){const lg=LS.get('pdv.progress',[]);lg.push({d:Date.now(),k:'lesson',id:L.id+':'+ai,name:L.title+' · '+(label||L.acts[ai].short),pct:Math.max(0,Math.min(100,Math.round(pct)))});LS.set('pdv.progress',lg.slice(-2000))}
function btn(t,fn,p){const b=el('button','btn'+(p?' primary':''),t);b.onclick=fn;return b}
function setActs(list){$('acts').replaceChildren(...list)}
function nextBtn(){return ai<L.acts.length-1?btn('Avanti: '+L.acts[ai+1].short,()=>{ai++;show()},true):el('span','done-all','Lezione completata!')}
function result(score,lines,pass){const R=$('res');R.replaceChildren();
 if(score!==null){const h=el('div');h.append(el('b','sc',score),el('span','muted','  '+(pass?'· superato':'· da migliorare')));R.append(h)}
 const ul=el('ul');lines.forEach(x=>ul.append(el('li','',x)));R.append(ul);R.hidden=false}
function endTask(user){if(!task)return;const t=task;task=null;silence();if(t.end)t.end(user)}
async function needMic(){if(!micOn)await startMic($('pill'),$('micBtn'));if(!micOn){result(null,['Serve il microfono per questa attività: premi «Attiva microfono» in alto e consenti l\'accesso.'],false);return false}return true}

function show(){if(task)endTask(true);const a=L.acts[ai];header();$('aTitle').textContent=a.title;$('aHow').textContent=a.how;
 $('chkBox').hidden=!a.check;$('aChk').textContent=a.check||'';$('res').hidden=true;$('area').replaceChildren();
 ({check:actCheck,breath:actBreath,sustain:actSustain,siren:actSiren,echo:actEcho})[a.type](a)}

// ---------- lista guidata (con timer facoltativo) ----------
function actCheck(a){const box=el('div','check');let left=a.items.length;
 a.items.forEach(it=>{const row=el('div','item'),mk=el('span','mk',''),tx=el('div','tx',it.t);row.append(mk,tx);
  const ok=()=>{if(row.classList.contains('ok'))return;row.classList.add('ok');mk.textContent='✓';b.remove();left--;if(left===0){markDone();setActs([nextBtn()])}};
  const b=it.secs?btn('Avvia '+it.secs+' s',()=>{b.disabled=true;let r=it.secs;b.textContent=r+' s';click(audio().currentTime+.02,true);
    const iv=setInterval(()=>{r--;if(r<=0){clearInterval(iv);click(audio().currentTime+.02,true);ok()}else b.textContent=r+' s'},1000)}):btn('Fatto',ok);
  row.append(b);box.append(row)});
 $('area').append(box);setActs(done.has(ai)?[nextBtn()]:[])}

// ---------- respirazione: «sss» a tempo ----------
function actBreath(a){const N=a.beats,IN=a.inhale||4;
 const big=el('div','big','Pronto?'),sub=el('div','sub','Premi Inizia: prima 2 secondi di silenzio, poi inspiri per '+IN+' tempi ed espiri per '+N+'.');
 const cv=el('canvas');cv.style.height='120px';
 const cells=el('div','cells');for(let i=0;i<N;i++)cells.append(el('i','',i+1));
 const meter=el('div','meter'),band=el('div','band'),lvl=el('div','lvl');meter.append(band,lvl);band.style.left='35%';band.style.width='35%';lvl.style.width='0%';
 const lab=el('div','sub','Forza del flusso: tienila ferma dentro la fascia verde');
 $('area').append(big,sub,cv,cells,meter,lab);drawBreath(cv,0,'');
 setActs([btn('Inizia',()=>run(),true)].concat(done.has(ai)?[nextBtn()]:[]));
 async function run(){if(!(await needMic()))return;$('res').hidden=true;[...cells.children].forEach(c=>c.className='');
  const CAL=2,c=audio(),T0=now(),tc=c.currentTime;
  for(let i=0;i<IN;i++)click(tc+CAL+i,i===0);for(let j=0;j<N;j++)click(tc+CAL+IN+j,j===0);
  const floor=[],fr=new Array(N).fill(0),hs=new Array(N).fill(0),lev=[],levB=[];let thr=0.01,ref=0,lastHiss=0,any=false;
  setActs([btn('Ferma',()=>endTask(true))]);
  task={frame(){const e=now()-T0;
    if(e<CAL){floor.push(rms);big.textContent='Silenzio…';sub.textContent='Sto ascoltando il rumore della stanza.';drawBreath(cv,0,'');return}
    if(!ref){thr=Math.max(.006,med(floor)*3);ref=1}
    if(e<CAL+IN){const b=Math.floor(e-CAL);big.textContent='Inspira… '+(b+1);sub.textContent='Dal naso, lento: si allargano pancia e fianchi, le spalle restano giù.';drawBreath(cv,(e-CAL)/IN,'in');return}
    const b=Math.floor(e-CAL-IN);
    if(b>=N){endTask(false);return}
    const hiss=rms>thr&&zcr>.12&&cur===null;fr[b]++;if(hiss){hs[b]++;lev.push(rms);levB.push(b);lastHiss=e;any=true}
    big.textContent='«sss»… '+(b+1)+' / '+N;sub.textContent=hiss?'Bene, continua uguale':'Non sento l\'«sss»: soffia tra i denti, «sss»';
    [...cells.children].forEach((c,i)=>{c.className=i<b?(hs[i]/Math.max(1,fr[i])>=.6?'g':hs[i]/Math.max(1,fr[i])>=.25?'m':'b'):i===b?'now':''});
    const m=lev.length>10?med(lev.slice(0,Math.min(lev.length,60))):thr*3,w=Math.min(100,rms/(m*2)*100);lvl.style.width=(hiss?w:0)+'%';
    lvl.style.background=hiss&&w>=35&&w<=70?'var(--good)':'var(--accent)';
    drawBreath(cv,1-(e-CAL-IN)/N,'out');
    if(any&&e-lastHiss>1.6&&b>=1){endTask(false)}},
   end(user){const ratio=fr.map((f,i)=>f?hs[i]/f:0);let held=0;for(const r of ratio){if(r>=.6)held++;else break}
    [...cells.children].forEach((c,i)=>{c.className=fr[i]?(ratio[i]>=.6?'g':ratio[i]>=.25?'m':'b'):''});
    lvl.style.width='0%';big.textContent=held+' tempi su '+N;sub.textContent='';drawBreath(cv,0,'');
    const tot=hs.reduce((x,y)=>x+y,0);
    if(tot<15){result(null,['Non ho sentito l\'«sss». Avvicinati al microfono (circa 30 cm) e fai un «sss» ben udibile, come uno pneumatico che si sgonfia.'],false);setActs([btn('Riprova',()=>run(),true)]);return}
    const cv_=sdev(lev)/Math.max(1e-6,mean(lev));const third=Math.max(1,Math.floor(N/3));
    const first=mean(lev.filter((_,i)=>levB[i]<third)),lastP=mean(lev.filter((_,i)=>levB[i]>=N-third));
    const pass=held>=N-1&&cv_<.5,lines=[];
    if(held>=N)lines.push('Hai tenuto l\'«sss» per tutti i '+N+' tempi.');else lines.push('Hai tenuto l\'«sss» per '+held+' tempi su '+N+'.');
    if(held<N-1)lines.push('Il fiato è finito prima: inspira più in basso (pancia e fianchi) e all\'inizio fai uscire meno aria.');
    if(cv_>=.5)lines.push('Il flusso era a scatti: cerca un «sss» uguale dall\'inizio alla fine, come un filo sottile.');else if(cv_>=.3)lines.push('Il flusso era abbastanza costante: puoi renderlo ancora più regolare.');else lines.push('Il flusso era costante: ottimo controllo.');
    if(first&&lastP&&first>lastP*1.8)lines.push('Parti troppo forte e poi cali: all\'inizio trattieni un po\' l\'aria.');
    if(pass)lines.push(a.next||'Esercizio superato!');
    const score=Math.round(Math.min(1,held/N)*100*(cv_<.5?1:.8));result(score+'%',lines,pass);log(score,a.short);
    if(pass)markDone();setActs([btn('Riprova',()=>run(),!pass)].concat(pass||done.has(ai)?[nextBtn()]:[]))}}}}
function drawBreath(cv,f,ph){const[g,W,H]=sizeCanvas(cv),k=C();g.clearRect(0,0,W,H);const r=12+Math.max(0,Math.min(1,f))*(H/2-16);
 g.fillStyle=ph==='in'?k.soft:ph==='out'?k.soft:k.lane;g.strokeStyle=ph?k.accent:k.line;g.lineWidth=3;g.beginPath();g.arc(W/2,H/2,r,0,7);g.fill();g.stroke();
 g.fillStyle=k.muted;g.font='12px "IBM Plex Sans",sans-serif';g.textAlign='center';g.textBaseline='middle';if(ph)g.fillText(ph==='in'?'aria che entra':'aria che esce',W/2,H/2)}

// ---------- nota tenuta (vocale o humming) ----------
function actSustain(a){const D=a.secs||5;
 const big=el('div','big','—'),sub=el('div','sub','Premi Inizia: dopo 3 clic canta e tieni la nota per '+D+' secondi.');const cv=el('canvas');cv.style.height='150px';
 $('area').append(big,sub,cv);drawSus(cv,[],null);setActs([btn('Inizia',()=>run(),true)].concat(done.has(ai)?[nextBtn()]:[]));
 async function run(){if(!(await needMic()))return;$('res').hidden=true;const c=audio(),T0=now();for(let i=0;i<3;i++)click(c.currentTime+i,i===0);
  const pts=[],vals=[];setActs([btn('Ferma',()=>endTask(true))]);
  task={frame(){const e=now()-T0;if(e<3){big.textContent=String(3-Math.floor(e));sub.textContent='Prepara il fiato…';return}
    const tt=e-3;if(tt>=D){endTask(false);return}
    if(cur!==null)vals.push(cur);const m=vals.length>8?med(vals):cur;pts.push({t:tt,v:cur});
    big.textContent=cur!==null?nameOf(cur):'…';sub.textContent=(a.syll?'«'+a.syll+'» · ':'')+Math.ceil(D-tt)+' s';drawSus(cv,pts,m,D)},
   end(){const voicedF=pts.length?pts.filter(p=>p.v!==null).length/pts.length:0;
    if(vals.length<15){result(null,['Non ti ho sentito cantare. Avvicinati al microfono e canta a volume normale.'],false);setActs([btn('Riprova',()=>run(),true)]);return}
    const m=med(vals),sd=sdev(vals.map(v=>(v-m)*100)),lines=[];big.textContent=nameOf(m);sub.textContent='la tua nota';
    lines.push('Oscillazione media: '+Math.round(sd)+' cents (100 cents = mezzo tono).');
    if(sd<=20)lines.push('Nota fermissima: ottimo.');else if(sd<=35)lines.push('Nota abbastanza ferma: buon controllo.');else lines.push('La nota oscilla: tieni il fiato costante e la mascella ferma, senza spingere.');
    if(voicedF<.7)lines.push('La voce si interrompe: usa più fiato e non chiudere la gola.');
    const pass=sd<=35&&voicedF>=.7;if(pass&&a.next)lines.push(a.next);
    const score=Math.round(Math.max(0,100-Math.max(0,sd-10)*1.6)*Math.min(1,voicedF/.8));result(score+'%',lines,pass);log(score,a.short);if(pass)markDone();
    setActs([btn('Riprova',()=>run(),!pass)].concat(pass||done.has(ai)?[nextBtn()]:[]))}}}}
function drawSus(cv,pts,m,D){const[g,W,H]=sizeCanvas(cv),k=C();g.fillStyle=k.lane;g.fillRect(0,0,W,H);const y=c=>H/2-c/100*(H/2-8);
 g.fillStyle='color-mix(in srgb,'+k.good+' 18%,transparent)';g.fillStyle=k.good;g.globalAlpha=.15;g.fillRect(0,y(25),W,y(-25)-y(25));g.globalAlpha=1;
 g.strokeStyle=k.good;g.lineWidth=1.5;g.beginPath();g.moveTo(0,H/2);g.lineTo(W,H/2);g.stroke();
 g.fillStyle=k.muted;g.font='11px "IBM Plex Mono",monospace';g.textBaseline='middle';g.fillText('+50',4,10);g.fillText('−50',4,H-10);
 if(m===null||!pts.length)return;g.lineWidth=3;g.lineCap='round';let pr=null;
 for(const p of pts){if(p.v===null){pr=null;continue}const c=Math.max(-100,Math.min(100,(p.v-m)*100)),px=p.t/D*W,py=y(c);if(pr){g.strokeStyle=Math.abs(c)<=25?k.good:k.warm;g.beginPath();g.moveTo(pr[0],pr[1]);g.lineTo(px,py);g.stroke()}pr=[px,py]}}

// ---------- sirena ----------
function actSiren(a){const D=a.secs||8;const big=el('div','big','—'),sub=el('div','sub','Premi Inizia: dopo 3 clic hai '+D+' secondi per la sirena: su e poi giù.');
 const cv=el('canvas');cv.style.height='190px';$('area').append(big,sub,cv);drawSir(cv,[],D);
 setActs([btn('Inizia',()=>run(),true)].concat(done.has(ai)?[nextBtn()]:[]));
 async function run(){if(!(await needMic()))return;$('res').hidden=true;const c=audio(),T0=now();for(let i=0;i<3;i++)click(c.currentTime+i,i===0);
  const pts=[];setActs([btn('Ferma',()=>endTask(true))]);
  task={frame(){const e=now()-T0;if(e<3){big.textContent=String(3-Math.floor(e));sub.textContent='Labbra morbide, pronte a vibrare…';return}
    const tt=e-3;if(tt>=D){endTask(false);return}pts.push({t:tt,v:cur});big.textContent=cur!==null?nameOf(cur):'…';
    sub.textContent=tt<D/2?'Sali piano ↑':'Ora scendi ↓';drawSir(cv,pts,D)},
   end(){const vs=pts.filter(p=>p.v!==null).map(p=>p.v).sort((x,y)=>x-y),vf=pts.length?vs.length/pts.length:0;
    if(vs.length<15){result(null,['Non ho sentito la voce. Se il trillo di labbra non parte, prova con «vvv» o «mmm» facendo la stessa sirena.'],false);setActs([btn('Riprova',()=>run(),true)]);return}
    const lo=vs[Math.floor(vs.length*.08)],hi=vs[Math.floor(vs.length*.92)],rng=Math.round(hi-lo),lines=[];
    big.textContent=nameOf(lo)+' → '+nameOf(hi);sub.textContent='la tua sirena';
    lines.push('Hai percorso '+rng+' semitoni'+(rng>=12?': più di un\'ottava, ottimo riscaldamento!':rng>=7?': buon riscaldamento.':': prova a salire un po\' di più, sempre senza sforzo.'));
    if(vf<.5)lines.push('La voce si interrompe spesso: soffia in modo continuo e tieni le labbra morbide.');
    const pass=rng>=7&&vf>=.4;if(pass&&a.next)lines.push(a.next);const score=Math.round(Math.min(1,rng/12)*100*Math.min(1,vf/.6));
    result(score+'%',lines,pass);log(score,a.short);if(pass)markDone();setActs([btn('Riprova',()=>run(),!pass)].concat(pass||done.has(ai)?[nextBtn()]:[]))}}}}
function drawSir(cv,pts,D){const[g,W,H]=sizeCanvas(cv),k=C();g.fillStyle=k.lane;g.fillRect(0,0,W,H);const vs=pts.filter(p=>p.v!==null).map(p=>p.v);
 let lo=48,hi=72;if(vs.length){lo=Math.min(lo,Math.floor(Math.min(...vs))-1);hi=Math.max(hi,Math.ceil(Math.max(...vs))+1)}
 const y=m=>8+(hi-m)/(hi-lo)*(H-16),lw=40;g.font='11px "IBM Plex Mono",monospace';g.textBaseline='middle';
 for(let m=Math.ceil(lo);m<=hi;m++)if(m%12===0||m%12===7){g.strokeStyle=k.line;g.lineWidth=1;g.beginPath();g.moveTo(lw,y(m));g.lineTo(W,y(m));g.stroke();g.fillStyle=k.muted;g.fillText(nameOf(m),2,y(m))}
 g.strokeStyle=k.accent;g.lineWidth=3;g.lineCap='round';let pr=null;for(const p of pts){if(p.v===null){pr=null;continue}const px=lw+p.t/D*(W-lw),py=y(p.v);if(pr){g.beginPath();g.moveTo(pr[0],pr[1]);g.lineTo(px,py);g.stroke()}pr=[px,py]}}

// ---------- gioco dell'eco ----------
function actEcho(a){const R=a.rounds||5;const big=el('div','big','Gioco dell\'eco'),sub=el('div','sub','Premi Inizia: ascolta la nota, poi ripetila su «la».');
 const cells=el('div','cells');for(let i=0;i<R;i++)cells.append(el('i','',i+1));cells.querySelectorAll('i').forEach(c=>c.style.width='64px');
 $('area').append(big,sub,cells);setActs([btn('Inizia',()=>run(),true)].concat(done.has(ai)?[nextBtn()]:[]));
 async function run(){if(!(await needMic()))return;$('res').hidden=true;[...cells.children].forEach((c,i)=>{c.className='';c.textContent=i+1});
  const base=a.low||52,notes=[];while(notes.length<R){const n=base+Math.floor(Math.random()*12);if(notes[notes.length-1]!==n)notes.push(n)}
  let r=0,phase='',T=0,vals=[];const res=[];setActs([btn('Ferma',()=>endTask(true))]);
  const startRound=()=>{phase='listen';T=now();vals=[];tone(notes[r],audio().currentTime+.05,1.2);cells.children[r].className='now'};
  startRound();
  task={frame(){const e=now()-T;
    if(phase==='listen'){big.textContent='Ascolta…';sub.textContent='Nota '+(r+1)+' di '+R;if(e>1.6){phase='sing';T=now()}return}
    if(phase==='sing'){big.textContent='Tocca a te: «la»';sub.textContent=cur!==null?'sento '+nameOf(cur):'canta la nota che hai sentito';
     if(e>.4&&cur!==null)vals.push(cur);
     if(e>3){const c=cells.children[r];if(vals.length<8){res.push(null);c.className='b';c.textContent='—'}
      else{const d=Math.round(fold(med(vals),notes[r])*100);res.push(d);c.className=Math.abs(d)<=35?'g':'m';c.textContent=(Math.abs(d)<=35?'✓':d>0?'↓':'↑')}
      r++;if(r>=R){endTask(false);return}phase='gap';T=now()}return}
    if(phase==='gap'&&e>.8)startRound()},
   end(user){const ok=res.filter(d=>d!==null&&Math.abs(d)<=35).length,lines=[];
    if(!res.length){$('res').hidden=true;setActs([btn('Inizia',()=>run(),true)]);big.textContent='Gioco dell\'eco';return}
    res.forEach((d,i)=>lines.push('Nota '+(i+1)+' ('+nameOf(notes[i])+'): '+(d===null?'non ti ho sentito':Math.abs(d)<=35?'giusta ('+(d>0?'+':'')+d+' cents)':(d<0?'calante':'crescente')+' di '+Math.abs(d)+' cents')));
    const sh=res.filter(d=>d!==null&&d>35).length,fl=res.filter(d=>d!==null&&d<-35).length;
    if(fl>sh&&fl>=2)lines.push('Tendi a stare sotto la nota: pensala un po\' più in alto prima di cantarla.');
    if(sh>fl&&sh>=2)lines.push('Tendi a stare sopra la nota: rilassati, non spingere.');
    const pass=ok>=Math.ceil(R*.8);if(pass&&a.next)lines.push(a.next);const score=ok/R*100;big.textContent=ok+' su '+R;sub.textContent='note giuste';
    result(Math.round(score)+'%',lines,pass);log(score,a.short);if(pass)markDone();setActs([btn('Gioca ancora',()=>run(),!pass)].concat(pass||done.has(ai)?[nextBtn()]:[]))}}}}

function loop(){readMic();readLevels();if(task&&task.frame)task.frame();requestAnimationFrame(loop)}
show();requestAnimationFrame(loop);
</script>
"""


def _base(theme):
    return _BASE.replace("__THEME__", theme if theme in ("light", "dark") else "")


def live_tuner(theme=None):
    components.html(_base(theme) + _TUNER, height=490)


def live_practice(plan, lyrics=None, theme=None, kind="song", item_id="", name="", coach=None):
    """Riquadro di pratica. Con coach (dict: syll, prep, focus) diventa un percorso guidato a 3 passi."""
    data = {"notes": plan["notes"], "bpm": plan["bpm"], "lead": plan["lead"],
            "total": plan["total"], "lyrics": lyrics or [], "kind": kind, "id": item_id,
            "name": name, "coach": coach}
    js = json.dumps(data, ensure_ascii=False).replace("</", "<\\/")
    components.html(_base(theme) + _PRACTICE.replace("__PLAN__", js), height=860 if coach else 640, scrolling=True)


def live_progress(theme=None):
    components.html(_base(theme) + _PROGRESS, height=1050, scrolling=True)


def live_lesson(lesson, theme=None):
    js = json.dumps(lesson, ensure_ascii=False).replace("</", "<\\/")
    components.html(_base(theme) + _LESSON.replace("__LESSON__", js), height=900, scrolling=True)
