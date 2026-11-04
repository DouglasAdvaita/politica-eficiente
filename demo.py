"""Datos de demostración para ver el mapa y los foros con volumen.

Uso:
    python demo.py crear      # crea cuentas demo y votos repartidos
    python demo.py limpiar    # borra todo lo creado por este script

Las cuentas demo usan el correo @ejemplo.uy y no deben existir en producción.
"""
import random
import sys

from werkzeug.security import generate_password_hash

import db as dbm

CLAVE = "demo12345"
FRASES = [
    "El dato está bien, pero falta saber cuánto cuesta implementarlo.",
    "Me interesa seguir este tema, sobre todo en mi departamento.",
    "Sin control ciudadano cualquier propuesta termina en la nada.",
    "Coincido en el diagnóstico, no tanto en la solución.",
    "Falta que se escuche a quien vive el problema todos los días.",
    "¿Hay números oficiales que respalden esto?",
    "Es de los temas que menos se explican y más afectan.",
    "Prefiero una medida chica y verificable antes que un anuncio grande.",
]


def crear():
    random.seed(7)
    with dbm.abrir() as db:
        temas = db.todos("SELECT id, categoria FROM temas")
        if not temas:
            print("No hay temas cargados. Sembrá primero con: python -c \"import db; db.sembrar()\"")
            return
        categorias = sorted({t["categoria"] for t in temas})
        perfiles = [
            ("simple", 0.40, (10, 45), (2, 4)),
            ("con_intereses", 0.25, (60, 145), (4, 9)),
            ("activo", 0.20, (160, 390), (9, 18)),
            ("muy_activo", 0.10, (420, 880), (18, 30)),
            ("referente", 0.05, (950, 2000), (30, 45)),
        ]
        creados = 0
        for i in range(1, 41):
            perfil = random.choices(
                [p[0] for p in perfiles], weights=[p[1] for p in perfiles]
            )[0]
            rango = next(p for p in perfiles if p[0] == perfil)
            puntos = random.randint(*rango[2])
            acciones = random.randint(*rango[3])
            email = f"demo{i}@ejemplo.uy"
            if db.uno("SELECT id FROM usuarios WHERE email = ?", (email,)):
                continue
            intereses = random.sample(categorias, k=min(3, len(categorias)))
            db.ejecutar(
                """INSERT INTO usuarios (email, nombre, clave_hash, puntos, intereses,
                       departamento, creado) VALUES (?, ?, ?, ?, ?, ?, ?)""",
                (
                    email, f"Vecino demo {i}", generate_password_hash(CLAVE), puntos,
                    ",".join(intereses), "Montevideo", dbm.ahora(),
                ),
            )
            uid = db.uno("SELECT id FROM usuarios WHERE email = ?", (email,))["id"]
            db.ejecutar(
                "INSERT INTO actividad (usuario_id, tipo, puntos, detalle, creado) VALUES (?, ?, ?, ?, ?)",
                (uid, "demo", puntos, "Cuenta de demostración", dbm.ahora()),
            )
            preferidos = [t for t in temas if t["categoria"] in intereses]
            otros = [t for t in temas if t["categoria"] not in intereses]
            elegidos = random.sample(preferidos, k=min(len(preferidos), random.randint(2, 5)))
            elegidos += random.sample(otros, k=min(len(otros), random.randint(0, 4)))
            for t in elegidos:
                db.ejecutar(
                    "INSERT INTO votos (usuario_id, tema_id, valor, creado) VALUES (?, ?, ?, ?) "
                    "ON CONFLICT (usuario_id, tema_id) DO NOTHING",
                    (uid, t["id"], 1, dbm.ahora()),
                )
            if i % 3 == 0:
                tema = random.choice(temas)
                db.ejecutar(
                    """INSERT INTO opiniones (tema_id, usuario_id, texto, creado)
                       VALUES (?, ?, ?, ?)""",
                    (tema["id"], uid, random.choice(FRASES), dbm.ahora()),
                )
            creados += 1
        print(f"cuentas demo creadas: {creados}")


def limpiar():
    with dbm.abrir() as db:
        ids = [f["id"] for f in db.todos("SELECT id FROM usuarios WHERE email LIKE 'demo%@ejemplo.uy'")]
        for uid in ids:
            for tabla in ("votos", "opiniones", "actividad", "solicitudes_vinculo"):
                db.ejecutar(f"DELETE FROM {tabla} WHERE usuario_id = ?", (uid,))
            db.ejecutar("DELETE FROM usuarios WHERE id = ?", (uid,))
        print(f"cuentas demo eliminadas: {len(ids)}")


if __name__ == "__main__":
    accion = sys.argv[1] if len(sys.argv) > 1 else "crear"
    if accion == "limpiar":
        limpiar()
    else:
        crear()
