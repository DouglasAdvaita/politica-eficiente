"""Trae actividad parlamentaria y la carga en la tabla 'acciones'.

Complementa traer_actuacion.py (que alimenta 'hitos'): aca cada hecho
se inserta como accion con estado 'hecho', para que aparezca en la home
('Lo ultimo que hicieron los cargos') y en la pagina del cargo.

Uso:
    python traer_acciones.py --dry
    python traer_acciones.py
    python traer_acciones.py --solo 5
"""
import sys
import os

ROOT = os.path.dirname(os.path.abspath(__file__))
sys.path.insert(0, ROOT)

import db as dbm
import traer_actuacion as ta
import traer_legisladores as leg


def main(dry=False, limite=None):
    dbm.crear_esquema()
    listado = leg.mapado()
    indice = {}
    for nombre, idleg in listado:
        indice[leg._plano(nombre)] = (idleg, nombre)

    with dbm.abrir() as db:
        gente = db.todos("SELECT id, nombre FROM politicos ORDER BY nombre")
    if limite:
        gente = gente[:limite]
    total = 0
    for g in gente:
        plano = leg._plano(g["nombre"])
        idleg, mejor = None, 0.0
        tokens_p = set(leg._tokens(g["nombre"]))
        for clave, (ident, visible) in indice.items():
            partes = [p.strip() for p in clave.split(",")]
            armado = leg._plano(partes[1] + " " + partes[0]) if len(partes) == 2 else clave
            if plano == armado:
                idleg = ident
                break
            tokens_c = set(leg._tokens(armado))
            if not tokens_p or not tokens_c:
                continue
            comunes = len(tokens_p & tokens_c)
            puntaje = comunes / max(len(tokens_p), len(tokens_c))
            if comunes >= 2 and puntaje >= 0.7 and puntaje > mejor:
                idleg, mejor = ident, puntaje
        if not idleg:
            continue
        registros = ta._get_json(ta._url(idleg))
        if not registros:
            print("%-40s sin datos" % g["nombre"][:40], flush=True)
            continue
        hechos = [h for h in (ta._hecho(r) for r in registros) if h]
        if len(hechos) > 20:
            hechos = hechos[-20:]
        nuevos = 0
        try:
            with dbm.abrir() as db:
                for anio, texto, enlace in hechos:
                    enlace = enlace or ("%s/camarasycomisiones/legisladores/%d" % (ta.BASE, idleg))
                    existe = db.uno(
                        "SELECT id FROM acciones WHERE politico_id = ? AND titulo = ?",
                        (g["id"], texto))
                    if existe:
                        continue
                    if not dry:
                        db.ejecutar(
                            """INSERT INTO acciones (politico_id, titulo, descripcion, estado,
                                   fecha, tema_categoria, fuente_url, creado)
                               VALUES (?, ?, ?, ?, ?, ?, ?, ?)""",
                            (g["id"], texto, "", "hecho", str(anio),
                             "", enlace, dbm.ahora()))
                    nuevos += 1
        except Exception as e:
            print("%-40s error: %s" % (g["nombre"][:40], str(e)[:60]), flush=True)
            continue
        total += nuevos
        print("%-40s %3d acciones nuevas" % (g["nombre"][:40], nuevos), flush=True)
    print("total nuevas:", total)


if __name__ == "__main__":
    sys.stdout.reconfigure(encoding="utf-8", errors="replace")
    lim = None
    if "--solo" in sys.argv:
        lim = int(sys.argv[sys.argv.index("--solo") + 1])
    main(dry="--dry" in sys.argv, limite=lim)
