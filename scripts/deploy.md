# Despliegue en Vercel

Pasos para publicar una landing (CLAUDE.md §8). La cuenta es la de Prophero (`hugogarcia-3760`), equipo `prop-hero1`, siempre a través del **conector de Vercel**. No uses la CLI `vercel` del Mac: está iniciada con otra cuenta.

## 1. Build y QA

```bash
python3 scripts/build.py <carpeta-o-slug>     # p. ej. montserrat-ausias-march → dist/ausiasmarchmontserrat/
python3 scripts/qa.py <carpeta-o-slug>        # headless; si falla, NO se despliega
```

- `build.py` avisa de los datos que faltan; esas secciones salen con «Pendiente». No se publica a producción con «Pendiente» sin el OK de Hugo.
- `qa.py` necesita Playwright para Python (`pip install --user playwright`) y usa Chrome del sistema en modo sin cabeza. Nunca abre ventanas.
- Para cambios de plantilla: `python3 scripts/build_all.py` y `qa.py` en todos los proyectos.

## 2. Despliegue

1. Despliega el contenido de `dist/<slug>/` (tal cual, es estático: no hay build en Vercel) en el proyecto `<slug>` del equipo `prop-hero1`.
2. Primero como **preview**, para revisión interna.
3. A **producción** solo con el OK de Hugo.
4. Un proyecto = un único enlace: `https://<slug>-prop-hero1.vercel.app`. Nunca se crean proyectos duplicados.

## 3. Después de cada despliegue

1. `update_project` con `ssoProtection: null` y `passwordProtection: null`.
2. Confirma con `get_project` que ambas protecciones han quedado desactivadas.
3. Entrega la URL de producción limpia (sin código aleatorio): `https://<slug>-prop-hero1.vercel.app`.

## 4. Proyectos antiguos de la misma promoción

Despliega en ellos solo un `vercel.json` que redirija todas las rutas a la URL canónica y repite el paso 3:

```json
{ "redirects": [{ "source": "/(.*)", "destination": "https://<slug>-prop-hero1.vercel.app/$1", "permanent": true }] }
```

## 5. Imágenes

- Renders en WebP, lado mayor 960 px, calidad 45, en `projects/<carpeta>/assets/`.
- Tras desplegar, comprueba que el hash de cada fichero publicado coincide con el local:

```bash
shasum -a 256 dist/<slug>/assets/*.webp
curl -s https://<slug>-prop-hero1.vercel.app/assets/<fichero>.webp | shasum -a 256
```
