# IEEE UP — Plan de construcción del sitio

Documento de traspaso. La base ya está hecha y funcionando; lo que queda son las
13 páginas restantes, que se arman con las piezas que ya existen.

---

## 1. Contexto

Se construye el sitio propio de la Rama (Ruta B) **sobre el template oficial de
IEEE** ya descargado en `01-SITIO-BASE-DESCARGADO/` (IEEE Sites Theme v1.2.3).
El sitio debe cumplir `IEEE-OFICIAL-INFORMATION.MD` y respetar la arquitectura
definida en `02-ARQUITECTURA-WEB-IEEE-UP/`, donde **Eventos es la sección
protagonista**.

**Stack: Python 3.11 + Jinja2 + Pillow → HTML estático.** No es una preferencia
estética: en esta máquina **no hay Node/npm instalado** (verificado), y el proxy
Zscaler ya rompió pip y curl antes. Python, Jinja2, Pillow y PyYAML ya están
instalados y funcionando. La salida es HTML plano, desplegable en GitHub Pages,
Netlify o el hosting legacy de IEEE, y legible por cualquier webmaster futuro sin
build tooling.

---

## 2. Lo que YA está hecho y verificado

| Pieza | Estado |
|---|---|
| `tools/parse_eventos.py` | Convierte las 35 fichas de `05-raw-eventos.md` → `data/eventos.yml`. Verificado: 17 Talleres, 3 Visitas, 8 Competencias, 7 Ecosistema. |
| `data/eventos.yml` | **Fuente de verdad de eventos.** 35 registros con schema estable. |
| `tools/build_media.py` | Cruza eventos ↔ 742 archivos de Instagram → fotos optimizadas. |
| `static/img/eventos/` | **266 imágenes (133 × 2 tamaños), 23.2 MB** — venían de 596 MB. 32 de 35 eventos con fotos. |
| `data/fotos.yml` | Mapa slug → fotos. Generado, no editar a mano. |
| `data/sitio.yml` | Navegación, textos legales IEEE, propósito, redes. |
| `templates/base.html` | Layout con header/footer **compliant** (7 desviaciones corregidas). |
| `static/css/ieee-up.css` | Tokens + correcciones de marca + identidad acotada + componentes nuevos. |
| `templates/pages/eventos.html` | **Página de referencia ya funcionando** — copiar su patrón. |
| `build.py` | Generador. `python build.py --servir` levanta localhost:8000. |
| `tools/verificar.py` | Chequea marca IEEE + assets rotos + accesibilidad. |
| `.gitignore` (en la raíz) | Excluye credenciales, los 596 MB y `dist/`. |

Estado actual de `python tools/verificar.py`: **cumplimiento y accesibilidad en
verde**; los 13 fallos que reporta son exactamente los enlaces a las 13 páginas
que faltan. Ese reporte **es la lista de tareas** — cuando llegue a cero, terminó.

---

## 3. Las 7 desviaciones del template que ya quedaron corregidas

No revertir ninguna al copiar markup del template original:

1. **Master Brand en negro**, no azul. El SVG del template viene `#0073AE`; la
   guía reserva el azul para ieee.org/enterprise. Se generaron
   `logo-ieee-black.svg` y `logo-ieee-white.svg`.
2. **Master Brand abre en la misma ventana** (el template usaba `target="_blank"`).
3. **Footer con "Contact"** — el template traía "Sitemap" y omitía Contact, que sí
   es obligatorio.
4. **Meta-nav con los 7 ítems**, incluidos "Join IEEE" y "Donate" que faltaban.
5. **Azul normalizado a `#00629B`** (el oficial) vía tokens CSS; el template
   repetía `#006699` 39 veces hard-codeado. Coincide exacto con `IEEE-UP-AZUL.png`.
6. **Meta-nav a 12px** (el template la traía a 11px, por debajo del mínimo).
7. **Un solo `<h1>` por página.** El template pone el nombre del sitio en `<h1>`,
   lo que produce dos `<h1>` por página. Ahora es `.site-title` con el mismo peso
   visual, y el `<h1>` es el título de cada página.

Pendiente y no resuelto aquí: **banner de cookies GDPR**. El script de Osano del
template pertenece a la cuenta corporativa de IEEE y no se puede reutilizar. Hace
falta uno propio antes de publicar (ver §7).

---

## 4. Cómo trabajar

```bash
cd "04-SITIO-WEB"
python build.py --servir      # genera dist/ y sirve en http://localhost:8000
python tools/verificar.py     # cumplimiento + assets + accesibilidad
```

Para agregar o corregir un evento: editar **`data/eventos.yml`** directamente.
**No volver a correr `parse_eventos.py`** salvo que se rehaga el catálogo desde
cero — sobrescribe el archivo y se perderían las correcciones manuales.

Para regenerar fotos: `python tools/build_media.py --limpiar`.

---

## 5. Las 13 páginas que faltan

Cada archivo va en `templates/pages/` y se genera solo. Todas heredan de
`base.html` y usan `{% extends "base.html" %}` + los bloques `title`,
`description`, `body_class`, `content`.

**Orden recomendado** (de más a menos estructural):

| # | Archivo | Contenido | Datos que usa |
|---|---|---|---|
| 1 | `index.html` | Portada, 9 secciones (ver §6) | `destacados`, `eventos_por_tipo`, `proposito` |
| 2 | `eventos-talleres.html` | Solo Talleres | `eventos_por_tipo['Taller']` |
| 3 | `eventos-visitas.html` | Solo Visitas | `eventos_por_tipo['Visita']` |
| 4 | `eventos-competencias.html` | Solo Competencias | `eventos_por_tipo['Competencia/Concurso']` |
| 5 | `eventos-ecosistema.html` | Ecosistema, agrupado por `escala` (País / Región 9 / Global) | `eventos_por_tipo['Ecosistema IEEE']` |
| 6 | `proyectos.html` | Catálogo de resultados | `proyectos` (ya filtrado) |
| 7 | `nosotros.html` | Propósito + organigrama + trayectoria | `03-organigrama-2026-y-modelo-de-datos.md`, `logros` |
| 8 | `grupos.html` | Índice de los 3 grupos | organigrama §3 |
| 9 | `grupo-wie.html` | WIE: misión, directiva, sus eventos | organigrama + eventos con `grupo == 'WIE'` |
| 10 | `grupo-sight.html` | SIGHT | ídem, `grupo == 'SIGHT'` |
| 11 | `grupo-cis.html` | CIS | ídem, `grupo == 'CIS'` |
| 12 | `unete.html` | Embudo de membresía en 2 niveles | — |
| 13 | `contacto.html` | Formulario + datos | — |

Las páginas 2–5 son prácticamente el mismo archivo cambiando la lista: conviene
resolverlas primero, son rápidas y hacen que la navegación deje de estar rota.

**Para páginas 4 y 6 (competencias / proyectos):** la regla de publicación cruzada
ya está resuelta en los datos (`en_proyectos`, `en_logros`). Un evento aparece en
ambas vistas **sin duplicar el registro** — solo filtrar, nunca copiar fichas.

---

## 6. Portada (`index.html`) — 9 secciones

Según `02-wireframe-home-y-paginas-clave.md`:

1. Header compliant *(ya viene de `base.html`)*
2. **Hero** — una sola idea con fecha: el evento más relevante. Botón "Inscríbete".
   Aquí sí va identidad: `.ident-bloque` + `.ident-anillo`.
3. **Propósito** — 3 bloques desde `sitio.proposito`.
4. **Eventos — dos bloques distintos, no uno:**
   - "Próximos eventos": 3–4 tarjetas (`partials/evento_card.html`).
   - "Nuestra presencia en el ecosistema IEEE": 1–2 hitos con tratamiento de
     banda grande (`.ident-bloque`), no tarjeta chica. Es otra historia: prestigio
     y representación, no "ven a nuestro taller".
5. **Grupos de Afinidad** — 3 tarjetas, logos en `static/img/logos/`.
6. **Testimonios** — 2–4 citas reales. *Si no hay citas reales todavía, omitir la
   sección entera; no inventar testimonios.*
7. **Proyectos destacados** — 3–4 desde `proyectos`.
8. **CTA "Únete"** + redes.
9. Footer compliant *(ya viene de `base.html`)*

---

## 7. Reglas que no se negocian

**Identidad geométrica — acotada.** Está definida en `static/css/ieee-up.css` §3
con las clases `.ident-bloque`, `.ident-circulo`, `.ident-anillo`,
`.ident-franja`, `.ident-subrayado`. Solo pueden usarse en: hero de portada,
separadores de sección, la banda de Ecosistema IEEE, y subrayados de título.
**Prohibido** en tarjetas de evento, tarjetas de proyecto, grillas de personas,
tablas y cuerpos de texto. Eventos y Proyectos son el protagonista visual.

**No inventar contenido.** Concretamente:
- 4 competencias no tienen ganador documentado. La tarjeta muestra "Resultado por
  confirmar" (`.dato-pendiente`), nunca un ganador supuesto.
- 3 eventos no tienen fotos (sus posts eran solo video): van sin galería.
- Las fechas se muestran con la precisión que realmente existe: si solo se conoce
  el mes, se muestra el mes. `fecha_precision` ya lo indica.
- Los 9 pendientes de `05-raw-eventos.md` §6 siguen abiertos.

**Privacidad del organigrama.** Los IDs `P000xxxxxx` de la planilla **no van al
sitio bajo ninguna circunstancia**, ni género ni facultad/carrera. Solo nombre y
cargo. Fotos únicamente del Directorio (14) y las 3 presidencias de grupo; el
resto, nombre y rol sin foto.

**Textos legales en inglés, literales.** La meta-navegación, los enlaces del
footer, la línea de copyright y el descriptor "A public charity, IEEE is the
world's largest…" son obligatorios y no se traducen. El resto del sitio va en
español.

---

## 8. Antes de publicar (fuera del código)

1. **Revocar la sesión de Instagram filtrada.** `03-INSTAGRAM-CONTENT/scripts/script_0.py`
   contiene una cookie de sesión activa en texto plano de la cuenta `jhoanvallas`.
   Está en `.gitignore`, pero eso no la invalida: hay que cerrarla desde Instagram
   → Configuración → Centro de cuentas → Contraseña y seguridad → Dónde iniciaste
   sesión, y borrar la línea del archivo.
2. **Banner de cookies GDPR propio** (el de Osano es de IEEE corporativo).
3. **Registro administrativo IEEE**: officers al día en vTools, y solicitar el
   registro del sitio/dominio con el IEEE Website and Social Media Site
   Registration Form. Dominio: "IEEE" + nombre de unidad, sin año.
4. **Completar `data/sitio.yml`**: LinkedIn y correo de contacto están vacíos.
5. **Formularios**: IEEE no permite backend propio en su hosting ni captura de
   datos de tarjeta. Usar Google Forms embebido (ver
   `00-TEMPLATE-OFICIAL-IEEE-DCI/05-formularios-y-limitaciones-hosting.md`).
6. Confirmar con Jazmin Gonzales (Directora de Eventos) el calendario del ciclo,
   para que Eventos no salga sin eventos próximos el día del lanzamiento.
7. Opcional pero recomendado: pedir revisión previa al equipo de Experience Design
   de IEEE y presentarse al Student Website Contest de la Región 9.
