#!/usr/bin/env python3
"""Genera la landing publicable de un proyecto: template/ + projects/<carpeta>/project.json → dist/<slug>/.

Uso:
    python3 scripts/build.py <carpeta-o-slug> [--modo unico|paquetizado] [--out DIR] [--estricto]

- <carpeta-o-slug>: nombre de la carpeta en projects/ (p. ej. montserrat-ausias-march) o su `slug` del JSON.
- --modo: fuerza un modo distinto al del JSON (solo para pruebas; la salida debe ir a --out, nunca a dist/).
- --out: carpeta de salida alternativa (por defecto dist/<slug>/).
- --estricto: termina con error si falta algún dato (por defecto, avisa y pinta «Pendiente»).

Solo usa la biblioteca estándar de Python. Las cifras derivadas (composición por tipología, m² totales,
€/m², yield, subtotales del cronograma, «X € por cada 100 €», meses) se calculan aquí o en app.js/ui.js,
con el mismo redondeo que JavaScript (toFixed y Math.round).
"""
import argparse
import html
import json
import math
import os
import re
import shutil
import sys
import urllib.parse
from decimal import Decimal, ROUND_HALF_UP

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
TEMPLATE = os.path.join(ROOT, 'template')
PROJECTS = os.path.join(ROOT, 'projects')
DIST = os.path.join(ROOT, 'dist')
NA = 'Pendiente'
MODOS = ('unico', 'paquetizado')
TIPO_NOMBRE = {0: 'Estudios', 1: '1 dormitorio', 2: '2 dormitorios'}
TIPO_COLOR = {0: 'var(--navy)', 1: 'var(--blue)', 2: 'var(--blue-l)'}
DRIVE_FINANCIAL = '01_DOCUMENTACIÓN/01.4_FINANCIAL'
NCLS = ' class="n"'


# ---------------------------------------------------------------- formato (idéntico a JavaScript)
def js_round(x):
    """Math.round de JavaScript."""
    return int(math.floor(x + 0.5))


def to_fixed(x, d):
    """Number.prototype.toFixed: redondeo sobre el valor binario exacto, empates hacia fuera."""
    q = Decimal(1).scaleb(-d) if d else Decimal(1)
    return str(Decimal(x).quantize(q, rounding=ROUND_HALF_UP))


def js_num(x):
    """Representación de un número como lo imprime JavaScript (String(n))."""
    if isinstance(x, float) and x.is_integer():
        x = int(x)
    return repr(x)


def g(n):
    s = str(int(n))
    neg = s.startswith('-')
    s = s.lstrip('-')
    s = re.sub(r'\B(?=(\d{3})+(?!\d))', '.', s)
    return ('-' if neg else '') + s


def coma(x, d):
    return to_fixed(x, d).replace('.', ',')


def M(n):
    return coma(n / 1e6, 1) + ' M€'


def K(n):
    return g(js_round(n / 1000)) + ' k€'


def P1(n):
    return coma(n * 100, 1) + ' %'


def E(n):
    return ('-' if n < 0 else '+') + g(abs(js_round(n / 1000)) * 1000) + ' €'


def mm(x):
    return to_fixed(x, 2) + 'mm'


def mix_txt(m):
    out = []
    for k in sorted(m):
        v = m[k]
        out.append(f"{v} {'estudios' if v > 1 else 'estudio'}" if k == '0' else f"{v} de {k} dorm.")
    return ' · '.join(out)


# ---------------------------------------------------------------- datos
class Datos:
    """Acceso al project.json con resolución de textos por modo y registro de lo que falta."""

    def __init__(self, data, modo):
        self.data = data
        self.modo = modo
        self.faltan = []

    def _resolve(self, v):
        if isinstance(v, dict) and v and set(v) <= set(MODOS):
            return v.get(self.modo)
        return v

    def get(self, path, default=NA, obligatorio=True):
        cur = self.data
        for part in path.split('.'):
            cur = self._resolve(cur)
            if isinstance(cur, dict) and part in cur:
                cur = cur[part]
            elif isinstance(cur, list) and part.isdigit() and int(part) < len(cur):
                cur = cur[int(part)]
            else:
                cur = None
                break
        cur = self._resolve(cur)
        if cur is None or cur == '' or cur == []:
            if obligatorio and path not in self.faltan:
                self.faltan.append(path)
            return default
        return cur

    def has(self, path):
        return self.get(path, None, obligatorio=False) is not None


def escribir_json(path, data):
    """Guarda project.json legible: arrays y objetos pequeños de valores simples en una sola línea."""
    txt = json.dumps(data, ensure_ascii=False, indent=1)
    txt = re.sub(r'\[\s*([^\[\]{}]*?)\s*\]', lambda m: '[' + re.sub(r'\s*\n\s*', ' ', m.group(1)) + ']', txt)
    txt = re.sub(r'\{\s*([^\[\]{}]*?)\s*\}', lambda m: '{' + re.sub(r'\s*\n\s*', ' ', m.group(1)) + '}' if len(m.group(0)) < 400 else m.group(0), txt)
    with open(path, 'w', encoding='utf-8') as f:
        f.write(txt + '\n')


# ---------------------------------------------------------------- plantillas
def render(tpl, ctx, flags, nombre):
    def cond(m):
        neg, flag, body = m.group(1) == '^', m.group(2), m.group(3)
        on = bool(flags.get(flag))
        return body if on != neg else ''
    prev = None
    while prev != tpl:
        prev = tpl
        tpl = re.sub(r'\{\{([#^])(\w+)\}\}(.*?)\{\{/\2\}\}', cond, tpl, flags=re.S)

    def val(m):
        k = m.group(1)
        if k not in ctx:
            raise SystemExit(f'ERROR: marcador {{{{{k}}}}} sin valor en {nombre}')
        return str(ctx[k])
    out = re.sub(r'\{\{(\w+)\}\}', val, tpl)
    resto = re.findall(r'\{\{[^}]*\}\}', out)
    if resto:
        raise SystemExit(f'ERROR: marcadores sin resolver en {nombre}: {sorted(set(resto))}')
    return out


def leer(nombre):
    with open(os.path.join(TEMPLATE, nombre), encoding='utf-8') as f:
        return f.read()


# ---------------------------------------------------------------- cálculos derivados
def viviendas(d):
    """Lista de viviendas [portal, planta, nº, m², tipología, orientación, precio]: `viviendas` o las de los packs."""
    v = d.data.get('viviendas')
    if v:
        return v
    out = []
    for p in d.data.get('packs') or []:
        out.extend(p.get('u') or [])
    return out


def composicion(us):
    """Filas de la tabla por tipología y fila total: viviendas, superficie media, precio medio, €/m²."""
    def fila(nombre, grupo, tot=False):
        n = len(grupo)
        m2 = sum(u[3] for u in grupo)
        pr = sum(u[6] for u in grupo)
        celdas = [nombre, g(n), coma(m2 / n, 1) + ' m²', g(js_round(pr / n / 100) * 100) + ' €', g(js_round(pr / m2))]
        cls = ' class="tot"' if tot else ''
        return f'<tr{cls}><td>{celdas[0]}</td>' + ''.join(f'<td class="n">{c}</td>' for c in celdas[1:]) + '</tr>'
    tipos = sorted({int(u[4]) for u in us})
    filas = [fila(TIPO_NOMBRE.get(t, f'{t} dormitorios'), [u for u in us if int(u[4]) == t]) for t in tipos]
    return filas, fila('Total edificio', us, tot=True)


def m2_total(us):
    """Superficie construida total: suma de las viviendas, truncada al m² (no se redondea al alza)."""
    return int(math.floor(round(sum(u[3] for u in us), 6)))


def cron_valores(cr):
    return [c + s for c, s in zip(cr['costes'], cr['cobros'])]


def cron_dossier(cr):
    """Cronograma estático del PDF (mismas proporciones que la referencia: 62 mm de alto)."""
    v = cron_valores(cr)
    tot = sum(v)
    allv = v + [tot]
    mx, mn = max(allv + [0]), min(allv + [0])
    H, top, span = 62, 7, 42
    y0 = top + mx / (mx - mn) * span
    sc = span / (mx - mn)
    cols = len(allv)
    st = 'height:62mm' + ('' if cols == 6 else f';grid-template-columns:repeat({cols},1fr)')
    out = [f'<div class="dch-c" style="{st}"><div class="dax" style="top:{mm(y0)}"></div>']
    for i, x in enumerate(allv):
        s = i == cols - 1
        cls = 's' if s else ('n' if x < 0 else 'p')
        h = max(abs(x) * sc, 0.6)
        bt = y0 if x < 0 else y0 - h
        lt = y0 + h + 1.6 if x < 0 else bt - 5
        q = 'Subtotal' if s else cr['trimestres'][i]
        out.append(f'<div class="cc"><div class="cb {cls}" style="top:{mm(bt)};height:{mm(h)}"></div>'
                   f'<span class="cv {cls}" style="top:{mm(lt)}">{E(x)}</span>'
                   f'<span class="cq{" s" if s else ""}">{q}</span></div>')
    out.append('</div>')
    return ''.join(out)


def telefono(wa):
    """34650522730 → +34 650 52 27 30 (formato español)."""
    w = re.sub(r'\D', '', str(wa))
    if w.startswith('34') and len(w) == 11:
        r = w[2:]
        return f'+34 {r[:3]} {r[3:5]} {r[5:7]} {r[7:]}'
    return '+' + w


def archivo_pdf(nombre_completo):
    base = re.sub(r'\s*·\s*', '-', nombre_completo)
    base = re.sub(r'[^\w-]+', '-', base, flags=re.U).strip('-')
    return base + '-dossier.pdf'


def fmt_pct_css(x):
    s = to_fixed(x, 1)
    return s[:-2] if s.endswith('.0') else s


# ---------------------------------------------------------------- zona ampliada (bloques)
def attrs(b):
    a = ''
    if b.get('clase'):
        a += f' class="{b["clase"]}"'
    if b.get('estilo'):
        a += f' style="{b["estilo"]}"'
    return a


def bloque(b):
    t = b.get('tipo')
    if t == 'p':
        return f'<p{attrs(b)}>{b["html"]}</p>'
    if t == 'grupo':
        return f'<div{attrs(b)}>\n' + '\n'.join(bloque(x) for x in b['bloques']) + '\n</div>'
    if t == 'dos_columnas':
        return '<div class="two">\n' + '\n'.join(bloque(x) for x in b['columnas']) + '\n</div>'
    if t == 'html':
        return b['html']
    if t == 'tabla':
        cols = b['columnas']
        th = ''.join(f'<th{NCLS if c.get("n") else ""}>{c["t"]}</th>' for c in cols)
        filas = []
        for f in b['filas']:
            tds = []
            for c, cel in zip(cols, f):
                if isinstance(cel, dict):
                    txt = cel['t'] + (f'<span class="sub">{cel["sub"]}</span>' if cel.get('sub') else '')
                else:
                    txt = cel
                tds.append(f'<td{NCLS if c.get("n") else ""}>{txt}</td>')
            filas.append('<tr>' + ''.join(tds) + '</tr>')
        st = f' style="{b["estilo"]}"' if b.get('estilo') else ''
        nota = (bloque(b['nota']) + '\n') if b.get('nota') else ''
        return (f'<div class="tw"{st}>\n<table>\n<thead><tr>{th}</tr></thead>\n<tbody>\n' + '\n'.join(filas) +
                f'\n</tbody>\n</table>\n{nota}</div>')
    if t == 'cita':
        f = f'<small>{b["fuente"]}</small>' if b.get('fuente') else ''
        return f'<div class="quote">{b["texto"]}{f}</div>'
    if t == 'kpis':
        cls = 'kpis' + (' ' + b['clase'] if b.get('clase') else '')
        return f'<div class="{cls}">\n' + '\n'.join(
            f'<div class="kpi"><b>{k["valor"]}</b><span>{k["texto"]}</span></div>' for k in b['items']) + '\n</div>'
    if t == 'barras':
        mx = b['max']
        out = []
        for r in b['filas']:
            w = max(r['valor'] / mx * 100, 18)
            out.append(f'<div class="b {r.get("clase", "")}"><div class="l">{r["etiqueta"]}<small>{r["sub"]}</small></div>'
                       f'<div class="track"><div class="fill" style="width:{js_num(w)}%">{g(js_round(r["valor"]))} €</div></div></div>')
        return '<div class="bars">' + ''.join(out) + '</div>'
    if t == 'rentabilidad':
        mx = b['max']
        out = []
        for r in b['filas']:
            txt = re.sub(r'0$', '', to_fixed(r['valor'], 2).replace('.', ','))
            out.append(f'<div class="y {"us" if r.get("destacada") else ""}"><div class="l">{r["etiqueta"]}'
                       f'<div class="small muted" style="font-weight:500">{r["sub"]}</div></div>'
                       f'<div class="track"><div class="fill" style="width:{js_num(r["valor"] / mx * 100)}%">{txt} %</div></div></div>')
        return '<div class="yield">' + ''.join(out) + '</div>'
    if t == 'tamanos':
        return '<div class="sizes">\n' + '\n'.join(
            f'<div class="size{" alt" if s.get("alt") else ""}"><b>{s["valor"]} <small>{s["unidad"]}</small></b><p>{s["texto"]}</p></div>'
            for s in b['items']) + '\n</div>'
    if t == 'relojes':
        return '<div class="clocks">\n' + '\n'.join(
            f'<div class="clock"><p class="ctag">{c["etiqueta"]}</p><h3>{c["titulo"]}</h3><p>{c["texto"]}</p></div>'
            for c in b['items']) + '\n</div>'
    raise SystemExit(f'ERROR: tipo de bloque desconocido en zona_ampliada: {t!r}')


def zona_ampliada(za):
    out = []
    for s in za['secciones']:
        cls = 'zsub' + (' mist' if s.get('fondo') == 'mist' else '')
        cuerpo = '\n'.join(bloque(b) for b in s.get('bloques', [])) or f'<p class="narrow">{NA}</p>'
        out.append(f'<section class="{cls}" id="{s["id"]}">\n<div class="wrap">\n<p class="label">{s["etiqueta"]}</p>\n'
                   f'<h2>{s["titulo"]}</h2>\n{cuerpo}\n</div>\n</section>')
    return '\n'.join(out)


# ---------------------------------------------------------------- build
def localizar(arg):
    cand = os.path.join(PROJECTS, arg)
    if os.path.isfile(os.path.join(cand, 'project.json')):
        return cand
    for n in sorted(os.listdir(PROJECTS)):
        pj = os.path.join(PROJECTS, n, 'project.json')
        if os.path.isfile(pj):
            with open(pj, encoding='utf-8') as f:
                if json.load(f).get('slug') == arg:
                    return os.path.join(PROJECTS, n)
    raise SystemExit(f'ERROR: no encuentro el proyecto «{arg}» en projects/')


def build(arg, modo=None, out=None, estricto=False, quiet=False):
    carpeta = localizar(arg)
    with open(os.path.join(carpeta, 'project.json'), encoding='utf-8') as f:
        data = json.load(f)
    modo = modo or data.get('modo')
    if modo not in MODOS:
        raise SystemExit('ERROR: project.json → modo debe ser "unico" o "paquetizado". '
                         'Nunca se elige por defecto: pregunta «¿Paquetizado o producto único?».')
    d = Datos(data, modo)
    slug = d.get('slug')
    unico, paq = modo == 'unico', modo == 'paquetizado'

    nombre = d.get('nombre')
    ncomp = d.get('nombre_completo')
    us = viviendas(d)
    if not us:
        d.faltan.append('packs[].u (viviendas)' if paq else 'viviendas (o packs[].u)')
    packs = data.get('packs') or []
    if paq:
        if not packs:
            d.faltan.append('packs')
        for p in packs:
            for k in ('id', 'n', 'mix', 'm2', 'c', 'v', 'b', 'r', 't', 'pesos', 'u'):
                if p.get(k) in (None, '', []):
                    d.faltan.append(f'packs[{p.get("id", "?")}].{k}')

    proy = data.get('proyecto') or {}
    proy_ok = all(proy.get(k) is not None for k in ('coste_iva', 'coste_sin_iva', 'ventas', 'tir'))
    if not proy_ok:
        d.faltan.append('proyecto (coste_iva, coste_sin_iva, ventas, tir)')
    pp = data.get('plan_pagos') or {}
    pp_ok = all(pp.get(k) is not None for k in ('aportas', 'recibes', 'ganancia_neta'))
    if not pp_ok:
        d.faltan.append('plan_pagos (aportas, recibes, ganancia_neta)')
    cr = data.get('cronograma') or {}
    cr_ok = bool(cr.get('trimestres')) and len(cr.get('costes') or []) == len(cr['trimestres']) == len(cr.get('cobros') or [])
    if not cr_ok:
        d.faltan.append('cronograma (trimestres, costes, cobros)')

    nviv = len(us)
    m2t = m2_total(us) if us else None
    garajes = d.get('facts.garajes')
    trasteros = d.get('facts.trasteros')
    wa = d.get('whatsapp')
    wa_msg = d.get('whatsapp_mensaje')
    wa_url = f'https://wa.me/{wa}?text=' + urllib.parse.quote(wa_msg, safe="-_.!~*'()") if NA not in (wa, wa_msg) else '#'
    rangos = {k: d.get('rangos.' + k) for k in ('yield', 'tir', 'beneficio')}
    listas_v = d.get('listas_para_alquilar.valor')
    listas_n = d.get('listas_para_alquilar.nota', None, obligatorio=False)
    renders = [r for r in (d.get('renders', []) or []) if isinstance(r, dict)]

    ctx = {}
    ctx['nombre'] = nombre
    ctx['nombre_completo'] = ncomp
    ctx['meta_descripcion'] = html.escape(re.sub('<[^>]+>', '', str(d.get('pagina.descripcion'))), quote=True)
    ctx['borrador_texto'] = d.get('borrador_texto', 'Borrador · cifras provisionales pendientes del modelo final', obligatorio=False)
    ctx['subtitulo'] = d.get('subtitulo')
    ctx['lede'] = d.get('lede')
    ctx['f_ubicacion'] = d.get('facts.ubicacion')
    ctx['f_tipologias'] = d.get('facts.tipologias', mix_txt({str(t): sum(1 for u in us if int(u[4]) == t) for t in {int(u[4]) for u in us}}) if us else NA)
    ctx['f_garajes'] = g(garajes) if isinstance(garajes, int) else garajes
    ctx['f_trasteros'] = g(trasteros) if isinstance(trasteros, int) else trasteros
    ctx['f_financiacion'] = d.get('facts.financiacion')
    ctx['wa_url'] = html.escape(wa_url, quote=True)
    ctx['listas_valor'] = listas_v
    ctx['listas_nota_html'] = f'<small>{listas_n}</small>' if listas_n else ''
    ctx['zona_titular'] = d.get('zona.titular')
    ctx['zona_texto'] = d.get('zona.texto')
    ctx['zona_distancias'] = '<div class="dist">' + ''.join(f'<span>{x}</span>' for x in d.get('zona.distancias', [])) + '</div>'
    kp = d.get('zona.kpis', [])
    if kp and len(kp) != 4:
        print(f'AVISO: zona.kpis debe tener 4 cifras (tiene {len(kp)}).')
    ctx['zona_kpis'] = '\n'.join(f'<div><b>{k["valor"]}</b><span>{k["texto"]}</span></div>' for k in kp) or f'<div><b>{NA}</b><span>KPIs de mercado</span></div>'
    bl = d.get('zona.bloques', [])
    if bl and [b.get('etiqueta') for b in bl] != ['Industria', 'Infraestructuras', 'Empleo y servicios']:
        print('AVISO: zona.bloques debe ser Industria · Infraestructuras · Empleo y servicios, en ese orden.')
    ctx['zona_bloques'] = '\n'.join(f'<div><i>{b["etiqueta"]}</i><h3>{b["titulo"]}</h3><p>{b["texto"]}</p></div>' for b in bl) or \
        '\n'.join(f'<div><i>{e}</i><h3>{NA}</h3><p></p></div>' for e in ('Industria', 'Infraestructuras', 'Empleo y servicios'))
    ctx['zona_fuentes'] = d.get('zona.fuentes')
    jsq = lambda v: "'" + str(v).replace('\\', '\\\\').replace("'", "\\'") + "'"
    ctx['rangos_js'] = '{yield:%s,tir:%s,beneficio:%s}' % (jsq(rangos['yield']), jsq(rangos['tir']), jsq(rangos['beneficio']))
    # Composición (modo único y PDF)
    if us:
        filas, total = composicion(us)
        ctx['comp_filas'] = '\n'.join(filas)
        ctx['comp_total'] = total
    else:
        ctx['comp_filas'] = f'<tr><td colspan="5">{NA}</td></tr>'
        ctx['comp_total'] = ''
    ctx['n_viviendas'] = g(nviv) if us else NA
    ctx['m2_total'] = g(m2t) if us else NA
    ctx['edificio_texto'] = d.get('edificio.texto') if unico else ''
    ctx['edificio_etiqueta_viviendas'] = d.get('edificio.etiqueta_viviendas', 'Viviendas', obligatorio=False)
    ctx['edificio_nota'] = d.get('edificio.nota', 'Superficies construidas con elementos comunes. Precios medios de mercado por vivienda según el modelo financiero.', obligatorio=False)
    ctx['n_packs'] = g(len(packs)) if packs else NA
    ctx['producto_titulo'] = d.get('producto.titulo')

    # ---- datos para app.js / ui.js
    D = {'modo': modo,
         'proj': {'c': proy['coste_iva'], 'cs': proy['coste_sin_iva'], 'v': proy['ventas'], 't': proy['tir']} if proy_ok else None,
         'pp': {'a': pp['aportas'], 'r': pp['recibes'], 'n': pp['ganancia_neta']} if pp_ok else None,
         'cron': {'q': cr['trimestres'], 'c': cr['costes'], 's': cr['cobros']} if cr_ok else None,
         'nviv': nviv, 'm2tot': m2t,
         'renders': [{'archivo': r['archivo'], 'titulo': r.get('titulo', ''), 'texto': r.get('texto', '')} for r in renders],
         'producto': {'titulo': d.get('producto.titulo'), 'texto': d.get('producto.texto')},
         'pie': d.get('pie')}
    if paq:
        D['packs'] = [{'id': p['id'], 'n': p['n'], 'mix': p['mix'], 'm2': p['m2'], 'c': p['c'], 'v': p['v'], 'b': p['b'],
                       'r': p['r'], 't': p['t'], 'w': p.get('pesos') or [0, 0], 'u': p.get('u') or []} for p in packs]
        todas_garaje = isinstance(garajes, int) and garajes >= nviv
        D['nota_viviendas'] = ('Todas las viviendas incluyen plaza de garaje. ' if todas_garaje else '') + 'm² construidos con elementos comunes.'

    # ---- dossier
    ctx['d_subtitulo'] = d.get('dossier.subtitulo')
    ctx['d_descripcion'] = d.get('dossier.descripcion')
    ctx['d_coste'] = '≈ ' + M(proy['coste_iva']) if proy_ok else NA
    ctx['rango_yield'], ctx['rango_tir'], ctx['rango_beneficio'] = rangos['yield'], rangos['tir'], rangos['beneficio']
    ctx['d_proyecto_titulo'] = d.get('dossier.proyecto_titulo')
    ctx['d_proyecto_texto'] = d.get('dossier.proyecto_texto')
    tipos = sorted({int(u[4]) for u in us})
    seg, ley = [], []
    for t in tipos:
        n = sum(1 for u in us if int(u[4]) == t)
        etiqueta = f'{n} estudios' if t == 0 else str(n)
        seg.append(f'<i style="width:{to_fixed(n / nviv * 100, 1)}%;background:{TIPO_COLOR.get(t, "var(--muted)")}">{etiqueta}</i>')
        ley.append(f'<span style="--c:{TIPO_COLOR.get(t, "var(--muted)")}">{TIPO_NOMBRE.get(t, f"{t} dormitorios")}</span>')
    ctx['d_mixbar'] = ''.join(seg)
    ctx['d_leyenda'] = ''.join(ley)
    ctx['d_viviendas_fact'] = (f'{g(nviv)}, en una única operación' if unico else f'{g(nviv)}, en {len(packs)} packs') if us else NA
    zt = d.get('dossier.zona_textos', [])
    ztxt = [f'<h2 style="font-size:19pt">{d.get("dossier.zona_titulo")}</h2>']
    for i, p in enumerate(zt if isinstance(zt, list) else []):
        ztxt.append(f'<p class="lead" style="font-size:9.8pt{";margin-top:2mm" if i else ""}">{p}</p>')
    ctx['d_zona_textos'] = '\n'.join(ztxt)
    zc = d.get('dossier.zona_cifras', [])
    ctx['d_zona_cifras'] = '\n'.join(f'<div><b>{z["valor"]}</b><span>{z["texto"]}</span></div>' for z in (zc if isinstance(zc, list) else [])) or f'<div><b>{NA}</b><span></span></div>'
    ctx['d_distancias_titulo'] = d.get('dossier.distancias_titulo')
    eje = d.get('dossier.eje', [])
    ejeh = [f'<div class="ln"></div><div class="o"></div><span>{nombre}</span>']
    if isinstance(eje, list) and eje:
        kmax = max(e['km'] for e in eje)
        for i, e in enumerate(eje):
            left = fmt_pct_css(e['km'] / kmax * 100)
            lab = '97' if left == '100' else left
            ejeh.append(f'<div class="p" style="left:{left}%"></div><div class="pl" style="left:{lab}%;top:{"12mm" if i % 2 == 0 else "0"}">{e["nombre"]}<small>{g(e["km"]) if isinstance(e["km"], int) else e["km"]} km</small></div>')
    ctx['d_eje'] = '\n'.join(ejeh)
    ctx['d_fuentes'] = d.get('dossier.fuentes')
    ctx['d_pie'] = d.get('dossier.pie')
    ctx['d_producto_texto'] = d.get('dossier.producto_texto')
    ctx['d_nota_comp'] = f'Superficies construidas con elementos comunes. Además, {ctx["f_garajes"]} plazas de garaje y {ctx["f_trasteros"]} trasteros.'
    rg = []
    for i, r in enumerate(renders):
        if i == 0:
            tx = r.get('texto', '')
            cap = f'<b>{r["titulo"]}</b> · {tx[:1].lower() + tx[1:]}' if tx else f'<b>{r["titulo"]}</b>'
            rg.append(f'<figure class="a"><img src="/assets/{r["archivo"]}" alt="{r["titulo"]}"><figcaption>{cap}</figcaption></figure>')
        else:
            rg.append(f'<figure><img src="/assets/{r["archivo"]}" alt="{r["titulo"]}"><figcaption><b>{r["titulo"]}</b></figcaption></figure>')
    ctx['d_renders'] = ('<div class="rg2">' + '\n'.join(rg) + '</div>') if rg else f'<p class="lead">{NA}</p>'
    ctx['d_renders_big'] = ('<div class="rg2 big">' + '\n'.join(rg) + '</div>') if rg else f'<p class="lead">{NA}</p>'
    if paq and packs:
        mxT = max(p['t'] for p in packs)
        ctx['d_packs_filas'] = '\n'.join(
            f'<tr><td><b>Pack {p["id"]}</b></td><td class="n">{p["n"]}</td><td class="mx">{mix_txt(p["mix"])}</td><td class="n">{g(p["m2"])}</td>'
            f'<td class="n">{K(p["c"])}</td><td class="n">{K(p["v"])}</td><td class="n">{K(p["b"])}</td><td class="n">{P1(p["r"])}</td>'
            f'<td class="n">{P1(p["t"])}</td><td><div class="tb2"><i style="width:{to_fixed(p["t"] / mxT * 100, 1)}%"></i></div></td></tr>'
            for p in packs)
        ctx['d_packs_total'] = (f'<tr class="tot"><td>Total</td><td class="n">{g(nviv)}</td><td></td><td class="n">{g(m2t) if us else NA}</td>'
                                + (f'<td class="n">{K(proy["coste_iva"])}</td><td class="n">{K(proy["ventas"])}</td><td class="n">{K(proy["ventas"] - proy["coste_sin_iva"])}</td>'
                                   f'<td class="n">{P1((proy["ventas"] - proy["coste_sin_iva"]) / proy["coste_sin_iva"])}</td><td class="n">{P1(proy["tir"])}</td><td></td></tr>'
                                   if proy_ok else f'<td class="n" colspan="6">{NA}</td></tr>'))
    else:
        ctx['d_packs_filas'] = f'<tr><td colspan="10">{NA}</td></tr>'
        ctx['d_packs_total'] = ''
    ctx['d_nota_packs'] = ('Todas las viviendas incluyen plaza de garaje. ' if isinstance(garajes, int) and garajes >= nviv else '') + \
        'm² construidos con elementos comunes. Yield: beneficio sobre inversión sin IVA. TIR estimada de cada pack según el modelo financiero.'
    ctx['d_aportas'] = M(pp['aportas']) if pp_ok else NA
    ctx['d_recibes'] = M(pp['recibes']) if pp_ok else NA
    ctx['d_ganancia'] = M(pp['ganancia_neta']) if pp_ok else NA
    meses = len(cr['trimestres']) * 3 if cr_ok else None
    ctx['d_meses_txt'] = f' en {meses} meses' if meses else ''
    ctx['d_cron'] = cron_dossier(cr) if cr_ok else f'<div class="dch-c" style="height:20mm"><p style="color:#C9CDD5;padding-top:6mm">{NA}</p></div>'
    if pp_ok:
        x = js_round(pp['recibes'] / pp['aportas'] * 100)
        en = f'en {meses} meses y ' if meses else ''
        ctx['d_mult'] = f'<div class="mult"><b>{x} €</b><p>se recuperan por cada 100 € aportados, {en}con el IVA incluido en ambos lados.</p></div>'
    else:
        ctx['d_mult'] = ''
    ctx['d_telefono'] = telefono(wa) if wa != NA else NA
    ctx['d_archivo'] = archivo_pdf(ncomp)
    pags = ['portada', 'zona', 'producto'] + (['packs'] if paq else []) + ['pagos']
    for i, p in enumerate(pags, 1):
        ctx['pg_' + p] = i
    ctx.setdefault('pg_packs', '')
    ctx['pg_total'] = len(pags)

    # ---- zona ampliada
    za = data.get('zona_ampliada')
    ctx['za_intro'] = d.get('zona_ampliada.intro')
    ctx['za_pie'] = d.get('zona_ampliada.pie_fuentes')
    if za and za.get('secciones'):
        ctx['za_secciones'] = zona_ampliada(za)
    else:
        d.get('zona_ampliada.secciones')
        ctx['za_secciones'] = f'<section class="zsub" id="pendiente">\n<div class="wrap">\n<p class="label">Información ampliada</p>\n<h2>{NA}</h2>\n</div>\n</section>'

    flags = {'unico': unico, 'paquetizado': paq, 'borrador': bool(data.get('borrador'))}

    # ---- validaciones de coherencia (avisos, no bloquean el build)
    avisos = []
    if paq and packs and proy_ok:
        tol = len(packs)  # cada pack se redondea al euro en el Excel
        for k, ref in (('c', proy['coste_iva']), ('v', proy['ventas'])):
            dif = sum(p[k] for p in packs) - ref
            if abs(dif) > tol:
                avisos.append(f'la suma de packs.{k} difiere de proyecto en {dif:+,.0f} €'.replace(',', '.'))
        if sum(p['n'] for p in packs) != nviv:
            avisos.append('la suma de viviendas de los packs no coincide con el total')
    if cr_ok and pp_ok and abs(sum(cron_valores(cr)) - pp['ganancia_neta']) > 1:
        avisos.append(f'el subtotal del cronograma ({sum(cron_valores(cr)):.2f}) no coincide con plan_pagos.ganancia_neta ({pp["ganancia_neta"]})')

    # ---- escritura
    dest = os.path.abspath(out or os.path.join(DIST, str(slug)))
    if os.path.isdir(dest):
        shutil.rmtree(dest)
    os.makedirs(os.path.join(dest, 'assets'))
    for nombre_t in ('index.html', 'zona.html', 'dossier.html'):
        txt = render(leer(nombre_t), ctx, flags, nombre_t)
        with open(os.path.join(dest, nombre_t), 'w', encoding='utf-8') as f:
            f.write(txt)
    app = leer('app.js').replace('/*{{DATA}}*/null', json.dumps(D, ensure_ascii=False, separators=(',', ':')))
    with open(os.path.join(dest, 'app.js'), 'w', encoding='utf-8') as f:
        f.write(app)
    shutil.copyfile(os.path.join(TEMPLATE, 'ui.js'), os.path.join(dest, 'ui.js'))
    for a in os.listdir(os.path.join(TEMPLATE, 'assets')):
        shutil.copyfile(os.path.join(TEMPLATE, 'assets', a), os.path.join(dest, 'assets', a))
    pa = os.path.join(carpeta, 'assets')
    for r in renders:
        src = os.path.join(pa, r['archivo'])
        if os.path.isfile(src):
            shutil.copyfile(src, os.path.join(dest, 'assets', r['archivo']))
        else:
            avisos.append(f'falta el render assets/{r["archivo"]}')

    rel = os.path.relpath(dest, ROOT)
    if not quiet:
        print(f'Build {slug} ({modo}) → {rel}/')
    if d.faltan:
        print('AVISO: faltan datos; esas secciones muestran «Pendiente»:')
        for x in d.faltan:
            print(f'  - {x}')
        print(f'  Pídelos a Hugo (cifras: Drive del proyecto → {DRIVE_FINANCIAL}).')
    for a in avisos:
        print(f'AVISO: {a}')
    if estricto and (d.faltan or avisos):
        raise SystemExit(1)
    return dest, d.faltan, avisos


def main():
    ap = argparse.ArgumentParser(description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter)
    ap.add_argument('proyecto')
    ap.add_argument('--modo', choices=MODOS)
    ap.add_argument('--out')
    ap.add_argument('--estricto', action='store_true')
    a = ap.parse_args()
    if a.modo and not a.out:
        raise SystemExit('ERROR: --modo solo para pruebas; indica también --out (fuera de dist/).')
    build(a.proyecto, a.modo, a.out, a.estricto)


if __name__ == '__main__':
    main()
