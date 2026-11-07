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

BASES = {
    "fuente": ("", "Con fuente"),
    "causalidad": ("", "Causalidad inferida"),
    "opinion": ("", "Opinión / lectura"),
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
        paso["base_clase"], paso["base_etiqueta"] = BASES.get(
            paso.get("base", ""), ("", ""))
    for interes in caso.get("intereses", []):
        interes["clase"], interes["etiqueta"] = CERTEZAS.get(
            interes.get("certeza", ""), ("", interes.get("certeza", "")))
        interes["base_clase"], interes["base_etiqueta"] = BASES.get(
            interes.get("base", ""), ("", ""))
    if caso.get("patron"):
        caso["patron"]["obs_base_clase"], caso["patron"]["obs_base_etiqueta"] = BASES.get(
            caso["patron"].get("base_observado", ""), ("", ""))
        caso["patron"]["nop_base_clase"], caso["patron"]["nop_base_etiqueta"] = BASES.get(
            caso["patron"].get("base_no_probado", ""), ("", ""))
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
    """Evolucion del acceso por pais y anio, con etapas evolutivas (estilo serie temporal)."""
    curvas = caso.get("curvas") or {}
    series = curvas.get("series") or []
    if not series:
        return ""
    etapas = curvas.get("etapas") or []
    anios = [p["anio"] for s in series for p in s["puntos"]]
    x0, x1 = min(anios) - 1, max(anios) + 1
    W, H = 780, 440
    izq, der = 46, 158
    y_top, y_base = 64, 376
    plot_w = W - izq - der

    def px(anio):
        return izq + (anio - x0) / float(x1 - x0) * plot_w

    def py(nivel):
        return y_base - nivel / 3.0 * (y_base - y_top)

    def _parse_periodo(txt):
        try:
            a, b = txt.split("-")
            return int(a), int(b)
        except Exception:
            return x0, x1

    colores_etapa = ["#e8edf3", "#c9d4e2", "#a3b3c6", "#7c8da3", "#d9a441", "#b4534b"]
    partes = ['<svg viewBox="0 0 %d %d" class="curvas-svg" role="img" '
              'aria-label="Evolución del acceso a bloqueadores por país y año">' % (W, H)]
    # ---- banda de etapas ----
    for i, et in enumerate(etapas):
        a, b = _parse_periodo(et["periodo"])
        xa, xb = px(a), px(b)
        color = colores_etapa[i % len(colores_etapa)]
        partes.append('<rect x="%.1f" y="12" width="%.1f" height="26" fill="%s">'
                      '<title>%s: %s</title></rect>'
                      % (xa, max(xb - xa, 2), color,
                         html.escape(et["periodo"]), html.escape(et.get("descripcion", ""))))
        partes.append('<text x="%.1f" y="30" text-anchor="middle" class="eje" '
                      'fill="%s">%s</text>'
                      % ((xa + xb) / 2, "#334155" if i < 4 else "#ffffff",
                         html.escape(et.get("etiqueta", ""))))
    # ---- rejilla y eje ----
    for nivel in range(4):
        y = py(nivel)
        partes.append('<line x1="%d" y1="%.1f" x2="%d" y2="%.1f" stroke="#e6e9ee"/>'
                      % (izq, y, izq + plot_w, y))
        partes.append('<text x="%d" y="%.1f" text-anchor="end" class="eje">%d</text>'
                      % (izq - 8, y + 4, nivel))
    for anio in range(1985, 2027, 5):
        partes.append('<text x="%.1f" y="%d" text-anchor="middle" class="eje">%d</text>'
                      % (px(anio), y_base + 16, anio))
    # ---- series (escalonadas) ----
    en_nivel = {}
    for serie in series:
        destacado = serie.get("destacado")
        puntos = serie["puntos"]
        ultimo_nivel = puntos[-1]["nivel"]
        if destacado:
            color, grosor, opac = "#1a222d", 2.6, 1.0
        elif ultimo_nivel <= 1:
            color, grosor, opac = "#b4534b", 1.5, 0.9
        elif ultimo_nivel == 2:
            color, grosor, opac = "#c9942f", 1.5, 0.9
        else:
            color, grosor, opac = "#7a8a9d", 1.3, 0.8
        # trazo escalonado hasta el borde derecho
        paso = []
        for i, p in enumerate(puntos):
            if i == 0:
                paso.append((px(p["anio"]), py(p["nivel"])))
            else:
                paso.append((px(p["anio"]), py(puntos[i - 1]["nivel"])))
                paso.append((px(p["anio"]), py(p["nivel"])))
        paso.append((izq + plot_w, py(puntos[-1]["nivel"])))
        partes.append('<polyline points="%s" fill="none" stroke="%s" stroke-width="%s" '
                      'opacity="%s"/>' % (" ".join("%.1f,%.1f" % (a, b) for a, b in paso),
                                          color, grosor, opac))
        for p in puntos:
            titulo = "%s · %s: %s" % (p["anio"], serie["pais"], p.get("hecho", ""))
            enlace = p.get("fuente") or "#"
            radio = 4.2 if destacado else 3.0
            partes.append('<a href="%s" target="_blank" rel="noopener">'
                          '<circle cx="%.1f" cy="%.1f" r="%s" fill="#ffffff" stroke="%s" '
                          'stroke-width="1.8"><title>%s</title></circle></a>'
                          % (html.escape(enlace), px(p["anio"]), py(p["nivel"]), radio, color,
                             html.escape(titulo)))
        # etiqueta al final
        k = en_nivel.get(ultimo_nivel, 0)
        en_nivel[ultimo_nivel] = k + 1
        ly = py(ultimo_nivel) + 4 + (k % 4) * 11
        partes.append('<text x="%d" y="%.1f" class="%s">%s</text>'
                      % (izq + plot_w + 8, ly, "nd" if destacado else "et",
                         html.escape(serie["pais"])))
    partes.append('<text x="%d" y="%d" class="eje">0 prohibido · 1 investigación · 2 cautela · 3 guía clínica</text>'
                  % (izq, y_base + 34))
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
    """Histograma poblacional compacto: muertes y superficies apiladas, banda del caso punteada."""
    pop = caso.get("poblacion") or {}
    edades = pop.get("edades") or []
    if not edades:
        return ""
    superficies = pop.get("superficies") or []
    muertes = pop.get("muertes") or []
    caso_banda = pop.get("caso_banda") or {}
    hx0, hx1 = 52, 716
    hy_top, hy_base = 20, 130
    ancho_anio = (hx1 - hx0) / 95.0
    max_c = max(c for _, c in edades)
    bar_h_max = hy_base - hy_top
    pat_id = "pt-%s" % (caso.get("slug", "x"))
    colores_muerte = ["#991b1b", "#b4530a", "#3f2d20"]
    # capas: muertes (con mínimo de altura) + superficies
    capas = []
    for i, m in enumerate(muertes):
        capas.append({
            "etiqueta": m["etiqueta"], "corto": "%s %s" % (m.get("emoji", "•"), m["etiqueta"]),
            "color": colores_muerte[i % 3], "desde": 0, "hasta": 95,
            "afectados": m["cantidad"], "min_h": 5.0, "anio": m.get("anio", ""),
            "sexo": m.get("sexo", ""),
        })
    capas += superficies
    partes = ['<svg viewBox="0 0 760 160" class="poblacion-svg" role="img" '
              'aria-label="Población de Uruguay por edad y problemas sociales">']
    partes.append('<pattern id="%s" width="5" height="5" patternUnits="userSpaceOnUse">'
                  '<circle cx="2.5" cy="2.5" r="1.1" fill="#dc2626"/></pattern>' % pat_id)
    # ---- histograma ----
    for edad, cuenta in edades:
        x = hx0 + edad * ancho_anio
        w = 5 * ancho_anio
        h = bar_h_max * cuenta / max_c
        partes.append('<rect x="%.1f" y="%.1f" width="%.1f" height="%.1f" fill="#e3e9f0" '
                      'stroke="#b9c4d2" stroke-width="0.5">'
                      '<title>%d–%d años: %s personas</title></rect>'
                      % (x, hy_base - h, w, h, edad, edad + 4, _fmt(cuenta)))
    # ---- capas apiladas desde la base ----
    for edad, cuenta in edades:
        x = hx0 + edad * ancho_anio
        w = 5 * ancho_anio
        bar_h = bar_h_max * cuenta / max_c
        acum = 0.0
        for s in capas:
            desde, hasta = s.get("desde"), s.get("hasta")
            if not (desde <= edad < hasta):
                continue
            base = s.get("base") or sum(c for e, c in edades if desde <= e < hasta)
            frac = (s.get("afectados", 0) / base) if base else 0
            h = frac * bar_h
            if s.get("min_h") is not None:
                h = max(h, s["min_h"])
            if h <= 0:
                continue
            color = s.get("color", "#0e7490")
            if s.get("min_h") is not None:
                sexo = (" — %s" % s.get("sexo")) if s.get("sexo") else ""
                titulo = "%s: %s por año (%s)%s" % (s["etiqueta"], _fmt(s["afectados"]), s.get("anio", ""), sexo)
            else:
                titulo = "%s: %s personas (%.1f%% de su franja %d–%d)" % (
                    s.get("etiqueta", ""), _fmt(s.get("afectados", 0)), frac * 100, desde, hasta)
            if s.get("slug"):
                partes.append('<a href="/tema/%s">' % html.escape(s["slug"]))
            partes.append('<rect x="%.1f" y="%.1f" width="%.1f" height="%.1f" fill="%s" '
                          'opacity="0.55" stroke="%s" stroke-width="0.4">'
                          '<title>%s</title></rect>'
                          % (x, hy_base - acum - h, w, h, color, color, html.escape(titulo)))
            if s.get("slug"):
                partes.append("</a>")
            acum += h
    # ---- banda del caso (punteada, en su edad) ----
    if caso_banda:
        desde, hasta = caso_banda.get("desde"), caso_banda.get("hasta")
        min_h = 6.0
        xb = hx0 + desde * ancho_anio
        wb = (hasta - desde) * ancho_anio
        partes.append('<rect x="%.1f" y="%.1f" width="%.1f" height="%.1f" fill="url(#%s)" '
                      'stroke="#dc2626" stroke-width="1">'
                      '<title>%s</title></rect>'
                      % (xb, hy_base - min_h, wb, min_h, pat_id,
                         html.escape(caso_banda.get("etiqueta", ""))))
    # ---- eje ----
    for edad in (0, 20, 40, 60, 80, 90):
        x = hx0 + edad * ancho_anio
        partes.append('<text x="%.1f" y="%d" text-anchor="middle" class="eje">%d%s</text>'
                      % (x, hy_base + 16, edad, "+" if edad == 90 else ""))
    partes.append("</svg>")
    return "".join(partes)


def svg_vinculos(caso):
    """Grafo de organismos y sus vínculos (quién financia/cita a quién)."""
    v = caso.get("vinculos") or {}
    organismos = v.get("organismos") or []
    vinculos = v.get("vinculos") or []
    if not organismos and not vinculos:
        return ""
    import math
    tipo = {o["nombre"]: o.get("tipo", "") for o in organismos}
    rol = {o["nombre"]: o.get("rol", "") for o in organismos}
    colores = {"promotora": "#b4534b", "profesional": "#64748b", "critica": "#0e7490"}
    abrevia = {"Erickson Educational Foundation": "Erickson Foundation",
               "Cass Review / BMJ": "Cass / BMJ"}

    def corto(nombre):
        return abrevia.get(nombre, nombre)

    def color(nombre):
        return colores.get(tipo.get(nombre, ""), "#94a3b8")

    # nodos únicos (dividiendo destinos compuestos con " y ")
    nodos = [o["nombre"] for o in organismos]
    for lk in vinculos:
        for n in (lk["origen"], lk["destino"]):
            for parte in n.split(" y "):
                if parte not in nodos:
                    nodos.append(parte)
    cx, cy, radio = 400, 200, 175
    pos = {}
    for i, n in enumerate(nodos):
        ang = -math.pi / 2 + 2 * math.pi * i / len(nodos)
        pos[n] = (cx + radio * math.cos(ang), cy + radio * math.sin(ang))
    partes = ['<svg viewBox="0 0 800 400" class="vinculos-svg" role="img" '
              'aria-label="Vínculos entre organismos">']
    # aristas
    for lk in vinculos:
        for destino in lk["destino"].split(" y "):
            if lk["origen"] in pos and destino in pos:
                xa, ya = pos[lk["origen"]]
                xb, yb = pos[destino]
                mx, my = (xa + xb) / 2, (ya + yb) / 2
                estilo = "stroke-dasharray=\"4 3\"" if lk.get("disputado") else ""
                partes.append('<line x1="%.1f" y1="%.1f" x2="%.1f" y2="%.1f" stroke="#c3cbd6" '
                              'stroke-width="1.2" %s>'
                              '<title>%s → %s (%s): %s</title></line>'
                              % (xa, ya, xb, yb, estilo, html.escape(lk["origen"]),
                                 html.escape(destino), html.escape(lk["tipo"]),
                                 html.escape(lk["evidencia"])))
                partes.append('<text x="%.1f" y="%.1f" text-anchor="middle" class="eje">%s</text>'
                              % (mx, my - 3, html.escape(lk["tipo"])))
    # nodos
    for n in nodos:
        x, y = pos[n]
        c = color(n)
        partes.append('<rect x="%.1f" y="%.1f" width="%d" height="%d" rx="7" fill="%s" '
                      'opacity="0.14" stroke="%s" stroke-width="1.2">'
                      '<title>%s</title></rect>'
                      % (x - 70, y - 15, 140, 30, c, c,
                         html.escape("%s — %s" % (n, rol.get(n, "")))))
        partes.append('<text x="%.1f" y="%.1f" text-anchor="middle" class="%s">%s</text>'
                      % (x, y + 4, "nd" if tipo.get(n) == "promotora" else "et",
                         html.escape(corto(n))))
    partes.append("</svg>")
    return "".join(partes)


def svg_bio(persona):
    """Minigráfica de la trayectoria de una persona: años con puntos y popups."""
    hitos = persona.get("hitos") or []
    if not hitos:
        return ""
    nombre = persona.get("nombre", "")
    rol = persona.get("rol", "")
    profesion = persona.get("profesion", "")
    vinculaciones = persona.get("vinculaciones") or []
    nota = persona.get("nota", "")
    resumen = "%s · %s. %s" % (rol, profesion, nota)
    for v in vinculaciones:
        resumen += "\n• %s: %s" % (v.get("tipo"), v.get("detalle"))
    xs = [h.get("x") for h in hitos if h.get("x") is not None]
    if not xs:
        return ""
    x0, x1 = min(xs) - 0.4, max(xs) + 0.4
    W, H = 760, 84
    izq, der, yline = 90, 30, 40
    partes = ['<svg viewBox="0 0 %d %d" class="bio-svg" role="img" '
              'aria-label="Trayectoria de %s">' % (W, H, html.escape(nombre))]
    partes.append('<text x="10" y="20" class="nt">%s <tspan class="suave" fill="#5d6877">· %s (%s)</tspan>'
                  '<title>%s</title></text>'
                  % (html.escape(nombre), html.escape(rol), html.escape(profesion),
                     html.escape(resumen)))

    def px(x):
        return izq + (x - x0) / float(x1 - x0) * (W - izq - der)

    partes.append('<line x1="%d" y1="%d" x2="%d" y2="%d" stroke="#d6dbe3"/>'
                  % (izq, yline, W - der, yline))
    import math
    rango = x1 - x0
    paso = 1
    for p in (1, 2, 5, 10, 20, 50):
        if rango / p <= 6:
            paso = p
            break
    inicio = int(math.ceil(x0 / paso)) * paso
    for anio in range(inicio, int(math.floor(x1)) + 1, paso):
        partes.append('<text x="%.1f" y="%d" text-anchor="middle" class="eje">%d</text>'
                      % (px(anio), yline + 20, anio))
    # puntos (de abajo hacia arriba, alternando altura para evitar superposición)
    for i, h in enumerate(hitos):
        x = px(h["x"])
        y = yline - (6 + (i % 3) * 12)
        titulo = "%s: %s" % (h.get("anio", ""), h.get("hecho", ""))
        enlace = h.get("fuente") or "#"
        partes.append('<a href="%s" target="_blank" rel="noopener">'
                      '<circle cx="%.1f" cy="%.1f" r="4" fill="#1a222d" stroke="#ffffff" '
                      'stroke-width="1.5"><title>%s</title></circle></a>'
                      % (html.escape(enlace), x, y, html.escape(titulo)))
        partes.append('<line x1="%.1f" y1="%.1f" x2="%.1f" y2="%d" stroke="#c3cbd6"/>'
                      % (x, y + 4, x, yline))
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
