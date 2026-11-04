"""Desempeno de un cargo publico con criterio configurable.

No mide intenciones: mide lo observable en la app (actividades cumplidas,
pendientes vencidas, actualidad y posturas declaradas). Los pesos viven en la
tabla config para que se puedan ajustar sin tocar codigo.
"""
from datetime import datetime, timezone

import db as dbm

CRITERIOS = {
    "peso_cumplidas": ("40", "Peso de las actividades marcadas como hechas"),
    "peso_actualidad": ("40", "Peso de haber tenido actividad en los ultimos 12 meses"),
    "peso_posturas": ("20", "Peso de declarar posturas en los temas"),
    "descuento_vencida": ("10", "Puntos que resta cada pendiente con fecha pasada"),
    "umbral_ok": ("65", "Puntaje desde el cual se considera que esta trabajando"),
    "umbral_regular": ("35", "Puntaje minimo para no quedar en falta"),
}


def criterios(db):
    valores = {}
    for clave, (defecto, _texto) in CRITERIOS.items():
        fila = db.uno("SELECT valor FROM config WHERE clave = ?", (clave,))
        valores[clave] = float(fila["valor"]) if fila else float(defecto)
    return valores


def sembrar_criterios(db):
    for clave, (valor, texto) in CRITERIOS.items():
        db.ejecutar(
            "INSERT INTO config (clave, valor, descripcion) VALUES (?, ?, ?) "
            "ON CONFLICT (clave) DO NOTHING",
            (clave, valor, texto),
        )


def calcular(acciones, posturas, cfg):
    if not acciones:
        return {
            "puntaje": None, "estado": "sin_datos", "texto": "Sin actividades cargadas",
            "hechas": 0, "pendientes": 0, "vencidas": 0, "dias": None, "total": 0,
        }
    hoy = datetime.now(timezone.utc).date()
    hechas = [a for a in acciones if a["estado"] == "hecho"]
    pendientes = [a for a in acciones if a["estado"] != "hecho"]
    vencidas = 0
    for a in pendientes:
        fecha = (a.get("fecha") or "")[:10]
        if len(fecha) == 10:
            try:
                if datetime.fromisoformat(fecha).date() < hoy:
                    vencidas += 1
            except ValueError:
                pass
    tasa = len(hechas) / len(acciones)
    fechas = sorted([a["fecha"][:10] for a in acciones if a.get("fecha")])
    dias = None
    if fechas:
        try:
            dias = (hoy - datetime.fromisoformat(fechas[-1]).date()).days
        except ValueError:
            dias = None
    actualidad = 1.0 if dias is None else max(0.0, 1 - dias / 365)
    posturas_factor = min(1.0, posturas / 3)
    puntaje = (
        tasa * cfg["peso_cumplidas"]
        + actualidad * cfg["peso_actualidad"]
        + posturas_factor * cfg["peso_posturas"]
        - vencidas * cfg["descuento_vencida"]
    )
    # Con pocas actividades el puntaje no puede ser concluyente.
    confianza = 0.6 + 0.4 * min(1.0, len(acciones) / 5)
    puntaje = max(0, min(100, round(puntaje * confianza)))
    if puntaje >= cfg["umbral_ok"]:
        estado, texto = "trabajando", "Trabajando"
    elif puntaje >= cfg["umbral_regular"]:
        estado, texto = "irregular", "Rendimiento irregular"
    else:
        estado, texto = "en_falta", "Debe rendir cuentas"
    return {
        "puntaje": puntaje, "estado": estado, "texto": texto,
        "hechas": len(hechas), "pendientes": len(pendientes), "vencidas": vencidas,
        "dias": dias, "total": len(acciones),
    }


def de_politico(db, politico_id, cfg=None):
    cfg = cfg or criterios(db)
    acciones = db.todos(
        "SELECT estado, fecha FROM acciones WHERE politico_id = ?", (politico_id,)
    )
    posturas = db.valor(
        "SELECT COUNT(*) FROM posiciones WHERE politico_id = ?", (politico_id,)
    )
    return calcular(acciones, posturas or 0, cfg)


def todos(db):
    cfg = criterios(db)
    filas = db.todos("SELECT id FROM politicos")
    return {f["id"]: de_politico(db, f["id"], cfg) for f in filas}
