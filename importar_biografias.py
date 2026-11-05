"""Importa las biografias de datos/fuentes/biografias.json a la base.

Uso:
    python importar_biografias.py

Es idempotente: actualiza la biografia del cargo y reemplaza sus hitos y
vinculos. Los datos salen de Wikipedia y se muestran con su enlace de fuente.
"""
import sys

import db as dbm


def importar():
    dbm.crear_esquema()
    with dbm.abrir() as db:
        r = dbm._cargar_biografias(db)
        sin_bio = db.todos(
            """SELECT p.nombre, p.camara FROM politicos p
               LEFT JOIN biografias b ON b.politico_id = p.id
               WHERE p.camara IN ('Senadores', 'Diputados') AND b.id IS NULL
               ORDER BY p.camara, p.nombre"""
        )
        con_bio = db.valor(
            "SELECT COUNT(*) FROM biografias b JOIN politicos p ON p.id = b.politico_id "
            "WHERE p.camara IN ('Senadores', 'Diputados')"
        )
    print(f"biografias: {r['biografias']} | hitos: {r['hitos']} | vinculos: {r['vinculos']}")
    print(f"legisladores con biografia: {con_bio} | sin biografia: {len(sin_bio)}")
    for f in sin_bio:
        print(f"  {f['camara']}: {f['nombre']}")


if __name__ == "__main__":
    sys.stdout.reconfigure(encoding="utf-8", errors="replace")
    importar()
