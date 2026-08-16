"""
Conecta cada evento de `data/eventos.yml` con las fotos reales de sus posts de
Instagram, y genera copias optimizadas dentro del sitio.

Flujo:
    eventos.yml (shortcodes)
      -> archivos en 03-INSTAGRAM-CONTENT/descargas/re.ieeeup/YYYY-MM-DD_SHORTCODE*.ext
      -> Pillow: recorte/redimension + strip de metadata
      -> static/img/eventos/<slug>/NN-card.jpg  (tarjetas, 720px)
                                   NN-full.jpg  (galeria, 1600px)
      -> data/fotos.yml  (mapa slug -> lista de fotos)

Decisiones tomadas:
  * Los 107 .mp4 (515 MB) NO se copian. Un sitio estatico no debe cargar medio GB
    de video; los videos quedan accesibles via el enlace al post original.
  * Se priorizan los posts de tipo "Recap"/"Fotos" sobre los de "Invitacion",
    porque los primeros son fotos reales del evento y los segundos son flyers.
  * Se toma primero UNA imagen de cada post (para que todos los posts del evento
    esten representados) y recien despues se rellena con las restantes.
  * `data/fotos.yml` es un archivo aparte a proposito: asi este script se puede
    volver a correr sin pisar las correcciones manuales de `data/eventos.yml`.

Uso:
    python tools/build_media.py                 -> genera todo
    python tools/build_media.py --dry-run       -> solo reporta, no escribe
    python tools/build_media.py --max-por-evento 10
"""

import argparse
import re
import shutil
import sys
from pathlib import Path

import yaml
from PIL import Image, ImageOps

SITE_DIR = Path(__file__).resolve().parent.parent
ROOT = SITE_DIR.parent
DESCARGAS = ROOT / "03-INSTAGRAM-CONTENT" / "descargas" / "re.ieeeup"
POSTS_JSON = ROOT / "03-INSTAGRAM-CONTENT" / "descargas" / "re.ieeeup_posts.json"
EVENTOS_YML = SITE_DIR / "data" / "eventos.yml"
FOTOS_YML = SITE_DIR / "data" / "fotos.yml"
OUT_IMG = SITE_DIR / "static" / "img" / "eventos"

EXT_IMAGEN = {".jpg", ".jpeg", ".webp", ".png"}
ANCHO_CARD = 720          # tarjetas: .featured-image del tema mide 278px de alto
ANCHO_FULL = 1600         # galeria / lightbox
ALTO_CARD = 480           # recorte 3:2 para que la grilla quede pareja
CALIDAD = 82
MAX_POR_EVENTO = 8

# Los roles que suelen traer fotos reales del evento van primero; los flyers al final.
PRIORIDAD_ROL = [
    (r"recap|foto|sesion de fotos|testimonio|entrevista", 0),
    (r"resultado|premio|logro|ganador", 1),
    (r"ponente|speaker|mentor|agenda|cronograma", 2),
    (r"invitaci|recordatorio|anuncio|convocatoria|lanzamiento|inscripci", 3),
]


def prioridad(rol: str) -> int:
    r = (rol or "").lower()
    for patron, peso in PRIORIDAD_ROL:
        if re.search(patron, r):
            return peso
    return 2


def indexar_descargas() -> dict[str, list[Path]]:
    """Agrupa los 742 archivos descargados por shortcode."""
    if not DESCARGAS.exists():
        sys.exit(f"No se encontro la carpeta de descargas: {DESCARGAS}")

    por_shortcode: dict[str, list[Path]] = {}
    # Nombres: YYYY-MM-DD_SHORTCODE.ext  o  YYYY-MM-DD_SHORTCODE_N.ext
    patron = re.compile(r"^\d{4}-\d{2}-\d{2}_(.+?)(?:_(\d+))?$")
    for archivo in DESCARGAS.iterdir():
        if not archivo.is_file():
            continue
        m = patron.match(archivo.stem)
        if not m:
            continue
        por_shortcode.setdefault(m.group(1), []).append(archivo)

    for archivos in por_shortcode.values():
        archivos.sort(key=lambda p: p.name)
    return por_shortcode


def procesar_imagen(origen: Path, destino_card: Path, destino_full: Path) -> bool:
    """Genera las dos versiones. Devuelve False si el archivo no es una imagen valida."""
    try:
        with Image.open(origen) as im:
            im = ImageOps.exif_transpose(im)      # respeta orientacion de camara
            im = im.convert("RGB")                # descarta alpha y perfiles raros

            # Version galeria: solo se limita el ancho, se conserva la proporcion.
            full = im.copy()
            if full.width > ANCHO_FULL:
                alto = round(full.height * ANCHO_FULL / full.width)
                full = full.resize((ANCHO_FULL, alto), Image.LANCZOS)
            destino_full.parent.mkdir(parents=True, exist_ok=True)
            full.save(destino_full, "JPEG", quality=CALIDAD, optimize=True, progressive=True)

            # Version tarjeta: recorte centrado 3:2 para que la grilla sea uniforme.
            card = ImageOps.fit(im, (ANCHO_CARD, ALTO_CARD), Image.LANCZOS, centering=(0.5, 0.4))
            card.save(destino_card, "JPEG", quality=CALIDAD, optimize=True, progressive=True)
        return True
    except Exception as exc:                      # archivo corrupto o formato raro
        print(f"    ! no se pudo procesar {origen.name}: {exc}")
        return False


def main() -> None:
    ap = argparse.ArgumentParser()
    ap.add_argument("--dry-run", action="store_true")
    ap.add_argument("--max-por-evento", type=int, default=MAX_POR_EVENTO)
    ap.add_argument("--limpiar", action="store_true", help="borra static/img/eventos antes")
    args = ap.parse_args()

    eventos = yaml.safe_load(EVENTOS_YML.read_text(encoding="utf-8"))
    indice = indexar_descargas()
    print(f"Archivos indexados: {sum(len(v) for v in indice.values())} en {len(indice)} shortcodes")

    if args.limpiar and OUT_IMG.exists() and not args.dry_run:
        shutil.rmtree(OUT_IMG)

    mapa: dict[str, list[dict]] = {}
    sin_fotos: list[str] = []
    total_generadas = 0
    bytes_salida = 0

    for ev in eventos:
        slug = ev["slug"]
        # Ordenar los posts del evento por utilidad fotografica.
        enlaces = sorted(
            [e for e in ev.get("enlaces", []) if e.get("valido")],
            key=lambda e: prioridad(e.get("rol", "")),
        )

        # Ronda 1: una imagen por post. Ronda 2+: el resto, hasta el tope.
        candidatas: list[tuple[str, Path]] = []
        colas: list[tuple[str, list[Path]]] = []
        for enlace in enlaces:
            archivos = [
                a for a in indice.get(enlace["shortcode"], [])
                if a.suffix.lower() in EXT_IMAGEN
            ]
            if archivos:
                colas.append((enlace["shortcode"], archivos))

        ronda = 0
        while len(candidatas) < args.max_por_evento:
            agrego = False
            for shortcode, archivos in colas:
                if ronda < len(archivos) and len(candidatas) < args.max_por_evento:
                    candidatas.append((shortcode, archivos[ronda]))
                    agrego = True
            if not agrego:
                break
            ronda += 1

        if not candidatas:
            sin_fotos.append(slug)
            continue

        fotos: list[dict] = []
        for i, (shortcode, origen) in enumerate(candidatas, start=1):
            nombre = f"{i:02d}"
            rel_card = f"img/eventos/{slug}/{nombre}-card.jpg"
            rel_full = f"img/eventos/{slug}/{nombre}-full.jpg"
            destino_card = SITE_DIR / "static" / rel_card
            destino_full = SITE_DIR / "static" / rel_full

            if not args.dry_run:
                if not procesar_imagen(origen, destino_card, destino_full):
                    continue
                bytes_salida += destino_card.stat().st_size + destino_full.stat().st_size

            fotos.append(
                {
                    "card": rel_card,
                    "full": rel_full,
                    "shortcode": shortcode,
                    # Alt descriptivo real: sin texto generico tipo "imagen".
                    # Guion normal, no raya: cero rayas en cualquier texto visible del sitio.
                    "alt": f"{ev['titulo']} - fotografía del evento",
                    "origen": f"https://www.instagram.com/p/{shortcode}/",
                }
            )
            total_generadas += 1

        mapa[slug] = fotos
        print(f"  {slug:52} {len(fotos):2} fotos")

    print(f"\nEventos con fotos : {len(mapa)}/{len(eventos)}")
    print(f"Imagenes generadas: {total_generadas} (x2 versiones)")
    if bytes_salida:
        print(f"Peso total        : {bytes_salida/1024/1024:.1f} MB")
    if sin_fotos:
        print(f"\nSIN FOTOS ({len(sin_fotos)}) -> necesitan imagen propia o quedan sin galeria:")
        for s in sin_fotos:
            print(f"  - {s}")

    if args.dry_run:
        print("\n(dry-run: no se escribio nada)")
        return

    cabecera = (
        "# Generado por tools/build_media.py — NO editar a mano.\n"
        "# Mapa slug de evento -> fotos optimizadas en static/img/eventos/.\n"
        "# Se regenera corriendo: python tools/build_media.py --limpiar\n\n"
    )
    with FOTOS_YML.open("w", encoding="utf-8") as fh:
        fh.write(cabecera)
        yaml.safe_dump(mapa, fh, allow_unicode=True, sort_keys=False, width=100)
    print(f"\nEscrito: {FOTOS_YML}")


if __name__ == "__main__":
    main()
