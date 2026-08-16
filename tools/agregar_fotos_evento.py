"""
Genera las fotos (card/full) de UN evento a partir de una carpeta local de
imagenes propias, sin depender de la carpeta externa 03-INSTAGRAM-CONTENT/
(esa solo la usa tools/build_media.py, pensado para el catalogo historico
importado de Instagram).

Usa exactamente el mismo procesamiento que tools/build_media.py (mismo
tamano de card/full, mismo recorte, misma calidad JPEG) para que las fotos
nuevas se vean identicas en la grilla a las ya existentes.

Uso:
    python tools/agregar_fotos_evento.py --slug mi-evento-2026 --origen "C:\ruta\a\fotos"
    python tools/agregar_fotos_evento.py --slug mi-evento-2026 --origen fotos_nuevas --alt "Texto alternativo"
    python tools/agregar_fotos_evento.py --slug mi-evento-2026 --origen fotos_nuevas --dry-run

Despues de correrlo: agregar/editar la ficha del evento en data/eventos.yml
(si todavia no existe) y correr `python build.py` para regenerar dist/.
"""

import argparse
import sys
from pathlib import Path

import yaml
from PIL import Image, ImageOps

SITE_DIR = Path(__file__).resolve().parent.parent
EVENTOS_YML = SITE_DIR / "data" / "eventos.yml"
FOTOS_YML = SITE_DIR / "data" / "fotos.yml"
STATIC = SITE_DIR / "static"

EXT_IMAGEN = {".jpg", ".jpeg", ".webp", ".png"}
ANCHO_CARD = 720          # igual que tools/build_media.py: .featured-image mide 278px de alto
ANCHO_FULL = 1600         # galeria / lightbox
ALTO_CARD = 480           # recorte 3:2 para que la grilla quede pareja
CALIDAD = 82


def procesar_imagen(origen: Path, destino_card: Path, destino_full: Path) -> bool:
    """Genera las dos versiones. Devuelve False si el archivo no es una imagen valida."""
    try:
        with Image.open(origen) as im:
            im = ImageOps.exif_transpose(im)      # respeta orientacion de camara
            im = im.convert("RGB")                # descarta alpha y perfiles raros

            full = im.copy()
            if full.width > ANCHO_FULL:
                alto = round(full.height * ANCHO_FULL / full.width)
                full = full.resize((ANCHO_FULL, alto), Image.LANCZOS)
            destino_full.parent.mkdir(parents=True, exist_ok=True)
            full.save(destino_full, "JPEG", quality=CALIDAD, optimize=True, progressive=True)

            card = ImageOps.fit(im, (ANCHO_CARD, ALTO_CARD), Image.LANCZOS, centering=(0.5, 0.4))
            card.save(destino_card, "JPEG", quality=CALIDAD, optimize=True, progressive=True)
        return True
    except Exception as exc:                      # archivo corrupto o formato raro
        print(f"    ! no se pudo procesar {origen.name}: {exc}")
        return False


def titulo_evento(slug: str) -> str | None:
    if not EVENTOS_YML.exists():
        return None
    eventos = yaml.safe_load(EVENTOS_YML.read_text(encoding="utf-8")) or []
    for ev in eventos:
        if ev.get("slug") == slug:
            return ev.get("titulo")
    return None


def main() -> None:
    ap = argparse.ArgumentParser()
    ap.add_argument("--slug", required=True, help="slug del evento (el mismo que en data/eventos.yml)")
    ap.add_argument("--origen", required=True, type=Path, help="carpeta local con las fotos originales")
    ap.add_argument("--alt", default=None, help='texto alternativo comun a todas las fotos (por defecto: "<titulo> - fotografía del evento")')
    ap.add_argument("--limpiar", action="store_true", help="borra las fotos previas del evento antes de generar")
    ap.add_argument("--dry-run", action="store_true", help="solo reporta, no escribe nada")
    args = ap.parse_args()

    if not args.origen.exists():
        sys.exit(f"No existe la carpeta de origen: {args.origen}")

    archivos = sorted(
        p for p in args.origen.iterdir()
        if p.is_file() and p.suffix.lower() in EXT_IMAGEN
    )
    if not archivos:
        sys.exit(f"No hay imagenes ({', '.join(sorted(EXT_IMAGEN))}) en {args.origen}")

    titulo = titulo_evento(args.slug)
    if titulo is None:
        print(f"  (aviso: el slug '{args.slug}' todavia no existe en data/eventos.yml - "
              f"agrega la ficha del evento por separado)")
    alt = args.alt or f"{titulo or args.slug} - fotografía del evento"

    out_dir = STATIC / "img" / "eventos" / args.slug
    print(f"Slug             : {args.slug}")
    print(f"Fotos encontradas: {len(archivos)} en {args.origen}")
    print(f"Destino          : {out_dir}")

    if args.dry_run:
        for a in archivos:
            print(f"  (dry-run) {a.name}")
        print("\n(dry-run: no se escribio nada)")
        return

    if args.limpiar and out_dir.exists():
        for f in out_dir.iterdir():
            f.unlink()

    fotos: list[dict] = []
    for i, origen in enumerate(archivos, start=1):
        nombre = f"{i:02d}"
        rel_card = f"img/eventos/{args.slug}/{nombre}-card.jpg"
        rel_full = f"img/eventos/{args.slug}/{nombre}-full.jpg"
        if not procesar_imagen(origen, STATIC / rel_card, STATIC / rel_full):
            continue
        fotos.append({"card": rel_card, "full": rel_full, "alt": alt})
        print(f"  {origen.name:40} -> {nombre}-card.jpg / {nombre}-full.jpg")

    if not fotos:
        sys.exit("Ninguna imagen se pudo procesar.")

    mapa: dict[str, list[dict]] = {}
    if FOTOS_YML.exists():
        mapa = yaml.safe_load(FOTOS_YML.read_text(encoding="utf-8")) or {}
    mapa[args.slug] = fotos

    cabecera = (
        "# Mapa slug de evento -> fotos optimizadas en static/img/eventos/.\n"
        "# La mayoria de estas entradas vienen de tools/build_media.py (catalogo\n"
        "# historico de Instagram); las agregadas a mano con\n"
        "# tools/agregar_fotos_evento.py no tienen shortcode/origen porque no\n"
        "# vienen de un post — eso es normal, la plantilla solo usa card/full/alt.\n\n"
    )
    with FOTOS_YML.open("w", encoding="utf-8") as fh:
        fh.write(cabecera)
        yaml.safe_dump(mapa, fh, allow_unicode=True, sort_keys=False, width=100)

    print(f"\n{len(fotos)} fotos generadas. Actualizado: {FOTOS_YML}")
    print("Siguiente paso: agrega/edita la ficha en data/eventos.yml (si falta) y corre `python build.py`.")


if __name__ == "__main__":
    main()
