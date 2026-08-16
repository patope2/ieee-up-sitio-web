"""
Generador estatico del sitio de IEEE UP.

Lee los datos de `data/`, renderiza las plantillas Jinja2 de `templates/pages/`
y escribe HTML plano + assets en `dist/`. Sin Node, sin dependencias mas alla de
Jinja2 y PyYAML.

Uso:
    python build.py            -> genera dist/
    python build.py --servir   -> genera y levanta http://localhost:8000
"""

import argparse
import http.server
import re
import shutil
import socketserver
import sys
from pathlib import Path

import yaml
from jinja2 import Environment, FileSystemLoader, StrictUndefined

BASE = Path(__file__).resolve().parent
DATA = BASE / "data"
TEMPLATES = BASE / "templates"
STATIC = BASE / "static"
DIST = BASE / "dist"

MESES = ["", "enero", "febrero", "marzo", "abril", "mayo", "junio", "julio",
         "agosto", "septiembre", "octubre", "noviembre", "diciembre"]

# Etiqueta corta que se muestra en el badge de cada tarjeta.
BADGE = {
    "Taller": "Taller",
    "Visita": "Visita",
    "Competencia/Concurso": "Competencia",
    "Ecosistema IEEE": "Ecosistema IEEE",
    # Proyectos humanitarios y de divulgacion (SIGHT y WIE). No encajaban en
    # ninguno de los 4 tipos originales y son el nucleo de la mision IEEE.
    "Impacto social": "Impacto social",
}


# Grupos de afinidad de la Rama. La clave es la que usa el campo `grupo` de
# data/eventos.yml; la etiqueta es como se muestra en el sitio.
GRUPOS_UP = (
    ("WIE", "IEEE WIE UP"),
    ("SIGHT", "IEEE SIGHT UP"),
    ("CIS", "IEEE CIS UP"),
)


def resolver_autoria(ev: dict) -> dict:
    """
    Quien firma el evento, para que el visitante lo sepa sin leer la ficha entera.

    Cuatro casos:
      rama         -> lo organiza IEEE UP sin un grupo de afinidad detras
      grupo        -> lo organiza uno de los grupos (WIE, SIGHT o CIS)
      colaboracion -> lo organizan VARIAS unidades de la Rama a la vez
      externo      -> lo organiza otra entidad y la Rama participa

    El grupo se toma del campo `grupo`; ademas se lee `organiza_texto` porque
    hay fichas antiguas donde el grupo solo aparece mencionado ahi.

    Tener auspiciadores o aliados externos NO convierte un evento en
    colaboracion: un taller de WIE con un auspiciador sigue siendo de WIE. La
    colaboracion es entre unidades de la Rama. Los aliados externos se declaran
    en el campo opcional `colaboracion` y solo se listan cuando ademas hay
    varias unidades involucradas; en el resto de casos ya salen como
    auspiciadores.
    """
    texto = f"{ev.get('organiza_texto', '')} {ev.get('titulo', '')}".upper()
    unidades = [
        etiqueta for clave, etiqueta in GRUPOS_UP
        if ev.get("grupo") == clave or re.search(rf"\b{clave}\b", texto)
    ]
    aliados = ev.get("colaboracion") or []

    if ev.get("organiza") != "IEEE UP":
        return {"tipo": "externo", "etiqueta": ev.get("organiza") or "Terceros",
                "unidades": unidades, "aliados": aliados}
    if len(unidades) > 1:
        return {"tipo": "colaboracion", "etiqueta": "Colaboración",
                "unidades": unidades, "aliados": aliados}
    if unidades:
        return {"tipo": "grupo", "etiqueta": unidades[0],
                "unidades": unidades, "aliados": aliados}
    return {"tipo": "rama", "etiqueta": "IEEE UP",
            "unidades": ["IEEE UP"], "aliados": aliados}


def cargar(nombre: str, por_defecto=None):
    ruta = DATA / nombre
    if not ruta.exists():
        if por_defecto is not None:
            return por_defecto
        sys.exit(f"Falta el archivo de datos: {ruta}")
    return yaml.safe_load(ruta.read_text(encoding="utf-8"))


def fecha_legible(evento: dict) -> str:
    """Muestra la fecha con la precision que realmente se tiene, sin inventar dias."""
    orden, precision = evento.get("fecha_orden", ""), evento.get("fecha_precision")
    if not orden or precision == "desconocida":
        return evento.get("fecha_texto", "Fecha por confirmar")
    anio, mes, dia = int(orden[:4]), int(orden[5:7]), int(orden[8:10])
    if precision == "dia":
        return f"{dia} de {MESES[mes]} de {anio}"
    if precision == "mes":
        return f"{MESES[mes].capitalize()} de {anio}"
    return str(anio)


def construir_contexto() -> dict:
    sitio = cargar("sitio.yml")
    eventos = cargar("eventos.yml")
    fotos = cargar("fotos.yml", {}) or {}
    organigrama = cargar("organigrama.yml")
    oportunidades = cargar("oportunidades.yml", []) or []

    # Adjuntar fotos y datos derivados a cada evento.
    for ev in eventos:
        ev["fotos"] = fotos.get(ev["slug"], [])
        ev["portada"] = ev["fotos"][0] if ev["fotos"] else None
        ev["fecha_legible"] = fecha_legible(ev)
        ev["badge"] = BADGE.get(ev["tipo"], ev["tipo"])
        ev["autoria"] = resolver_autoria(ev)

    eventos.sort(key=lambda e: e["fecha_orden"], reverse=True)

    # Cada grupo de afinidad necesita sus propios eventos y proyectos
    # (filtra por el campo `grupo`, ya resuelto en data/eventos.yml).
    for grupo in organigrama["grupos"]:
        grupo["eventos"] = [e for e in eventos if e.get("grupo") == grupo["slug"].upper()]
        grupo["proyectos"] = [e for e in grupo["eventos"] if e.get("en_proyectos")]

    # Cada oportunidad puede apuntar a la ficha de un evento (evento_slug) para
    # no duplicar informacion: aqui se resuelve el enlace una sola vez.
    por_slug = {e["slug"]: e for e in eventos}
    for op in oportunidades:
        op["evento"] = por_slug.get(op.get("evento_slug"))

    orden_estado = {"Abierta": 0, "Permanente": 1, "Cerrada": 2}

    # Las reglas de publicacion cruzada ya vienen resueltas en los datos
    # (en_proyectos / en_logros): aqui solo se filtran. Un registro, varias vistas.
    return {
        "sitio": sitio,
        "eventos": eventos,
        "oportunidades": sorted(
            oportunidades, key=lambda o: orden_estado.get(o["estado"], 9)
        ),
        "oportunidades_abiertas": [
            o for o in oportunidades if o["estado"] in ("Abierta", "Permanente")
        ],
        "eventos_por_tipo": {
            tipo: [e for e in eventos if e["tipo"] == tipo]
            for tipo in ("Taller", "Visita", "Competencia/Concurso",
                         "Impacto social", "Ecosistema IEEE")
        },
        "proyectos": [e for e in eventos if e.get("en_proyectos")],
        "logros": [e for e in eventos if e.get("en_logros")],
        "destacados": [e for e in eventos if e["fotos"]][:4],
        "organigrama": organigrama,
        "proximo_evento": next((e for e in eventos if e.get("estado") == "Próximo"), None),
    }


def construir(servir: bool = False) -> None:
    # Se borra el CONTENIDO en vez de la carpeta dist/ en si: en Windows, si el
    # IDE o un explorador tiene la carpeta abierta, rmdir sobre dist/ falla con
    # PermissionError aunque los archivos de adentro si se puedan borrar.
    if DIST.exists():
        for item in DIST.iterdir():
            if item.is_dir():
                shutil.rmtree(item)
            else:
                item.unlink()
    else:
        DIST.mkdir(parents=True)

    shutil.copytree(STATIC, DIST, dirs_exist_ok=True)

    env = Environment(
        loader=FileSystemLoader(str(TEMPLATES)),
        undefined=StrictUndefined,   # falla ruidosamente si falta un dato
        trim_blocks=True,
        lstrip_blocks=True,
        autoescape=True,
    )
    ctx = construir_contexto()

    paginas = sorted((TEMPLATES / "pages").glob("*.html"))
    if not paginas:
        sys.exit("No hay plantillas en templates/pages/")

    for plantilla in paginas:
        salida = DIST / plantilla.name
        html = env.get_template(f"pages/{plantilla.name}").render(
            **ctx, rel="", pagina_actual=plantilla.name
        )
        salida.write_text(html, encoding="utf-8")
        print(f"  {plantilla.name}")

    print(f"\n{len(paginas)} paginas -> {DIST}")

    if servir:
        import os
        os.chdir(DIST)

        # ThreadingTCPServer, no TCPServer: el servidor de un solo hilo atiende
        # UNA conexion a la vez, y un navegador abre varias en paralelo (CSS,
        # fuentes, decenas de fotos). Bastaba con que una quedara a medias para
        # que el servidor dejara de responder y hubiera que reiniciarlo a mano.
        # `daemon_threads` evita que esos hilos impidan cerrar con Ctrl+C, y
        # `allow_reuse_address` permite relanzar de inmediato sin esperar a que
        # el sistema libere el puerto.
        class Servidor(socketserver.ThreadingTCPServer):
            daemon_threads = True
            allow_reuse_address = True

        with Servidor(("", 8000), http.server.SimpleHTTPRequestHandler) as srv:
            print("\nhttp://localhost:8000   (Ctrl+C para detener)")
            srv.serve_forever()


if __name__ == "__main__":
    ap = argparse.ArgumentParser()
    ap.add_argument("--servir", action="store_true")
    construir(servir=ap.parse_args().servir)
