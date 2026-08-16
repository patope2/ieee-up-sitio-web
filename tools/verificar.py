"""
Verifica el sitio ya generado en `dist/`:
  1. Cumplimiento de marca IEEE (elementos obligatorios de header y footer)
  2. Integridad de assets y enlaces internos
  3. Chequeos basicos de accesibilidad (WCAG 2.0 A)

Uso:
    python build.py && python tools/verificar.py
"""

import re
import sys
from pathlib import Path

BASE = Path(__file__).resolve().parent.parent
DIST = BASE / "dist"

# (nombre, patron que debe aparecer en cada pagina)
OBLIGATORIOS = [
    ('Master Brand con alt="IEEE"',          r'alt="IEEE"'),
    ("Master Brand en negro o blanco",       r"logo-ieee-(black|white)\.svg"),
    ("Meta-nav: IEEE.org",                   r"https://www\.ieee\.org/\""),
    ("Meta-nav: IEEE Xplore",                r"ieeexplore\.ieee\.org"),
    ("Meta-nav: IEEE Standards",             r"standards\.ieee\.org"),
    ("Meta-nav: IEEE Spectrum",              r"spectrum\.ieee\.org"),
    ("Meta-nav: More Sites",                 r"More Sites"),
    ("Meta-nav: Join IEEE",                  r"Join IEEE"),
    ("Meta-nav: Donate",                     r"Donate"),
    ("Footer: Contact",                      r">Contact<"),
    ("Footer: Accessibility",                r"accessibility-statement"),
    ("Footer: Nondiscrimination Policy",     r"p9-26\.html"),
    ("Footer: IEEE Ethics Reporting",        r"ethicspoint"),
    ("Footer: IEEE Privacy Policy",          r"security_privacy"),
    ("Footer: Terms & Disclosures",          r"site_terms_conditions"),
    ("Descriptor obligatorio",               r"A public charity, IEEE is the world"),
    ("Linea de copyright",                   r"©\s*Copyright \d{4} IEEE"),
    ("Favicon",                              r"favicon\.png"),
    ("Enlace de salto al contenido",         r"skip-link"),
    ("Idioma declarado",                     r'<html lang="\w+"'),
]


def main() -> None:
    if not DIST.exists():
        sys.exit("No existe dist/. Corre primero: python build.py")

    paginas = sorted(DIST.glob("*.html"))
    if not paginas:
        sys.exit("dist/ no tiene paginas HTML.")

    fallos = 0

    print(f"Verificando {len(paginas)} paginas en dist/\n")
    print("== 1. Cumplimiento de marca IEEE ==")
    for nombre, patron in OBLIGATORIOS:
        sin = [p.name for p in paginas
               if not re.search(patron, p.read_text(encoding="utf-8"))]
        if sin:
            fallos += 1
            detalle = ", ".join(sin[:3]) + (" ..." if len(sin) > 3 else "")
            print(f"  [FALLA] {nombre} -> falta en: {detalle}")
        else:
            print(f"  [ok]    {nombre}")

    # El Master Brand nunca debe abrir en pestaña nueva.
    for p in paginas:
        if re.search(r'id="logo-ieee"[^>]*target=', p.read_text(encoding="utf-8")):
            fallos += 1
            print(f"  [FALLA] Master Brand abre en pestaña nueva en {p.name}")

    print("\n== 2. Integridad de assets y enlaces internos ==")
    rotos: set[str] = set()
    for p in paginas:
        html = p.read_text(encoding="utf-8")
        for ref in re.findall(r'(?:href|src)="([^"#:]+)"', html):
            if ref.startswith(("http", "//", "mailto:", "javascript:")) or not ref.strip():
                continue
            if not (DIST / ref).exists():
                rotos.add(f"{p.name} -> {ref}")
    if rotos:
        fallos += len(rotos)
        for r in sorted(rotos):
            print(f"  [FALLA] referencia rota: {r}")
    else:
        print("  [ok]    todas las referencias internas resuelven")

    # Enlaces a un popup especifico (pagina.html#modal-slug): el chequeo de
    # arriba corta el fragmento, asi que se valida aparte que ese id exista
    # de verdad en la pagina de destino.
    ids_por_pagina: dict[str, set[str]] = {}
    for p in paginas:
        ids_por_pagina[p.name] = set(re.findall(r'\bid="([^"]+)"', p.read_text(encoding="utf-8")))

    anclas_rotas: set[str] = set()
    for p in paginas:
        html = p.read_text(encoding="utf-8")
        for archivo, ancla in re.findall(r'href="([^"#:]*)#(modal-[^"]+)"', html):
            destino = archivo or p.name
            if destino not in ids_por_pagina or ancla not in ids_por_pagina[destino]:
                anclas_rotas.add(f"{p.name} -> {destino}#{ancla}")
    if anclas_rotas:
        fallos += len(anclas_rotas)
        for r in sorted(anclas_rotas):
            print(f"  [FALLA] enlace a popup roto: {r}")
    else:
        print("  [ok]    todos los enlaces a popups de evento resuelven")

    print("\n== 3. Accesibilidad basica ==")
    sin_alt = 0
    for p in paginas:
        for tag in re.findall(r"<img\b[^>]*>", p.read_text(encoding="utf-8")):
            if "alt=" not in tag:
                sin_alt += 1
                print(f"  [FALLA] <img> sin alt en {p.name}: {tag[:70]}")
    if not sin_alt:
        print("  [ok]    todas las imagenes tienen atributo alt")
    fallos += sin_alt

    for p in paginas:
        n = len(re.findall(r"<h1\b", p.read_text(encoding="utf-8")))
        if n != 1:
            fallos += 1
            print(f"  [FALLA] {p.name} tiene {n} <h1> (debe tener exactamente 1)")

    print(f"\n{'SIN PROBLEMAS' if fallos == 0 else f'{fallos} PROBLEMA(S) A CORREGIR'}")
    sys.exit(1 if fallos else 0)


if __name__ == "__main__":
    main()
