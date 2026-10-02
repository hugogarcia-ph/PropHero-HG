# Changelog de la plantilla

Cada cambio de plantilla (`template/`), con fecha, qué cambia, motivo y quién lo pidió.

## 2026-10-02 · Plantilla única y migración de Montserrat

- **Qué:** se crea la plantilla parametrizada (`template/`), el contrato de datos (`projects/<carpeta>/project.json`) y los scripts `build.py`, `build_all.py`, `qa.py` y `extract_excel.py`, siguiendo CLAUDE.md §0–§9.
- **Punto de partida:** los ficheros publicados en https://ausiasmarchmontserrat-prop-hero1.vercel.app (`index.html`, `app2.js` → `app.js`, `ui2.js` → `ui.js`, `zona.html`, `dossier.html`, `assets/`).
- **Montserrat · Ausias March** migrado como primer proyecto (modo `unico`). Verificado contra la referencia en local y sin cabeza: texto renderizado idéntico y capturas idénticas píxel a píxel a 1280 y 390 px en `index.html`, `zona.html` y `dossier.html`.
- **Modo único:** ya no se emite el DOM oculto de packs que arrastraba la referencia (tabla, comparador, modales y selector del cronograma); el texto de web y PDF no contiene «pack».
- **Modo paquetizado (nuevo diseño):** sección «El proyecto, también por packs» con la tabla en un desplegable, filtros, orden, comparador de hasta 3 packs con ★ y modal de viviendas; selector de pack en el cronograma; en el PDF, página de packs (5 páginas en total). Diseño sobre el sistema de §6; la lógica parte de la de `app2.js`.
- **Cifras derivadas** calculadas en el build o en el navegador (composición por tipología, m², €/m², yield, subtotales, «X € por cada 100 €», meses), con el redondeo de JavaScript. La superficie total se trunca al m² (8.347 m² en Montserrat).
- **Corrección respecto a la referencia (PDF, modo único, página 3):** la línea del pie tachaba la nota «Imágenes orientativas…» (solape de ≈2 mm, incumple §7). El render principal pasa de 82 a 78 mm de alto. Es la única diferencia visual con la referencia.
- **Pedido por:** Hugo García.
