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
        partes.append('<text x="%.1f" y="29" text-anchor="middle" class="eje" '
                      'font-size="8.5" fill="%s">%s</text>'
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
    labels = []
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
        labels.append((serie["pais"], ultimo_nivel, destacado, color))
    # etiquetas al final, agrupadas por nivel (de arriba abajo) y sin superposición
    labels.sort(key=lambda t: (-t[1], not t[2]))
    last_y = -1e9
    for nombre, nivel, destacado, color in labels:
        y = py(nivel) + 4
        if y < last_y + 14:
            y = last_y + 14
        last_y = y
        partes.append('<line x1="%d" y1="%.1f" x2="%d" y2="%.1f" stroke="%s" stroke-width="1"/>'
                      % (izq + plot_w, py(nivel), izq + plot_w + 6, y, color))
        partes.append('<text x="%d" y="%.1f" class="et" style="fill:%s%s">%s</text>'
                      % (izq + plot_w + 8, y, color,
                         ";font-weight:700" if destacado else "",
                         html.escape(nombre)))
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
    partes.append('<text x="10" y="18" class="nt">Ipsen (la empresa del bloqueador): cuánto vende en total</text>')
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
                  '<text x="%d" y="%d" class="et">todo el grupo Ipsen</text>'
                  % (izq + 10, 246, izq + 26, 250))
    partes.append('<rect x="%d" y="%d" width="11" height="3" fill="#c2410c"/>'
                  '<text x="%d" y="%d" class="nd">Decapeptyl (el bloqueador)</text>'
                  % (izq + 120, 246, izq + 136, 250))
    # ---- panel B: fracción del negocio total (barra apilada) ----
    partes.append('<text x="10" y="262" class="nt">El negocio completo (2025): qué fracción es este fármaco</text>')
    total = sum(m["valor"] for m in mercado)
    x0b, x1b = 54, 720
    ybar = 288
    cx = x0b
    for i, m in enumerate(mercado):
        w = m["valor"] / total * (x1b - x0b)
        destacado = m.get("destacado")
        color = "#c2410c" if destacado else ("#e2e8ef" if i % 2 == 0 else "#cbd5e1")
        partes.append('<rect x="%.1f" y="%d" width="%.1f" height="34" fill="%s" '
                      'stroke="%s" stroke-width="%s">'
                      '<title>%s: US$ %s M (%.0f%% del total) — %s</title></rect>'
                      % (cx, ybar, w, color, "#7c2d12" if destacado else "#b8c1cd",
                         "1.4" if destacado else "0.6",
                         html.escape(m["molecula"]), _fmt(m["valor"]),
                         m["valor"] / total * 100, html.escape(m["nota"])))
        if w > 55:
            partes.append('<text x="%.1f" y="%d" text-anchor="middle" class="et" '
                          'fill="%s">%.0f%%</text>'
                          % (cx + w / 2, ybar + 21, "#ffffff" if destacado else "#334155",
                             m["valor"] / total * 100))
        cx += w
    # leyenda con valores visibles
    ly = 342
    col = 0
    for m in mercado:
        cx2 = 12 + (col % 2) * 370
        yy = ly + (col // 2) * 16
        color = "#c2410c" if m.get("destacado") else "#94a3b8"
        partes.append('<rect x="%d" y="%d" width="10" height="10" fill="%s"/>' % (cx2, yy - 9, color))
        partes.append('<text x="%d" y="%d" class="%s">%s · US$ %s M (%.0f%%)</text>'
                      % (cx2 + 15, yy, "nd" if m.get("destacado") else "et",
                         html.escape(m["molecula"]), _fmt(m["valor"]), m["valor"] / total * 100))
        col += 1
    ly += 30
    partes.append('<text x="12" y="%d" class="eje">Decapeptyl (Ipsen, 543 M€) es la mayor parte del triptorelin. El uso como bloqueador en menores es una fracción aún menor, sin dato público.</text>' % ly)
    partes.append('<text x="12" y="%d" class="eje">%s</text>' % (ly + 16, html.escape(neg.get("fuente_mercado", ""))))
    partes.append("</svg>")
    return "".join(partes)


def svg_poblacion(caso):
    """Histograma poblacional compacto: muertes, superficies y la banda del caso (dentro, punteada)."""
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
    # capas: muertes + superficies + banda del caso (punteada)
    capas = []
    for i, m in enumerate(muertes):
        capas.append({
            "etiqueta": m["etiqueta"], "color": colores_muerte[i % 3],
            "desde": 0, "hasta": 95, "afectados": m["cantidad"],
            "min_h": 5.0, "anio": m.get("anio", ""), "sexo": m.get("sexo", ""),
        })
    capas += superficies
    if caso_banda:
        capas.append({
            "etiqueta": caso_banda.get("etiqueta", ""), "color": "#dc2626",
            "desde": caso_banda.get("desde"), "hasta": caso_banda.get("hasta"),
            "afectados": caso_banda.get("afectados", 0), "min_h": 6.0, "punteado": True,
        })
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
            if s.get("punteado"):
                fill, opac, stroke, sw = "url(#%s)" % pat_id, 1.0, "#dc2626", "1.0"
                titulo = s["etiqueta"]
            elif s.get("min_h") is not None:
                fill, opac, stroke, sw = color, 0.55, color, "0.4"
                sexo = (" — %s" % s.get("sexo")) if s.get("sexo") else ""
                titulo = "%s: %s por año (%s)%s" % (s["etiqueta"], _fmt(s["afectados"]), s.get("anio", ""), sexo)
            else:
                fill, opac, stroke, sw = color, 0.55, color, "0.4"
                titulo = "%s: %s personas (%.1f%% de su franja %d–%d)" % (
                    s.get("etiqueta", ""), _fmt(s.get("afectados", 0)), frac * 100, desde, hasta)
            if s.get("slug"):
                partes.append('<a href="/tema/%s">' % html.escape(s["slug"]))
            partes.append('<rect x="%.1f" y="%.1f" width="%.1f" height="%.1f" fill="%s" '
                          'opacity="%s" stroke="%s" stroke-width="%s">'
                          '<title>%s</title></rect>'
                          % (x, hy_base - acum - h, w, h, fill, opac, stroke, sw, html.escape(titulo)))
            if s.get("slug"):
                partes.append("</a>")
            acum += h
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
                      'opacity="0.28" stroke="%s" stroke-width="1.2">'
                      '<title>%s</title></rect>'
                      % (x - 70, y - 15, 140, 30, c, c,
                         html.escape("%s — %s" % (n, rol.get(n, "")))))
        partes.append('<text x="%.1f" y="%.1f" text-anchor="middle" class="%s">%s</text>'
                      % (x, y + 4, "nd" if tipo.get(n) == "promotora" else "et",
                         html.escape(corto(n))))
    partes.append("</svg>")
    return "".join(partes)


def svg_bio(persona):
    """Minigráfica compacta de la trayectoria."""
    hitos = persona.get("hitos") or []
    if not hitos:
        return ""
    nombre = persona.get("nombre", "")
    rol = persona.get("rol", "")
    profesion = persona.get("profesion", "")
    vinculaciones = persona.get("vinculaciones") or []
    nota = persona.get("nota", "")
    emoji = persona.get("emoji", "")
    resumen = "%s · %s. %s" % (rol, profesion, nota)
    for v in vinculaciones:
        resumen += "\n• %s: %s" % (v.get("tipo"), v.get("detalle"))
    xs = [h.get("x") for h in hitos if h.get("x") is not None]
    if not xs:
        return ""
    x0, x1 = min(xs) - 0.4, max(xs) + 0.4
    W, H = 760, 62
    izq, der, yline = 60, 20, 26
    partes = ['<svg viewBox="0 0 %d %d" class="bio-svg" role="img" '
              'aria-label="Trayectoria de %s">' % (W, H, html.escape(nombre))]
    partes.append('<text x="10" y="16" class="nt">%s %s <tspan class="suave" fill="#5d6877">· %s (%s)</tspan>'
                  '<title>%s</title></text>'
                  % (html.escape(emoji), html.escape(nombre), html.escape(rol), html.escape(profesion),
                     html.escape(resumen)))

    def px(x):
        return izq + (x - x0) / float(x1 - x0) * (W - izq - der)

    partes.append('<line x1="%d" y1="%d" x2="%d" y2="%d" stroke="#d6dbe3"/>'
                  % (izq, yline, W - der, yline))
    import math
    inicio = int(math.ceil(x0 / 5.0)) * 5
    for anio in range(inicio, int(math.floor(x1)) + 1, 5):
        x = px(anio)
        partes.append('<line x1="%.1f" y1="%d" x2="%.1f" y2="%d" stroke="#9aa4b2" stroke-width="1"/>'
                      % (x, yline, x, yline + 5))
        partes.append('<text x="%.1f" y="%d" text-anchor="middle" class="eje" '
                      'font-size="6">%d</text>'
                      % (x, yline + 14, anio))
    for i, h in enumerate(hitos):
        x = px(h["x"])
        y = yline - (4 + (i % 2) * 8)
        titulo = "%s: %s" % (h.get("anio", ""), h.get("hecho", ""))
        enlace = h.get("fuente") or "#"
        color = "#c2410c" if h.get("relevante") else "#9aa4b2"
        partes.append('<a href="%s" target="_blank" rel="noopener">'
                      '<circle cx="%.1f" cy="%.1f" r="3" fill="%s" stroke="#ffffff" '
                      'stroke-width="1.2"><title>%s</title></circle></a>'
                      % (html.escape(enlace), x, y, color, html.escape(titulo)))
        partes.append('<line x1="%.1f" y1="%.1f" x2="%.1f" y2="%d" stroke="%s"/>'
                      % (x, y + 3, x, yline, color))
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
