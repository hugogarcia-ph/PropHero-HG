## ⚠️ NORMA PRINCIPAL: PLANTILLA ÚNICA Y HOMOGÉNEA

El objetivo de este proyecto es la precomercialización de los proyectos de Prophero
(Avenida Ciudad, Montserrat, Pego y los que se añadan) mediante páginas web
publicadas en Vercel, todas basadas en UNA ÚNICA PLANTILLA.

1. Plantilla maestra: la plantilla oficial se indicará mediante una URL que Hugo
   proporcionará. Hasta que esté disponible, NO inventes una estructura propia:
   pregunta antes de crear cualquier página.

2. Homogeneidad obligatoria: todas las páginas de todos los proyectos deben tener
   EXACTAMENTE las mismas secciones, en el mismo orden, con los mismos nombres,
   el mismo diseño, la misma tipografía, los mismos colores y los mismos componentes.
   Lo ÚNICO que cambia entre proyectos es el contenido: datos de la zona, cifras,
   textos descriptivos, fotos y planos.

3. Prohibido personalizar la estructura por proyecto: nunca añadas, quites, reordenes
   ni renombres una sección solo en un proyecto. Si hace falta un cambio de estructura,
   se aplica a la plantilla y, por tanto, a TODOS los proyectos a la vez, y solo si
   Hugo lo aprueba.

4. Datos que falten: si a un proyecto le falta información para una sección,
   la sección se mantiene igualmente, con el texto "Pendiente", y me avisas de qué
   falta y en qué carpeta de Drive debería estar. Nunca elimines la sección.

5. Implementación técnica: un único código de plantilla compartido por todos los
   proyectos y un archivo de datos por proyecto (por ejemplo, datos de Avenida Ciudad,
   Montserrat y Pego por separado). Así es imposible que las páginas diverjan.

6. Publicación en Vercel: cada página se despliega en Vercel tras hacer commit y push.
   Las páginas deben ser públicas: justo después del primer despliegue, desactiva
   Vercel Authentication y la protección por contraseña del proyecto. Confirma que
   ha quedado desactivado y dame el enlace de producción limpio
   (<proyecto>-<equipo>.vercel.app), sin el código aleatorio del despliegue.

7. Antes de publicar cualquier cambio, comprueba que todas las páginas siguen
   teniendo las mismas secciones que la plantilla y avísame si alguna no cuadra.

# Normas del proyecto

- Después de cada cambio en los archivos del proyecto, haz commit con un mensaje descriptivo en español y haz push a GitHub (rama main).
- Este proyecto es exclusivamente de Prophero. No menciones, consultes ni uses información de otros proyectos, sesiones o cuentas de Claude Code.
- Esta carpeta es una excepción: haz commit y push a GitHub después de cada cambio sin pedir confirmación.

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

- Antes de trabajar en el deck de un proyecto, consulta siempre su carpeta de Drive con el conector de Google Drive para usar la información más reciente.
- Solo lectura: no modifiques, muevas ni borres nada en Drive.
- No copies archivos de Drive a este repositorio ni los subas a GitHub.
