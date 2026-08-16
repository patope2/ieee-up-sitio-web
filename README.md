# IEEE UP — Sitio web (v2, carpeta autónoma)

Copia completa y ordenada de `04-SITIO-WEB`, verificada para que funcione **sola**:
no depende de ninguna otra carpeta del repo. Es una duplicación 1:1 — ningún HTML,
CSS o imagen fue modificado visualmente. Ver [`VERIFICACION.md`](VERIFICACION.md)
para el detalle de qué se comprobó.

## Estructura

```
07-SITIO-WEB-v2/
├── dist/                  ← EL SITIO YA CONSTRUIDO. Esto es lo que se publica.
│   ├── index.html, eventos.html, ...   (14 páginas)
│   ├── css/  fonts/  img/  js/
│
├── data/                  ← Contenido editable (fuente de verdad)
│   ├── eventos.yml           35+ fichas de eventos
│   ├── fotos.yml              mapa evento → fotos ya optimizadas
│   ├── organigrama.yml       directiva y grupos de afinidad
│   └── sitio.yml              navegación, textos legales, redes
│
├── templates/             ← Plantillas Jinja2 (el diseño; no tocar sin querer
│   │                         cambiar el layout)
│   ├── base.html, pages/*.html, partials/*.html
│
├── static/                 ← Assets fuente (build.py los copia a dist/ tal cual)
│   ├── css/  fonts/  img/  js/
│
├── tools/
│   ├── agregar_fotos_evento.py   ← usar este para fotos de eventos nuevos
│   ├── verificar.py               chequea marca IEEE + links rotos + accesibilidad
│   ├── build_media.py             (legado, ver nota abajo)
│   └── parse_eventos.py           (legado, ver nota abajo)
│
└── build.py                ← genera dist/ desde templates/ + data/ + static/
```

**Regla simple:** `dist/` se ve, `data/` se edita, `build.py` conecta ambos.
Nunca edites los archivos dentro de `dist/` a mano — se pisan en el próximo build.

## Ver el sitio

- **Rápido:** doble clic en `dist/index.html` (funciona sin servidor, todas las
  rutas son relativas).
- **Con servidor local** (recomendado si vas a probar cambios):
  ```
  python build.py --servir
  ```
  y abre `http://localhost:8000`.

## Cómo agregar un evento nuevo

1. **Si tiene fotos propias**, procésalas primero:
   ```
   python tools/agregar_fotos_evento.py --slug mi-evento-2026 --origen "C:\ruta\a\las\fotos"
   ```
   Esto genera `static/img/eventos/mi-evento-2026/01-card.jpg` / `01-full.jpg` (y
   siguientes) con el mismo tamaño y recorte que usa el resto del sitio, y agrega
   la entrada al mapa `data/fotos.yml`. Usa `--dry-run` primero si querés ver qué
   va a hacer sin escribir nada, y `--alt "texto"` para un texto alternativo
   propio (por defecto usa el título del evento).

2. **Agrega la ficha en `data/eventos.yml`** (es una lista; agrega un bloque
   nuevo, en cualquier posición — el sitio los ordena solo por fecha). Plantilla
   mínima para un Taller/Visita/Competencia normal:

   ```yaml
   - slug: mi-evento-2026
     titulo: Nombre del evento
     tipo: Taller              # Taller | Visita | Competencia/Concurso | Ecosistema IEEE
     etiqueta: ''               # texto corto opcional para el badge
     organiza: IEEE UP          # IEEE UP | IEEE Perú | IEEE Región 9 | Terceros
     organiza_texto: ''
     escala: null
     grupo: null                 # WIE | SIGHT | CIS | null
     fecha_texto: '15 de marzo de 2026'
     fecha_orden: '2026-03-15'    # AAAA-MM-DD, se usa para ordenar
     anio: 2026
     fecha_precision: dia         # dia | mes | anio | desconocida
     modalidad: Presencial        # Presencial | Virtual | Híbrido | No especificada
     ubicacion_texto: ''
     estado: Pasado                # Pasado | Próximo
     descripcion: Descripción real del evento, sin inventar datos.
     ponentes: []                  # o [{nombre: '...', rol: '...'}]
     premio: ''
     resultado: ''
     logro_obtenido: ''
     alcance: ''
     rol: ''
     participantes: ''
     talleres_incluidos: ''
     becas_aliados: ''
     auspiciadores: ''
     nota_interna: ''
     enlaces: []
     shortcodes: []
     fotos: []                     # dejalo así: build.py lo llena solo desde fotos.yml
     en_proyectos: false
     en_logros: false
   ```

   Campos obligatorios de verdad: `slug` (único, en minúsculas y con guiones),
   `titulo`, `tipo`, `fecha_orden`, `fecha_precision`, `estado`, `descripcion`.
   El resto puede quedar vacío (`''`, `null` o `[]`) — el generador usa
   `StrictUndefined`, así que **no borres ningún campo de la lista**, aunque
   quede vacío, o el build falla con un error claro señalando cuál falta.

   **Caso especial — evento de Ecosistema IEEE marcado como `Próximo`:** además
   de lo anterior necesita `fecha_dias`, `fecha_mes_anio`, `lugar_nombre`,
   `lugar_ciudad_pais` (los usa el widget "Nos verás en" de la portada) y
   opcionalmente `enlaces_externos: [{texto: '...', url: '...'}]`. Las fichas
   `lacci-2026` e `ieee-rising-stars-lac-2026`, al principio de
   `data/eventos.yml`, son el ejemplo real a copiar.

3. **Reconstruye el sitio:**
   ```
   python build.py
   ```
4. **Verifica que no rompiste nada** (opcional pero recomendado):
   ```
   python tools/verificar.py
   ```
   Debe terminar en "SIN PROBLEMAS". Si un evento nuevo quedó sin fotos, es
   normal — la tarjeta se muestra sin imagen, no es un error.

## Cómo publicar una oportunidad (becas, delegaciones, voluntariado)

Las oportunidades viven en **`data/oportunidades.yml`**, separadas de los
eventos. Es la sección que las bases del Student Website Contest piden de forma
explícita (becas, *travel grants*, voluntariado, programas de liderazgo).

Para publicar una nueva, agrega un bloque:

```yaml
- slug: delegacion-ejemplo-2027
  titulo: Delegación IEEE UP a ...
  categoria: Delegación internacional     # texto libre, sale como badge
  estado: Abierta                          # Abierta | Permanente | Cerrada
  resumen: Qué es y a qué da acceso.
  financiamiento: Viaje financiado por ...  # opcional
  seleccion: Convocatoria abierta + entrevista.   # opcional
  dirigido_a: Miembros de IEEE UP           # opcional
  cierre_texto: Cierra el 30 de abril.      # opcional
  url_postulacion: https://forms.gle/...    # opcional; sin esto sale "Pedir las bases"
  url_info: https://...                     # opcional; botón "Sitio oficial"
  evento_slug: mi-evento-2027               # opcional; enlaza a la ficha del evento
  pendiente: Fechas por confirmar.          # opcional; sale en cursiva como dato pendiente
  actividades:                              # opcional; lista "A qué da acceso"
    - Programas de liderazgo
  incluye:                                  # opcional; lista con ✓
    - Hospedaje y alimentación
  no_incluye:                               # opcional; lista con ✕
    - Pasajes aéreos
```

**Nunca publiques enlaces privados aquí.** Los invites de grupo de WhatsApp y
las salas de Google Meet no van al sitio: son de acceso restringido (o de un
solo uso) y publicarlos abre la puerta a cualquiera. Si una convocatoria se
coordina por un grupo privado, deja el campo `pendiente` pidiendo que escriban
por Contacto, como está hecho en `voluntariado-lacci-2026`.

Reglas prácticas:
- **`estado: Abierta`** la sube al tope de la página *y* muestra un aviso en la
  portada. Cuando cierre, cambia a `Cerrada` — **no la borres**: el historial es
  la prueba de que la convocatoria es recurrente y real.
- Solo `slug`, `titulo`, `categoria`, `estado` y `resumen` son obligatorios; los
  demás campos, si faltan, simplemente no se muestran.
- `evento_slug` enlaza con la ficha en `data/eventos.yml` en vez de duplicar el
  contenido.

Después: `python build.py`.

## Agregar fotos a un evento que ya existe

Mismo comando del paso 1, con el `--slug` del evento existente. Si querés
reemplazar sus fotos actuales en vez de sumarlas, agregá `--limpiar`. Después
corre `python build.py` de nuevo.

## Sobre `tools/build_media.py` y `tools/parse_eventos.py`

Son las herramientas que se usaron **una sola vez** para armar el catálogo
original desde el scraping de Instagram y el markdown de investigación. Leen
carpetas que están fuera de `07-SITIO-WEB-v2` (`03-INSTAGRAM-CONTENT/`,
`02-ARQUITECTURA-WEB-IEEE-UP/`) y por eso **no son necesarias para el uso
normal** de esta carpeta — `tools/agregar_fotos_evento.py` cubre el flujo de
"tengo fotos nuevas en mi PC" sin esa dependencia externa. Se dejan como
referencia/legado por si algún día se vuelve a hacer una importación masiva.

## Antes de publicar en producción

1. ~~Correo de contacto vacío~~ — resuelto: `r.ieee.upacifico@gmail.com`.
2. **Falta banner de cookies propio.** El sitio no trackea nada todavía, pero
   si se agrega analytics/pixel más adelante hace falta un consentimiento de
   cookies propio (el de Osano del template original es de la cuenta
   corporativa de IEEE y no se puede reutilizar).

Fuera de esta carpeta, también sigue pendiente (ver `PLAN-DE-CONSTRUCCION.md`
§8): registrar el sitio ante IEEE (Website and Social Media Site Registration
Form) y revocar la sesión de Instagram expuesta en
`03-INSTAGRAM-CONTENT/scripts/script_0.py`.

### Datos que faltan para cerrar el contenido

Marcados en el sitio como "dato pendiente" (en cursiva), para no inventar nada:

- **SBRM 2026 (México)** — ⚠️ la postulación **cierra el 2 de agosto de 2026**.
  Cuando cierre, cambiar `estado: Abierta` → `Cerrada` en
  `data/oportunidades.yml` y quitar el botón "Postula" del evento
  `sbrm-2026-guadalajara` en `data/eventos.yml`. Un formulario vencido que sigue
  publicado cuenta como contenido desactualizado.
- **LACCI 2026** — canal y plazo por los que un estudiante postula.
- **SBRM 2025** — confirmar qué cubrió exactamente la Rama/universidad en esa
  edición (hoy está publicado en términos generales, con nota de pendiente).
- **STEM HER FUTURE (WIE)** — falta la fecha exacta (hoy se muestra solo "2026")
  y las fotos, que están en el Instagram de WIE (se descarga aparte).
- **Primera asamblea de WIE UP (25 de abril de 2026)** — sin publicar: es una
  actividad interna y ninguno de los 4 tipos de evento (Taller / Visita /
  Competencia / Ecosistema IEEE) le corresponde. Ver nota abajo.

### Nota: eventos internos no tienen categoría

Los 4 tipos actuales cubren actividad de cara al público. Una asamblea o
reunión interna de la Rama no encaja en ninguno: ponerla como "Taller" sería
falso y como "Ecosistema IEEE" la mezclaría con las delegaciones
internacionales, que es la página de mayor peso. Si se quiere publicar este
tipo de actividad hace falta una categoría nueva ("Vida de la Rama"), lo que
implica tocar `build.py` (tupla de tipos y `BADGE`), `data/sitio.yml` (submenú
de Eventos) y una página `eventos-*.html` nueva.
- **Rising Stars 2026** — discrepancia de fecha de cierre entre la convocatoria
  por WhatsApp (24 de julio) y la ficha original (27/07). Se publicó el 24;
  confirmar cuál es la correcta.
- **Formulario de contacto / inscripción** — sigue como placeholder en
  `templates/pages/contacto.html` y `unete.html`. Al publicar el Google Form
  real, reemplazar el bloque por su `<iframe>`.
- **SBRM 2025** — fecha exacta del encuentro (ya venía anotado en
  `nota_interna` dentro de `data/eventos.yml`).
