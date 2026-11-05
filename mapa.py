"""Mapa de lineas: ciudadania, temas y cargos publicos en un solo SVG.

La idea es que se vea de un vistazo que le preocupa a la gente, que hacen
los cargos y donde se cruzan o se ignoran.
"""
import html
import math
from collections import defaultdict

import gamificacion

ANCHO = 1440
X_TEMAS = 20
ANCHO_TEMA = 372
X_POL = 900
ANCHO_POL = 124
GAP_POL = 8
Y0 = 96
PASO = 36
ALTO_CAJA = 30

COLOR_CAMARA = {
    "Senadores": "#2a3f6b",
    "Diputados": "#243a5e",
    "Poder Ejecutivo": "#3a2a5e",
    "Intendencias": "#1f4a45",
    "Organismos": "#4a3a22",
}


def esc(texto):
    return html.escape(str(texto if texto is not None else ""))


def recortar(texto, n):
    texto = " ".join(str(texto or "").split())
    return texto if len(texto) <= n else texto[: n - 1].rstrip() + "…"


def datos(db, camara="todas", categoria="todas"):
    where, params = [], []
    if categoria != "todas":
        where.append("t.categoria = ?")
        params.append(categoria)
    filtro = ("WHERE " + " AND ".join(where)) if where else ""
    temas = db.todos(
        f"""SELECT t.*,
              (SELECT COUNT(*) FROM votos v WHERE v.tema_id = t.id AND v.valor = 1) AS a_favor,
              (SELECT COUNT(*) FROM votos v WHERE v.tema_id = t.id AND v.valor = -1) AS en_contra,
              (SELECT COUNT(*) FROM opiniones o WHERE o.tema_id = t.id) AS opiniones
            FROM temas t {filtro}
            ORDER BY a_favor DESC,
                     CASE t.urgencia WHEN 'alta' THEN 0 WHEN 'media' THEN 1 ELSE 2 END,
                     t.titulo
            LIMIT 20""",
        tuple(params),
    )
    where_p, params_p = [], []
    if camara != "todas":
        where_p.append("camara = ?")
        params_p.append(camara)
    filtro_p = ("WHERE " + " AND ".join(where_p)) if where_p else ""
    politicos = db.todos(
        f"""SELECT * FROM politicos {filtro_p}
            ORDER BY CASE camara WHEN 'Poder Ejecutivo' THEN 0 WHEN 'Senadores' THEN 1
                     WHEN 'Diputados' THEN 2 WHEN 'Intendencias' THEN 3 ELSE 4 END,
                     nombre
            LIMIT 28""",
        tuple(params_p),
    )
    ids_temas = [t["id"] for t in temas]
    ids_pol = [p["id"] for p in politicos]

    posiciones = {}
    acciones = {}
    if ids_temas and ids_pol:
        marcas = ",".join("?" * len(ids_temas))
        marcas_p = ",".join("?" * len(ids_pol))
        for fila in db.todos(
            f"""SELECT politico_id, tema_id, valor FROM posiciones
                WHERE tema_id IN ({marcas}) AND politico_id IN ({marcas_p})""",
            tuple(ids_temas) + tuple(ids_pol),
        ):
            posiciones[(fila["politico_id"], fila["tema_id"])] = fila["valor"]
        for fila in db.todos(
            f"""SELECT politico_id, tema_categoria, COUNT(*) AS n FROM acciones
                WHERE politico_id IN ({marcas_p}) AND tema_categoria != ''
                GROUP BY politico_id, tema_categoria""",
            tuple(ids_pol),
        ):
            acciones[(fila["politico_id"], fila["tema_categoria"])] = fila["n"]

    usuarios = db.todos(
        """SELECT u.id, u.puntos, u.intereses,
                  (SELECT COUNT(*) FROM actividad a WHERE a.usuario_id = u.id) AS acciones
           FROM usuarios u WHERE u.rol != 'admin'"""
    )
    votos = db.todos("SELECT usuario_id, tema_id FROM votos WHERE valor = 1")
    voto_de = defaultdict(set)
    for v in votos:
        voto_de[v["usuario_id"]].add(v["tema_id"])

    grupos = {}
    apoyo = defaultdict(int)
    total_grupo = defaultdict(int)
    for u in usuarios:
        clave = gamificacion.grupo(u["puntos"], u["acciones"], u["intereses"] or "")
        grupos.setdefault(clave, gamificacion.datos_grupo(clave))
        total_grupo[clave] += 1
        for tema_id in voto_de[u["id"]]:
            apoyo[(clave, tema_id)] += 1

    return {
        "temas": temas,
        "politicos": politicos,
        "posiciones": posiciones,
        "acciones": acciones,
        "grupos": [grupos[k] for k in [g[0] for g in gamificacion.GRUPOS] if k in grupos],
        "apoyo": apoyo,
        "total_grupo": total_grupo,
        "usuarios_total": len(usuarios),
        "camara": camara,
        "categoria": categoria,
    }


def _curva(x1, y1, x2, y2):
    medio = (x2 - x1) / 2
    return f"M {x1:.1f} {y1:.1f} C {x1 + medio:.1f} {y1:.1f} {x2 - medio:.1f} {y2:.1f} {x2:.1f} {y2:.1f}"


def _categoria_fuerte(d, politico_id):
    """Categoria donde el cargo tiene mas actividad declarada."""
    pares = [
        (cat, n)
        for (pid, cat), n in d["acciones"].items()
        if pid == politico_id
    ]
    return max(pares, key=lambda x: x[1])[0] if pares else None


def svg(d):
    temas = d["temas"]
    politicos = d["politicos"]
    grupos = d["grupos"]
    filas_pol = max(1, math.ceil(len(politicos) / 4))
    alto_cuerpo = max(len(temas), filas_pol) * PASO
    y_usuarios = Y0 + alto_cuerpo + 42
    altura = y_usuarios + 86

    piezas = [
        f'<svg viewBox="0 0 {ANCHO} {altura}" role="img" aria-label="Mapa de temas, cargos y ciudadanía" '
        f'xmlns="http://www.w3.org/2000/svg" class="mapa-svg">',
        """<defs>
        <linearGradient id="fondo" x1="0" y1="0" x2="0" y2="1">
          <stop offset="0%" stop-color="#0a1224"/><stop offset="100%" stop-color="#070c18"/>
        </linearGradient>
        </defs>""",
        f'<rect width="{ANCHO}" height="{altura}" fill="url(#fondo)"/>',
        f'<text x="{X_TEMAS}" y="50" fill="#8fb8ff" font-size="14" font-weight="700" letter-spacing="1.5">TEMAS QUE PREOCUPAN</text>',
        f'<text x="{X_POL}" y="50" fill="#ffb4d1" font-size="14" font-weight="700" letter-spacing="1.5">CARGOS PÚBLICOS</text>',
    ]

    pos_y = {}
    for i, t in enumerate(temas):
        y = Y0 + i * PASO
        pos_y[t["id"]] = y
        favor = t["a_favor"] or 0
        contra = t["en_contra"] or 0
        total = max(1, favor + contra)
        ancho_apoyo = int((ANCHO_TEMA - 12) * favor / total)
        piezas.append(
            f'<g class="nodo tema" data-tema="{t["id"]}">'
            f'<title>{esc(t["titulo"])} · {favor} a favor, {contra} en contra, {t["opiniones"]} opiniones</title>'
            f'<rect x="{X_TEMAS}" y="{y}" width="{ANCHO_TEMA}" height="{ALTO_CAJA}" rx="8" fill="#12203a" stroke="#2b4a7a"/>'
            f'<rect x="{X_TEMAS + 6}" y="{y + 24}" width="{ancho_apoyo}" height="3" rx="1.5" fill="#39ff88" opacity="0.8"/>'
            f'<text x="{X_TEMAS + 11}" y="{y + 20}" font-size="13">{esc(t["emoji"])}</text>'
            f'<text x="{X_TEMAS + 33}" y="{y + 20}" fill="#e8f1ff" font-size="11.5">{esc(recortar(t["titulo"], 46))}</text>'
            f'</g>'
        )

    pos_pol = {}
    for i, p in enumerate(politicos):
        col = i % 4
        fila = i // 4
        x = X_POL + col * (ANCHO_POL + GAP_POL)
        y = Y0 + fila * PASO
        pos_pol[p["id"]] = (x, y)
        fondo = COLOR_CAMARA.get(p["camara"], "#243a5e")
        piezas.append(
            f'<g class="nodo politico" data-pol="{p["id"]}">'
            f'<title>{esc(p["nombre"])} · {esc(p["cargo"])} · {esc(p["organismo"])}</title>'
            f'<rect x="{x}" y="{y}" width="{ANCHO_POL}" height="{ALTO_CAJA}" rx="7" fill="{fondo}" stroke="#3f5d94"/>'
            f'<text x="{x + 6}" y="{y + 20}" font-size="11">{esc(p["emoji"])}</text>'
            f'<text x="{x + 21}" y="{y + 13}" fill="#ffffff" font-size="9" font-weight="600">{esc(recortar(p["nombre"], 16))}</text>'
            f'<text x="{x + 21}" y="{y + 24}" fill="#9fc0ee" font-size="7.5">{esc(recortar(p["cargo"], 22))}</text>'
            f'</g>'
        )

    # Lineas de cargos: postura explicita primero; si no hay, su categoria fuerte
    # y como maximo dos temas de esa categoria (evita la maraña).
    lineas = []
    for p in politicos:
        xp, yp = pos_pol[p["id"]]
        cat_fuerte = _categoria_fuerte(d, p["id"])
        por_categoria = defaultdict(list)
        for t in temas:
            por_categoria[t["categoria"]].append(t)
        for t in temas:
            valor = d["posiciones"].get((p["id"], t["id"]))
            if not valor:
                continue
            color = "#39ff88" if valor > 0 else "#ff3b6b"
            grosor = 2.0 + (1.4 if t["urgencia"] == "alta" else 0)
            estado = "a favor" if valor > 0 else "en contra"
            lineas.append(
                f'<path d="{_curva(X_TEMAS + ANCHO_TEMA, pos_y[t["id"]] + 15, xp, yp + 15)}" '
                f'fill="none" stroke="{color}" stroke-width="{grosor:.1f}" opacity="0.6" '
                f'class="linea-politico"><title>{esc(p["nombre"])} — {estado} de “{esc(t["titulo"])}”</title></path>'
            )
        if cat_fuerte:
            for t in por_categoria.get(cat_fuerte, [])[:1]:
                if d["posiciones"].get((p["id"], t["id"])):
                    continue
                lineas.append(
                    f'<path d="{_curva(X_TEMAS + ANCHO_TEMA, pos_y[t["id"]] + 15, xp, yp + 15)}" '
                    f'fill="none" stroke="#ffb84c" stroke-width="1.2" opacity="0.25" '
                    f'stroke-dasharray="4 5" class="linea-actividad">'
                    f'<title>{esc(p["nombre"])} tiene actividad en {esc(t["categoria"])}, sin postura declarada</title></path>'
                )

    lineas_usuario = []
    if grupos:
        piezas.append(
            f'<text x="410" y="{y_usuarios - 16}" fill="#63f5c8" font-size="12" '
            f'font-weight="700" letter-spacing="1.2">CIUDADANÍA POR GRUPO</text>'
        )
        ancho_grupo = 90
        gap = 8
        total_ancho = len(grupos) * ancho_grupo + (len(grupos) - 1) * gap
        x0 = 405 + max(0, (495 - total_ancho) / 2)
        for gi, g in enumerate(grupos):
            xg = x0 + gi * (ancho_grupo + gap)
            cantidad = d["total_grupo"][g["clave"]]
            piezas.append(
                f'<g class="nodo grupo"><title>{g["nombre"]}: {cantidad} personas</title>'
                f'<rect x="{xg:.0f}" y="{y_usuarios}" width="{ancho_grupo}" height="52" rx="11" '
                f'fill="#0f1c33" stroke="{g["color"]}" stroke-width="1.5"/>'
                f'<text x="{xg + ancho_grupo / 2:.0f}" y="{y_usuarios + 20}" text-anchor="middle" font-size="14">{g["emoji"]}</text>'
                f'<text x="{xg + ancho_grupo / 2:.0f}" y="{y_usuarios + 34}" text-anchor="middle" fill="#dbe9ff" font-size="8.5">{esc(g["nombre"])}</text>'
                f'<text x="{xg + ancho_grupo / 2:.0f}" y="{y_usuarios + 46}" text-anchor="middle" fill="{g["color"]}" font-size="10" font-weight="700">{cantidad}</text>'
                f'</g>'
            )
            for t in temas:
                n = d["apoyo"].get((g["clave"], t["id"]), 0)
                if not n:
                    continue
                pct = n / max(1, cantidad)
                grosor = 1 + 11 * pct * (0.45 + 0.55 * min(1, n / 8))
                lineas_usuario.append(
                    f'<path d="{_curva(xg + ancho_grupo / 2, y_usuarios, X_TEMAS + ANCHO_TEMA, pos_y[t["id"]] + 15)}" '
                    f'fill="none" stroke="{g["color"]}" stroke-width="{grosor:.1f}" opacity="0.42" '
                    f'class="linea-usuario"><title>{g["nombre"]}: {n} de {cantidad} ({pct * 100:.0f}%) apoya “{esc(t["titulo"])}”</title></path>'
                )

    piezas.extend(lineas_usuario)
    piezas.extend(lineas)
    leyenda = (
        f'<tspan fill="#39ff88">━</tspan> cargo a favor   '
        f'<tspan fill="#ff3b6b">━</tspan> cargo en contra   '
        f'<tspan fill="#ffb84c">┅</tspan> actividad declarada'
    )
    if grupos:
        leyenda += (
            '   <tspan fill="#63f5c8">━</tspan> apoyo ciudadano '
            '(grosor = % del grupo)'
        )
    piezas.append(
        f'<g class="leyenda"><text x="{X_TEMAS}" y="{altura - 20}" fill="#8fb8ff" '
        f'font-size="10.5">{leyenda}</text></g>'
    )
    piezas.append("</svg>")
    return "".join(piezas)


def brecha(db):
    """Compara lo que preocupa a la gente con lo que hacen los cargos."""
    ciudadano = {
        f["categoria"]: f["n"]
        for f in db.todos(
            """SELECT t.categoria, COUNT(*) AS n FROM votos v
               JOIN temas t ON t.id = v.tema_id WHERE v.valor = 1 GROUP BY t.categoria"""
        )
    }
    politico = {
        f["tema_categoria"]: f["n"]
        for f in db.todos(
            """SELECT tema_categoria, COUNT(*) AS n FROM acciones
               WHERE tema_categoria != '' GROUP BY tema_categoria"""
        )
    }
    total_c = max(1, sum(ciudadano.values()))
    total_p = max(1, sum(politico.values()))
    filas = []
    for categoria in sorted(set(ciudadano) | set(politico)):
        c = ciudadano.get(categoria, 0)
        p = politico.get(categoria, 0)
        pc = 100 * c / total_c
        pp = 100 * p / total_p
        filas.append(
            {
                "categoria": categoria,
                "votos": c,
                "acciones": p,
                "pct_ciudadano": pc,
                "pct_politico": pp,
                "brecha": pc - pp,
            }
        )
    # Las barras se escalan al valor mas alto para que se lean aunque los
    # porcentajes sean chicos; el numero real queda en el tooltip.
    escala = max([max(f["pct_ciudadano"], f["pct_politico"]) for f in filas] + [1])
    for f in filas:
        f["ancho_c"] = 100 * f["pct_ciudadano"] / escala
        f["ancho_p"] = 100 * f["pct_politico"] / escala
    filas.sort(key=lambda f: f["brecha"], reverse=True)
    return filas
