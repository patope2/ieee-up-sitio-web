"""
Convierte el catalogo escrito a mano `02-ARQUITECTURA-WEB-IEEE-UP/05-raw-eventos.md`
en datos estructurados (`data/eventos.yml`) que consume el generador del sitio.

Se corre UNA vez para generar el YAML. A partir de ahi la fuente de verdad para
editar eventos pasa a ser `data/eventos.yml`, no el markdown: el markdown queda
como documento de investigacion/trazabilidad.

Uso:
    python tools/parse_eventos.py              -> escribe data/eventos.yml
    python tools/parse_eventos.py --check      -> solo valida e imprime el resumen
"""

import argparse
import re
import sys
import unicodedata
from pathlib import Path

import yaml

SITE_DIR = Path(__file__).resolve().parent.parent
ROOT = SITE_DIR.parent
RAW_MD = ROOT / "02-ARQUITECTURA-WEB-IEEE-UP" / "05-raw-eventos.md"
OUT_YAML = SITE_DIR / "data" / "eventos.yml"

# Seccion "## N. Titulo" -> valor del campo `tipo` del modelo Evento.
# Solo se parsean estas 4; la 5 (Contenido descartado) y la 6 (Pendientes) se ignoran.
SECCION_A_TIPO = {
    "talleres": "Taller",
    "visitas": "Visita",
    "competencias y concursos": "Competencia/Concurso",
    "ecosistema ieee": "Ecosistema IEEE",
}

# Las ~13 etiquetas distintas que en el markdown significan "quien expuso/dirigio".
# Todas colapsan al mismo campo `ponentes` (lista), conservando el matiz del rol
# original en `ponentes_rol` para no perder informacion.
LABELS_PONENTES = {
    "ponente": "Ponente",
    "ponentes": "Ponentes",
    "ponentes destacados": "Ponentes destacados",
    "speakers": "Speakers",
    "sesiones y facilitadores": "Sesiones y facilitadores",
    "mentores": "Mentores",
    "facilitadoras invitadas": "Facilitadoras invitadas",
    "invitado especial": "Invitado especial",
    "invitados": "Invitados",
    "docente acompanante": "Docente acompañante",
    "asesora academica": "Asesora académica",
}
# "Speakers — Panel 1 (IA en los negocios)" y similares: prefijo variable.
RE_LABEL_PONENTES_PANEL = re.compile(r"^speakers?\s*[—–-]\s*panel", re.I)

# Etiquetas que se mapean 1:1 a un campo escalar del modelo.
LABELS_SIMPLES = {
    "etiqueta": "etiqueta",
    "fecha": "fecha_texto",
    "ubicacion / modalidad": "ubicacion_texto",
    "ubicacion": "ubicacion_texto",
    "organiza": "organiza_texto",
    "descripcion": "descripcion",
    "escala": "escala",
    "resultado": "resultado_texto",
    "logro obtenido": "logro_obtenido",
    "premio": "premio",
    "premios": "premio",
    "alcance": "alcance",
    "nota": "nota",
    "rol de ieee up": "rol",
    "talleres incluidos": "talleres_incluidos",
    "becas de aliados": "becas_aliados",
    "auspiciadores": "auspiciadores",
    "delegaciones internacionales participantes": "participantes",
}

RE_HEADING = re.compile(r"^(#{2,4})\s+(.*?)\s*$")
RE_BULLET_LABEL = re.compile(r"^\s*-\s+\*\*(.+?):\*\*\s*(.*)$")
RE_SUBITEM = re.compile(r"^\s{2,}(?:[-*]|\d+\.)\s+(.*)$")
RE_INSTAGRAM = re.compile(r"https?://www\.instagram\.com/p/([A-Za-z0-9_\-]+)/?")
# Un shortcode real de Instagram tiene 11 caracteres. Los de 39 que dejo el
# scraper (posts colaborativos) no resuelven como permalink -> se marcan rotos.
LEN_SHORTCODE_VALIDO = 11


def deacentuar(texto: str) -> str:
    return "".join(
        c for c in unicodedata.normalize("NFD", texto) if unicodedata.category(c) != "Mn"
    )


def normalizar_label(label: str) -> str:
    return deacentuar(label).strip().lower()


def slugify(texto: str) -> str:
    base = deacentuar(texto).lower()
    base = re.sub(r"[^a-z0-9]+", "-", base)
    return base.strip("-")


def limpiar_valor(texto: str) -> str:
    """Quita el enfasis markdown y las cursivas de nota que rodean muchos valores."""
    texto = texto.strip()
    texto = re.sub(r"\*\*(.+?)\*\*", r"\1", texto)
    texto = re.sub(r"\*(.+?)\*", r"\1", texto)
    return texto.strip()


def parsear_fecha(fecha_texto: str) -> dict:
    """
    Extrae una fecha ordenable del texto libre en español.

    Las fichas mezclan formatos: "Miercoles 27 de mayo de 2026, 1:30 p.m.",
    "29 al 31 de mayo de 2026", "Febrero de 2024", "Octubre de 2021 (fecha de
    publicacion...)". Se devuelve la fecha de INICIO con la precision disponible,
    porque el sitio solo necesita ordenar y agrupar por año.
    """
    meses = {
        "enero": 1, "febrero": 2, "marzo": 3, "abril": 4, "mayo": 5, "junio": 6,
        "julio": 7, "agosto": 8, "setiembre": 9, "septiembre": 9, "octubre": 10,
        "noviembre": 11, "diciembre": 12,
    }
    t = deacentuar(fecha_texto).lower()

    anio_match = re.search(r"\b(20\d{2})\b", t)
    anio = int(anio_match.group(1)) if anio_match else None

    mes = None
    for nombre, num in meses.items():
        if re.search(rf"\b{deacentuar(nombre)}\b", t):
            mes = num
            break

    # Primer numero de 1-2 digitos que aparezca antes del mes -> dia de inicio.
    dia = None
    if mes is not None:
        nombre_mes = next(n for n, v in meses.items() if v == mes)
        antes = t.split(deacentuar(nombre_mes))[0]
        dias = re.findall(r"\b(\d{1,2})\b", antes)
        if dias:
            dia = int(dias[0])
            if not 1 <= dia <= 31:
                dia = None

    if anio and mes and dia:
        precision = "dia"
        orden = f"{anio:04d}-{mes:02d}-{dia:02d}"
    elif anio and mes:
        precision = "mes"
        orden = f"{anio:04d}-{mes:02d}-01"
    elif anio:
        precision = "anio"
        orden = f"{anio:04d}-01-01"
    else:
        precision = "desconocida"
        orden = "1900-01-01"

    return {"orden": orden, "anio": anio, "precision": precision}


def parsear_modalidad(ubicacion_texto: str) -> str:
    t = deacentuar(ubicacion_texto or "").lower()
    tiene_presencial = "presencial" in t
    tiene_virtual = "virtual" in t or "zoom" in t or "teams" in t
    if tiene_presencial and tiene_virtual:
        return "Híbrido"
    if tiene_presencial:
        return "Presencial"
    if tiene_virtual:
        return "Virtual"
    if "mixta" in t:
        return "Híbrido"
    return "No especificada"


def parsear_organiza(organiza_texto: str) -> str:
    """Normaliza el texto libre de organizador al enum del modelo Evento."""
    t = deacentuar(organiza_texto or "").lower()
    if "region 9" in t or "r9" in t:
        return "IEEE Región 9"
    if "seccion peru" in t:
        return "IEEE Perú"
    # "Ramas IEEE de UP, Continental y UNTELS" -> varias ramas = nivel pais.
    if "ramas ieee" in t or "ieee uni" in t or "ieee unsaac" in t:
        return "IEEE Perú"
    if "ieee up" in t or "wie up" in t or "sight" in t:
        return "IEEE UP"
    return "Terceros"


def parsear_grupo(titulo: str, organiza_texto: str) -> str | None:
    """Detecta si la ficha pertenece a un grupo de afinidad."""
    t = deacentuar(f"{titulo} {organiza_texto or ''}").lower()
    if "wie" in t:
        return "WIE"
    if "sight" in t:
        return "SIGHT"
    if re.search(r"\bcis\b", t):
        return "CIS"
    return None


def extraer_enlaces(lineas_sub: list[str], inline: str) -> list[dict]:
    """
    Los enlaces vienen de dos formas:
      - inline:   `- **Enlaces Instagram:** https://...`
      - anidados: `  - Invitación (22 may): https://...`
    Devuelve [{rol, url, shortcode, valido}].
    """
    enlaces: list[dict] = []

    def agregar(rol: str, url: str) -> None:
        m = RE_INSTAGRAM.search(url)
        if not m:
            return
        shortcode = m.group(1)
        enlaces.append(
            {
                "rol": rol.strip(" :-—–") or "Publicación",
                "url": f"https://www.instagram.com/p/{shortcode}/",
                "shortcode": shortcode,
                # Los shortcodes de 39 chars no resuelven -> no enlazar en el sitio.
                "valido": len(shortcode) == LEN_SHORTCODE_VALIDO,
            }
        )

    if inline.strip():
        agregar("Publicación", inline)

    for linea in lineas_sub:
        if "instagram.com" not in linea:
            continue
        # "Invitación (22 may): https://..." -> rol = todo antes del ultimo ':'
        partes = linea.rsplit(":", 1)
        if len(partes) == 2 and "http" in partes[1]:
            rol_raw = partes[0]
        else:
            rol_raw = "Publicación"
        # quitar la fecha corta entre parentesis del rol
        rol = re.sub(r"\s*\([^)]*\)\s*$", "", limpiar_valor(rol_raw))
        agregar(rol, linea)

    return enlaces


def parsear() -> list[dict]:
    if not RAW_MD.exists():
        sys.exit(f"No se encontro el catalogo fuente: {RAW_MD}")

    lineas = RAW_MD.read_text(encoding="utf-8").splitlines()

    eventos: list[dict] = []
    tipo_actual: str | None = None
    ficha: dict | None = None
    label_actual: str | None = None
    subitems: list[str] = []

    def cerrar_label() -> None:
        """Vuelca los sub-bullets acumulados en el campo que estaba abierto."""
        nonlocal label_actual, subitems
        if ficha is None or label_actual is None:
            label_actual, subitems = None, []
            return

        norm = normalizar_label(label_actual)
        if norm.startswith("enlaces instagram"):
            ficha["_enlaces_sub"] = subitems[:]
        elif norm in LABELS_PONENTES or RE_LABEL_PONENTES_PANEL.match(norm):
            rol = LABELS_PONENTES.get(norm, limpiar_valor(label_actual))
            for item in subitems:
                ficha["ponentes"].append({"nombre": limpiar_valor(item), "rol": rol})
        elif subitems:
            campo = LABELS_SIMPLES.get(norm)
            texto = " · ".join(limpiar_valor(s) for s in subitems)
            if campo:
                previo = ficha.get(campo)
                ficha[campo] = f"{previo} · {texto}" if previo else texto
        label_actual, subitems = None, []

    def cerrar_ficha() -> None:
        nonlocal ficha
        if ficha is None:
            return
        cerrar_label()
        eventos.append(ficha)
        ficha = None

    for linea in lineas:
        heading = RE_HEADING.match(linea)
        if heading:
            nivel, titulo = len(heading.group(1)), heading.group(2).strip()

            if nivel == 2:
                cerrar_ficha()
                clave = normalizar_label(re.sub(r"^\d+\.\s*", "", titulo))
                tipo_actual = SECCION_A_TIPO.get(clave)
                continue

            # "### Nivel Region 9" / "### Logro documentado (...)" son agrupadores
            # dentro de Ecosistema, no fichas. La escala real sale del campo Escala.
            if tipo_actual == "Ecosistema IEEE" and nivel == 3:
                cerrar_ficha()
                continue

            if tipo_actual is None:
                cerrar_ficha()
                continue

            cerrar_ficha()
            ficha = {
                "titulo": limpiar_valor(titulo),
                "slug": slugify(titulo),
                "tipo": tipo_actual,
                "ponentes": [],
                "_enlaces_sub": [],
                "_enlaces_inline": "",
            }
            continue

        if ficha is None:
            continue

        bullet = RE_BULLET_LABEL.match(linea)
        if bullet:
            cerrar_label()
            label, valor = bullet.group(1), bullet.group(2)
            norm = normalizar_label(label)

            if norm.startswith("enlaces instagram"):
                ficha["_enlaces_inline"] = valor
                label_actual = label
                continue

            if norm in LABELS_PONENTES or RE_LABEL_PONENTES_PANEL.match(norm):
                rol = LABELS_PONENTES.get(norm, limpiar_valor(label))
                if valor.strip():
                    ficha["ponentes"].append(
                        {"nombre": limpiar_valor(valor), "rol": rol}
                    )
                label_actual = label
                continue

            campo = LABELS_SIMPLES.get(norm)
            if campo and valor.strip():
                ficha[campo] = limpiar_valor(valor)
            label_actual = label
            continue

        sub = RE_SUBITEM.match(linea)
        if sub and label_actual:
            subitems.append(sub.group(1))
            continue

        # Linea suelta sin etiqueta: es el fragmento colgado de la ficha
        # "Futuros Escritos" (perdio su label al editar). Se anexa a descripcion
        # en vez de descartarse, para no perder contenido real.
        if linea.strip() and not linea.startswith("#") and label_actual is None:
            if ficha.get("descripcion"):
                ficha["descripcion"] += " " + limpiar_valor(linea)

    cerrar_ficha()
    return [normalizar_ficha(f) for f in eventos]


def normalizar_ficha(f: dict) -> dict:
    """Aplica el modelo de datos final y las reglas de publicacion cruzada."""
    enlaces = extraer_enlaces(f.pop("_enlaces_sub", []), f.pop("_enlaces_inline", ""))
    fecha = parsear_fecha(f.get("fecha_texto", ""))
    organiza = parsear_organiza(f.get("organiza_texto", ""))
    resultado = f.get("resultado_texto", "")
    logro = f.get("logro_obtenido", "")

    # "no documentado en el scrapeo" / "pendiente de confirmar" NO son resultados
    # publicables: se tratan como ausencia de resultado para no inventar contenido.
    resultado_real = resultado
    if resultado:
        t = deacentuar(resultado).lower()
        if "no documentado" in t or "pendiente de confirmar" in t:
            resultado_real = ""

    evento = {
        "slug": f["slug"],
        "titulo": f["titulo"],
        "tipo": f["tipo"],
        "etiqueta": f.get("etiqueta", ""),
        "organiza": organiza,
        "organiza_texto": f.get("organiza_texto", ""),
        "escala": f.get("escala") or None,
        "grupo": parsear_grupo(f["titulo"], f.get("organiza_texto", "")),
        "fecha_texto": f.get("fecha_texto", ""),
        "fecha_orden": fecha["orden"],
        "anio": fecha["anio"],
        "fecha_precision": fecha["precision"],
        "modalidad": parsear_modalidad(f.get("ubicacion_texto", "")),
        "ubicacion_texto": f.get("ubicacion_texto", ""),
        # Todo el catalogo es historico; los proximos eventos se agregan a mano.
        "estado": "Pasado",
        "descripcion": f.get("descripcion", ""),
        "ponentes": f.get("ponentes", []),
        "premio": f.get("premio", ""),
        "resultado": resultado_real,
        "logro_obtenido": logro,
        "alcance": f.get("alcance", ""),
        "rol": f.get("rol", ""),
        "participantes": f.get("participantes", ""),
        "talleres_incluidos": f.get("talleres_incluidos", ""),
        "becas_aliados": f.get("becas_aliados", ""),
        "auspiciadores": f.get("auspiciadores", ""),
        "nota_interna": f.get("nota", ""),
        "enlaces": enlaces,
        "shortcodes": [e["shortcode"] for e in enlaces if e["valido"]],
        # Lo llena tools/build_media.py; se declara aqui para que el schema sea estable.
        "fotos": [],
    }

    # Reglas de publicacion cruzada (04-estructura-eventos.md): un registro,
    # varias vistas. Se resuelven UNA vez aqui, no en cada plantilla.
    evento["en_proyectos"] = bool(
        evento["tipo"] == "Competencia/Concurso" and evento["resultado"]
    )
    evento["en_logros"] = bool(evento["organiza"] != "IEEE UP" and evento["logro_obtenido"])
    return evento


def main() -> None:
    parser = argparse.ArgumentParser()
    parser.add_argument("--check", action="store_true", help="solo validar, no escribir")
    args = parser.parse_args()

    eventos = parsear()
    eventos.sort(key=lambda e: e["fecha_orden"], reverse=True)

    print(f"Fichas parseadas: {len(eventos)}")
    for tipo in ("Taller", "Visita", "Competencia/Concurso", "Ecosistema IEEE"):
        print(f"  {tipo:22} {sum(1 for e in eventos if e['tipo'] == tipo)}")

    total_enlaces = sum(len(e["enlaces"]) for e in eventos)
    rotos = [x["shortcode"] for e in eventos for x in e["enlaces"] if not x["valido"]]
    sin_fecha = [e["slug"] for e in eventos if e["fecha_precision"] == "desconocida"]
    print(f"  Enlaces Instagram      {total_enlaces} ({len(rotos)} con shortcode invalido)")
    print(f"  En Proyectos           {sum(1 for e in eventos if e['en_proyectos'])}")
    print(f"  En Logros/Trayectoria  {sum(1 for e in eventos if e['en_logros'])}")
    if sin_fecha:
        print(f"  SIN FECHA legible: {sin_fecha}")
    if rotos:
        print(f"  Shortcodes invalidos: {rotos}")

    if args.check:
        return

    OUT_YAML.parent.mkdir(parents=True, exist_ok=True)
    cabecera = (
        "# Generado por tools/parse_eventos.py desde\n"
        "# 02-ARQUITECTURA-WEB-IEEE-UP/05-raw-eventos.md\n"
        "#\n"
        "# A PARTIR DE AQUI ESTE ARCHIVO ES LA FUENTE DE VERDAD.\n"
        "# Editalo directamente para corregir datos o agregar eventos nuevos.\n"
        "# No vuelvas a correr el parser salvo que rehagas el catalogo desde cero\n"
        "# (sobreescribe todo y perderias las correcciones manuales).\n\n"
    )
    with OUT_YAML.open("w", encoding="utf-8") as fh:
        fh.write(cabecera)
        yaml.safe_dump(eventos, fh, allow_unicode=True, sort_keys=False, width=100)
    print(f"\nEscrito: {OUT_YAML}")


if __name__ == "__main__":
    main()
