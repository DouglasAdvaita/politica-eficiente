"""Marca la importancia de cada accion cargada.

Criterio: mide el alcance de la decision, no la simpatia por quien la toma.
  alta  = cambia una norma, una obra grande, un nombramiento o un acuerdo internacional.
  media = gestion, reunion o presentacion de datos con efecto acotado.
  baja  = ceremonia, aniversario, participacion en un evento o exposicion.

El comparador usa esta marca para contrastar acciones de distinto peso. Se
puede volver a correr: solo actualiza la columna `importancia`.

Uso:
    python marcar_acciones.py
"""
import sys

import db as dbm

ALTA = (
    "Proyecto de transparencia en tiempos de espera",
    "Control previo de concursos en entes autónomos",
    "Reforma del Código del Proceso Penal",
    "Regulación de la pesca artesanal",
    "Avances en derechos de las trabajadoras domésticas",
    "Acuerdo de logística regional con Paraguay y Bolivia",
    "Regulación del trabajo en privación de libertad",
    "Plan de obras de infraestructura educativa",
    "Licitación para renovar la flota de ambulancias",
    "Cierre del Anillo del Norte de 500 kV",
)

BAJA = (
    "Sesión ordinaria del Senado",
    "Exposición sobre estabilidad macroeconómica en Argentina",
    "Participación en la Fiesta de la Chacra en Canelones",
    "Día Nacional de Solidaridad con las Víctimas de Violencia",
    "Sesión del Congreso de Intendentes en Salto",
    "34° aniversario de las representaciones sociales",
    "Participación del BROU en la Expo Prado 2026",
    "52° aniversario de ANTEL",
    "Exposición en el 41° período de sesiones de la CEPAL",
)


def nivel(titulo):
    texto = (titulo or "").strip().lower()
    for clave in ALTA:
        if clave.lower() in texto:
            return "alta"
    for clave in BAJA:
        if clave.lower() in texto:
            return "baja"
    return "media"


def marcar():
    dbm.crear_esquema()
    with dbm.abrir() as db:
        filas = db.todos("SELECT id, titulo FROM acciones")
        cuenta = {}
        for f in filas:
            valor = nivel(f["titulo"])
            cuenta[valor] = cuenta.get(valor, 0) + 1
            db.ejecutar("UPDATE acciones SET importancia = ? WHERE id = ?", (valor, f["id"]))
    print("acciones marcadas:", len(filas), "|", cuenta)


if __name__ == "__main__":
    sys.stdout.reconfigure(encoding="utf-8", errors="replace")
    marcar()
