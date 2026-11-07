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


def _fmt(n):
    """1234 -> '1.234' (miles con punto)."""
    return format(int(round(n)), ",").replace(",", ".")


def _fmt_m(n):
    """Millones de euros: 1065.6 -> '1.065,6'."""
    s = ("%.1f" % n).replace(".", ",")
    ent, dec = s.split(",")
    ent = format(int(ent), ",").replace(",", ".")
    return ent + ("," + dec if dec != "0" else "")


def svg_negocio(caso):
    """Ventas de Ipsen desde 2005 y el mercado mundial de GnRH por molecula."""
    neg = caso.get("negocio") or {}
    historico = neg.get("historico") or []
    mercado = neg.get("mercado") or []
    if not historico and not mercado:
        return ""
    partes = ['<svg viewBox="0 0 760 470" class="negocio-svg" role="img" '
              'aria-label="Negocio de Ipsen y mercado mundial de GnRH">']
    # ---- panel A: serie desde 2005 ----
    partes.append('<text x="10" y="18" class="nt">Ventas del grupo Ipsen desde 2005 (millones de €)</text>')
    izq, der, y_top, y_base = 54, 720, 34, 212
    x0, x1, max_v = 2004, 2026, 3600.0

    def px(anio):
        return izq + (anio - x0) / float(x1 - x0) * (der - izq)

    def py(v):
        return y_base - v / max_v * (y_base - y_top)

    for nivel in (0, 1000, 2000, 3000):
        y = py(nivel)
        partes.append('<line x1="%d" y1="%.1f" x2="%d" y2="%.1f" stroke="#e6e9ee"/>' % (izq, y, der, y))
        partes.append('<text x="%d" y="%.1f" text-anchor="end" class="eje">%d</text>' % (izq - 8, y + 4, nivel))
    for anio in range(2004, 2026, 4):
        partes.append('<text x="%.1f" y="%d" text-anchor="middle" class="eje">%d</text>'
                      % (px(anio), y_base + 16, anio))
    total_pts = [h for h in historico if h.get("total")]
    deca_pts = [h for h in historico if h.get("deca")]
    partes.append('<polyline points="%s" fill="none" stroke="#9aa4b2" stroke-width="1.6" opacity="0.85"/>'
                  % " ".join("%.1f,%.1f" % (px(h["anio"]), py(h["total"])) for h in total_pts))
    partes.append('<polyline points="%s" fill="none" stroke="#c2410c" stroke-width="2.4"/>'
                  % " ".join("%.1f,%.1f" % (px(h["anio"]), py(h["deca"])) for h in deca_pts))
    for h in total_pts:
        t = "%d: grupo %s M€ — %s" % (h["anio"], _fmt_m(h["total"]), h.get("fuente", ""))
        partes.append('<circle cx="%.1f" cy="%.1f" r="3.4" fill="#ffffff" stroke="#9aa4b2" '
                      'stroke-width="1.6"><title>%s</title></circle>'
                      % (px(h["anio"]), py(h["total"]), html.escape(t)))
    for h in deca_pts:
        aprox = h.get("aprox")
        t = "Decapeptyl %d: %s M€%s — %s" % (h["anio"], _fmt_m(h["deca"]),
                                             " (estimación)" if aprox else "", h.get("fuente", ""))
        partes.append('<circle cx="%.1f" cy="%.1f" r="4" fill="#c2410c" stroke="#7c2d12" '
                      'stroke-width="1.2"><title>%s</title></circle>'
                      % (px(h["anio"]), py(h["deca"]), html.escape(t)))
        partes.append('<text x="%.1f" y="%.1f" class="nd">%s</text>'
                      % (px(h["anio"]) + 6, py(h["deca"]) - 4, ("≈" if aprox else "") + _fmt_m(h["deca"])))
    partes.append('<rect x="%d" y="%d" width="11" height="3" fill="#9aa4b2"/>'
                  '<text x="%d" y="%d" class="et">grupo (total)</text>'
                  % (izq + 10, 226, izq + 26, 230))
    partes.append('<rect x="%d" y="%d" width="11" height="3" fill="#c2410c"/>'
                  '<text x="%d" y="%d" class="nd">Decapeptyl (análogo GnRH)</text>'
                  % (izq + 120, 226, izq + 136, 230))
    # ---- panel B: mercado mundial de GnRH por molecula (2025) ----
    partes.append('<text x="10" y="262" class="nt">Mercado mundial de análogos de GnRH en 2025 (US$ millones)</text>')
    bx0, bmax = 150, 470.0
    max_m = max(m["valor"] for m in mercado)
    fila = 36
    for i, m in enumerate(mercado):
        ry = 286 + i * fila
        destacado = m.get("destacado")
        w = m["valor"] / max_m * bmax
        color = "#c2410c" if destacado else "#d3dae4"
        partes.append('<text x="12" y="%d" class="%s">%s</text>'
                      % (ry, "nd" if destacado else "et", html.escape(m["molecula"])))
        partes.append('<rect x="%d" y="%d" width="%.1f" height="18" rx="4" fill="%s" '
                      'stroke="%s" stroke-width="%s">'
                      '<title>%s — %s</title></rect>'
                      % (bx0, ry - 13, w, color,
                         "#7c2d12" if destacado else "#b8c1cd",
                         "1.4" if destacado else "0.6",
                         html.escape(m["molecula"]), html.escape(m["nota"])))
        partes.append('<text x="%.1f" y="%d" class="%s">US$ %s M</text>'
                      % (bx0 + w + 8, ry, "nd" if destacado else "et", _fmt(m["valor"])))
    partes.append('<text x="12" y="%d" class="eje">%s</text>'
                  % (286 + len(mercado) * fila + 8, html.escape(neg.get("fuente_mercado", ""))))
    partes.append("</svg>")
    return "".join(partes)


def svg_poblacion(caso):
    """Histograma poblacional por edad + superficies acumuladas + barras sin edad."""
    pop = caso.get("poblacion") or {}
    edades = pop.get("edades") or []
    if not edades:
        return ""
    superficies = pop.get("superficies") or []
    barras = sorted([b for b in (pop.get("barras") or [])],
                    key=lambda b: b.get("personas", 0) or 0, reverse=True)
    hx0, hx1 = 52, 716
    hy_top, hy_base = 40, 240
    ancho_anio = (hx1 - hx0) / 95.0
    max_c = max(c for _, c in edades)
    bar_h_max = hy_base - hy_top
    partes = []
    partes.append('<text x="10" y="20" class="nt">Población de Uruguay por edad (Censo 2023)</text>')
    for edad, cuenta in edades:
        x = hx0 + edad * ancho_anio
        w = 5 * ancho_anio
        h = bar_h_max * cuenta / max_c
        partes.append('<rect x="%.1f" y="%.1f" width="%.1f" height="%.1f" fill="#e3e9f0" '
                      'stroke="#b9c4d2" stroke-width="0.5">'
                      '<title>%d–%d años: %s personas</title></rect>'
                      % (x, hy_base - h, w, h, edad, edad + 4, _fmt(cuenta)))
    for s in superficies:
        desde, hasta = s.get("desde"), s.get("hasta")
        base = s.get("base") or sum(c for e, c in edades if desde <= e < hasta)
        frac = (s.get("afectados", 0) / base) if base else 0
        for edad, cuenta in edades:
            if not (desde <= edad < hasta):
                continue
            x = hx0 + edad * ancho_anio
            w = 5 * ancho_anio
            h = frac * (bar_h_max * cuenta / max_c)
            if h <= 0:
                continue
            titulo = "%s: %s personas (%.1f%% de %s personas de %d–%d años)" % (
                s.get("etiqueta", ""), _fmt(s.get("afectados", 0)), frac * 100,
                _fmt(base), desde, hasta)
            if s.get("slug"):
                partes.append('<a href="/tema/%s">' % html.escape(s["slug"]))
            partes.append('<rect x="%.1f" y="%.1f" width="%.1f" height="%.1f" '
                          'fill="#0e7490" opacity="0.55" stroke="#0e7490" stroke-width="0.5">'
                          '<title>%s</title></rect>' % (x, hy_base - h, w, h, html.escape(titulo)))
            if s.get("slug"):
                partes.append("</a>")
    for edad in (0, 20, 40, 60, 80, 90):
        x = hx0 + edad * ancho_anio
        partes.append('<text x="%.1f" y="%d" text-anchor="middle" class="eje">%d%s</text>'
                      % (x, hy_base + 16, edad, "+" if edad == 90 else ""))
    partes.append('<text x="10" y="%d" class="eje">años →</text>' % (hy_base + 16))
    ly = hy_base + 34
    for s in superficies:
        desde, hasta = s.get("desde"), s.get("hasta")
        base = s.get("base") or sum(c for e, c in edades if desde <= e < hasta)
        frac = (s.get("afectados", 0) / base) if base else 0
        partes.append('<rect x="10" y="%d" width="11" height="11" fill="#0e7490" opacity="0.55"/>'
                      % (ly - 10))
        partes.append('<text x="26" y="%d" class="et">%s: %s personas (%.1f%% de la franja %d–%d)</text>'
                      % (ly, html.escape(s.get("etiqueta", "")), _fmt(s.get("afectados", 0)),
                         frac * 100, desde, hasta))
        ly += 16
    by = hy_base + 54 + len(superficies) * 16
    partes.append('<text x="10" y="%d" class="nt">Problemas sin edad — personas afectadas</text>' % by)
    bx0, bmax = 210, 430.0
    max_p = max((b.get("personas", 0) or 0 for b in barras), default=1)
    row_h = 42
    for i, b in enumerate(barras):
        ry = by + 22 + i * row_h
        personas = b.get("personas", 0) or 0
        partes.append('<text x="16" y="%d" font-size="17">%s</text>'
                      % (ry, html.escape(b.get("emoji", "•"))))
        partes.append('<text x="48" y="%d" class="et">%s</text>'
                      % (ry, html.escape(b.get("etiqueta", ""))))
        partes.append('<line x1="%d" y1="%d" x2="%d" y2="%d" stroke="#c3cbd6"/>'
                      % (bx0 - 22, ry - 6, bx0, ry - 6))
        if personas > 0:
            w = personas / max_p * bmax
            if b.get("slug"):
                partes.append('<a href="/tema/%s">' % html.escape(b["slug"]))
            partes.append('<rect x="%d" y="%d" width="%.1f" height="15" rx="4" fill="#333d4b">'
                          '<title>%s</title></rect>' % (bx0, ry - 11, w, html.escape(b.get("nota", ""))))
            if b.get("slug"):
                partes.append("</a>")
            partes.append('<text x="%.1f" y="%d" class="et">%s personas</text>'
                          % (bx0 + w + 8, ry, _fmt(personas)))
        else:
            partes.append('<rect x="%d" y="%d" width="%d" height="15" rx="4" fill="none" '
                          'stroke="#b4534b" stroke-dasharray="4 3">'
                          '<title>%s</title></rect>'
                          % (bx0, ry - 11, 150, html.escape(b.get("nota", "Sin dato público."))))
            partes.append('<text x="%d" y="%d" class="et" style="fill:#b4534b">sin dato público</text>'
                          % (bx0 + 158, ry))
    H = by + 24 + len(barras) * row_h + 10
    return ('<svg viewBox="0 0 760 %d" class="poblacion-svg" role="img" '
            'aria-label="Población por edad y magnitud de problemas sociales">' % int(H)
            + "".join(partes) + "</svg>")


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
    if caso.get("negocio"):
        caso["negocio"]["nota_html"] = marcar(caso["negocio"].get("nota"), glosario)
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
