"""Cambia el correo del usuario administrador de la app.

Uso:
    python cambiar_admin.py nuevo@correo.com

No toca la clave ni los datos: solo el correo con el que se entra a /admin.
El correo real se pasa por argumento o por la variable ADMIN_EMAIL, para no
dejarlo escrito en el repositorio.
"""
import os
import re
import sys

import db as dbm

PATRON = re.compile(r"^[^@\s]+@[^@\s]+\.[A-Za-z]{2,}$")


def cambiar(email, promover=False, poner_clave=False):
    email = (email or "").strip().lower()
    if not PATRON.match(email):
        print("correo invalido:", email)
        return False
    with dbm.abrir() as db:
        admin = db.uno("SELECT id, email FROM usuarios WHERE rol = 'admin' ORDER BY id LIMIT 1")
        existente = db.uno("SELECT id, rol FROM usuarios WHERE email = ?", (email,))
        destino_id = None
        if existente:
            if not promover:
                print("ese correo ya pertenece a otro usuario; agregá --promover "
                      "para convertirlo en administrador")
                return False
            db.ejecutar("UPDATE usuarios SET rol = 'admin' WHERE id = ?", (existente["id"],))
            if admin and admin["id"] != existente["id"]:
                db.ejecutar("UPDATE usuarios SET rol = 'ciudadano' WHERE id = ?", (admin["id"],))
            destino_id = existente["id"]
            print(f"cuenta {destino_id} promovida a administrador")
        else:
            if not admin:
                print("no hay usuario administrador en esta base")
                return False
            db.ejecutar("UPDATE usuarios SET email = ? WHERE id = ?", (email, admin["id"]))
            destino_id = admin["id"]
            print(f"administrador actualizado (usuario {destino_id})")
        if poner_clave:
            from werkzeug.security import generate_password_hash

            db.ejecutar(
                "UPDATE usuarios SET clave_hash = ? WHERE id = ?",
                (generate_password_hash(dbm.clave_admin()), destino_id),
            )
            print("clave del administrador alineada con ADMIN_CLAVE")
        return True


if __name__ == "__main__":
    sys.stdout.reconfigure(encoding="utf-8", errors="replace")
    promover = "--promover" in sys.argv
    poner_clave = "--clave" in sys.argv
    args = [a for a in sys.argv[1:] if not a.startswith("--")]
    destino = args[0] if args else os.environ.get("ADMIN_EMAIL", "")
    cambiar(destino, promover, poner_clave)
