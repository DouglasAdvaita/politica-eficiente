"""Casos: un tema trabajado a fondo, con cadena causal y contexto.

Cada caso vive en datos/casos/<slug>.json y se muestra en capas: sintesis,
cadena causal, cronologia, intereses y datos faltantes.
"""
import html
import json
import os

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
    return caso


def svg_curvas(caso):
    """Grafica el nivel de acceso por pais y por anio, como indice 0-3."""
    curvas = caso.get("curvas") or {}
    series = curvas.get("series") or []
    if not series:
        return ""
    anios = [p[0] for s in series for p in s["puntos"]]
    x0, x1 = min(anios) - 1, max(anios) + 1
    W, H = 760, 300
    izq, der, arriba, abajo = 44, 20, 16, 42

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
    en_nivel = {}
    for serie in series:
        puntos = " ".join("%.1f,%.1f" % (px(a), py(n)) for a, n in serie["puntos"])
        destacado = serie.get("destacado")
        color = "#1a222d" if destacado else serie.get("color", "#9aa4b2")
        grosor = "2.8" if destacado else "1.6"
        guion = ' stroke-dasharray="5 4"' if serie.get("nota") else ""
        partes.append('<polyline points="%s" fill="none" stroke="%s" stroke-width="%s"%s/>'
                      % (puntos, color, grosor, guion))
        anio, nivel = serie["puntos"][-1]
        k = en_nivel.get(nivel, 0)
        en_nivel[nivel] = k + 1
        dy = 4 + k * 13
        partes.append('<text x="%.1f" y="%.1f" class="et">%s</text>'
                      % (px(anio) + 6, py(nivel) + dy, html.escape(serie["pais"])))
    partes.append("</svg>")
    return "".join(partes)


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
