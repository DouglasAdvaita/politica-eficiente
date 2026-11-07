"""Registro, ingreso y vinculo de cargos publicos con cuentas de usuario."""
import os
import re
import secrets
from datetime import datetime, timedelta, timezone
from functools import wraps

from flask import g, redirect, request, session, url_for
from werkzeug.security import check_password_hash, generate_password_hash

import db as dbm

EMAIL = re.compile(r"^[^@\s]+@[^@\s]+\.[^@\s]+$")


def clave_secreta():
    if os.environ.get("SECRET_KEY"):
        return os.environ["SECRET_KEY"]
    ruta = os.path.join(dbm.BASE, ".secret")
    if os.path.exists(ruta):
        with open(ruta, encoding="utf-8") as f:
            return f.read().strip()
    valor = secrets.token_hex(32)
    with open(ruta, "w", encoding="utf-8") as f:
        f.write(valor)
    return valor


def _normalizar(email):
    return (email or "").strip().lower()


def registrar(nombre, email, clave, intereses="", departamento=""):
    nombre = (nombre or "").strip()
    email = _normalizar(email)
    if len(nombre) < 2:
        return None, "Escribí tu nombre (mínimo 2 letras)."
    if not EMAIL.match(email):
        return None, "Ese correo no parece válido."
    if len(clave or "") < 8:
        return None, "La clave necesita al menos 8 caracteres."
    with dbm.abrir() as db:
        if db.uno("SELECT id FROM usuarios WHERE email = ?", (email,)):
            return None, "Ya existe una cuenta con ese correo."
        db.ejecutar(
            """INSERT INTO usuarios (email, nombre, clave_hash, puntos, intereses,
                   departamento, creado) VALUES (?, ?, ?, ?, ?, ?, ?)""",
            (
                email, nombre, generate_password_hash(clave),
                __import__("gamificacion").PUNTOS["registro"],
                intereses.strip(), departamento.strip(), dbm.ahora(),
            ),
        )
        fila = db.uno("SELECT id FROM usuarios WHERE email = ?", (email,))
        # migrar votos y opiniones anonimos de esta sesion a la nueva cuenta
        anon = None
        try:
            anon = session.get("anon_id")
        except Exception:
            anon = None
        if anon:
            db.ejecutar(
                "INSERT INTO votos (usuario_id, tema_id, valor, creado) "
                "SELECT ?, tema_id, valor, creado FROM votos_anon va WHERE anon_id = ? "
                "AND NOT EXISTS (SELECT 1 FROM votos v WHERE v.usuario_id = ? AND v.tema_id = va.tema_id)",
                (fila["id"], anon, fila["id"]),
            )
            db.ejecutar("DELETE FROM votos_anon WHERE anon_id = ?", (anon,))
            db.ejecutar(
                "INSERT INTO opiniones (tema_id, usuario_id, texto, hash, creado) "
                "SELECT tema_id, ?, texto, hash, creado FROM opiniones_anon WHERE anon_id = ?",
                (fila["id"], anon),
            )
            db.ejecutar("DELETE FROM opiniones_anon WHERE anon_id = ?", (anon,))
        dbm.registrar_actividad(
            db, fila["id"], "registro",
            __import__("gamificacion").PUNTOS["registro"], "Se sumó a la comunidad",
        )
        return fila["id"], None


def ingresar(email, clave):
    email = _normalizar(email)
    with dbm.abrir() as db:
        fila = db.uno("SELECT * FROM usuarios WHERE email = ?", (email,))
        if not fila or not check_password_hash(fila["clave_hash"], clave or ""):
            return None, "Correo o clave incorrectos."
        db.ejecutar(
            "UPDATE usuarios SET ultimo_acceso = ? WHERE id = ?",
            (dbm.ahora(), fila["id"]),
        )
        return fila["id"], None


def usuario_actual():
    if "usuario" in g:
        return g.usuario
    uid = session.get("usuario_id")
    g.usuario = None
    if uid:
        with dbm.abrir() as db:
            fila = db.uno(
                """SELECT u.*, (SELECT COUNT(*) FROM actividad a
                       WHERE a.usuario_id = u.id) AS acciones
                   FROM usuarios u WHERE u.id = ?""",
                (uid,),
            )
            if fila:
                fila["politico"] = db.uno(
                    "SELECT * FROM politicos WHERE usuario_id = ?", (uid,)
                )
                g.usuario = fila
    return g.usuario


def requiere_sesion(vista):
    @wraps(vista)
    def envoltura(*args, **kwargs):
        if not usuario_actual():
            return redirect(url_for("ingresar", volver=request.path))
        return vista(*args, **kwargs)

    return envoltura


def requiere_admin(vista):
    @wraps(vista)
    def envoltura(*args, **kwargs):
        yo = usuario_actual()
        if not yo:
            return redirect(url_for("ingresar", volver=request.path))
        if yo["rol"] != "admin":
            return redirect(url_for("inicio"))
        return vista(*args, **kwargs)

    return envoltura


def crear_solicitud(politico_id, usuario_id):
    token = secrets.token_urlsafe(24)
    expira = (datetime.now(timezone.utc) + timedelta(days=7)).isoformat(timespec="seconds")
    with dbm.abrir() as db:
        db.ejecutar(
            """INSERT INTO solicitudes_vinculo (politico_id, usuario_id, token,
                   estado, creado, expira) VALUES (?, ?, ?, 'pendiente', ?, ?)""",
            (politico_id, usuario_id, token, dbm.ahora(), expira),
        )
    return token


def resolver_solicitud(token, aprobar=True):
    with dbm.abrir() as db:
        sol = db.uno("SELECT * FROM solicitudes_vinculo WHERE token = ?", (token,))
        if not sol:
            return None, "El enlace no existe."
        if sol["estado"] != "pendiente":
            return None, "Ese enlace ya fue usado."
        if sol["expira"] and sol["expira"] < dbm.ahora():
            return None, "El enlace venció. Pedí uno nuevo desde Configuración."
        estado = "aprobada" if aprobar else "rechazada"
        db.ejecutar(
            "UPDATE solicitudes_vinculo SET estado = ?, resuelto = ? WHERE id = ?",
            (estado, dbm.ahora(), sol["id"]),
        )
        if aprobar:
            db.ejecutar(
                "UPDATE politicos SET usuario_id = ? WHERE id = ?",
                (sol["usuario_id"], sol["politico_id"]),
            )
        return sol, None
