"""Importa o actualiza cargos desde los JSON de datos/fuentes.

Uso:
    python importar_politicos.py

Es idempotente: busca por slug y actualiza el registro existente. Las
actividades solo se reemplazan cuando el archivo trae alguna.
"""
import json
import os
import sys

import db as dbm

ARCHIVOS = [
    "politicos.json",
    "senadores.json",
    "diputados_a_f.json",
    "diputados_g_o.json",
    "diputados_p_z.json",
    "diputados_faltantes.json",
]

# Personas que ya tienen un cargo cargado a mano (Poder Ejecutivo, organismos,
# intendentes o vicepresidencia): manda ese registro y se saltean en los archivos
# de cámaras, porque quien asume el Ejecutivo deja la banca al suplente.
def _cargos_curados():
    ruta = os.path.join(dbm.CARPETA_FUENTES, "politicos.json")
    if not os.path.exists(ruta):
        return set()
    with open(ruta, encoding="utf-8") as f:
        return {p.get("slug") for p in json.load(f).get("politicos", []) if p.get("slug")}


NO_PISAR = _cargos_curados()

CAMPOS = (
    "nombre", "cargo", "camara", "organismo", "partido", "departamento",
    "emoji", "funciones", "email_publico", "telefono_oficina", "celular_publico",
    "web", "contacto_fuente_url",
)


def _slug_unico(db, base, usados):
    """El slug identifica a la persona: si aparece en dos archivos, se actualiza."""
    return base or "sin-nombre"


def importar():
    dbm.crear_esquema()
    total = nuevos = actualizados = 0
    usados = set()
    with dbm.abrir() as db:
        for archivo in ARCHIVOS:
            ruta = os.path.join(dbm.CARPETA_FUENTES, archivo)
            if not os.path.exists(ruta):
                continue
            with open(ruta, encoding="utf-8") as f:
                datos = json.load(f)
            gente = datos.get("politicos") or datos.get("faltantes") or []
            for p in gente:
                slug = _slug_unico(db, p.get("slug"), usados)
                if archivo != "politicos.json" and slug in NO_PISAR:
                    print("se mantiene el cargo ejecutivo de:", p.get("nombre"))
                    continue
                valores = [p.get(c) or "" for c in CAMPOS]
                existe = db.uno("SELECT id FROM politicos WHERE slug = ?", (slug,))
                if existe:
                    db.ejecutar(
                        "UPDATE politicos SET " + ", ".join(f"{c} = ?" for c in CAMPOS) +
                        " WHERE slug = ?",
                        tuple(valores) + (slug,),
                    )
                    actualizados += 1
                else:
                    db.ejecutar(
                        "INSERT INTO politicos (slug, " + ", ".join(CAMPOS) + ", verificado, creado) "
                        "VALUES (?" + ", ?" * len(CAMPOS) + ", ?, ?)",
                        (slug,) + tuple(valores) + (1 if p.get("verificado") else 0, dbm.ahora()),
                    )
                    nuevos += 1
                fila = db.uno("SELECT id FROM politicos WHERE slug = ?", (slug,))
                actividades = p.get("actividades") or []
                if actividades:
                    db.ejecutar("DELETE FROM acciones WHERE politico_id = ?", (fila["id"],))
                    for act in actividades:
                        db.ejecutar(
                            """INSERT INTO acciones (politico_id, titulo, descripcion, estado,
                                   fecha, tema_categoria, fuente_url, creado)
                               VALUES (?, ?, ?, ?, ?, ?, ?, ?)""",
                            (
                                fila["id"], act.get("titulo", ""), act.get("descripcion", ""),
                                act.get("estado", "pendiente"), act.get("fecha"),
                                act.get("tema", ""), act.get("fuente_url"), dbm.ahora(),
                            ),
                        )
                total += 1
        resumen = db.todos(
            "SELECT camara, COUNT(*) AS n, "
            "SUM(CASE WHEN email_publico IS NOT NULL AND email_publico != '' THEN 1 ELSE 0 END) AS con_correo "
            "FROM politicos GROUP BY camara ORDER BY camara"
        )
        sin_correo = db.valor("SELECT COUNT(*) FROM politicos WHERE email_publico IS NULL OR email_publico = ''")
    print(f"importados: {total} (nuevos {nuevos}, actualizados {actualizados})")
    for r in resumen:
        print(f"  {r['camara']}: {r['n']} cargos, {r['con_correo']} con correo")
    print("sin correo:", sin_correo)


if __name__ == "__main__":
    importar()
