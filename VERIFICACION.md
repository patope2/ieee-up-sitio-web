# Verificación de esta copia

Hecha el 2026-08-01, al crear `07-SITIO-WEB-v2` a partir de `04-SITIO-WEB`.
Registro de qué se comprobó para asegurar que esta carpeta es autónoma,
completa y funcional, y que no se modificó nada visualmente.

## 1. Duplicación exacta
`data/`, `templates/`, `static/`, `dist/` y `tools/` se copiaron de
`04-SITIO-WEB` y se compararon archivo por archivo (`diff -rq`): **idénticos**.

## 2. Independencia real (no solo copiada — reconstruida)
Se corrió `python build.py` **desde dentro de `07-SITIO-WEB-v2`**, sin tocar
`04-SITIO-WEB` para nada. Generó las 14 páginas sin errores. Esto prueba que
la carpeta no depende de rutas ni archivos externos a sí misma — `build.py`
resuelve todo con rutas relativas a su propia ubicación.

## 3. Integridad de assets y cumplimiento de marca
`python tools/verificar.py` sobre el `dist/` reconstruido:
- Marca IEEE (Master Brand, meta-nav de 7 ítems, footer con los 7 enlaces
  obligatorios, descriptor, copyright, favicon, idioma, skip-link): **todo ok**.
- Enlaces e imágenes internas de las 14 páginas: **todas resuelven**, ninguna
  referencia rota.
- Enlaces a popups de evento (`#modal-slug`): **todos resuelven**.
- Accesibilidad básica (`alt` en imágenes, un solo `<h1>` por página): **ok**.

Resultado: `SIN PROBLEMAS`.

## 4. Cero cambios visuales
Se comparó el `dist/` reconstruido contra el `dist/` original de
`04-SITIO-WEB` con `diff -rq`: **byte a byte idéntico**. Ningún HTML, CSS,
imagen, fuente o script cambió.

## 5. Herramienta nueva probada y revertida
`tools/agregar_fotos_evento.py` se probó con imágenes de prueba (slug
`__test-evento`, fuera de esta carpeta): generó `card`/`full` correctamente y
actualizó `data/fotos.yml` sin tocar ninguna de las 32 entradas existentes.
Después de la prueba se confirmó por YAML (no solo por texto) que el
contenido de `data/fotos.yml` quedó igual al original salvo el encabezado del
archivo (actualizado para reflejar que ahora también se edita con este
script, no solo con `build_media.py`), y se volvió a reconstruir + verificar
el sitio para confirmar que quedó en el mismo estado limpio del punto 4.

## Pendientes de contenido (no de esta copia)
Ver la sección "Antes de publicar en producción" en `README.md` — correo de
contacto vacío y banner de cookies pendiente. Ya estaban así en
`04-SITIO-WEB`; esta copia los hereda tal cual, sin inventar valores.
