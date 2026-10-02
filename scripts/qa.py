#!/usr/bin/env python3
"""QA automático de una landing (CLAUDE.md §9) antes de publicar.

Uso:
    python3 scripts/qa.py <carpeta-o-slug> [--dir DIR] [--modo unico|paquetizado] [--sin-red]

- Sirve dist/<slug>/ (o --dir) con un servidor HTTP local y lo recorre con Playwright SIN CABEZA
  (Chrome del sistema en modo headless; si no está, el Chromium de Playwright, también headless).
  Nunca abre una ventana visible.
- --modo: modo con el que se generó --dir (por defecto, el del project.json).
- --sin-red: no comprueba los enlaces externos del pie.
Termina con código 1 si alguna comprobación falla. Requiere: pip install --user playwright.
"""
import argparse
import functools
import http.server
import json
import os
import re
import sys
import tempfile
import threading
import urllib.request

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
import build as B  # noqa: E402  (formateadores idénticos a los de la web)

MM = 96 / 25.4
PROHIBIDAS = ['mínimo', 'minimo', 'recompra', 'garantía', 'garantia']
SECCIONES = {'unico': ['zona', 'pagos', 'edificio', 'producto', 'cierre'],
             'paquetizado': ['zona', 'pagos', 'packs', 'producto', 'cierre']}
ANCHOS = [320, 390, 768, 1280]


class Informe:
    def __init__(self):
        self.filas = []

    def ok(self, nombre, detalle=''):
        self.filas.append(('OK', nombre, detalle))

    def fallo(self, nombre, detalle=''):
        self.filas.append(('FALLO', nombre, detalle))

    def aviso(self, nombre, detalle=''):
        self.filas.append(('AVISO', nombre, detalle))

    def check(self, cond, nombre, detalle=''):
        (self.ok if cond else self.fallo)(nombre, detalle)

    def imprimir(self):
        for est, n, d in self.filas:
            print(f'[{est:5}] {n}' + (f' · {d}' if d else ''))
        nf = sum(1 for f in self.filas if f[0] == 'FALLO')
        na = sum(1 for f in self.filas if f[0] == 'AVISO')
        print(f'\nResultado: {"SUPERADO" if nf == 0 else "NO SUPERADO"} · {len(self.filas)} comprobaciones, {nf} fallos, {na} avisos')
        return nf == 0


def servidor(directorio):
    class H(http.server.SimpleHTTPRequestHandler):
        def log_message(self, *a):
            pass
    srv = http.server.ThreadingHTTPServer(('127.0.0.1', 0), functools.partial(H, directory=directorio))
    threading.Thread(target=srv.serve_forever, daemon=True).start()
    return srv, f'http://127.0.0.1:{srv.server_address[1]}'


def lanzar(p):
    try:
        return p.chromium.launch(channel='chrome', headless=True)
    except Exception:
        return p.chromium.launch(headless=True)


JS_DESBORDE = r'''() => {
 const W=document.documentElement.clientWidth, bad=[];
 if(document.documentElement.scrollWidth>W+1) bad.push('scrollWidth '+document.documentElement.scrollWidth+' > '+W);
 const d=e=>e.tagName.toLowerCase()+(e.id?'#'+e.id:'')+(e.className&&typeof e.className==='string'?'.'+e.className.trim().split(/\s+/).join('.'):'');
 for(const el of document.body.querySelectorAll('*')){
  if(el.closest('dialog:not([open])')||el.closest('[hidden]')) continue;
  const cs=getComputedStyle(el); if(cs.display==='none'||cs.visibility==='hidden'||cs.position==='fixed') continue;
  let p=el.parentElement, recorte=false;
  while(p&&p!==document.body){if(getComputedStyle(p).overflowX!=='visible'){recorte=true;break;} p=p.parentElement;}
  if(recorte) continue;
  const r=el.getBoundingClientRect(); if(!r.width||!r.height) continue;
  if(r.right>W+1||r.left<-1) bad.push(d(el)+' ['+Math.round(r.left)+', '+Math.round(r.right)+']');
 }
 return bad.slice(0,12);
}'''

JS_MARGENES = r'''(mm) => {
 const out=[];
 document.querySelectorAll('.page').forEach((pg,i)=>{
  const P=pg.getBoundingClientRect(), F=pg.querySelector('.foot'), FT=F?F.getBoundingClientRect().top:Infinity;
  pg.querySelectorAll('*').forEach(el=>{
   if(el.closest('.plan')||el.classList.contains('fade')) return;
   if(F&&!el.closest('.foot')&&el.getBoundingClientRect().height&&el.getBoundingClientRect().bottom>FT+0.5&&getComputedStyle(el).display!=='none')
     out.push('pág. '+(i+1)+': '+el.tagName.toLowerCase()+' solapa con el pie «'+(el.textContent||'').trim().slice(0,30)+'»');
   const cs=getComputedStyle(el); if(cs.display==='none') return;
   const r=el.getBoundingClientRect(); if(!r.width||!r.height) return;
   const tag=el.tagName.toLowerCase()+(el.className&&typeof el.className==='string'?'.'+el.className.split(' ')[0]:'');
   if(r.left<P.left+16*mm-0.6||r.right>P.right-16*mm+0.6||r.top<P.top+9*mm-0.6||r.bottom>P.bottom-9*mm+0.6)
     out.push('pág. '+(i+1)+': '+tag+' «'+(el.textContent||'').trim().slice(0,30)+'»');
   if((el.tagName==='TD'||el.tagName==='TH')&&el.scrollWidth>el.clientWidth+1) out.push('pág. '+(i+1)+': celda recortada «'+el.textContent.trim().slice(0,30)+'»');
  });
 });
 return out.slice(0,20);
}'''


def numeros_pdf(path):
    with open(path, 'rb') as f:
        raw = f.read()
    paginas = len(re.findall(rb'/Type\s*/Page(?!s)', raw))
    a4 = re.findall(rb'/MediaBox\s*\[\s*0\s+0\s+([\d.]+)\s+([\d.]+)\s*\]', raw)
    return raw[:5] == b'%PDF-', paginas, a4


def main():
    ap = argparse.ArgumentParser(description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter)
    ap.add_argument('proyecto')
    ap.add_argument('--dir')
    ap.add_argument('--modo', choices=B.MODOS)
    ap.add_argument('--sin-red', action='store_true')
    a = ap.parse_args()

    carpeta = B.localizar(a.proyecto)
    with open(os.path.join(carpeta, 'project.json'), encoding='utf-8') as f:
        data = json.load(f)
    modo = a.modo or data.get('modo')
    d = B.Datos(data, modo)
    directorio = os.path.abspath(a.dir or os.path.join(B.DIST, data['slug']))
    if not os.path.isfile(os.path.join(directorio, 'index.html')):
        raise SystemExit(f'ERROR: no existe {directorio}/index.html. Ejecuta antes scripts/build.py.')

    from playwright.sync_api import sync_playwright

    inf = Informe()
    srv, base = servidor(directorio)
    us = B.viviendas(d)
    print(f'QA {data["slug"]} · modo {modo} · {directorio}\n')
    with sync_playwright() as p:
        br = lanzar(p)
        ctx = br.new_context(viewport={'width': 1280, 'height': 900}, accept_downloads=True)
        textos = {}

        # 1. Errores de consola y texto renderizado
        for pag in ('index.html', 'zona.html', 'dossier.html'):
            pg = ctx.new_page()
            errores = []
            pg.on('console', lambda m, e=errores: e.append(m.text) if m.type == 'error' else None)
            pg.on('pageerror', lambda ex, e=errores: e.append(str(ex)))
            pg.on('requestfailed', lambda r, e=errores: e.append('petición fallida: ' + r.url) if r.url.startswith(base) else None)
            pg.goto(f'{base}/{pag}', wait_until='networkidle')
            pg.wait_for_timeout(300)
            textos[pag] = pg.inner_text('body')
            inf.check(not errores, f'0 errores de consola en {pag}', '; '.join(errores[:5]))
            pg.close()

        # 2. Scroll horizontal
        for pag in ('index.html', 'zona.html', 'dossier.html'):
            for w in ANCHOS:
                pg = ctx.new_page()
                pg.set_viewport_size({'width': w, 'height': 900})
                pg.goto(f'{base}/{pag}', wait_until='networkidle')
                if pag == 'dossier.html':
                    bad = pg.evaluate('() => document.documentElement.scrollWidth > document.documentElement.clientWidth + 1 ? ["scrollWidth " + document.documentElement.scrollWidth] : []')
                    fuera = pg.evaluate('() => [...document.querySelectorAll(".page")].some(p => { const r = p.getBoundingClientRect(); return r.left < -1 || r.right > innerWidth + 1; })')
                    if fuera:
                        inf.aviso(f'vista previa de dossier.html recortada a {w} px', 'las páginas A4 no caben centradas en pantalla (heredado de la referencia; el PDF no se ve afectado)')
                else:
                    bad = pg.evaluate(JS_DESBORDE)
                inf.check(not bad, f'sin scroll horizontal en {pag} a {w} px', '; '.join(bad))
                pg.close()

        # 3. Palabras prohibidas y «pack» en modo único
        for pag, t in textos.items():
            low = t.lower()
            hits = [w for w in PROHIBIDAS if w in low]
            inf.check(not hits, f'{pag} sin «mínimo», «recompra» ni «garantía»', ', '.join(hits))
            if modo == 'unico':
                n = low.count('pack')
                inf.check(n == 0, f'modo único: {pag} no contiene «pack»', f'{n} apariciones' if n else '')
            if 'Pendiente' in t:
                inf.aviso(f'{pag} contiene «Pendiente»', 'faltan datos del proyecto')

        pg = ctx.new_page()
        pg.goto(f'{base}/index.html', wait_until='networkidle')
        txt = lambda sel: pg.eval_on_selector(sel, 'e => e.textContent.trim()')

        # 4. Rangos del hero y de la portada del PDF
        rg = {k: d.get('rangos.' + k) for k in ('yield', 'tir', 'beneficio')}
        hero = {'yield': txt('#k-r'), 'tir': txt('#k-t'), 'beneficio': txt('#k-b')}
        inf.check(hero == rg, 'rangos del hero = project.json → rangos', json.dumps(hero, ensure_ascii=False))
        pd = ctx.new_page()
        pd.goto(f'{base}/dossier.html', wait_until='networkidle')
        cf = pd.eval_on_selector_all('.cfig div', 'es => es.map(e => [e.querySelector("span").textContent, e.querySelector("b").textContent])')
        cfd = dict(cf)
        portada = {'yield': cfd.get('Yield estimado'), 'tir': cfd.get('TIR estimada'), 'beneficio': cfd.get('Beneficio estimado')}
        inf.check(portada == rg, 'rangos de la portada del PDF = project.json → rangos', json.dumps(portada, ensure_ascii=False))

        # 5. Totales = Excel
        pp = data.get('plan_pagos') or {}
        if pp:
            web = [txt('#p-a'), txt('#p-r'), txt('#p-n')]
            esp = [B.M(pp['aportas']), B.M(pp['recibes']), B.M(pp['ganancia_neta'])]
            inf.check(web == esp, 'plan de pagos (web) = Excel', f'{web} vs {esp}')
            pdf = pd.eval_on_selector_all('.sum b', 'es => es.map(e => e.textContent)')
            inf.check(pdf == esp, 'plan de pagos (PDF) = Excel', f'{pdf} vs {esp}')
        cr = data.get('cronograma') or {}
        if cr:
            vals = B.cron_valores(cr)
            esp = [B.E(x) for x in vals + [sum(vals)]]
            web = pg.eval_on_selector_all('#cr-ch .v', 'es => es.map(e => e.textContent)')
            inf.check(web == esp, 'cronograma (web) = Excel', f'{web}')
            pdf = pd.eval_on_selector_all('.dch-c .cv', 'es => es.map(e => e.textContent)')
            inf.check(pdf == esp, 'cronograma (PDF) = Excel', f'{pdf}')
            if pp:
                dif = sum(vals) - pp['ganancia_neta']
                inf.check(abs(dif) <= 1, 'subtotal del cronograma = ganancia neta (±1 €)', f'diferencia {dif:+.2f} €')
            tit = txt('#cr-t')
            inf.check(tit == 'Cronograma de pagos · Proyecto completo', 'el cronograma arranca en «Proyecto completo»', tit)
        packs = data.get('packs') or []
        if modo == 'paquetizado' and packs:
            proy = data['proyecto']
            tol = len(packs)
            for k, ref, n in (('c', proy['coste_iva'], 'inversión'), ('v', proy['ventas'], 'ventas')):
                dif = sum(x[k] for x in packs) - ref
                inf.check(abs(dif) <= tol, f'suma de packs ({n}) = Excel (±1 € por pack)', f'diferencia {dif:+} €')
            inf.check(sum(x['n'] for x in packs) == len(us), 'suma de viviendas de los packs = total')
            for i, nom in ((0, 'coste'), (1, 'venta')):
                s = sum(x['pesos'][i] for x in packs)
                inf.check(abs(s - 1) < 0.002, f'pesos de {nom} de los packs suman 1', f'{s:.5f}')

        # 6/7. Según el modo
        if modo == 'paquetizado':
            inf.check(pg.locator('#pk').get_attribute('open') is None, 'el desplegable de packs empieza cerrado')
            pg.click('#pk > summary')
            inf.check(pg.locator('#pk').get_attribute('open') is not None, 'el desplegable de packs abre')
            nfil = pg.locator('#rows tr').count()
            inf.check(nfil == len(packs), 'la tabla muestra todos los packs', f'{nfil} filas')
            boxes = pg.locator('#rows input[type=checkbox]')
            boxes.nth(0).check(); boxes.nth(1).check()
            inf.check('show' in (pg.get_attribute('#cbar', 'class') or ''), 'la barra del comparador aparece al marcar packs')
            pg.click('#cgo')
            ok2 = pg.evaluate('() => document.getElementById("cdl").open') and pg.locator('#c-b .cmp > div').count() == 2
            inf.check(ok2, 'el comparador funciona con 2 packs')
            inf.check(pg.locator('#c-b dd.best').count() > 0, 'el comparador marca ★ el mejor valor')
            pg.keyboard.press('Escape')
            if len(packs) >= 3:
                boxes.nth(2).check()
                pg.click('#cgo')
                ok3 = pg.evaluate('() => document.getElementById("cdl").open') and pg.locator('#c-b .cmp > div').count() == 3
                inf.check(ok3, 'el comparador funciona con 3 packs')
                pg.keyboard.press('Escape')
            if len(packs) >= 4:
                boxes.nth(3).click()
                inf.check(pg.locator('#rows input:checked').count() == 3, 'el comparador no admite un 4.º pack')
            pg.click('#cclr')
            pg.locator('#rows tr').nth(0).locator('td').nth(2).click()
            okd = pg.evaluate('() => document.getElementById("dlg").open')
            nviv = pg.locator('#d-b tbody tr').count()
            inf.check(okd and nviv == packs[0]['n'], 'el modal de viviendas abre con sus viviendas', f'{nviv} viviendas')
            pg.keyboard.press('Escape')
            inf.check(not pg.evaluate('() => document.getElementById("dlg").open'), 'el modal se cierra con Esc')
            pg.select_option('#cr-p', '1')
            inf.check(txt('#cr-t') == 'Cronograma de pagos · Pack 1', 'el selector de pack del cronograma funciona')
            pg.select_option('#cr-p', '0')
        else:
            inf.check(pg.locator('#cr-p').count() == 0, 'modo único: sin selector de pack en el cronograma')
            inf.check(pg.locator('#rows, #cbar, #cdl, #dlg').count() == 0, 'modo único: sin DOM de packs')
            filas = pg.eval_on_selector_all('#edificio tbody tr', 'es => es.map(e => [...e.cells].map(c => c.textContent))')
            tot = pg.eval_on_selector_all('#edificio tfoot tr td', 'es => es.map(e => e.textContent)')
            suma = sum(int(f[1].replace('.', '')) for f in filas)
            inf.check(suma == int(tot[1].replace('.', '')) == len(us), 'la tabla de composición suma el total de viviendas', f'{suma} = {tot[1]} = {len(us)}')
            m2 = sum(u[3] for u in us)
            m2_web = int(pg.eval_on_selector('#edificio .comp-g div:nth-child(2) b', 'e => e.textContent').replace(' m²', '').replace('.', ''))
            m2_pond = sum(int(f[1].replace('.', '')) * float(f[2].replace(' m²', '').replace(',', '.')) for f in filas)
            inf.check(m2_web == B.m2_total(us) and abs(m2_web - m2) < 1 and abs(m2_pond - m2) <= 0.05 * len(us),
                      'la composición suma los m² del edificio', f'{m2_web} m² mostrados; suma de viviendas {m2:.1f}; viviendas × media {m2_pond:.1f}')
            pdft = pd.eval_on_selector_all('table.comp tr', 'es => es.map(e => e.textContent)')
            webt = pg.eval_on_selector_all('#edificio table tr', 'es => es.map(e => e.textContent)')
            inf.check(pdft == webt, 'la tabla de composición del PDF = la de la web')

        # 8. Galería y lightbox
        pg.locator('#producto').scroll_into_view_if_needed()
        pg.wait_for_timeout(400)
        imgs = pg.eval_on_selector_all('#producto img', 'es => es.map(e => [e.complete && e.naturalWidth > 0, e.getAttribute("src")])')
        inf.check(imgs and all(i[0] for i in imgs), 'la galería de renders carga', ', '.join(i[1] for i in imgs if not i[0]))
        if imgs:
            pg.click('#producto figure >> nth=0')
            ab = pg.evaluate('() => document.getElementById("gdl").open')
            pg.keyboard.press('Escape')
            c1 = not pg.evaluate('() => document.getElementById("gdl").open')
            pg.click('#producto figure >> nth=1')
            pg.click('#gdl button')
            c2 = not pg.evaluate('() => document.getElementById("gdl").open')
            inf.check(ab and c1 and c2, 'el lightbox abre y cierra (Esc y botón)')

        # 9. Secciones
        ids = pg.eval_on_selector_all('main > section[id], main > div.hero', 'es => es.map(e => e.id || "hero")')
        inf.check(ids == ['hero'] + SECCIONES[modo], 'secciones y orden = plantilla', ' · '.join(ids))
        inf.check((pg.locator('.draft').count() > 0) == bool(data.get('borrador')), 'franja de borrador según project.json → borrador')
        inf.check(pg.locator('footer.pf').count() == 1 and pg.locator('footer.pf .pf-badge').count() == 2, 'pie PropHero completo')

        # 10. Enlaces del pie
        enlaces = sorted(set(pg.eval_on_selector_all('footer.pf a[href^="http"]', 'es => es.map(e => e.href)')))
        pg.close()
        if a.sin_red:
            inf.aviso('enlaces del pie no comprobados (--sin-red)')
        else:
            caidos, avisos = [], []
            for u in enlaces:
                try:
                    rq = urllib.request.Request(u, headers={'User-Agent': 'Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/124 Safari/537.36', 'Accept-Language': 'es-ES,es'})
                    with urllib.request.urlopen(rq, timeout=20) as r:
                        st = r.status
                except urllib.error.HTTPError as e:
                    st = e.code
                except Exception as e:
                    st = None
                    caidos.append(f'{u} ({type(e).__name__})')
                    continue
                if st in (404, 410):
                    caidos.append(f'{u} ({st})')
                elif st >= 400:
                    avisos.append(f'{u} ({st})')
            inf.check(not caidos, f'enlaces del pie responden ({len(enlaces)})', '; '.join(caidos))
            if avisos:
                inf.aviso('enlaces del pie que responden con error (posible bloqueo anti-robots)', '; '.join(avisos))

        # 11. PDF: márgenes, celdas y descarga
        bad = pd.evaluate(JS_MARGENES, MM)
        inf.check(not bad, 'PDF sin elementos fuera de márgenes, solapes con el pie ni celdas recortadas', '; '.join(bad))
        npag = pd.locator('.page').count()
        pd.close()
        dl = ctx.new_page()
        tmp = tempfile.mkdtemp(prefix='qa-pdf-')
        try:
            with dl.expect_download(timeout=90000) as info:
                dl.goto(f'{base}/dossier.html?dl=1')
            ruta = os.path.join(tmp, info.value.suggested_filename)
            info.value.save_as(ruta)
            es_pdf, n, cajas = numeros_pdf(ruta)
            a4 = all(abs(float(w) - 595.28) < 1 and abs(float(h) - 841.89) < 1 for w, h in cajas) and len(cajas) >= n
            inf.check(es_pdf and 4 <= n <= 5 and n == npag and a4, 'dossier.html?dl=1 descarga un PDF A4 de 4–5 páginas',
                      f'{info.value.suggested_filename}: {n} páginas, {os.path.getsize(ruta) // 1024} KB')
        except Exception as e:
            inf.fallo('dossier.html?dl=1 descarga un PDF A4 de 4–5 páginas', f'{type(e).__name__}: {e}'[:200])
        br.close()
    srv.shutdown()
    sys.exit(0 if inf.imprimir() else 1)


if __name__ == '__main__':
    main()
