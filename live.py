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
<div class="card">
  <div class="head">
    <span class="eyebrow">Pratica in diretta</span>
    <div class="row"><span class="pill" id="pill">Microfono spento</span><button class="btn primary" id="micBtn">Attiva microfono</button></div>
  </div>
  <canvas id="cv" style="height:280px"></canvas>
  <div id="lyr" style="font-family:var(--f-display);font-size:22px;min-height:1.4em;font-weight:800;letter-spacing:-.01em"></div>
  <style>#lyr .s{color:var(--muted);transition:color .1s}#lyr .s.done{color:var(--accent)}#lyr .s.now{color:var(--accent);text-decoration:underline;text-decoration-thickness:3px;text-underline-offset:5px}</style>
  <div class="row">
    <button class="btn primary" id="sing">Canta</button>
    <button class="btn" id="listen">Solo ascolto</button>
    <button class="btn" id="stop" disabled>Ferma</button>
    <label><input type="checkbox" id="guide" checked> Suona la guida</label>
    <label><input type="checkbox" id="loop"> Ripeti</label>
  </div>
  <div class="mono muted" id="status" style="font-size:13px">Attiva il microfono, poi premi Canta: partono 4 colpi di metronomo.</div>
  <div id="res" hidden style="border-top:1px solid var(--line);padding-top:10px;display:flex;flex-direction:column;gap:8px"></div>
</div>
<script>
const P=__PLAN__;
const $=id=>document.getElementById(id),cv=$('cv'),st=$('status');
$('micBtn').onclick=()=>{if(micOn&&run)stop(true);toggleMic($('pill'),$('micBtn'))};
let run=false,sing=false,t0=0,t=P.lead,voice=[],full=false;
const lo0=Math.min(...P.notes.map(n=>n.midi))-2,hi0=Math.max(...P.notes.map(n=>n.midi))+2;
let lo=lo0,hi=hi0;if(hi-lo<12){const p=12-(hi-lo);lo-=Math.floor(p/2);hi+=Math.ceil(p/2)}
const target=tt=>P.notes.find(n=>tt>=n.start&&tt<n.start+n.dur);
async function start(s){if(s&&!micOn)await startMic($('pill'),$('micBtn'));const c=audio();silence();sing=s&&micOn;voice=[];full=false;$('res').hidden=true;
 t0=c.currentTime+.15;const spb=60/P.bpm;for(let i=0;i<4;i++)click(t0+i*spb,i===0);
 if(!s||$('guide').checked)for(const n of P.notes)tone(n.midi,t0+n.start,n.dur);
 run=true;$('stop').disabled=false;$('sing').disabled=$('listen').disabled=true;
 st.textContent=s?(micOn?'Al quarto colpo inizia a cantare.':'Microfono non attivo: ascolta senza punteggio.'):'Ascolta la melodia.'}
function stop(user){silence();run=false;$('stop').disabled=true;$('sing').disabled=$('listen').disabled=false;if(user){st.textContent='Fermato.';if(sing&&voice.length)finish()}}
$('sing').onclick=()=>start(true);$('listen').onclick=()=>start(false);$('stop').onclick=()=>stop(true);
function finish(){
 const per=P.notes.map(n=>{const a=n.start+Math.min(.12,n.dur*.25),b=n.start+n.dur,fr=voice.filter(v=>v.t>=a&&v.t<b),vo=fr.filter(v=>v.m!==null);
  const ok=vo.filter(v=>Math.abs(fold(v.m,n.midi))<.5).length,avg=vo.length?vo.reduce((s,v)=>s+fold(v.m,n.midi),0)/vo.length:null;return{n,p:fr.length?ok/fr.length:0,avg}});
 const tot=per.reduce((s,x)=>s+x.n.dur,0),pct=Math.round(per.reduce((s,x)=>s+x.p*x.n.dur,0)/tot*100);
 const fl=per.filter(x=>x.avg!==null&&x.avg<-.3).length,sh=per.filter(x=>x.avg!==null&&x.avg>.3).length;
 let msg=pct>=80?'Ottima intonazione.':pct>=55?'Buona base: lavora sulle note arancioni.':'Continua: usa la guida e abbassa il tempo.';
 if(fl>sh+1)msg+=' Tendi a calare: sostieni il fiato fino alla fine della nota.';else if(sh>fl+1)msg+=' Tendi a crescere: rilassa collo e mascella.';
 const r=$('res');r.replaceChildren();const h=document.createElement('div');h.innerHTML='<b style="font-family:var(--f-display);font-size:40px;font-weight:800;letter-spacing:-.03em">'+pct+'%</b> ';
 const sp=document.createElement('span');sp.textContent='del tempo intonato. '+msg+' (Vale anche un\'ottava sopra o sotto.)';h.append(sp);
 const ch=document.createElement('div');ch.className='chips';per.slice(0,80).forEach(x=>{const c=document.createElement('span');c.className='chip '+(x.p>=.7?'g':x.p>=.35?'m':'b');c.textContent=nameOf(x.n.midi)+' '+Math.round(x.p*100)+'%';ch.append(c)});
 r.append(h,ch);r.hidden=false;st.textContent='Fatto.';full=true}
function draw(){const[g,W,H]=sizeCanvas(cv),k=C();g.fillStyle=k.lane;g.fillRect(0,0,W,H);const lw=44,py=12,y=m=>py+(hi-m)/(hi-lo)*(H-2*py);
 let x;if(full){const a=Math.max(0,P.lead-.6),b=P.total+.3;x=tt=>lw+(tt-a)/(b-a)*(W-lw-8)}else{const pps=(W-lw)*.72/5,ph=lw+(W-lw)*.26;x=tt=>ph+(tt-t)*pps}
 g.font='11px "IBM Plex Mono",ui-monospace,monospace';g.textBaseline='middle';
 for(let m=lo;m<=hi;m++){const nat=[0,2,4,5,7,9,11].includes(((m%12)+12)%12);g.strokeStyle=k.line;g.globalAlpha=nat?1:.35;g.beginPath();g.moveTo(lw,y(m));g.lineTo(W,y(m));g.stroke();g.globalAlpha=1;if(nat&&(hi-lo<=20||m%12===0||m%12===7)){g.fillStyle=k.muted;g.fillText(nameOf(m),4,y(m))}}
 const rh=Math.max(6,(H-2*py)/(hi-lo)*.8);
 for(const n of P.notes){const x0=x(n.start),x1=x(n.start+n.dur);if(x1<lw||x0>W)continue;const act=!full&&t>=n.start&&t<n.start+n.dur;
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
 const ns=P.notes.filter(n=>n.phrase===p),has=ns.some(n=>n.syl);
 if(!has){L.textContent=(P.lyrics&&P.lyrics[p])||'';return}
 for(const n of ns){if(!n.syl)continue;const s=document.createElement('span');s.className='s';s.textContent=n.syl;L.append(s);lyrS.push({s,n});if(n.we)L.append(' ')}}
function updLyr(tt){for(const o of lyrS){o.s.classList.toggle('done',tt>=o.n.start+o.n.dur);o.s.classList.toggle('now',tt>=o.n.start&&tt<o.n.start+o.n.dur)}}
if(P.notes.length)renderLyr(P.notes[0].phrase);
function loop(){readMic();
 if(run){t=ctx.currentTime-t0;if(sing)voice.push({t,m:cur});const n=target(t);
  if(n&&n.phrase!==lyrP)renderLyr(n.phrase);updLyr(t);
  if(t<P.lead)st.textContent='Attacco tra '+Math.ceil((P.lead-t)/(60/P.bpm))+'…';else if(n)st.textContent='Nota: '+nameOf(n.midi)+(sing&&cur!==null?'   ·   tu: '+nameOf(cur):'');
  if(t>P.total+.4){stop(false);if(sing)finish();else st.textContent='Fine. Ora prova a cantarla.';
   if($('loop').checked)setTimeout(()=>start(sing),900);else if(micOn)stopMic($('pill'),$('micBtn'))}}
 draw();requestAnimationFrame(loop)}
requestAnimationFrame(loop);
</script>
"""


def _base(theme):
    return _BASE.replace("__THEME__", theme if theme in ("light", "dark") else "")


def live_tuner(theme=None):
    components.html(_base(theme) + _TUNER, height=490)


def live_practice(plan, lyrics=None, theme=None):
    data = {"notes": plan["notes"], "bpm": plan["bpm"], "lead": plan["lead"],
            "total": plan["total"], "lyrics": lyrics or []}
    js = json.dumps(data, ensure_ascii=False).replace("</", "<\\/")
    components.html(_base(theme) + _PRACTICE.replace("__PLAN__", js), height=620)
