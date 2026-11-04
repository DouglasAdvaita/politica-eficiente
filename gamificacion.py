"""Puntos, niveles y categorias de participacion."""

NIVELES = [
    (0, "Curioso", "🌱"),
    (50, "Informado", "📘"),
    (150, "Participativo", "🗣️"),
    (400, "Influyente", "📣"),
    (900, "Referente", "⭐"),
    (1800, "Ciudadano Clave", "🏆"),
]

PUNTOS = {
    "registro": 10,
    "voto": 2,
    "opinion": 5,
    "propuesta": 15,
    "vinculo": 25,
    "invitacion": 8,
}

GRUPOS = [
    ("simple", "Simples", "👤", "#7fd4ff"),
    ("con_intereses", "Con intereses", "🎯", "#63f5c8"),
    ("activo", "Activos", "⚡", "#ffd166"),
    ("muy_activo", "Muy activos", "🔥", "#ff8a4c"),
    ("referente", "Referentes", "⭐", "#ff5fa2"),
]


def nivel(puntos):
    actual = NIVELES[0]
    siguiente = None
    for i, (piso, nombre, emoji) in enumerate(NIVELES):
        if puntos >= piso:
            actual = (piso, nombre, emoji)
            siguiente = NIVELES[i + 1] if i + 1 < len(NIVELES) else None
    if siguiente:
        falta = siguiente[0] - puntos
        avance = int(100 * (puntos - actual[0]) / max(1, siguiente[0] - actual[0]))
    else:
        falta = 0
        avance = 100
    return {
        "nombre": actual[1],
        "emoji": actual[2],
        "piso": actual[0],
        "siguiente": siguiente[1] if siguiente else None,
        "falta": falta,
        "avance": min(100, max(0, avance)),
    }


def grupo(puntos, acciones=0, intereses=""):
    """Categoria que se usa para agrupar a los usuarios en el mapa."""
    if puntos >= 900:
        return "referente"
    if puntos >= 400 or acciones >= 25:
        return "muy_activo"
    if puntos >= 150 or acciones >= 10:
        return "activo"
    if intereses.strip() or acciones >= 3:
        return "con_intereses"
    return "simple"


def datos_grupo(clave):
    for g in GRUPOS:
        if g[0] == clave:
            return {"clave": g[0], "nombre": g[1], "emoji": g[2], "color": g[3]}
    return {"clave": "simple", "nombre": "Simples", "emoji": "👤", "color": "#7fd4ff"}
