"""Correlaciona las noticias recolectadas con la linea de tiempo (hitos) del cargo.

- Las noticias 'aceptadas' (con politico_id ya asignado) se promueven a hitos
  con su fecha y enlace. Idempotente: no duplica por URL.
- Las 'por_revisar' se resuelven a mano con --revisar / --asignar / --descartar.

Uso:
    python procesar_noticias.py                  # promueve las aceptadas a hitos
    python procesar_noticias.py --revisar        # lista las pendientes con candidatos
    python procesar_noticias.py --asignar ID POLITICO_ID
    python procesar_noticias.py --descartar ID
"""
import sys
import unicodedata
import re

import db as dbm


def _plano(texto):
    return "".join(c for c in unicodedata.normalize("NFD", texto or "")
                   if unicodedata.category(c) != "Mn").lower()


def _tokens(nombre):
    basura = {"de", "del", "la", "las", "los", "y", "e", "da", "do", "dos", "das"}
    return [t for t in re.split(r"[\s\-]+", _plano(nombre)) if len(t) > 2 and t not in basura]


def _candidatos(titulo):
    plano = _plano(titulo)
    todos = dbm.consulta("SELECT id, nombre FROM politicos ORDER BY nombre")
    return [t for t in todos if any(a in plano for a in _tokens(t["nombre"])[1:])]


def promover():
    dbm.crear_esquema()
    with dbm.abrir() as db:
        pendientes = db.todos(
            "SELECT id, politico_id, titulo, anio, url FROM noticias "
            "WHERE politico_id IS NOT NULL AND estado = 'aceptada' ORDER BY anio")
        agregados = 0
        for n in pendientes:
            ya = db.valor(
                "SELECT 1 FROM hitos WHERE politico_id = ? AND fuente_url = ?",
                (n["politico_id"], n["url"]))
            if not ya:
                db.ejecutar(
                    "INSERT INTO hitos (politico_id, anio, texto, fuente_url, creado) "
                    "VALUES (?, ?, ?, ?, ?)",
                    (n["politico_id"], n["anio"], n["titulo"], n["url"], dbm.ahora()))
                agregados += 1
            db.ejecutar("UPDATE noticias SET estado = 'procesada' WHERE id = ?", (n["id"],))
    print(f"hitos agregados: {agregados} | noticias procesadas: {len(pendientes)}")


def revisar():
    filas = dbm.consulta(
        "SELECT id, titulo, medio, fecha, url FROM noticias "
        "WHERE estado = 'por_revisar' ORDER BY fecha DESC LIMIT 200")
    if not filas:
        print("no hay noticias por revisar")
        return
    for f in filas:
        print(f"\n[{f['id']}] {f['fecha']} · {f['medio']}")
        print(f"    {f['titulo']}")
        for c in _candidatos(f["titulo"])[:4]:
            print(f"      -> {c['id']} {c['nombre']}")
        print(f"    url: {f['url']}")
    print(f"\n{len(filas)} pendientes")


def asignar(nid, politico_id):
    with dbm.abrir() as db:
        db.ejecutar(
            "UPDATE noticias SET politico_id = ?, estado = 'aceptada' WHERE id = ?",
            (politico_id, nid))
    print(f"noticia {nid} asignada al politico {politico_id} (lista para promover)")


def descartar(nid):
    with dbm.abrir() as db:
        db.ejecutar("UPDATE noticias SET estado = 'descartada' WHERE id = ?", (nid,))
    print(f"noticia {nid} descartada")


if __name__ == "__main__":
    sys.stdout.reconfigure(encoding="utf-8", errors="replace")
    args = sys.argv[1:]
    if "--revisar" in args:
        revisar()
    elif "--asignar" in args:
        i = args.index("--asignar")
        asignar(int(args[i + 1]), int(args[i + 2]))
    elif "--descartar" in args:
        i = args.index("--descartar")
        descartar(int(args[i + 1]))
    else:
        promover()
