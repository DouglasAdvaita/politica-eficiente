"""Casos: un tema trabajado a fondo, con cadena causal y contexto.

Cada caso vive en datos/casos/<slug>.json y se muestra en capas: sintesis,
cadena causal, cronologia, intereses y datos faltantes.
"""
import html
import json
import os
import re

BASE = os.path.dirname(os.path.abspath(__file__))
CARPETA = os.path.join(BASE, "datos", "casos")

CERTEZAS = {
    "probado": ("verde", "Probado con fuente"),
    "parcial": ("ambar", "Dato parcial"),
    "indicios": ("ambar", "Indicios, no prueba"),
    "hipotesis": ("azul", "Hipótesis"),
    "interpretacion": ("", "Interpretación"),
    "sin datos": ("", "Sin datos"),
    "sin_datos": ("", "Sin datos"),
}


def _ruta(slug):
    return os.path.join(CARPETA, slug + ".json")


def uno(slug):
    ruta = _ruta(slug)
    if not os.path.exists(ruta):
        return None
    with open(ruta, encoding="utf-8") as f:
        caso = json.load(f)
    caso["certeza_clase"], caso["certeza_texto"] = CERTEZAS.get(
        caso.get("certeza", ""), ("", caso.get("certeza", "")))
    for paso in caso.get("cadena", []):
        paso["clase"], paso["etiqueta"] = CERTEZAS.get(
            paso.get("certeza", ""), ("", paso.get("certeza", "")))
    for interes in caso.get("intereses", []):
        interes["clase"], interes["etiqueta"] = CERTEZAS.get(
            interes.get("certeza", ""), ("", interes.get("certeza", "")))
    return enriquecer(caso)


def marcar(texto, definiciones=None, limite=4):
    """Escapa el texto y explica hasta `limite` terminos con una ventana emergente."""
    if not texto:
        return ""
    definiciones = definiciones or {}
    salida = html.escape(str(texto))
    if not definiciones:
        return salida
    terminos = sorted(definiciones, key=len, reverse=True)
    patron = re.compile(
        r"(?<![\wáéíóúüñ])(" + "|".join(re.escape(t) for t in terminos) + r")(?![\wáéíóúüñ])",
        re.IGNORECASE)
    partes, ultimo, usados = [], 0, 0
    for m in patron.finditer(salida):
        if usados >= limite:
            break
        definicion = definiciones.get(m.group(1).lower()) or definiciones.get(m.group(1))
        if not definicion:
            continue
        partes.append(salida[ultimo:m.start()])
        partes.append('<span class="palabra" tabindex="0" data-tip="%s">%s</span>'
                      % (html.escape(definicion, quote=True), m.group(0)))
        ultimo = m.end()
        usados += 1
    partes.append(salida[ultimo:])
    return "".join(partes)


def svg_curvas(caso):
    """Grafica el nivel de acceso por pais y por anio, con un punto por cambio de norma."""
    curvas = caso.get("curvas") or {}
    series = curvas.get("series") or []
    if not series:
        return ""
    anios = [p["anio"] for s in series for p in s["puntos"]]
    x0, x1 = min(anios) - 1, max(anios) + 1
    W, H = 760, 330
    izq, der, arriba, abajo = 44, 96, 18, 44

    def px(anio):
        return izq + (anio - x0) / (x1 - x0) * (W - izq - der)

    def py(nivel):
        return H - abajo - nivel / 3 * (H - arriba - abajo)

    partes = ['<svg viewBox="0 0 %d %d" class="curvas-svg" role="img" '
              'aria-label="Nivel de acceso a bloqueadores por pais y anio">' % (W, H)]
    for nivel in range(4):
        y = py(nivel)
        partes.append('<line x1="%d" y1="%.1f" x2="%d" y2="%.1f" stroke="#e6e9ee"/>'
                      % (izq, y, W - der, y))
        partes.append('<text x="%d" y="%.1f" text-anchor="end" class="eje">%d</text>'
                      % (izq - 8, y + 4, nivel))
    for anio in range(x0, x1 + 1, 2):
        partes.append('<text x="%.1f" y="%d" text-anchor="middle" class="eje">%d</text>'
                      % (px(anio), H - abajo + 18, anio))
    for serie in series:
        destacado = serie.get("destacado")
        color = "#1a222d" if destacado else serie.get("color", "#9aa4b2")
        grosor = "2.6" if destacado else "1.5"
        puntos = " ".join("%.1f,%.1f" % (px(p["anio"]), py(p["nivel"]))
                          for p in serie["puntos"])
        partes.append('<polyline points="%s" fill="none" stroke="%s" stroke-width="%s" '
                      'opacity="%s"/>' % (puntos, color, grosor, "1" if destacado else ".85"))
        for p in serie["puntos"]:
            titulo = "%s · %s: %s" % (p["anio"], serie["pais"], p.get("hecho", ""))
            enlace = p.get("fuente") or "#"
            radio = 4.5 if destacado else 3.5
            partes.append('<a href="%s" target="_blank" rel="noopener">'
                          '<circle cx="%.1f" cy="%.1f" r="%s" fill="#ffffff" stroke="%s" '
                          'stroke-width="2"><title>%s</title></circle></a>'
                          % (html.escape(enlace), px(p["anio"]), py(p["nivel"]), radio, color,
                             html.escape(titulo)))
        ultimo = serie["puntos"][-1]
        partes.append('<text x="%.1f" y="%.1f" class="et">%s</text>'
                      % (px(ultimo["anio"]) + 8, py(ultimo["nivel"]) + 4,
                         html.escape(serie["pais"])))
    partes.append("</svg>")
    return "".join(partes)


def svg_necesidades(caso):
    """Barras horizontales (escala log) con la magnitud de cada problema."""
    datos = caso.get("donde_encaja") or {}
    filas = datos.get("prioridades") or []
    if not filas:
        return ""
    import math
    tope = max(f["poblacion"] for f in filas)
    W, alto_fila = 760, 38
    H = alto_fila * (len(filas) + 1) + 20
    etiqueta, barra_ini, barra_fin = 210, 220, 620
    partes = ['<svg viewBox="0 0 %d %d" class="necesidades-svg" role="img" '
              'aria-label="Magnitud de distintos problemas sociales">' % (W, H)]
    for i, f in enumerate(filas):
        y = 12 + i * alto_fila
        ancho = (math.log10(max(f["poblacion"], 1)) / math.log10(tope)) * (barra_fin - barra_ini)
        partes.append('<a href="/tema/%s">' % html.escape(f["slug"]))
        partes.append('<text x="0" y="%d" class="et">%s</text>' % (y + 14, html.escape(f["tema"])))
        partes.append('<rect x="%d" y="%d" width="%.1f" height="14" rx="3" fill="#333d4b"/>'
                      % (barra_ini, y + 3, ancho))
        partes.append('<text x="%.1f" y="%d" class="eje">%s %s</text>'
                      % (barra_ini + ancho + 8, y + 14, format(f["poblacion"], ",").replace(",", "."),
                         html.escape(f.get("unidad", ""))))
        partes.append('<title>%s: %s %s</title></a>'
                      % (html.escape(f["tema"]), format(f["poblacion"], ",").replace(",", "."),
                         html.escape(f.get("unidad", ""))))
    caso_fila = datos.get("caso") or {}
    y = 12 + len(filas) * alto_fila
    partes.append('<text x="0" y="%d" class="et">%s</text>'
                  % (y + 14, html.escape(caso_fila.get("nota", "Este caso"))))
    partes.append('<rect x="%d" y="%d" width="%d" height="14" rx="3" fill="none" '
                  'stroke="#b4534b" stroke-dasharray="4 3"/>' % (barra_ini, y + 3, 120))
    partes.append('<text x="%d" y="%d" class="eje" style="fill:#b4534b">sin dato público</text>'
                  % (barra_ini + 128, y + 14))
    partes.append("</svg>")
    return "".join(partes)


def enriquecer(caso):
    """Aplica el glosario del caso a los textos que se muestran."""
    glosario = {k.lower(): v for k, v in (caso.get("glosario") or {}).items()}
    campos = ("sintesis", "mecanismo", "costo_duda", "carga_prueba", "cierre")
    for campo in campos:
        if caso.get(campo):
            caso[campo + "_html"] = marcar(caso[campo], glosario)
    for paso in caso.get("cadena", []):
        paso["texto_html"] = marcar(paso.get("texto"), glosario)
    for interes in caso.get("intereses", []):
        interes["interes_html"] = marcar(interes.get("interes"), glosario, limite=2)
        interes["nota_html"] = marcar(interes.get("nota"), glosario, limite=1)
    for h in caso.get("cronologia", []):
        h["hecho_html"] = marcar(h.get("hecho"), glosario, limite=1)
    if caso.get("patron"):
        caso["patron"]["observado_html"] = marcar(caso["patron"].get("observado"), glosario, 2)
        caso["patron"]["no_probado_html"] = marcar(caso["patron"].get("no_probado"), glosario, 1)
    return caso


def todos():
    if not os.path.isdir(CARPETA):
        return []
    salida = []
    for nombre in sorted(os.listdir(CARPETA)):
        if nombre.endswith(".json"):
            caso = uno(nombre[:-5])
            if caso:
                salida.append(caso)
    return salida
