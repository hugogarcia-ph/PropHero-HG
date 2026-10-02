# PropHero-HG

Landings de precomercialización de PropHero: **una plantilla única** y un `project.json` por promoción. Las normas completas están en `CLAUDE.md`.

- `template/` — la plantilla (`index.html`, `app.js`, `ui.js`, `zona.html`, `dossier.html`, `assets/mark.webp`). Todo cambio de diseño se hace aquí.
- `projects/<carpeta>/` — datos de cada promoción: `project.json` y `assets/` (renders WebP). Hoy: `montserrat-ausias-march` (modo `unico`).
- `scripts/` — `build.py` (plantilla + JSON → `dist/<slug>/`), `build_all.py`, `qa.py` (comprobaciones automáticas, sin cabeza), `extract_excel.py` (Excel del modelo → cifras) y `deploy.md`.
- `dist/<slug>/` — salida estática publicable en Vercel. No se edita a mano.
- `CHANGELOG.md` — historial de cambios de la plantilla.
- `Avenida Ciudad/`, `Montserrat/`, `Pego/` — material de trabajo de cada proyecto (decks e informes).

```bash
python3 scripts/build.py montserrat-ausias-march
python3 scripts/qa.py montserrat-ausias-march
```
