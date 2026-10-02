#!/usr/bin/env python3
"""Excel del modelo → cifras de project.json (CLAUDE.md §4). Primera versión.

Uso:
    python3 scripts/extract_excel.py <carpeta-o-slug> --excel RUTA.xlsx [--escribir] [--json SALIDA.json]

- Lee el Excel (que vive FUERA del repo: se descarga de Drive a una carpeta temporal; nunca se versiona).
- Busca cada dato por su ETIQUETA, nunca por posición fija. Las etiquetas aceptadas están en ETIQUETAS
  (sin tildes ni mayúsculas: la comparación se hace normalizada). Si un modelo usa otra etiqueta, se añade aquí.
- Solo extrae el escenario de PRECIO DE MERCADO. Las columnas o bloques de precio mínimo se ignoran.
- Sin --escribir solo informa: lo encontrado, lo que no ha encontrado y las diferencias con el project.json actual.
- Con --escribir actualiza en project.json únicamente las cifras (proyecto, plan_pagos, cronograma, packs) y solo si
  TODAS las validaciones cuadran. Si algo no cuadra, para y muestra la diferencia exacta (código de salida 2).
- Los textos, rangos (los fija dirección), renders y zona no se tocan nunca.
Requiere openpyxl (pip install --user openpyxl).
"""
import argparse
import datetime as dt
import json
import os
import re
import sys
import unicodedata

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
import build as B  # noqa: E402

# ------------------------------------------------------------------ etiquetas (normalizadas)
ETIQUETAS = {
    # Hoja «Detalle inversión» (proyecto completo)
    'coste_iva': ['TOTAL INVESTMENT', 'TOTAL INVESTMENT IVA INCLUIDO', 'TOTAL INVERSION', 'TOTAL INVERSION CON IVA', 'INVERSION TOTAL CON IVA'],
    'coste_sin_iva': ['TOTAL INVESTMENT SIN IVA', 'TOTAL INVESTMENT (SIN IVA)', 'TOTAL INVERSION SIN IVA', 'INVERSION TOTAL SIN IVA'],
    'ventas': ['VENTAS', 'TOTAL VENTAS', 'VENTAS TOTALES', 'INGRESOS POR VENTAS', 'TOTAL SALES', 'GDV'],
    # Hoja TIR
    'tir': ['TIR', 'TIR PROYECTO', 'TIR DEL PROYECTO', 'IRR', 'PROJECT IRR'],
    # Plan de pagos
    'aportas': ['APORTAS', 'TOTAL APORTADO', 'TOTAL APORTACIONES', 'APORTACION TOTAL'],
    'recibes': ['RECIBES', 'TOTAL RECIBIDO', 'TOTAL COBROS', 'TOTAL A RECIBIR'],
    'ganancia_neta': ['GANANCIA NETA', 'BENEFICIO NETO DE CAJA', 'RESULTADO NETO DE CAJA'],
    # Cashflow mensual (filas)
    'cf_costes': ['TOTAL COSTES', 'COSTES', 'TOTAL PAGOS', 'PAGOS', 'TOTAL OUTFLOWS'],
    'cf_cobros': ['TOTAL COBROS', 'COBROS', 'TOTAL INGRESOS', 'INGRESOS', 'TOTAL INFLOWS'],
    # Bloque de pack (referencia Montserrat)
    'p_gla': ['GLA'],
    'p_year': ['YEAR BUILT'],
    'p_purchase': ['PURCHASE PRICE'],
    'p_adq': ['ADQUISICION'],
    'p_hard': ['HARD COST'],
    'p_soft': ['SOFT COST'],
    'p_hardsoft': ['HARD&SOFT COST', 'HARD & SOFT COST'],
    'p_fees': ['FEES&FINANCIACION', 'FEES & FINANCIACION'],
    'p_total': ['TOTAL INVESTMENT'],
    'p_total_sin_iva': ['TOTAL INVESTMENT SIN IVA', 'TOTAL INVESTMENT (SIN IVA)'],
    'p_ventas': ['VENTAS', 'TOTAL VENTAS', 'GDV'],
    'p_tir': ['TIR', 'IRR'],
}
# Cabeceras de la tabla de viviendas de cada pack
CAB_VIVIENDAS = {
    'portal': ['PORTAL'], 'planta': ['PLANTA'], 'num': ['N', 'NO', 'NUM', 'NUMERO', 'VIVIENDA', 'PUERTA'],
    'm2': ['M2', 'M2 CONSTRUIDOS', 'M2 CONSTRUIDOS CON COMUNES', 'SUPERFICIE'], 'tipo': ['TIPOLOGIA', 'HAB', 'DORMITORIOS'],
    'orient': ['ORIENTACION'], 'precio': ['PRECIO MERCADO', 'PRECIO DE MERCADO', 'PVP MERCADO'],
}
HOJAS = {
    'detalle': r'detalle\s*(de\s*)?inversi',
    'tir': r'^\s*(tir|irr)\b',
    'cashflow': r'cash\s*-?\s*flow|flujo',
    'pack': r'pack',
}
MERCADO = re.compile(r'MERCADO|MARKET')
MINIMO = re.compile(r'MINIMO|MINIMUM')


def norm(v):
    s = unicodedata.normalize('NFKD', str(v)).encode('ascii', 'ignore').decode()
    s = re.sub(r'[\s:]+', ' ', s.upper()).strip()
    return s


def num(v):
    return isinstance(v, (int, float)) and not isinstance(v, bool)


class Hoja:
    def __init__(self, ws):
        self.ws = ws
        self.celdas = [[c.value for c in fila] for fila in ws.iter_rows()]
        self.col_mercado = self._columnas(MERCADO)
        self.col_minimo = self._columnas(MINIMO)

    def _columnas(self, rx):
        cols = set()
        for fila in self.celdas:
            for j, v in enumerate(fila):
                if isinstance(v, str) and rx.search(norm(v)):
                    cols.add(j)
        return cols

    def buscar(self, etiquetas, exacta=True):
        """Celdas (fila, col) cuyo texto normalizado coincide con alguna etiqueta."""
        ets = [norm(e) for e in etiquetas]
        out = []
        for i, fila in enumerate(self.celdas):
            for j, v in enumerate(fila):
                if isinstance(v, str):
                    n = norm(v)
                    if (n in ets) if exacta else any(n.startswith(e) for e in ets):
                        out.append((i, j))
        return out

    def valor(self, etiquetas):
        """Primer número a la derecha de la etiqueta, en la columna de precio de mercado si la hoja distingue escenarios."""
        for i, j in self.buscar(etiquetas):
            fila = self.celdas[i]
            cands = [(k, fila[k]) for k in range(j + 1, len(fila)) if num(fila[k])]
            if self.col_minimo:
                cands = [(k, v) for k, v in cands if k not in self.col_minimo]
            if self.col_mercado:
                pref = [(k, v) for k, v in cands if k in self.col_mercado]
                cands = pref or cands
            if cands:
                return cands[0][1], f'{self.ws.title}!{celda(i, cands[0][0])} («{fila[j]}»)'
        return None, None


def celda(i, j):
    col = ''
    j += 1
    while j:
        j, r = divmod(j - 1, 26)
        col = chr(65 + r) + col
    return f'{col}{i + 1}'


def hojas(wb, clave):
    return [wb[n] for n in wb.sheetnames if re.search(HOJAS[clave], n, re.I)]


def trimestres(fechas, valores):
    """Agrupa meses por trimestre natural; si el último trimestre está incompleto, sus meses se suman al anterior."""
    grupos = []
    for f, v in zip(fechas, valores):
        q = f'Q{(f.month - 1) // 3 + 1} {f.year}'
        if grupos and grupos[-1][0] == q:
            grupos[-1][1].append(v)
        else:
            grupos.append([q, [v]])
    if len(grupos) > 1 and len(grupos[-1][1]) < 3:
        q, vs = grupos.pop()
        grupos[-1][1].extend(vs)
    return [q for q, _ in grupos], [round(sum(vs), 2) for _, vs in grupos]


def tir_mensual(flujos):
    """TIR anual equivalente desde flujos mensuales (bisección)."""
    def vpn(r):
        return sum(f / (1 + r) ** k for k, f in enumerate(flujos))
    lo, hi = -0.99, 1.0
    if vpn(lo) * vpn(hi) > 0:
        return None
    for _ in range(200):
        mid = (lo + hi) / 2
        if vpn(lo) * vpn(mid) <= 0:
            hi = mid
        else:
            lo = mid
    return (1 + (lo + hi) / 2) ** 12 - 1


def fila_meses(h):
    """Fila con al menos 6 fechas consecutivas (cabecera de meses del cashflow)."""
    for i, fila in enumerate(h.celdas):
        idx = [j for j, v in enumerate(fila) if isinstance(v, (dt.date, dt.datetime))]
        if len(idx) >= 6:
            return i, idx
    return None, None


def xirr(flujos, fechas):
    """TIR anual con fechas reales (misma convención que XIRR de Excel: días/365). Bisección."""
    d0 = fechas[0]

    def vpn(r):
        return sum(f / (1 + r) ** ((d - d0).days / 365) for f, d in zip(flujos, fechas))
    lo, hi = -0.99, 10.0
    if vpn(lo) * vpn(hi) > 0:
        return None
    for _ in range(300):
        mid = (lo + hi) / 2
        if vpn(lo) * vpn(mid) <= 0:
            hi = mid
        else:
            lo = mid
    return (lo + hi) / 2


def trimestres_naturales(fechas, valores):
    """Agrupa por trimestre natural sin fusionar el último (los trimestres tal y como los define el Excel)."""
    grupos = []
    for f, v in zip(fechas, valores):
        q = f'Q{(f.month - 1) // 3 + 1} {f.year}'
        if grupos and grupos[-1][0] == q:
            grupos[-1][1].append(v)
        else:
            grupos.append([q, [v]])
    return [q for q, _ in grupos], [round(sum(vs), 2) for _, vs in grupos]


# ------------------------------------------------------------------ modelo «VP por unidades»
# Modelos en los que «Detalle inversión» tiene una columna por vivienda (fila PACKS con el pack de cada una,
# fila UNIDADES con V1…Vn y una columna TOTAL), una hoja «Pack» con el proyecto completo y una hoja TIR con dos
# bloques de escenario: el de venta a cliente final a precio de mercado es el único que se lee.
def _fila(h, etiqueta, desde=0):
    for i in range(desde, len(h.celdas)):
        for j, v in enumerate(h.celdas[i][:3]):
            if isinstance(v, str) and norm(v) == norm(etiqueta):
                return i, j
    return None, None


def es_modelo_vp(wb):
    for ws in hojas(wb, 'detalle'):
        h = Hoja(ws)
        i, _ = _fila(h, 'PACKS')
        u, _ = _fila(h, 'UNIDADES')
        if i is not None and u is not None and any(isinstance(v, str) and norm(v) == 'TOTAL' for v in h.celdas[u]):
            return True
    return False


def extraer_vp(wb):
    res, fuentes, falta, avisos = {}, {}, [], []
    det = Hoja(hojas(wb, 'detalle')[0])
    T = det.ws.title
    rp, _ = _fila(det, 'PACKS')
    ru, _ = _fila(det, 'UNIDADES')
    fila_u = det.celdas[ru]
    cols = [j for j, v in enumerate(fila_u) if isinstance(v, str) and re.fullmatch(r'V\d+', norm(v))]
    ctot = next(j for j, v in enumerate(fila_u) if isinstance(v, str) and norm(v) == 'TOTAL')
    # Filas por etiqueta, solo en el primer bloque (inversión) hasta el siguiente «PACKS»
    rp2, _ = _fila(det, 'PACKS', rp + 1)
    rango = (rp, rp2 if rp2 is not None else len(det.celdas))

    def f(etiqueta, bloque=rango):
        for i in range(*bloque):
            v = det.celdas[i][0]
            if isinstance(v, str) and norm(v) == norm(etiqueta):
                return i
        return None
    r_m2, r_dist, r_planta, r_inv = f('M2'), f('DISTRIBUCION'), f('NUMERO DE PLANTA'), f('TOTAL INVERSION')
    r_pm = f('PRECIO MERCADO', (rango[1], len(det.celdas)))
    r_gar, r_tra = f('NUMERO DE GARAJES'), f('NUMERO DE TRASTEROS')
    for n, r in (('M2', r_m2), ('DISTRIBUCIÓN', r_dist), ('TOTAL INVERSIÓN', r_inv), ('PRECIO MERCADO', r_pm)):
        if r is None:
            falta.append(f'{T}: fila «{n}»')
    if falta:
        return res, fuentes, falta, avisos
    res['coste_iva'] = det.celdas[r_inv][ctot]
    fuentes['coste_iva'] = f'{T}!{celda(r_inv, ctot)} («TOTAL INVERSIÓN», columna TOTAL, IVA incluido)'
    res['ventas'] = det.celdas[r_pm][ctot]
    fuentes['ventas'] = f'{T}!{celda(r_pm, ctot)} («PRECIO MERCADO», columna TOTAL)'

    # Hoja Pack (proyecto completo): coste sin IVA, ventas y TIR de mercado (verificación cruzada)
    pk = next((Hoja(wb[n]) for n in wb.sheetnames if norm(n) == 'PACK'), None)
    if pk is None:
        falta.append('hoja «Pack»')
        return res, fuentes, falta, avisos
    cab = pk.celdas[0]
    c_sin = next((j for j, v in enumerate(cab) if isinstance(v, str) and 'PACK COMPLETO' in norm(v)), None)
    c_con = next((j for j, v in enumerate(cab) if isinstance(v, str) and 'TOTAL CON IVA' in norm(v)), None)
    i_ti, _ = _fila(pk, 'TOTAL INVERSION')
    i_vm, _ = _fila(pk, 'TOTAL VENTAS VIVIENDAS PRECIO DE MERCADO')
    if None in (c_sin, c_con, i_ti, i_vm):
        falta.append('Pack: «TOTAL INVERSIÓN» / «TOTAL VENTAS VIVIENDAS PRECIO DE MERCADO» / cabeceras')
        return res, fuentes, falta, avisos
    res['coste_sin_iva'] = pk.celdas[i_ti][c_sin]
    fuentes['coste_sin_iva'] = f'Pack!{celda(i_ti, c_sin)} («TOTAL INVERSIÓN», «Pack Completo», sin IVA)'
    for nombre, v, ref, src in (('coste con IVA', pk.celdas[i_ti][c_con], res['coste_iva'], celda(i_ti, c_con)),
                                ('ventas de mercado', pk.celdas[i_vm][c_sin], res['ventas'], celda(i_vm, c_sin))):
        if abs(v - ref) > 0.5:
            falta.append(f'Pack!{src} ({nombre} {v}) ≠ «Detalle inversión» ({ref})')
    tir = None
    for i, fila in enumerate(pk.celdas):
        for j, v in enumerate(fila):
            if isinstance(v, str) and norm(v) == 'TIR MERCADO':
                tir = next((x for x in fila[j + 1:] if num(x)), None)
                fuentes['tir'] = f'Pack!{celda(i, fila.index(tir, j + 1))} («TIR MERCADO»)' if tir is not None else None
    if tir is None:
        falta.append('Pack: «TIR MERCADO»')
    res['tir'] = tir
    for et, clave in (('GLA', 'gla'), ('BENEFICIO MERCADO', 'beneficio')):
        for i, fila in enumerate(pk.celdas):
            for j, v in enumerate(fila):
                if isinstance(v, str) and norm(v) == et:
                    res['_' + clave] = next((x for x in fila[j + 1:] if num(x)), None)
                    fuentes['_' + clave] = f'Pack, fila {i + 1} («{v}»)'

    # Hoja TIR: bloque de venta a cliente final a precio de mercado
    th = next((Hoja(ws) for ws in hojas(wb, 'tir')), None)
    if th is None:
        falta.append('hoja TIR')
        return res, fuentes, falta, avisos
    ib, _ = _fila(th, 'Total Ventas Finalistas')
    if ib is None:
        falta.append('TIR: bloque de mercado («Total Ventas Finalistas»)')
        return res, fuentes, falta, avisos
    filas = {}
    for et in ('Cash outflows', 'Cash inflows', 'Total liquidacion IVA', 'Total Cashflow', 'TIR Anualizada', 'Unidades'):
        i, j = _fila(th, et, ib if et != 'Unidades' else max(0, ib - 40))
        filas[et] = (i, j)
        if i is None:
            falta.append(f'TIR (bloque de mercado): fila «{et}»')
    if falta:
        return res, fuentes, falta, avisos
    i_tot = filas['Total Cashflow'][0]
    i_f = next(i for i in range(i_tot, ib, -1) if sum(isinstance(v, (dt.date, dt.datetime)) for v in th.celdas[i]) >= 6)
    idx = [j for j, v in enumerate(th.celdas[i_f]) if isinstance(v, (dt.date, dt.datetime))]
    serie = lambda et: [th.celdas[filas[et][0]][j] if num(th.celdas[filas[et][0]][j]) else 0 for j in idx]
    fechas = [th.celdas[i_f][j] for j in idx]
    out, inn, iva, tot = serie('Cash outflows'), serie('Cash inflows'), serie('Total liquidacion IVA'), serie('Total Cashflow')
    for k in range(len(idx)):
        if abs(out[k] + inn[k] + iva[k] - tot[k]) > 0.01:
            falta.append(f'TIR!{celda(i_tot, idx[k])}: Total Cashflow ≠ outflows + inflows + IVA')
    ult = max(k for k in range(len(idx)) if abs(tot[k]) > 0.005 or abs(out[k]) > 0.005 or abs(inn[k]) > 0.005)
    fechas, out, inn, iva, tot = fechas[:ult + 1], out[:ult + 1], inn[:ult + 1], iva[:ult + 1], tot[:ult + 1]
    for et in ('Cash outflows', 'Cash inflows', 'Total liquidacion IVA', 'Total Cashflow'):
        fuentes['cf ' + et] = f'{th.ws.title}!fila {filas[et][0] + 1}, {celda(i_f, idx[0])}:{celda(i_f, idx[ult])} (M1–M{ult + 1}, bloque de mercado)'
    i_t, j_t = filas['TIR Anualizada']
    res['_tir_hoja'] = next((x for x in th.celdas[i_t][j_t + 1:] if num(x)), None)
    fuentes['_tir_hoja'] = f'{th.ws.title}, fila {i_t + 1} («TIR Anualizada», bloque de mercado)'
    i_un, j_un = filas['Unidades']
    res['_unidades'] = next((x for x in th.celdas[i_un][j_un + 1:] if num(x)), None)
    # Cronograma: costes = salidas + liquidación de IVA; cobros = entradas (mismo criterio que Montserrat)
    costes_m = [o + v for o, v in zip(out, iva)]
    q, c = trimestres_naturales(fechas, costes_m)
    _, s = trimestres_naturales(fechas, inn)
    res['cronograma'] = {'trimestres': q, 'costes': c, 'cobros': s}
    res['_flujos_mensuales'] = tot
    res['_fechas'] = fechas
    res['aportas'] = -sum(out)
    res['recibes'] = sum(inn) + sum(iva)
    res['ganancia_neta'] = sum(tot)
    fuentes['aportas'] = 'suma de «Cash outflows» (bloque de mercado)'
    fuentes['recibes'] = 'suma de «Cash inflows» + «Total liquidación IVA» (bloque de mercado)'
    fuentes['ganancia_neta'] = 'suma de «Total Cashflow» (bloque de mercado)'
    k_arras = next((k for k, v in enumerate(inn) if v > 0), None)
    arras = inn[k_arras] if k_arras is not None and k_arras < ult else 0
    res['_desglose'] = {'aportacion_inicial': round(-out[0]), 'obra': round(-sum(out[1:])),
                        'arras': round(arras), 'venta': round(res['recibes'] - arras)}

    # Viviendas y packs (columnas de «Detalle inversión»)
    unidades = []
    for j in cols:
        dist = norm(det.celdas[r_dist][j] or '')
        if dist.startswith('ESTUDIO'):
            tipo = 0
        else:
            m = re.match(r'(\d+)H', dist)
            tipo = int(m.group(1)) if m else None
        if tipo is None:
            falta.append(f'{T}!{celda(r_dist, j)}: distribución «{det.celdas[r_dist][j]}» sin tipología reconocible')
            continue
        pl = det.celdas[r_planta][j] if r_planta is not None else None
        planta = 'Baja' if num(pl) and pl == 0 else (f'{int(pl)}ª' if num(pl) else B.NA)
        unidades.append({'pack': norm(det.celdas[rp][j] or ''), 'id': str(det.celdas[ru][j]).strip(), 'm2': det.celdas[r_m2][j],
                         'tipo': tipo, 'planta': planta, 'c': det.celdas[r_inv][j], 'v': det.celdas[r_pm][j],
                         'garajes': det.celdas[r_gar][j] if r_gar is not None else None,
                         'trasteros': det.celdas[r_tra][j] if r_tra is not None else None})
    fuentes['viviendas'] = (f'{T}: filas {rp + 1} (PACKS), {r_dist + 1} (DISTRIBUCIÓN), {ru + 1} (UNIDADES), {r_m2 + 1} (M2), '
                            f'{r_inv + 1} (TOTAL INVERSIÓN), {r_pm + 1} (PRECIO MERCADO), columnas {celda(0, cols[0])[:-1]}–{celda(0, cols[-1])[:-1]}')
    res['_m2_unidades'] = sum(u['m2'] for u in unidades)
    res['_garajes'] = sum(u['garajes'] or 0 for u in unidades)
    res['_trasteros'] = sum(u['trasteros'] or 0 for u in unidades)
    if res.get('_gla') is not None and abs(res['_gla'] - res['_m2_unidades']) > 0.5:
        avisos.append(f'm²: la suma de las viviendas ({B.g(round(res["_m2_unidades"]))} m², {T}!{celda(r_m2, ctot)}) '
                      f'≠ GLA de la hoja Pack ({B.g(round(res["_gla"]))} m²). Se usa la suma de viviendas; no se resuelve aquí.')
    nombres = []
    for u in unidades:
        if u['pack'] not in nombres:
            nombres.append(u['pack'])
    packs = []
    ci, cs, V = res['coste_iva'], res['coste_sin_iva'], res['ventas']
    for n, nom in enumerate(nombres, 1):
        us = [u for u in unidades if u['pack'] == nom]
        c, v = sum(u['c'] for u in us), sum(u['v'] for u in us)
        wc, wv = c / ci, v / V
        cs_p = cs * wc                      # coste sin IVA del pack, repartido por su peso de coste
        b = v - cs_p
        flujos = [k * wc + i * wv for k, i in zip(costes_m, inn)]
        t = xirr(flujos, fechas)
        mixd = {}
        for u in us:
            mixd[str(u['tipo'])] = mixd.get(str(u['tipo']), 0) + 1
        packs.append({'id': n, 'nombre_excel': nom.title(), 'n': len(us), 'mix': dict(sorted(mixd.items())),
                      'm2': round(sum(u['m2'] for u in us)), 'c': round(c), 'v': round(v), 'b': round(b),
                      'r': round(b / cs_p, 4), 't': round(t, 4) if t is not None else None,
                      'pesos': [round(wc, 8), round(wv, 8)],
                      'u': [[B.NA, u['planta'], u['id'], round(float(u['m2']), 1), u['tipo'], B.NA, int(round(u['v']))] for u in us]})
        fuentes[f'pack{n}'] = f'«{nom}» = viviendas {", ".join(u["id"] for u in us)}; b y yield con coste sin IVA repartido por peso de coste; TIR = XIRR del cashflow de mercado × pesos'
    res['_packs_vp'] = packs
    return res, fuentes, falta, avisos


def extraer(path):
    from openpyxl import load_workbook
    wb = load_workbook(path, data_only=True, read_only=False)
    if es_modelo_vp(wb):
        res, fuentes, falta, avisos = extraer_vp(wb)
        res['_avisos'] = avisos
        return res, fuentes, falta
    res, fuentes, falta = {}, {}, []

    def tomar(clave, hs, destino=None):
        for ws in hs:
            v, src = Hoja(ws).valor(ETIQUETAS[clave])
            if v is not None:
                (destino if destino is not None else res)[clave] = v
                fuentes[clave] = src
                return v
        falta.append(clave)
        return None

    det = hojas(wb, 'detalle')
    if not det:
        falta.append('hoja «Detalle inversión»')
    for k in ('coste_iva', 'coste_sin_iva', 'ventas'):
        tomar(k, det)
    tomar('tir', hojas(wb, 'tir') + det)
    for k in ('aportas', 'recibes', 'ganancia_neta'):
        tomar(k, list(wb.worksheets))

    # Cashflow mensual
    cf = hojas(wb, 'cashflow')
    res['cronograma'] = None
    for ws in cf:
        h = Hoja(ws)
        i, idx = fila_meses(h)
        if i is None:
            continue
        fechas = [h.celdas[i][j] for j in idx]
        filas = {}
        for k in ('cf_costes', 'cf_cobros'):
            pos = h.buscar(ETIQUETAS[k])
            if pos:
                r = pos[0][0]
                filas[k] = [h.celdas[r][j] if num(h.celdas[r][j]) else 0 for j in idx]
                fuentes[k] = f'{ws.title}!fila {r + 1} («{h.celdas[r][pos[0][1]]}»)'
        if len(filas) == 2:
            costes = [-abs(x) if x > 0 and all(y >= 0 for y in filas['cf_costes']) else x for x in filas['cf_costes']]
            q, c = trimestres(fechas, costes)
            _, s = trimestres(fechas, filas['cf_cobros'])
            res['cronograma'] = {'trimestres': q, 'costes': c, 'cobros': s}
            res['_flujos_mensuales'] = [a + b for a, b in zip(costes, filas['cf_cobros'])]
            break
    if not res['cronograma']:
        falta.append('cashflow mensual (fila de meses + filas de costes y cobros)')

    # Packs
    packs = []
    for ws in hojas(wb, 'pack'):
        m = re.search(r'(\d+)', ws.title)
        if not m:
            continue
        h = Hoja(ws)
        p = {'id': int(m.group(1))}
        for k in ('p_gla', 'p_total', 'p_total_sin_iva', 'p_ventas', 'p_tir'):
            v, src = h.valor(ETIQUETAS[k])
            p[k] = v
            if v is None:
                falta.append(f'{ws.title}: {ETIQUETAS[k][0]}')
            else:
                fuentes[f'pack{p["id"]}.{k}'] = src
        p['u'] = viviendas(h, falta)
        packs.append(p)
    res['_packs'] = sorted(packs, key=lambda p: p['id'])
    return res, fuentes, falta


def viviendas(h, falta):
    """Tabla de viviendas del pack, localizada por cabeceras."""
    cab = {k: [norm(x) for x in v] for k, v in CAB_VIVIENDAS.items()}
    for i, fila in enumerate(h.celdas):
        cols = {}
        for j, v in enumerate(fila):
            if isinstance(v, str):
                n = norm(v)
                for k, vs in cab.items():
                    if n in vs and k not in cols:
                        cols[k] = j
        if {'m2', 'tipo', 'precio'} <= set(cols):
            out = []
            for fila2 in h.celdas[i + 1:]:
                if not num(fila2[cols['m2']]) or not num(fila2[cols['precio']]):
                    if out:
                        break
                    continue
                tipo = fila2[cols['tipo']]
                tn = 0 if isinstance(tipo, str) and 'ESTUDIO' in norm(tipo) else int(re.sub(r'\D', '', str(tipo)) or 0)
                g = lambda k: fila2[cols[k]] if k in cols else ''
                out.append([str(g('portal')), str(g('planta')), str(g('num')), round(float(fila2[cols['m2']]), 1), tn,
                            str(g('orient')), int(round(fila2[cols['precio']]))])
            return out
    falta.append(f'{h.ws.title}: tabla de viviendas (cabeceras m², tipología y precio de mercado)')
    return []


def componer(res, falta):
    """Pasa lo extraído al formato del contrato de project.json y ejecuta las validaciones de §4."""
    errores = []
    out = {}
    if all(res.get(k) is not None for k in ('coste_iva', 'coste_sin_iva', 'ventas', 'tir')):
        tir = res['tir'] / 100 if res['tir'] > 1 else res['tir']
        out['proyecto'] = {'coste_iva': round(res['coste_iva']), 'coste_sin_iva': round(res['coste_sin_iva']),
                           'ventas': round(res['ventas']), 'tir': round(tir, 4)}
    if all(res.get(k) is not None for k in ('aportas', 'recibes', 'ganancia_neta')):
        out['plan_pagos'] = {k: round(res[k]) for k in ('aportas', 'recibes', 'ganancia_neta')}
    if res.get('cronograma'):
        out['cronograma'] = res['cronograma']
    pr = out.get('proyecto')
    if res.get('_desglose') and out.get('plan_pagos'):
        out['plan_pagos']['desglose'] = res['_desglose']
    packs = list(res.get('_packs_vp') or [])
    for p in packs:
        if not p['u'] or p.get('t') is None:
            errores.append(f'Pack {p["id"]}: le faltan viviendas o no se puede calcular su TIR')
    if res.get('_packs_vp') is not None:
        nu = sum(p['n'] for p in packs)
        if res.get('_unidades') is not None and nu != res['_unidades']:
            errores.append(f'La suma de viviendas de los packs ({nu}) no coincide con las unidades del modelo ({res["_unidades"]:g})')
        if res.get('_beneficio') is not None and out.get('plan_pagos'):
            dif = res['ganancia_neta'] - res['_beneficio']
            if abs(dif) > 1:
                errores.append(f'Ganancia neta del cashflow ({res["ganancia_neta"]:.2f} €) ≠ «BENEFICIO MERCADO» ({res["_beneficio"]:.2f} €): {dif:+.2f} €')
        if res.get('_tir_hoja') is not None and pr and abs(res['_tir_hoja'] - pr['tir']) > 0.00005:
            errores.append(f'TIR de la hoja Pack ({pr["tir"]}) ≠ «TIR Anualizada» del bloque de mercado ({res["_tir_hoja"]})')
        for p in packs:
            if pr:
                cs_p = pr['coste_sin_iva'] * p['pesos'][0]
                if abs(p['v'] - cs_p - p['b']) > 1:
                    errores.append(f'Pack {p["id"]}: beneficio incoherente')
    for p in res.get('_packs', []):
        us = p['u']
        if not us or p['p_total'] is None or p['p_ventas'] is None or p['p_gla'] is None:
            errores.append(f'Pack {p["id"]}: le faltan viviendas, m² o precio (no se puede publicar)')
            continue
        cs = p['p_total_sin_iva']
        mixd = {}
        for u in us:
            mixd[str(u[4])] = mixd.get(str(u[4]), 0) + 1
        q = {'id': p['id'], 'n': len(us), 'mix': mixd, 'm2': round(p['p_gla']), 'c': round(p['p_total']), 'v': round(p['p_ventas'])}
        if cs is not None:
            q['b'] = round(p['p_ventas'] - cs)
            q['r'] = round((p['p_ventas'] - cs) / cs, 4)
        else:
            errores.append(f'Pack {p["id"]}: falta TOTAL INVESTMENT sin IVA (para beneficio y yield)')
        if p['p_tir'] is not None:
            q['t'] = round(p['p_tir'] / 100 if p['p_tir'] > 1 else p['p_tir'], 4)
        if pr:
            q['pesos'] = [round(p['p_total'] / pr['coste_iva'], 8), round(p['p_ventas'] / pr['ventas'], 8)]
        q['u'] = us
        packs.append(q)
    if packs:
        out['packs'] = packs
        if pr:
            tol = len(packs)
            for k, ref, n in (('c', pr['coste_iva'], 'inversiones'), ('v', pr['ventas'], 'ventas')):
                dif = sum(x[k] for x in packs) - ref
                if abs(dif) > tol:
                    errores.append(f'La suma de {n} de los packs ({B.g(sum(x[k] for x in packs))} €) no coincide con el proyecto ({B.g(ref)} €): diferencia {dif:+} €')
    if res.get('_flujos_mensuales') and pr:
        t = xirr(res['_flujos_mensuales'], res['_fechas']) if res.get('_fechas') else tir_mensual(res['_flujos_mensuales'])
        res['_tir_calculada'] = t
        if t is None or abs(t - pr['tir']) > 0.001:
            tir_hoja = pr['tir']
            calc = 'no calculable' if t is None else ('%.2f %%' % (t * 100)).replace('.', ',')
            dif_pp = '—' if t is None else ('%+.2f pp' % ((t - tir_hoja) * 100)).replace('.', ',')
            errores.append(f'TIR calculada desde el cashflow ({calc}) ≠ hoja TIR ({B.coma(tir_hoja * 100, 2)} %): '
                           f'diferencia {dif_pp} (tolerancia ±0,10 pp)')
    if res.get('cronograma') and out.get('plan_pagos'):
        tot = sum(res['cronograma']['costes']) + sum(res['cronograma']['cobros'])
        dif = tot - out['plan_pagos']['ganancia_neta']
        if abs(dif) > 1:
            errores.append(f'Subtotal del cronograma ({tot:,.2f} €) ≠ ganancia neta ({out["plan_pagos"]["ganancia_neta"]} €): diferencia {dif:+.2f} €')
    return out, errores


def main():
    ap = argparse.ArgumentParser(description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter)
    ap.add_argument('proyecto')
    ap.add_argument('--excel', required=True)
    ap.add_argument('--escribir', action='store_true')
    ap.add_argument('--json', help='guarda aquí lo extraído (fuera del repo)')
    a = ap.parse_args()
    carpeta = B.localizar(a.proyecto)
    pj = os.path.join(carpeta, 'project.json')
    with open(pj, encoding='utf-8') as f:
        data = json.load(f)
    res, fuentes, falta = extraer(a.excel)
    out, errores = componer(res, falta)
    nviv_json = len(B.viviendas(B.Datos(data, data.get('modo') or 'unico')))
    if out.get('packs') and nviv_json and sum(p['n'] for p in out['packs']) != nviv_json:
        errores.append(f'La suma de viviendas de los packs ({sum(p["n"] for p in out["packs"])}) no coincide con el total del proyecto ({nviv_json})')

    print(f'Excel: {a.excel}\nEncontrado:')
    for k, v in sorted(fuentes.items()):
        print(f'  - {k}: {v}')
    if res.get('_tir_calculada') is not None:
        print(f'  - TIR recalculada desde el cashflow: {res["_tir_calculada"]:.6f} (hoja: {out.get("proyecto", {}).get("tir")})')
    for x in res.get('_avisos', []):
        print(f'AVISO: {x}')
    if falta:
        print('No encontrado (revisa la etiqueta en el Excel o añádela a ETIQUETAS):')
        for x in falta:
            print(f'  - {x}')
    for k in ('proyecto', 'plan_pagos', 'cronograma'):
        if k in out and any((data.get(k) or {}).get(c) != v for c, v in out[k].items()):
            print(f'Cambia {k}: {json.dumps(data.get(k), ensure_ascii=False)} → {json.dumps(out[k], ensure_ascii=False)}')
    if a.json:
        with open(a.json, 'w', encoding='utf-8') as f:
            json.dump(out, f, ensure_ascii=False, indent=1)
    if errores:
        print('\nPARA: hay descuadres; no se escribe nada ni se publica:')
        for e in errores:
            print(f'  ✗ {e}')
        sys.exit(2)
    if a.escribir:
        if falta:
            print('\nNo se escribe: faltan datos (ver arriba). Pídelos antes de publicar.')
            sys.exit(2)
        for k, v in out.items():
            if isinstance(v, dict) and isinstance(data.get(k), dict):
                data[k].update(v)  # conserva claves adicionales (p. ej. plan_pagos.desglose)
            else:
                data[k] = v
        B.escribir_json(pj, data)
        print(f'\nproject.json actualizado ({", ".join(out)}). Ejecuta build.py y qa.py.')
    else:
        print('\nValidaciones correctas. Usa --escribir para actualizar project.json.')


if __name__ == '__main__':
    main()
