# Normas del proyecto

- Este proyecto es exclusivamente de Prophero. No menciones, consultes ni uses información de otros proyectos, sesiones o cuentas de Claude Code.
- Después de cada cambio en los archivos del proyecto, haz commit con un mensaje descriptivo en español y haz push a GitHub (rama main). Esta carpeta es una excepción: commit y push sin pedir confirmación.

## Vercel

- Cuenta de Vercel: la de Prophero (`hugogarcia-3760`, hugo.garcia@prophero.com), equipo `prop-hero1`, a través del conector de Vercel.
- No uses la CLI `vercel` instalada en el Mac: está iniciada con otra cuenta.

## Fuentes de información (Google Drive)

- Avenida Ciudad: https://drive.google.com/drive/folders/1nWbRtla_37qnwjbbgNBzckmIf41aPc1_
- Montserrat: https://drive.google.com/drive/folders/1uMykXOgeNcBv575oSWbG_OCfJbGauFrv
- Pego: https://drive.google.com/drive/folders/1Co_ubLF8XKKBhd6qNYTucwe4tToP4tB8

Todas siguen la misma estructura:

- `00_ESTUDIO PREVIO`
- `01_DOCUMENTACIÓN` (con `01.4_FINANCIAL` para los números)
- `02_PROYECTO`
- `03_TRÁMITES Y LICENCIAS`
- `04_SEGUIMIENTO DE OBRA`
- `05_DECK` (donde están los decks comerciales existentes)

Normas:

- Antes de trabajar en la landing o el deck de un proyecto, consulta siempre su carpeta de Drive con el conector de Google Drive para usar la información más reciente.
- Solo lectura: no modifiques, muevas ni borres nada en Drive.
- No copies archivos de Drive a este repositorio ni los subas a GitHub. El Excel del modelo se lee desde Drive y se procesa fuera del repo; nunca se versiona (`modelo.xlsx` está en `.gitignore`). Los renders solo entran como WebP optimizados para publicar.

---

# Plantilla de landing de inversión PropHero

## 0. Tu misión

Eres el responsable técnico de la **plantilla única de landings de precomercialización de PropHero**. Cada promoción (proyecto inmobiliario) tiene una landing pública para inversores con el mismo diseño, la misma estructura y las mismas reglas. La referencia viva es:

**https://ausiasmarchmontserrat-prop-hero1.vercel.app** (proyecto Montserrat · Ausias March, 168 viviendas, 27 packs)

Tareas iniciales, en este orden:

1. Crea el repositorio con la estructura del apartado 2.
2. Descarga los ficheros publicados en la URL de referencia como punto de partida de la plantilla. Los ficheros son `/index.html`, `/app2.js`, `/ui2.js`, `/zona.html`, `/dossier.html`, `/assets/mark.webp` y `/assets/render-*.webp`. Sepáralos en plantilla (estructura, estilos y lógica) y datos del proyecto (cifras, textos de zona, renders).
3. Convierte la página en una plantilla parametrizada: **todo lo que cambia entre proyectos debe salir de `projects/<slug>/project.json`**, nunca escrito a mano en el HTML.
4. Crea el script de build que genera `dist/<slug>/` a partir de la plantilla y el JSON del proyecto.
5. Migra Montserrat como primer proyecto y comprueba que el resultado es idéntico a la URL de referencia.
6. Guarda este documento como `CLAUDE.md` en la raíz para que rija todas las sesiones futuras.

---

## 1. Reglas fundamentales (no negociables)

1. **Idioma:** todo en español de España: textos, comentarios de cara al usuario y mensajes.
2. **Solo precio de mercado.** Nunca se muestra el «precio mínimo», ni el escenario de precio mínimo, ni horquillas mínimo–mercado. Las palabras «recompra» y «garantía» no aparecen nunca.
3. **Rangos solo en la tarjeta principal (hero).** Yield, beneficio y TIR del proyecto completo se muestran como rangos conservadores **fijados por dirección** en `project.json → rangos`. No se calculan ni se inventan. Ejemplo de Montserrat: yield `18–22 %`, TIR `16–20 %`, beneficio `2,3–2,8 M€`.
4. **Todo lo demás sale exacto del Excel del proyecto**: plan de pagos, cronograma, packs, comparador, ficha de viviendas y precios por vivienda. No se aplican descuentos, hipótesis ni escenarios propios. Si falta un dato, se pregunta; no se rellena. Mientras tanto, la sección se mantiene con el texto «Pendiente» (nunca se elimina) y se avisa a Hugo de qué falta y en qué carpeta de Drive debería estar.
5. **Cifras provisionales.** Mientras el modelo no esté cerrado, `project.json → borrador: true` muestra la franja amarilla «Borrador · cifras provisionales…». Se quita solo cuando dirección lo confirme.
6. **Un proyecto = un único enlace.** Cada promoción tiene un solo proyecto de Vercel y una sola URL canónica, `https://<slug>-prop-hero1.vercel.app`. Nunca se crean proyectos duplicados. Si existe uno antiguo, se sustituye su contenido por un `vercel.json` que redirige todas las rutas a la URL canónica.
7. **Vercel siempre público.** Tras cada despliegue: `update_project` con `ssoProtection: null` y `passwordProtection: null`. Después se confirma que ha quedado desactivado y se entrega la URL de producción limpia (sin código aleatorio).
8. **Enfoque proyecto completo.** Los CTA invitan al proyecto entero, nunca a «tu pack». Los packs existen, pero en segundo plano, dentro de un desplegable.
9. **Modo de comercialización: siempre se pregunta.** Cada proyecto se publica en uno de dos modos, definido en `project.json → modo`:
   - `"paquetizado"`: el producto se divide en packs. Se usan la sección de packs, el comparador, la ficha de viviendas y el selector de pack en el cronograma.
   - `"unico"`: un solo producto, el edificio completo, pensado para fondos que compran el total. **No aparece ninguna referencia a packs.**
   Cuando el usuario diga «plantilla» o pida un proyecto nuevo, lo primero es preguntar: **«¿Paquetizado o producto único?»**. Nunca se elige por defecto.
10. **Toda modificación se hace en la plantilla** (`template/`) y se propaga a todos los proyectos con el build. Está prohibido editar a mano un `dist/` o un proyecto suelto. Todas las landings tienen exactamente las mismas secciones, en el mismo orden, con los mismos nombres, diseño, tipografía, colores y componentes; lo único que cambia es el contenido de `project.json` y sus assets (y las secciones que dependen del `modo`).

---

## 2. Estructura del repositorio

```
/
├── CLAUDE.md                  ← este documento
├── CHANGELOG.md               ← cada cambio de plantilla, con fecha y motivo
├── template/
│   ├── index.html             ← landing (con marcadores {{...}})
│   ├── app.js                 ← lógica: hero, packs, comparador, ficha, plan de pagos
│   ├── ui.js                  ← cronograma, pie PropHero, galería de renders
│   ├── zona.html              ← información ampliada de la zona
│   ├── dossier.html           ← PDF descargable (A4) generado en el navegador
│   └── assets/mark.webp       ← favicon/logo PropHero
├── projects/
│   └── montserrat-ausias-march/
│       ├── project.json       ← TODOS los datos del proyecto
│       ├── modelo.xlsx        ← Excel fuente (no se versiona: se lee desde Drive)
│       └── assets/            ← renders .webp del proyecto
├── scripts/
│   ├── extract_excel.py       ← Excel → project.json (cifras)
│   ├── build.py               ← template + project.json → dist/<slug>/
│   ├── build_all.py           ← reconstruye todos los proyectos
│   ├── qa.py                  ← comprobaciones automáticas (apartado 9)
│   └── deploy.md              ← pasos de despliegue en Vercel
└── dist/<slug>/               ← salida publicable (no se edita a mano)
```

---

## 3. `project.json` (contrato de datos)

```json
{
  "slug": "ausiasmarchmontserrat",
  "nombre": "Montserrat",
  "subtitulo": "Ausias March · 168 viviendas",
  "lede": "Finalización de un edificio residencial en Montserrat (Ribera Alta, València): 168 viviendas compactas con garaje, disponibles para el proyecto completo o por packs.",
  "facts": { "ubicacion": "...", "tipologias": "119 estudios · 31 de 1 dorm. · 18 de 2 dorm.", "garajes": 168, "trasteros": 89, "financiacion": "Sin financiación" },
  "modo": "unico",            // "unico" | "paquetizado"
  "borrador": true,
  "rangos": { "yield": "18–22 %", "tir": "16–20 %", "beneficio": "2,3–2,8 M€" },
  "listas_para_alquilar": { "valor": "4T 2027", "nota": "Estimado, a fin de obra" },
  "whatsapp": "34650522730",
  "proyecto": { "coste_iva": 14457101, "coste_sin_iva": 12673602, "ventas": 15540663, "tir": 0.1939 },
  "plan_pagos": { "aportas": 14457101, "recibes": 17324161, "ganancia_neta": 2867061 },
  "cronograma": { "trimestres": ["Q1 2027","Q2 2027","Q3 2027","Q4 2027","Q1 2028"], "costes": [...], "cobros": [...] },
  "packs": [ { "id": 1, "n": 7, "mix": {"0":7}, "m2": 305, "c": 529110, "v": 553929, "b": 90721, "r": 0.1959, "t": 0.1666, "pesos": [wc, ws],
               "u": [["A","Baja","2",38.8,0,"Interior patio",58100], ...] } ],
  "zona": { "titular": "...", "texto": "...", "distancias": [...], "kpis": [4 cifras], "bloques": [industria, infraestructuras, empleo], "fuentes": "..." },
  "renders": [ { "archivo": "render-estudio.webp", "titulo": "Estudio", "texto": "..." } ]
}
```

- Cifras en euros sin redondear. El redondeo se hace al pintar: M€ con 1 decimal y k€ sin decimales, con formato español (punto de miles y coma decimal).
- `u` de cada vivienda: portal, planta, nº, m² construidos con comunes, tipología (0 estudio, 1 o 2 hab.), orientación y **precio de mercado**.
- Claves adicionales (las usa `scripts/build.py`):
  - `nombre_completo` (p. ej. «Montserrat · Ausias March»: títulos, WhatsApp, pies) y `whatsapp_mensaje` (texto prefijado, sobre *el proyecto*).
  - `borrador_texto` (texto de la franja amarilla), `pagina.descripcion` (meta description) y `pie` (línea del pie PropHero).
  - `facts.ubicacion/tipologias/garajes/trasteros/financiacion`, `plan_pagos.desglose` (informativo) y `packs[].pesos` = `[peso de coste, peso de venta]` del cronograma por pack.
  - `viviendas` (opcional): lista `u` del edificio cuando no hay packs; si falta, se usan las de `packs[].u`.
  - `edificio`: `texto`, `etiqueta_viviendas` y `nota` de la sección «El edificio» (modo `unico`).
  - `producto`: `titulo` y `texto` de la galería de renders.
  - `dossier`: `subtitulo`, `descripcion`, `proyecto_titulo`, `proyecto_texto`, `zona_titulo`, `zona_textos` (2), `zona_cifras` (6), `distancias_titulo`, `eje` (`nombre`, `km`), `fuentes`, `producto_texto` y `pie`.
  - `zona_ampliada`: `intro`, `pie_fuentes` y `secciones` (`id`, `fondo`, `etiqueta`, `titulo`, `bloques`). Tipos de bloque: `p`, `grupo`, `dos_columnas`, `tabla`, `kpis`, `cita`, `barras`, `rentabilidad`, `tamanos`, `relojes` y `html` (SVG de mapa o gráfico).
- Cualquier texto puede ser `{"unico": "…", "paquetizado": "…"}` para cambiar de modo sin tocar la plantilla. Los textos admiten HTML en línea (`&nbsp;`, `<b>`).

---

## 4. Extracción del Excel (`extract_excel.py`)

El Excel del modelo es la única fuente de las cifras. Para cada proyecto nuevo:

1. Localiza las hojas de pack, detalle de inversión, cashflow mensual y TIR. Las ventas totales salen de **«Detalle inversión»**.
2. Extrae siempre el **escenario de precio de mercado**. El de precio mínimo se ignora.
3. Bloque de pack, referencia de Montserrat: YEAR BUILT, GLA, PURCHASE PRICE, ADQUISICIÓN, HARD COST, SOFT COST (con alarmas incluidas), HARD&SOFT COST, FEES&FINANCIACIÓN y TOTAL INVESTMENT. Las posiciones pueden cambiar entre modelos, así que **verifica cada celda por su etiqueta, no por su posición**.
4. Validaciones obligatorias antes de seguir:
   - La suma de las inversiones de los packs coincide con el coste total con IVA.
   - La suma de las ventas de los packs coincide con las ventas de mercado.
   - La suma de las viviendas coincide con el total del proyecto.
   - La TIR del proyecto calculada desde el cashflow coincide con la hoja TIR (±0,1 pp).
   - Cada pack tiene viviendas, m² y precio.
5. Si algo no cuadra, **para y avisa** con la diferencia exacta. No se publica con descuadres.
6. Cronograma: agrupa el cashflow mensual por trimestre (los meses sueltos al final se suman al último trimestre). Los packs se reparten con sus pesos de coste y de venta.

---

## 5. Estructura de la landing (orden fijo)

1. **Franja de borrador**, solo si `borrador: true`.
2. **Cabecera fija:** logo PropHero, botón «Descargar PDF» (abre `/dossier.html?dl=1`) y botón «Solicitar información» (WhatsApp con mensaje sobre *el proyecto*).
3. **Hero, en dos columnas:**
   - Izquierda: eyebrow «Proyecto de inversión · Value Partner», nombre, subtítulo, lede, facts y botones «Ver plan de pagos» y «Por qué [municipio]».
   - Derecha: tarjeta navy con la etiqueta «Rangos estimados · precomercialización» y tres cifras grandes. El yield estimado es la más destacada; las otras dos son total investment (≈, con IVA y sin IVA) y beneficio estimado.
   - Debajo, en pequeño: TIR estimada (rango) y «Listas para alquilar». **No se muestran las ventas ni el plazo en meses.**
4. **Por qué [municipio]:**
   - Titular y un párrafo, chips de distancias y **4 KPIs** de mercado.
   - **3 bloques: Industria · Infraestructuras · Empleo y servicios**, con foco en tejido productivo, no en estadísticas.
   - Enlace a `zona.html` y nota de fuentes.
5. **Plan de pagos:** tres tarjetas (Aportas / Recibes / Ganancia neta) con cifras del Excel y el **cronograma de pagos** (apartado 6), con selector «Proyecto completo / Pack N».
6. **Producto según el modo** (`project.json → modo`):
   - **Modo `unico`** (por ejemplo, Montserrat para un fondo): sección **«El edificio · Un único producto: el edificio completo»**.
     - 4 cifras: viviendas, superficie construida, trasteros y fecha de listas para alquilar.
     - Tabla de composición por tipología: viviendas, superficie media, precio medio de mercado y €/m², con fila de total del edificio. Todo calculado desde las viviendas del Excel.
     - Sin packs, sin comparador y sin selector de pack en el cronograma, que muestra siempre «Proyecto completo».
     - En los textos: «en una única operación: el edificio completo».
   - **Modo `paquetizado`:** sección de packs como se describe a continuación.

   **Packs (solo modo `paquetizado`)**, título «El proyecto, también por packs». La tabla va **cerrada en un `<details>`** con el texto «Ver los 27 packs individualizados». Dentro:
   - Filtros (Todos / Estudios / 1 y 2 dorm.) y orden (nº, TIR, yield, beneficio, inversión).
   - Tabla: pack, viviendas, m², inversión, ventas, beneficio, yield y TIR, con fila de total.
   - Casillas para comparar hasta 3 packs: barra flotante y modal lado a lado con ★ en el mejor valor.
   - Al pulsar una fila, modal con las viviendas del pack.
7. **El producto (renders), siempre al final:** galería con una imagen grande y dos apiladas, lightbox al pulsar y nota «Imágenes orientativas (renders)…». Si los renders no son del edificio, se etiquetan como imágenes tipo o se quitan.
8. **Cierre:** bloque navy «¿Te enviamos el proyecto completo?» con botón a WhatsApp y aviso legal de precomercialización.
9. **Pie PropHero**, idéntico al de prophero.com/es:
   - Logo y descripción oficial, con el botón «Reservar una llamada».
   - Columnas PropHero (Acerca de, Cómo funciona, Datos e IA, Valencia Real Estate Summit) y Recursos (Prensa y blogs, Recomendar a un amigo, FAQ, Canal de denuncias).
   - Insignias negras de App Store y Google Play (estilo oficial «Download on the / GET IT ON»), redes sociales (YouTube, Facebook, Instagram) y «© año PropHero».

---

## 6. Sistema de diseño

- **Tipografía:** Inter (Google Fonts), números tabulares en tablas.
- **Colores de marca:** navy `#061031`, navy oscuro `#03081F`, azul `#0D35F0`, azul claro `#7D96FB`, texto `#4B5771`, gris `#8B93A6`, fondo suave `#F4F6FB`, líneas `#DCE2EF`. **No se usa rosa en elementos de marca.**
- **Cronograma de pagos**, estética fija calcada de la referencia aprobada:
  - Fondo `#111214`, título en mayúsculas con tracking y leyenda Negativo / Positivo / Subtotal.
  - **Negativo** rojo, degradado `#EF6F86 → #5A2B36`, cifra `#EF6F86`, barra hacia abajo.
  - **Positivo** verde, degradado `#6EDC98 → #2D5C45` (claro abajo), cifra `#6EDC98`.
  - **Subtotal** degradado horizontal `#6CC3E3 → #3554FF`, cifra y etiqueta `#5B76FF` / `#4F6BFF`.
  - Eje gris `#34373E`, etiquetas de trimestre `#A1A6B2` y cifras en euros con punto de miles.
- **Packs:** cada pack tiene su color pastel en el punto y la etiqueta de TIR (paleta de 27 colores de `app.js`). En el PDF los packs van sin puntos de color.
- **Responsive:** sin scroll horizontal de 320 a 1280 px. Tablas y cronograma con scroll propio en móvil.
- **Accesibilidad:** foco visible, `aria-label` en botones de icono y modales `<dialog>` que se cierran con Esc o al pulsar fuera.

---

## 7. PDF descargable (`dossier.html`)

- Página A4 vertical (210×297 mm) que se descarga como PDF directamente, sin diálogo de impresión. Se genera en el navegador con **html2canvas 1.4.1 + jsPDF 2.5.1** desde cdnjs, a escala 2,2, en JPEG 0,92, una imagen por página.
- `?dl=1` lanza la descarga automática. Si falla, se muestra un enlace «pulsa aquí» con el blob y, como último recurso, «Imprimir → Guardar como PDF».
- Páginas:
  1. **Portada** navy: plano técnico en líneas blancas difuminado arriba y abajo, título grande y franja de cifras principales con **los mismos rangos del hero**.
  2. **Proyecto y zona.**
  3. **Producto (renders).**
  4. **Según el modo:**
     - `paquetizado`: página de packs, tabla con columnas de ancho fijo (TIR y su barra en columnas separadas) y cifras del Excel.
     - `unico`: página «El producto», con la tabla de composición del edificio y los renders.
  5. **Plan de pagos:** cronograma con la misma estética que la web y cierre de contacto.
- Lecciones técnicas obligatorias para que funcione en Safari y Chrome:
  - **Nada de imágenes SVG** (ni `data:image/svg+xml` ni `<use>`). Los logos y el plano se dibujan en `<canvas>` (Path2D) y se insertan como PNG.
  - No usar `inset:` en CSS (html2canvas no lo entiende): usar `top/left/right/bottom`.
  - Fondo blanco explícito en `.page` y `backgroundColor:'#ffffff'`.
  - Números proporcionales fuera de tablas para evitar huecos raros.
  - Verificar con un script que ningún elemento sobrepasa el margen de 16 mm y que ninguna celda se recorta.

---

## 8. Despliegue en Vercel (`scripts/deploy.md`)

1. `python scripts/build.py <slug>` y luego `python scripts/qa.py <slug>`. Si el QA falla, no se despliega.
2. Despliega `dist/<slug>/` en el proyecto `<slug>` del equipo `prop-hero1`:
   - Primero como **preview** para revisión interna.
   - A **producción** solo con el OK del usuario.
3. Inmediatamente después de cada despliegue: `update_project` con `ssoProtection: null` y `passwordProtection: null`. Confirma que está desactivado y entrega `https://<slug>-prop-hero1.vercel.app`.
4. Si existían otros proyectos para la misma promoción, despliega en ellos solo un `vercel.json` con redirección de todas las rutas a la URL canónica, y repite el paso 3.
5. Las imágenes van en WebP (lado mayor 960 px, calidad 45). Comprueba que el hash del fichero publicado coincide con el local.

---

## 9. QA automático (`scripts/qa.py`) antes de cada publicación

- [ ] 0 errores de consola (Playwright) en `index.html`, `zona.html` y `dossier.html`.
- [ ] Sin scroll horizontal a 320, 390, 768 y 1280 px.
- [ ] El texto renderizado **no contiene** «mínimo», «recompra» ni «garantía».
- [ ] Los rangos del hero y de la portada del PDF coinciden con `project.json → rangos`.
- [ ] Totales de packs, plan de pagos y cronograma = Excel (tolerancia de 1 €).
- [ ] Modo `paquetizado`: el desplegable de packs abre, el comparador funciona con 2 y 3 packs y el modal de viviendas abre.
- [ ] Modo `unico`: el texto renderizado de la web y del PDF **no contiene «pack»** y la tabla de composición suma el total de viviendas y m².
- [ ] `dossier.html?dl=1` descarga un PDF de 4–5 páginas A4 sin elementos fuera de márgenes.
- [ ] La galería de renders carga y el lightbox abre y cierra.
- [ ] Todos los enlaces del pie responden.
- [ ] Todas las landings tienen las mismas secciones que la plantilla (según su `modo`); si alguna no cuadra, se avisa a Hugo.

---

## 10. Cómo se gestionan los cambios

- **Cambio de diseño o estructura** (afecta a todos; solo con aprobación de Hugo):
  1. Edita `template/`.
  2. Anótalo en `CHANGELOG.md` con fecha, qué cambia y quién lo pidió.
  3. `build_all.py`, luego `qa.py` en todos los proyectos.
  4. Despliegue en preview, y en producción con el OK.
- **Cambio de datos de un proyecto** (cifras, rangos, fecha, textos de zona, renders): solo `projects/<slug>/project.json` o sus assets, después build y QA de ese proyecto.
- **Proyecto nuevo:**
  0. Pregunta primero: **«¿Paquetizado o producto único?»**, y guárdalo en `modo`.
  1. Copia la carpeta de un proyecto existente.
  2. Pon el nuevo Excel y ejecuta `extract_excel.py`.
  3. Pide al usuario los rangos del hero, la fecha de listas para alquilar, los renders y el WhatsApp.
  4. Redacta la zona con 4 KPIs y los 3 bloques, citando fuentes.
  5. Build, QA y preview.
- Si una petición contradice una regla del apartado 1, avisa y pide confirmación antes de cambiar la regla. Si se confirma, actualiza este `CLAUDE.md`.

---

## 11. Historial de decisiones (contexto)

- La dirección (David Gras) pidió:
  - Formato ejecutivo; arriba total investment, yield y beneficio, sin ventas; TIR abajo.
  - Plazo hasta «listas para alquilar».
  - Packs en desplegable, porque se envía a fondos grandes.
  - Más foco en industria, servicios e infraestructuras en la zona.
  - Fotos al final y plan de pagos antes de los packs.
  - Fuera el gancho «¿Hablamos de tu pack?».
  - **Rangos conservadores en el hero para no comprometer una cifra exacta.**
- Montserrat pasa a **modo `unico`**: se ofrece entero a un fondo y paquetizar no tiene sentido. El modo se elige por proyecto y se puede cambiar en cualquier momento sin tocar la plantilla.
- Precio mínimo eliminado como norma fundamental. Solo se muestra el precio de mercado.
- Estética del cronograma: rojo/verde/azul sobre fondo oscuro, según captura aprobada.
- El PDF anterior basado en «imprimir página» se descartó. Ahora es un dossier A4 maquetado que se descarga directamente.
