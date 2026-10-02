/* Plantilla PropHero · lógica de la landing: tarjeta principal, plan de pagos y (modo paquetizado) packs, comparador y ficha de viviendas.
   Los datos (D) los inyecta scripts/build.py desde projects/<slug>/project.json. No editar en dist/. */
const D={"modo":"unico","proj":{"c":14457101,"cs":12673602,"v":15540663,"t":0.1939},"pp":{"a":14457101,"r":17324161,"n":2867061},"cron":{"q":["Q1 2027","Q2 2027","Q3 2027","Q4 2027","Q1 2028"],"c":[-11292078.0,-1802160.0,-1031202.0,-331660.8,1783498.9],"s":[0.0,0.0,0.0,1554066.26,13986596.33]},"nviv":168,"m2tot":8347,"renders":[{"archivo":"render-estudio.webp","titulo":"Estudio","texto":"Dormitorio, cocina y comedor en un único espacio"},{"archivo":"render-cocina-salon.webp","titulo":"Cocina abierta","texto":"Cocina lineal con el salón al fondo"},{"archivo":"render-cocina-comedor.webp","titulo":"Cocina y comedor","texto":"Zona de día junto a la ventana"}],"producto":{"titulo":"Viviendas compactas, terminadas y listas para entrar","texto":"Espacios abiertos con cocina equipada, suelo de madera y mucha luz natural: el producto que busca el inquilino de la zona."},"pie":"Montserrat · Ausias March · Dossier de precomercialización, septiembre 2026"};
const PC=['#F19D9D','#79EC9B','#DBB8F5','#E9E0A5','#85D1E0','#EFBED8','#AFF797','#7771F4','#F9CBB4','#9DF1D2','#E279EC','#E8F5B8','#A5C7E9','#E08598','#BEEFC2','#BB97F7','#F4C871','#B4F9F6','#F19DDC','#ADEC79','#B8C2F5','#E9AEA5','#85E0AB','#E1BEEF','#F6F797','#71CDF4','#F9B4D0'];
const PORC=['#FFAB91','#B39DDB','#80DEEA','#FFE082','#A5D6A7','#F48FB1'],PLC={'Baja':'#FFCC80','1ª':'#A5D6A7','2ª':'#90CAF9','3ª':'#FFE082','4ª':'#F48FB1','Ático':'#CE93D8'},DIC=['#FFF59D','#F48FB1','#80CBC4','#B39DDB'];
const NA='Pendiente';
const g=n=>String(n).replace(/\B(?=(\d{3})+(?!\d))/g,'.');
const mix=m=>Object.keys(m).sort().map(k=>k==='0'?`${m[k]} ${m[k]>1?'estudios':'estudio'}`:`${m[k]} de ${k} dorm.`).join(' · ');
const $=id=>document.getElementById(id);
const M=n=>(n/1e6).toFixed(1).replace('.',',')+' M€';
const K=n=>g(Math.round(n/1000))+' k€';
const P1=n=>(n*100).toFixed(1).replace('.',',')+' %';
const put=(id,v)=>{const e=$(id);if(e)e.textContent=v;};
/* Tarjeta principal: se calcula desde el Excel; el script final de index.html la sustituye por los rangos de dirección. */
const P=D.proj;
if(P){const B=P.v-P.cs;
put('k-c','≈ '+M(P.c));put('k-cs','≈ '+M(P.cs)+' sin IVA');put('k-b',M(B));put('k-r',P1(B/P.cs));put('k-t',P1(P.t));}
else ['k-c','k-r','k-b','k-t'].forEach(i=>put(i,NA));
/* Plan de pagos */
const pp=D.pp;
if(pp){put('p-a',M(pp.a));put('p-r',M(pp.r));put('p-n',M(pp.n));}
else ['p-a','p-r','p-n'].forEach(i=>put(i,NA));
/* Packs: solo en modo paquetizado (en modo único no existe ni el DOM ni los datos) */
if(D.modo==='paquetizado'&&$('rows')){
const PK=D.packs||[];
const byId=id=>PK.find(p=>p.id===id);
const PCK=p=>PC[(p.id-1)%PC.length];
const isEst=p=>Object.keys(p.mix).every(k=>k==='0'), isDorm=p=>Object.keys(p.mix).every(k=>k!=='0');
let F='all',SORT='id';const SEL=new Set();
function rows(){
if(!PK.length){$('rows').innerHTML=`<tr><td colspan="9">${NA}</td></tr>`;return;}
let list=PK.filter(p=>F==='all'||(F==='est'?isEst(p):isDorm(p)));
const key={id:p=>p.id,t:p=>-p.t,r:p=>-p.r,b:p=>-p.b,c:p=>p.c}[SORT];list=list.slice().sort((a,b)=>key(a)-key(b));
$('rows').innerHTML=list.map(p=>`<tr data-id="${p.id}" tabindex="0" class="${SEL.has(p.id)?'on':''}" aria-label="Ver viviendas del pack ${p.id}"><td class="ck"><input type="checkbox" data-c="${p.id}" ${SEL.has(p.id)?'checked':''} aria-label="Comparar pack ${p.id}"></td><td><i class="dot" style="background:${PCK(p)}"></i><b>Pack ${p.id}</b></td><td>${p.n} <span class="mixt">· ${mix(p.mix)}</span></td><td class="n">${g(p.m2)}</td><td class="n">${K(p.c)}</td><td class="n">${K(p.v)}</td><td class="n">${K(p.b)}</td><td class="n">${P1(p.r)}</td><td class="n"><span class="tirc" style="background:${PCK(p)}">${P1(p.t)}</span></td></tr>`).join('');
}
function cbar(){const n=SEL.size,b=$('cbar');b.classList.toggle('show',n>0);
$('cdots').innerHTML=[...SEL].sort((a,b)=>a-b).map(i=>`<i style="background:${PCK(byId(i))}">${i}</i>`).join('');
$('cn').textContent=n===1?'1 pack · marca otro para comparar':n+' packs seleccionados';$('cgo').disabled=n<2;$('cgo').style.opacity=n<2?.5:1;}
function compare(){const ps=[...SEL].sort((a,b)=>a-b).map(byId);if(ps.length<2)return;
const mxT=Math.max(...PK.map(p=>p.t));
const best=(f,low)=>{const v=ps.map(f);return low?Math.min(...v):Math.max(...v)};
const R=[['Viviendas',p=>`${p.n} · ${mix(p.mix)}`,null],['Superficie',p=>g(p.m2)+' m²',null],['Inversión (IVA incl.)',p=>K(p.c),p=>p.c,1],['Ventas',p=>K(p.v),p=>p.v],['Beneficio',p=>K(p.b),p=>p.b],['Yield',p=>P1(p.r),p=>p.r],['TIR estimada',p=>P1(p.t),p=>p.t]];
$('c-b').innerHTML=`<div class="cmp" style="--n:${ps.length}">${ps.map(p=>`<div><div class="ch" style="background:${PCK(p)}"><b>Pack ${p.id}</b><span>${p.n} viviendas</span></div><dl>${R.map(([l,f,k,low])=>`<div><dt>${l}</dt><dd class="${k&&k(p)===best(k,low)?'best':''}">${f(p)}</dd>${l==='TIR estimada'?`<div class="tbar"><i style="width:${p.t/mxT*100}%;background:${PCK(p)}"></i></div>`:''}</div>`).join('')}</dl></div>`).join('')}</div><p class="src">★ Mejor valor entre los packs comparados (en inversión, el menor). Cifras del modelo financiero a precio de mercado.</p>`;
$('cdl').showModal();}
rows();
$('rows').addEventListener('change',e=>{const c=e.target.closest('[data-c]');if(!c)return;const id=+c.dataset.c;
if(c.checked){if(SEL.size>=3){c.checked=false;$('cn').textContent='Máximo 3 packs';setTimeout(cbar,1600);return;}SEL.add(id);}else SEL.delete(id);
c.closest('tr').classList.toggle('on',c.checked);cbar();});
document.querySelectorAll('.chip').forEach(b=>b.onclick=()=>{F=b.dataset.f;document.querySelectorAll('.chip').forEach(x=>x.setAttribute('aria-pressed',String(x===b)));rows();});
$('sort').onchange=e=>{SORT=e.target.value;rows();};
$('cclr').onclick=()=>{SEL.clear();rows();cbar();};$('cgo').onclick=compare;
$('c-x').onclick=()=>$('cdl').close();$('cdl').addEventListener('click',e=>{if(e.target.id==='cdl')e.target.close();});
if(P)$('tot').innerHTML=`<tr class="tot"><td class="ck"></td><td>Total</td><td>${g(D.nviv)}</td><td class="n">${g(D.m2tot)}</td><td class="n">${K(P.c)}</td><td class="n">${K(P.v)}</td><td class="n">${K(P.v-P.cs)}</td><td class="n">${P1((P.v-P.cs)/P.cs)}</td><td class="n">${P1(P.t)}</td></tr>`;
const dl=$('dlg');
function open(id){const p=byId(id);
$('d-t').innerHTML=`<i class="dot" style="background:${PCK(p)}"></i>Pack ${id}`;
$('d-s').textContent=`${p.n} viviendas · ${mix(p.mix)} · ${g(p.m2)} m² · precio de mercado`;
$('d-b').innerHTML=`<div class="dk"><div><span>Inversión (IVA incl.)</span><b>${K(p.c)}</b></div><div><span>Ventas</span><b>${K(p.v)}</b></div><div><span>Beneficio · yield</span><b>${K(p.b)}</b><span>${P1(p.r)}</span></div><div><span>TIR estimada</span><b>${P1(p.t)}</b></div></div>
<div class="tw"><table><thead><tr><th>Portal</th><th>Planta</th><th>Viv.</th><th class="n">m²</th><th>Tipología</th><th>Orientación</th><th class="n">Precio de mercado</th></tr></thead><tbody>${(p.u||[]).map(u=>`<tr style="cursor:default"><td><span class="xc" style="background:${PORC[(String(u[0]).charCodeAt(0)-65+PORC.length)%PORC.length]}">${u[0]}</span></td><td><span class="xc" style="background:${PLC[u[1]]||'#E7ECF7'}">${u[1]}</span></td><td>${u[2]}</td><td class="n">${(+u[3]).toFixed(1).replace('.',',')}</td><td><span class="xc" style="background:${DIC[u[4]%DIC.length]}">${u[4]===0?'Estudio':u[4]+' hab.'}</span></td><td>${u[5]}</td><td class="n">${g(u[6])} €</td></tr>`).join('')}</tbody></table></div>
<p class="src">${D.nota_viviendas}</p>`;
dl.showModal();}
$('rows').addEventListener('click',e=>{if(e.target.closest('.ck'))return;const r=e.target.closest('tr[data-id]');if(r)open(+r.dataset.id);});
$('rows').addEventListener('keydown',e=>{if(e.target.closest('.ck'))return;const r=e.target.closest('tr[data-id]');if(r&&(e.key==='Enter'||e.key===' ')){e.preventDefault();open(+r.dataset.id);}});
$('d-x').onclick=()=>dl.close();dl.addEventListener('click',e=>{if(e.target===dl)dl.close();});
}
