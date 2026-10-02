#!/usr/bin/env python3
"""Reconstruye todos los proyectos de projects/ en dist/ (CLAUDE.md §10).

Uso:
    python3 scripts/build_all.py [--estricto]

Después, ejecuta scripts/qa.py en cada proyecto antes de desplegar.
"""
import argparse
import os
import sys

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
import build as B  # noqa: E402


def main():
    ap = argparse.ArgumentParser(description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter)
    ap.add_argument('--estricto', action='store_true')
    a = ap.parse_args()
    carpetas = sorted(n for n in os.listdir(B.PROJECTS) if os.path.isfile(os.path.join(B.PROJECTS, n, 'project.json')))
    if not carpetas:
        raise SystemExit('No hay proyectos en projects/.')
    con_avisos = []
    for n in carpetas:
        _, faltan, avisos = B.build(n, estricto=False)
        if faltan or avisos:
            con_avisos.append(n)
        print()
    print(f'{len(carpetas)} proyecto(s) generados. ' + (f'Con avisos: {", ".join(con_avisos)}.' if con_avisos else 'Sin avisos.'))
    print('Siguiente paso: python3 scripts/qa.py <proyecto> en cada uno.')
    if a.estricto and con_avisos:
        sys.exit(1)


if __name__ == '__main__':
    main()
