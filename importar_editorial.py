"""Importa los datos editoriales de cada tema: responsable, fecha, critica,
contexto, preguntas abiertas y el indice de personas y organismos.

Idempotente: actualiza el tema y reemplaza sus participantes.

Uso:
    python importar_editorial.py
"""
import json
import sys

import db as dbm

ARCHIVOS = ("leyes.json", "propuestas.json")


def importar():
    dbm.crear_esquema()
    total = con_responsable = con_critica = con_participantes = 0
    with dbm.abrir() as db:
        for archivo in ARCHIVOS:
            datos = dbm._leer(archivo) or {}
            for t in (datos.get("leyes") or datos.get("propuestas") or []):
                slug = t.get("slug")
                if not slug:
                    continue
                fila = db.uno("SELECT id FROM temas WHERE slug = ?", (slug,))
                if not fila:
                    continue
                total += 1
                db.ejecutar(
                    "UPDATE temas SET fecha = ?, responsable = ?, critica = ?, contexto = ?, preguntas = ? WHERE id = ?",
                    (t.get("fecha", ""), t.get("responsable", ""),
                     t.get("critica", ""), t.get("contexto", ""),
                     json.dumps(t.get("preguntas") or [], ensure_ascii=False), fila["id"]),
                )
                if t.get("responsable"):
                    con_responsable += 1
                if t.get("critica"):
                    con_critica += 1
                db.ejecutar("DELETE FROM participantes WHERE tema_id = ?", (fila["id"],))
                partes = t.get("participantes") or []
                for p in partes:
                    db.ejecutar(
                        "INSERT INTO participantes (tema_id, nombre, rol, emoji, nota, creado) "
                        "VALUES (?, ?, ?, ?, ?, ?)",
                        (fila["id"], p.get("nombre", ""), p.get("rol", ""),
                         p.get("emoji", "👤"), p.get("nota", ""), dbm.ahora()),
                    )
                if partes:
                    con_participantes += 1
    print(f"temas: {total} | con responsable: {con_responsable} | "
          f"con critica: {con_critica} | con participantes: {con_participantes}")


if __name__ == "__main__":
    sys.stdout.reconfigure(encoding="utf-8", errors="replace")
    importar()
