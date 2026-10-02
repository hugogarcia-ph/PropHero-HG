/* Plantilla PropHero · cronograma de pagos, pie PropHero y galería de renders. Usa D y los formateadores de app.js. */
const CR=D.cron;
let CP=0;
const E=n=>(n<0?'-':'+')+g(Math.abs(Math.round(n/1000))*1000)+' €';
function cron(){
const ch=$('cr-ch');
if(!CR){$('cr-t').textContent='Cronograma de pagos · Proyecto completo';ch.style.height='auto';ch.style.minWidth='0';ch.innerHTML='<p style="margin:24px 0;color:#C9CDD5">'+NA+'</p>';return;}
const pk=CP&&D.packs?D.packs.find(p=>p.id===CP):null, w=pk?pk.w:[1,1];
const QL=CR.q, v=QL.map((_,k)=>CR.c[k]*w[0]+CR.s[k]*w[1]);
const tot=v.reduce((a,b)=>a+b,0), all=[...v,tot], last=all.length-1;
const mx=Math.max(...all,0), mn=Math.min(...all,0);
const H=360, top=36, bot=78, span=H-top-bot, y0=top+mx/(mx-mn)*span, sc=span/(mx-mn);
$('cr-t').textContent='Cronograma de pagos · '+(pk?'Pack '+CP:'Proyecto completo');
if(all.length!==6)ch.style.gridTemplateColumns=`repeat(${all.length},1fr)`;
ch.innerHTML=`<div class="ax" style="top:${y0}px"></div>`+all.map((x,i)=>{const s=i===last,cls=s?'s':(x<0?'n':'p'),hgt=Math.max(Math.abs(x)*sc,3);
const bt=x<0?y0:y0-hgt, lt=x<0?y0+hgt+8:y0-hgt-24;
return `<div class="col"><div class="b ${cls}${s&&x<0?' neg':''}" style="top:${bt}px;height:${hgt}px"></div><span class="v ${cls}" style="top:${lt}px">${E(x)}</span><span class="q${s?' s':''}">${s?'Subtotal':QL[i]}</span></div>`}).join('');
}
if($('cr-p')&&D.packs){
$('cr-p').innerHTML='<option value="0">Proyecto completo</option>'+D.packs.map(p=>`<option value="${p.id}">Pack ${p.id}</option>`).join('');
$('cr-p').onchange=e=>{CP=+e.target.value;cron();};
}
cron();
$('pdf').onclick=()=>{location.href='/dossier.html?dl=1';};
(function(){
const ES='https://www.prophero.com/es/';
const L=[['PropHero',[['Acerca de PropHero',ES+'quienes-somos/'],['Cómo funciona',ES+'como-funciona/'],['Datos e IA',ES+'datos-e-ia/'],['Valencia Real Estate Summit 2026','https://valenciarealestatesummit2026.prophero.com']]],
['Recursos',[['Prensa y blogs',ES+'prensa-y-blog/'],['Recomendar a un amigo',ES+'programa-de-referidos/'],['Preguntas más frecuentes',ES+'faq/'],['Canal de denuncias','https://www.suiteadeplus.com/web/canal-etico/registro?id=PropHero47']]]];
const ic={yt:'<path d="M21.6 7.2a2.5 2.5 0 0 0-1.8-1.8C18.2 5 12 5 12 5s-6.2 0-7.8.4A2.5 2.5 0 0 0 2.4 7.2 26 26 0 0 0 2 12a26 26 0 0 0 .4 4.8 2.5 2.5 0 0 0 1.8 1.8C5.8 19 12 19 12 19s6.2 0 7.8-.4a2.5 2.5 0 0 0 1.8-1.8A26 26 0 0 0 22 12a26 26 0 0 0-.4-4.8zM10 15V9l5.2 3z"/>',fb:'<path d="M13.5 21v-7.5h2.5l.4-3h-2.9V8.6c0-.9.3-1.5 1.5-1.5h1.5V4.4a20 20 0 0 0-2.2-.1c-2.2 0-3.7 1.3-3.7 3.8v2.4H8v3h2.6V21z"/>',ig:'<path d="M12 7.3A4.7 4.7 0 1 0 16.7 12 4.7 4.7 0 0 0 12 7.3zm0 7.7a3 3 0 1 1 3-3 3 3 0 0 1-3 3zm4.9-7.9a1.1 1.1 0 1 1-1.1-1.1 1.1 1.1 0 0 1 1.1 1.1zM12 4.2c2.5 0 2.8 0 3.8.1 2.6.1 3.8 1.3 3.9 3.9.1 1 .1 1.3.1 3.8s0 2.8-.1 3.8c-.1 2.6-1.3 3.8-3.9 3.9-1 .1-1.3.1-3.8.1s-2.8 0-3.8-.1c-2.6-.1-3.8-1.3-3.9-3.9-.1-1-.1-1.3-.1-3.8s0-2.8.1-3.8c.1-2.6 1.3-3.8 3.9-3.9 1-.1 1.3-.1 3.8-.1zM12 2.5c-2.6 0-2.9 0-3.9.1C4.6 2.7 2.7 4.6 2.6 8.1 2.5 9.1 2.5 9.4 2.5 12s0 2.9.1 3.9c.1 3.5 2 5.4 5.5 5.5 1 .1 1.3.1 3.9.1s2.9 0 3.9-.1c3.5-.1 5.4-2 5.5-5.5.1-1 .1-1.3.1-3.9s0-2.9-.1-3.9c-.1-3.5-2-5.4-5.5-5.5-1-.1-1.3-.1-3.9-.1z"/>'};
const soc=[['YouTube','https://www.youtube.com/@prophero','yt'],['Facebook','https://www.facebook.com/PropHeroInvestmentSpain/','fb'],['Instagram','https://www.instagram.com/prophero.es/','ig']];
const st=document.createElement('style');
st.textContent=`.pf .wrap{display:block}
.pf{background:var(--navy-d);color:#A3ABC4;font-size:14px;padding:56px 0 calc(28px + env(safe-area-inset-bottom,0px))}
.pf a{color:#C7CEE6;text-decoration:none}.pf a:hover{color:#fff}
.pf-g{display:grid;grid-template-columns:1.4fr 1fr 1fr 1fr;gap:32px 40px}
.pf-g>*{min-width:0}
.pf-b svg{height:26px;width:auto;color:#fff}
.pf-b p{margin:16px 0 20px;max-width:36ch;line-height:1.55}
.pf h4{margin:0 0 14px;color:#fff;font-size:14px;font-weight:600}
.pf ul{list-style:none;margin:0;padding:0;display:grid;gap:10px}
.pf-apps{display:grid;gap:10px}
.pf-badge{display:inline-flex;align-items:center;gap:10px;background:#000;border:1px solid #A6A6A6;border-radius:10px;padding:7px 16px 7px 12px;min-width:172px;color:#fff!important;transition:border-color .15s,transform .15s}
.pf-badge:hover{border-color:#fff;transform:translateY(-1px)}
.pf-i{width:26px;height:26px;flex:none}
.pf-badge span{display:flex;flex-direction:column;line-height:1.05}
.pf-badge small{font-size:10.5px;font-weight:500;letter-spacing:.01em}
.pf-badge b{font-size:19px;font-weight:600;letter-spacing:-.01em;color:#fff}
.pf-soc{display:flex;gap:10px;margin-top:18px}
.pf-soc a{width:38px;height:38px;border-radius:50%;display:grid;place-items:center;border:1px solid rgba(255,255,255,.18)}
.pf-soc svg{width:18px;height:18px;fill:currentColor}
.pf-bot{display:flex;flex-wrap:wrap;justify-content:space-between;gap:10px 24px;margin-top:44px;padding-top:20px;border-top:1px solid rgba(255,255,255,.12);font-size:12.5px;color:#7F88A6}
@media (max-width:860px){.pf-g{grid-template-columns:1fr 1fr}.pf-b{grid-column:1/-1}}
@media (max-width:480px){.pf-g{grid-template-columns:1fr}}
@media print{.pf{display:none}}`;
document.head.appendChild(st);
const f=document.querySelector('footer');
f.className='pf';
const apple='<svg class="pf-i" viewBox="0 0 24 24" aria-hidden="true"><path fill="#fff" d="M16.4 12.6c0-2.6 2.1-3.8 2.2-3.9-1.2-1.8-3.1-2-3.7-2-1.6-.2-3.1.9-3.9.9s-2-.9-3.4-.9c-1.7 0-3.3 1-4.2 2.6-1.8 3.1-.5 7.7 1.3 10.2.9 1.2 1.9 2.6 3.2 2.6 1.3-.1 1.8-.8 3.3-.8s2 .8 3.4.8c1.4 0 2.3-1.3 3.1-2.5 1-1.4 1.4-2.8 1.4-2.9-.1 0-2.7-1-2.7-4.1zM13.9 5.1c.7-.9 1.2-2 1.1-3.2-1 0-2.3.7-3 1.6-.7.8-1.2 2-1.1 3.1 1.2.1 2.3-.6 3-1.5z"/></svg>';
const play='<svg class="pf-i" viewBox="0 0 24 24" aria-hidden="true"><path fill="#00D7FE" d="M3.6 1.8 13.3 12l-9.7 10.2c-.4-.2-.6-.7-.6-1.2V3c0-.5.2-1 .6-1.2z"/><path fill="#FFCE00" d="m16.6 8.6-3.3 3.4 3.3 3.4 3.9-2.2c1.1-.6 1.1-1.8 0-2.4z"/><path fill="#FF3A44" d="M13.3 12 3.6 22.2c.4.2.9.2 1.4-.1l11.6-6.7z"/><path fill="#00F076" d="M3.6 1.8c.5-.3 1-.3 1.4-.1l11.6 6.9-3.3 3.4z"/></svg>';
f.innerHTML=`<div class="wrap"><div class="pf-g">
<div class="pf-b"><a href="${ES}" aria-label="PropHero, web principal"><svg viewBox="12 12 1801 392" aria-hidden="true"><use href="#ph-logo"/></svg></a><p>Crea tu cartera inmobiliaria sin complicaciones. PropHero selecciona los mejores activos y gestiona todo el proceso de principio a fin.</p><a class="btn" href="${ES}formulario-para-concertar-una-llamada/" target="_blank" rel="noopener">Reservar una llamada</a></div>
${L.map(([h,ls])=>`<nav aria-label="${h}"><h4>${h}</h4><ul>${ls.map(([t,u])=>`<li><a href="${u}" target="_blank" rel="noopener">${t}</a></li>`).join('')}</ul></nav>`).join('')}
<div><h4>App PropHero Portfolio</h4><div class="pf-apps"><a class="pf-badge" href="https://apps.apple.com/es/app/prophero-portfolio/id1659329688" target="_blank" rel="noopener" aria-label="Descargar PropHero Portfolio en App Store">${apple}<span><small>Download on the</small><b>App Store</b></span></a><a class="pf-badge" href="https://play.google.com/store/apps/details?id=com.prophero.portfolio" target="_blank" rel="noopener" aria-label="Descargar PropHero Portfolio en Google Play">${play}<span><small>GET IT ON</small><b>Google Play</b></span></a></div>
<div class="pf-soc">${soc.map(([n,u,k])=>`<a href="${u}" target="_blank" rel="noopener" aria-label="PropHero en ${n}"><svg viewBox="0 0 24 24" aria-hidden="true">${ic[k]}</svg></a>`).join('')}</div></div>
</div>
<div class="pf-bot"><span>© ${new Date().getFullYear()} PropHero</span><span>${D.pie}</span></div></div>`;
})();
(function(){
const G=(D.renders||[]).map(r=>[r.archivo,r.titulo,r.texto]);
const s=document.createElement('style');
s.textContent=`#producto{padding:48px 0 24px}
.gal{display:grid;grid-template-columns:1.6fr 1fr;grid-template-rows:1fr 1fr;gap:14px;margin-top:26px;height:clamp(360px,44vw,560px)}
.gal figure{position:relative;margin:0;border-radius:18px;overflow:hidden;cursor:zoom-in;background:var(--cream)}
.gal figure:first-child{grid-row:1/3}
.gal img{width:100%;height:100%;object-fit:cover;display:block;transition:transform .5s}
.gal figure:hover img{transform:scale(1.03)}
.gal figcaption{position:absolute;left:12px;bottom:12px;right:12px;display:flex;flex-wrap:wrap;gap:4px 8px;align-items:baseline;color:#fff;font-size:13px;text-shadow:0 1px 8px rgba(0,0,0,.35)}
.gal figcaption b{color:#fff;background:rgba(6,16,49,.72);backdrop-filter:blur(6px);padding:5px 11px;border-radius:999px;font-size:13px;text-shadow:none}
.gal figcaption span{display:none}
.gal figure:first-child figcaption span{display:inline}
.gal-n{font-size:12.5px;color:var(--muted);margin-top:12px}
#gdl{border:0;padding:0;background:transparent;max-width:min(1200px,calc(100% - 24px));width:auto;max-height:none;overflow:visible}
#gdl::backdrop{background:rgba(3,8,31,.85)}
#gdl img{display:block;max-width:100%;max-height:calc(100dvh - 120px);border-radius:14px}
#gdl p{color:#fff;margin:12px 4px 0;font-size:14px}
#gdl button{position:absolute;top:-14px;right:-14px;width:40px;height:40px;border-radius:50%;border:0;background:#fff;color:#061031;font-size:20px;cursor:pointer;box-shadow:0 6px 20px rgba(0,0,0,.3)}
@media (max-width:700px){.gal{grid-template-columns:1fr 1fr;grid-template-rows:auto auto;height:auto}.gal figure:first-child{grid-column:1/-1;grid-row:auto;aspect-ratio:4/3}.gal figure{aspect-ratio:1/1}.gal figure:first-child figcaption span{display:none}}
@media print{#producto{display:none}}`;
document.head.appendChild(s);
const sec=document.createElement('section');sec.id='producto';
sec.innerHTML=`<div class="wrap"><p class="eyebrow">El producto</p><h2>${D.producto.titulo}</h2><p class="lede" style="margin-top:0">${D.producto.texto}</p>
${G.length?`<div class="gal">${G.map(([f,t,d],i)=>`<figure tabindex="0" data-i="${i}"><img src="/assets/${f}" alt="${t}: ${d}" loading="lazy" width="960" height="700"><figcaption><b>${t}</b><span>${d}</span></figcaption></figure>`).join('')}</div>`:`<p class="lede">${NA}</p>`}
<p class="gal-n">Imágenes orientativas (renders). El mobiliario y la decoración son ilustrativos y no se incluyen en la venta.</p></div>`;
const slot=document.getElementById('producto-slot');slot.replaceWith(sec);
const d=document.createElement('dialog');d.id='gdl';d.setAttribute('aria-label','Render ampliado');d.innerHTML='<button type="button" aria-label="Cerrar">×</button><img alt=""><p></p>';document.body.appendChild(d);
const op=i=>{const [f,t,x]=G[i];d.querySelector('img').src='/assets/'+f;d.querySelector('img').alt=t;d.querySelector('p').textContent=t+' · '+x;d.showModal();};
sec.querySelectorAll('figure').forEach(fg=>{fg.onclick=()=>op(+fg.dataset.i);fg.onkeydown=e=>{if(e.key==='Enter'||e.key===' '){e.preventDefault();op(+fg.dataset.i);}};});
d.querySelector('button').onclick=()=>d.close();d.addEventListener('click',e=>{if(e.target===d)d.close();});
})();
