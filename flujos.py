"""Flujos de capital del Estado: Sankey y claves."""
import html
import math
from collections import defaultdict

ANCHO = 1440
X_I = 20
W_I = 270
X_E = 540
W_E = 360
X_G = 1040
W_G = 380
Y0 = 90
GAP = 6
ALTO_MIN = 12


def _esc(t):
    return html.escape(str(t if t is not None else ""))


def _recortar(t, n):
    t = " ".join(str(t or "").split())
    return t if len(t) <= n else t[: n - 1].rstrip() + "…"


def _fmt(monto, unidad):
    if unidad == "pct_pib":
        return f"{monto:.1f}% del PIB"
    if abs(monto) >= 1000:
        return f"{monto:,.0f} M UYU".replace(",", ".")
    return f"{monto:,.1f} M UYU".replace(",", ".")


def datos(db, pais="UY", anio=None):
    where, params = ["pais = ?"], [pais]
    if anio:
        where.append("anio = ?")
        params.append(anio)
    filas = db.todos(
        "SELECT * FROM flujos WHERE " + " AND ".join(where) + " ORDER BY tipo, monto DESC",
        tuple(params),
    )
    ingresos = [f for f in filas if f["tipo"] == "ingreso"]
    gastos = [f for f in filas if f["tipo"] == "gasto"]
    transferencias = [f for f in filas if f["tipo"] == "transferencia"]
    ingresos.sort(key=lambda f: f["monto"], reverse=True)
    gastos.sort(key=lambda f: f["monto"], reverse=True)
    total_i = sum(f["monto"] for f in ingresos) or 1
    total_g = sum(f["monto"] for f in gastos) or 1
    anios = sorted({f["anio"] for f in filas if f["anio"]})
    comparacion = db.todos(
        "SELECT * FROM flujos WHERE unidad = 'pct_pib' ORDER BY pais, monto DESC"
    )
    return {
        "filas": filas,
        "ingresos": ingresos,
        "gastos": gastos,
        "transferencias": transferencias,
        "total_i": total_i,
        "total_g": total_g,
        "anios": anios,
        "anio": anio or (anios[-1] if anios else None),
        "pais": pais,
        "comparacion": comparacion,
        "hay_datos": bool(filas),
    }


def svg(d):
    ingresos = d["ingresos"]
    gastos = d["gastos"]
    if not ingresos and not gastos:
        return ""
    # alto proporcional a la mayor cantidad de filas
    filas = max(len(ingresos), len(gastos), 1)
    alto = 120 + filas * 34 + 40
    ANCHO_LOCAL = 1440
    Y0_LOCAL = 90
    # apilar ingresos
    y_i = []
    y = Y0_LOCAL
    for f in ingresos:
        h = max(ALTO_MIN, 6 + int(22 * f["monto"] / max(1, max(x["monto"] for x in ingresos))))
        y_i.append(y)
        y += h + GAP
    y_g = []
    y = Y0_LOCAL
    for f in gastos:
        h = max(ALTO_MIN, 6 + int(22 * f["monto"] / max(1, max(x["monto"] for x in gastos))))
        y_g.append(y)
        y += h + GAP
    # centro: el Estado ocupa el rango de los ingresos
    y_estado_top = y_i[0] if y_i else Y0_LOCAL
    y_estado_bot = (y_i[-1] + max(ALTO_MIN, 6 + int(22 * ingresos[-1]["monto"] / max(1, max(x["monto"] for x in ingresos))))) if y_i else Y0_LOCAL + 40
    piezas = [
        f'<svg viewBox="0 0 {ANCHO_LOCAL} {alto}" role="img" aria-label="Flujo de capital del Estado" '
        f'xmlns="http://www.w3.org/2000/svg" class="mapa-svg">',
        f'<rect width="{ANCHO_LOCAL}" height="{alto}" fill="#070c18"/>',
        f'<text x="{X_I}" y="50" fill="#8fb8ff" font-size="14" font-weight="700" letter-spacing="1.5">INGRESOS DEL ESTADO</text>',
        f'<text x="{X_E + W_E / 2}" y="50" fill="#63f5c8" font-size="14" font-weight="700" letter-spacing="1.5" text-anchor="middle">ESTADO</text>',
        f'<text x="{X_G}" y="50" fill="#ffb4d1" font-size="14" font-weight="700" letter-spacing="1.5">GASTOS DEL ESTADO</text>',
    ]
    # caja del Estado
    piezas.append(
        f'<rect x="{X_E}" y="{y_estado_top}" width="{W_E}" height="{y_estado_bot - y_estado_top}" '
        f'rx="10" fill="#0f2a3a" stroke="#63f5c8" stroke-width="1.6"/>'
    )
    piezas.append(
        f'<text x="{X_E + W_E / 2}" y="{(y_estado_top + y_estado_bot) / 2}" text-anchor="middle" '
        f'fill="#e8f1ff" font-size="13" font-weight="700">Tesoro Nacional</text>'
    )
    # ingresos
    for i, f in enumerate(ingresos):
        h = max(ALTO_MIN, 6 + int(22 * f["monto"] / max(1, max(x["monto"] for x in ingresos))))
        y = y_i[i]
        piezas.append(
            f'<g class="nodo flujo"><title>{_esc(f["nombre"])} · {_fmt(f["monto"], f["unidad"])}</title>'
            f'<rect x="{X_I}" y="{y}" width="{W_I}" height="{h}" rx="7" fill="#12203a" stroke="#2b4a7a"/>'
            f'<text x="{X_I + 10}" y="{y + h / 2 + 4}" fill="#e8f1ff" font-size="11.5">{_esc(_recortar(f["nombre"], 26))}</text>'
            f'<text x="{X_I + W_I - 8}" y="{y + h / 2 + 4}" text-anchor="end" fill="#8fb8ff" font-size="10">{_esc(_fmt(f["monto"], f["unidad"]))}</text>'
            f'</g>'
        )
        # linea al Estado
        piezas.append(
            f'<path d="M {X_I + W_I} {y + h / 2} C {X_I + W_I + 80} {y + h / 2} '
            f'{X_E - 80} {(y_estado_top + y_estado_bot) / 2} {X_E} {(y_estado_top + y_estado_bot) / 2}" '
            f'fill="none" stroke="#7fd4ff" stroke-width="{max(1.5, h * 0.6):.1f}" opacity="0.45" '
            f'class="linea-flujo"><title>{_esc(f["nombre"])} → Estado</title></path>'
        )
    # gastos
    for i, f in enumerate(gastos):
        h = max(ALTO_MIN, 6 + int(22 * f["monto"] / max(1, max(x["monto"] for x in gastos))))
        y = y_g[i]
        piezas.append(
            f'<g class="nodo flujo"><title>{_esc(f["nombre"])} · {_fmt(f["monto"], f["unidad"])}</title>'
            f'<rect x="{X_G}" y="{y}" width="{W_G}" height="{h}" rx="7" fill="#2a1230" stroke="#7a2b5e"/>'
            f'<text x="{X_G + 10}" y="{y + h / 2 + 4}" fill="#ffe6f2" font-size="11.5">{_esc(_recortar(f["nombre"], 30))}</text>'
            f'<text x="{X_G + W_G - 8}" y="{y + h / 2 + 4}" text-anchor="end" fill="#ffb4d1" font-size="10">{_esc(_fmt(f["monto"], f["unidad"]))}</text>'
            f'</g>'
        )
        piezas.append(
            f'<path d="M {X_E + W_E} {(y_estado_top + y_estado_bot) / 2} C {X_E + W_E + 80} {(y_estado_top + y_estado_bot) / 2} '
            f'{X_G - 80} {y + h / 2} {X_G} {y + h / 2}" '
            f'fill="none" stroke="#ff8a4c" stroke-width="{max(1.5, h * 0.6):.1f}" opacity="0.45" '
            f'class="linea-flujo"><title>Estado → {_esc(f["nombre"])}</title></path>'
        )
    piezas.append("</svg>")
    return "".join(piezas)


def claves(d):
    """Ratios y comparaciones para el panel de claves."""
    ingresos = d["ingresos"]
    gastos = d["gastos"]
    total_i = d["total_i"]
    total_g = d["total_g"]
    sueldos = sum(f["monto"] for f in gastos if "sueldo" in f["nombre"].lower() or "salario" in f["nombre"].lower())
    infra = sum(f["monto"] for f in gastos if "infra" in f["nombre"].lower() or "invers" in f["nombre"].lower())
    return {
        "total_i": total_i,
        "total_g": total_g,
        "sueldos": sueldos,
        "infra": infra,
        "ratio_sueldos_infra": (sueldos / infra) if infra else None,
        "top_ingresos": ingresos[:4],
        "top_gastos": gastos[:4],
    }
