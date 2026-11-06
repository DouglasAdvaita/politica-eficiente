"""Copia la base entre SQLite local y Neon (Postgres).

Sirve para desarrollar rapido en local y publicar cuando este listo.

    python copiar_db.py --bajar     # Neon  -> SQLite (trae lo que hay en produccion)
    python copiar_db.py --subir     # SQLite -> Neon (publica lo trabajado en local)
    python copiar_db.py --bajar --solo hitos,noticias

La copia reemplaza el contenido de cada tabla, no lo mezcla.
"""
import os
import sys

import db as dbm

# Orden de padres a hijos, para respetar las referencias.
TABLAS = [
    "config", "usuarios", "politicos", "temas", "solicitudes_vinculo",
    "votos", "opiniones", "acciones", "posiciones", "actividad", "avisos",
    "flujos", "biografias", "hitos", "vinculos", "noticias", "participantes",
]


def _dsn_neon():
    ruta = os.path.join(dbm.BASE, "datos", "dsn_neon.txt")
    with open(ruta, encoding="utf-8") as f:
        return f.read().strip()


def _columnas_sqlite(cx, tabla):
    return [f[1] for f in cx.execute("PRAGMA table_info(%s)" % tabla)]


def bajar(tablas):
    import psycopg2
    origen = psycopg2.connect(_dsn_neon())
    destino = __import__("sqlite3").connect(dbm.RUTA_DB)
    destino.execute("PRAGMA foreign_keys = OFF")
    total = 0
    for tabla in reversed(tablas):
        destino.execute("DELETE FROM %s" % tabla)
    for tabla in tablas:
        columnas = _columnas_sqlite(destino, tabla)
        if not columnas:
            continue
        cur = origen.cursor()
        cur.execute("SELECT %s FROM %s" % (", ".join(columnas), tabla))
        filas = cur.fetchall()
        if filas:
            marcas = ", ".join("?" * len(columnas))
            destino.executemany(
                "INSERT INTO %s (%s) VALUES (%s)" % (tabla, ", ".join(columnas), marcas),
                filas)
        total += len(filas)
        print("%-22s %6d filas" % (tabla, len(filas)), flush=True)
    destino.commit()
    origen.close()
    destino.close()
    print("total:", total)


def subir(tablas):
    import psycopg2
    origen = __import__("sqlite3").connect(dbm.RUTA_DB)
    destino = psycopg2.connect(_dsn_neon())
    cur = destino.cursor()
    total = 0
    for tabla in reversed(tablas):
        cur.execute("DELETE FROM %s" % tabla)
    for tabla in tablas:
        columnas = _columnas_sqlite(origen, tabla)
        if not columnas:
            continue
        filas = origen.execute(
            "SELECT %s FROM %s" % (", ".join(columnas), tabla)).fetchall()
        if filas:
            marcas = ", ".join(["%s"] * len(columnas))
            cur.executemany(
                "INSERT INTO %s (%s) VALUES (%s)" % (tabla, ", ".join(columnas), marcas),
                filas)
            if "id" in columnas:
                cur.execute(
                    "SELECT setval(pg_get_serial_sequence(%s, 'id'), "
                    "COALESCE((SELECT MAX(id) FROM " + tabla + "), 1))", (tabla,))
        total += len(filas)
        print("%-22s %6d filas" % (tabla, len(filas)), flush=True)
    destino.commit()
    origen.close()
    destino.close()
    print("total:", total)


if __name__ == "__main__":
    sys.stdout.reconfigure(encoding="utf-8", errors="replace")
    dbm.crear_esquema()
    elegidas = TABLAS
    if "--solo" in sys.argv:
        pedidas = sys.argv[sys.argv.index("--solo") + 1].split(",")
        elegidas = [t for t in TABLAS if t in pedidas]
    if "--bajar" in sys.argv:
        bajar(elegidas)
    elif "--subir" in sys.argv:
        subir(elegidas)
    else:
        print(__doc__)
