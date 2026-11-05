"""Capa de datos de Politica Eficiente.

SQLite local ahora; el mismo esquema corre en Neon/Postgres cambiando
DATABASE_URL. Los placeholders se escriben con '?' y se traducen a '%s'.
"""
import json
import os
import secrets
import socket
import sqlite3
from contextlib import contextmanager
from datetime import datetime, timezone
from urllib.parse import urlparse

from flask import g, has_app_context

BASE = os.path.dirname(os.path.abspath(__file__))
RUTA_DB = os.environ.get("POLITICA_DB") or os.path.join(BASE, "politica.db")
CARPETA_FUENTES = os.path.join(BASE, "datos", "fuentes")
URL = os.environ.get("DATABASE_URL", "").strip()
ES_PG = URL.startswith("postgres")
AUTO = "SERIAL PRIMARY KEY" if ES_PG else "INTEGER PRIMARY KEY AUTOINCREMENT"


def ahora():
    return datetime.now(timezone.utc).isoformat(timespec="seconds")


ESQUEMA = f"""
CREATE TABLE IF NOT EXISTS usuarios (
    id {AUTO},
    email TEXT UNIQUE NOT NULL,
    nombre TEXT NOT NULL,
    clave_hash TEXT NOT NULL,
    rol TEXT NOT NULL DEFAULT 'ciudadano',
    puntos INTEGER NOT NULL DEFAULT 0,
    intereses TEXT NOT NULL DEFAULT '',
    departamento TEXT NOT NULL DEFAULT '',
    creado TEXT NOT NULL,
    ultimo_acceso TEXT
);

CREATE TABLE IF NOT EXISTS politicos (
    id {AUTO},
    slug TEXT UNIQUE NOT NULL,
    nombre TEXT NOT NULL,
    cargo TEXT NOT NULL DEFAULT '',
    camara TEXT NOT NULL DEFAULT '',
    organismo TEXT NOT NULL DEFAULT '',
    partido TEXT NOT NULL DEFAULT '',
    departamento TEXT NOT NULL DEFAULT '',
    emoji TEXT NOT NULL DEFAULT '🏛️',
    funciones TEXT NOT NULL DEFAULT '',
    email_publico TEXT,
    telefono_oficina TEXT,
    celular_publico TEXT,
    web TEXT,
    contacto_fuente_url TEXT,
    verificado SMALLINT NOT NULL DEFAULT 0,
    usuario_id INTEGER,
    creado TEXT NOT NULL
);

CREATE TABLE IF NOT EXISTS solicitudes_vinculo (
    id {AUTO},
    politico_id INTEGER NOT NULL,
    usuario_id INTEGER NOT NULL,
    token TEXT UNIQUE NOT NULL,
    estado TEXT NOT NULL DEFAULT 'pendiente',
    creado TEXT NOT NULL,
    expira TEXT,
    resuelto TEXT
);

CREATE TABLE IF NOT EXISTS temas (
    id {AUTO},
    slug TEXT UNIQUE NOT NULL,
    tipo TEXT NOT NULL DEFAULT 'propuesta',
    titulo TEXT NOT NULL,
    resumen TEXT NOT NULL DEFAULT '',
    categoria TEXT NOT NULL DEFAULT 'Social',
    subcategoria TEXT NOT NULL DEFAULT '',
    emoji TEXT NOT NULL DEFAULT '📌',
    problema TEXT NOT NULL DEFAULT '',
    evidencia TEXT NOT NULL DEFAULT '',
    propuesta TEXT NOT NULL DEFAULT '',
    datos_clave TEXT NOT NULL DEFAULT '',
    urgencia TEXT NOT NULL DEFAULT 'media',
    etapa TEXT NOT NULL DEFAULT 'propuesta',
    impacto TEXT NOT NULL DEFAULT 'medio',
    estado_legal TEXT NOT NULL DEFAULT '',
    fuente_url TEXT,
    verificado SMALLINT NOT NULL DEFAULT 0,
    creado TEXT NOT NULL
);

CREATE TABLE IF NOT EXISTS votos (
    id {AUTO},
    usuario_id INTEGER NOT NULL,
    tema_id INTEGER NOT NULL,
    valor SMALLINT NOT NULL,
    creado TEXT NOT NULL,
    UNIQUE (usuario_id, tema_id)
);

CREATE TABLE IF NOT EXISTS opiniones (
    id {AUTO},
    tema_id INTEGER NOT NULL,
    usuario_id INTEGER NOT NULL,
    politico_id INTEGER,
    padre_id INTEGER,
    texto TEXT NOT NULL,
    creado TEXT NOT NULL
);

CREATE TABLE IF NOT EXISTS acciones (
    id {AUTO},
    politico_id INTEGER NOT NULL,
    titulo TEXT NOT NULL,
    descripcion TEXT NOT NULL DEFAULT '',
    estado TEXT NOT NULL DEFAULT 'pendiente',
    fecha TEXT,
    tema_categoria TEXT NOT NULL DEFAULT '',
    fuente_url TEXT,
    creado TEXT NOT NULL
);

CREATE TABLE IF NOT EXISTS posiciones (
    id {AUTO},
    politico_id INTEGER NOT NULL,
    tema_id INTEGER NOT NULL,
    valor SMALLINT NOT NULL,
    nota TEXT NOT NULL DEFAULT '',
    creado TEXT NOT NULL,
    UNIQUE (politico_id, tema_id)
);

CREATE TABLE IF NOT EXISTS actividad (
    id {AUTO},
    usuario_id INTEGER NOT NULL,
    tipo TEXT NOT NULL,
    puntos INTEGER NOT NULL DEFAULT 0,
    detalle TEXT NOT NULL DEFAULT '',
    creado TEXT NOT NULL
);

CREATE TABLE IF NOT EXISTS avisos (
    id {AUTO},
    para TEXT NOT NULL,
    asunto TEXT NOT NULL,
    cuerpo TEXT NOT NULL DEFAULT '',
    enlace TEXT,
    creado TEXT NOT NULL
);

CREATE TABLE IF NOT EXISTS config (
    clave TEXT PRIMARY KEY,
    valor TEXT NOT NULL,
    descripcion TEXT NOT NULL DEFAULT ''
);

CREATE INDEX IF NOT EXISTS idx_votos_tema ON votos (tema_id);
CREATE INDEX IF NOT EXISTS idx_acciones_pol ON acciones (politico_id);
CREATE INDEX IF NOT EXISTS idx_opiniones_tema ON opiniones (tema_id);
CREATE INDEX IF NOT EXISTS idx_actividad_usuario ON actividad (usuario_id);
"""


def conectar():
    if ES_PG:
        import psycopg2
        import psycopg2.extras
        c = psycopg2.connect(
            _url_postgres(),
            cursor_factory=psycopg2.extras.RealDictCursor,
            connect_timeout=15,
            application_name="politica-eficiente",
        )
        c.autocommit = False
        return c
    c = sqlite3.connect(RUTA_DB, timeout=15)
    c.row_factory = sqlite3.Row
    c.execute("PRAGMA foreign_keys = ON")
    return c


_URL_PG = None


def _url_postgres():
    """En Windows fija la IP IPv4: la espera de IPv6 cuelga la conexión.

    En Linux (Render) se usa la URL tal cual, que resuelve bien.
    """
    global _URL_PG
    if _URL_PG:
        return _URL_PG
    url = URL
    if os.name == "nt":
        try:
            partes = urlparse(url)
            if partes.hostname and "hostaddr=" not in url:
                infos = socket.getaddrinfo(
                    partes.hostname, partes.port or 5432, socket.AF_INET, socket.SOCK_STREAM
                )
                ip = infos[0][4][0]
                url = f"{url}{'&' if partes.query else '?'}hostaddr={ip}"
        except Exception:
            pass
    _URL_PG = url
    return url


def _traducir(sql):
    return sql.replace("?", "%s") if ES_PG else sql


class DB:
    """Envoltorio minimo para escribir el mismo SQL en SQLite y Postgres."""

    def __init__(self, conexion=None):
        self.c = conexion or conectar()

    def ejecutar(self, sql, params=()):
        cur = self.c.cursor()
        cur.execute(_traducir(sql), params)
        return cur

    def uno(self, sql, params=()):
        fila = self.ejecutar(sql, params).fetchone()
        return dict(fila) if fila is not None else None

    def todos(self, sql, params=()):
        return [dict(f) for f in self.ejecutar(sql, params).fetchall()]

    def valor(self, sql, params=()):
        fila = self.uno(sql, params)
        return next(iter(fila.values())) if fila else None

    def commit(self):
        self.c.commit()

    def rollback(self):
        self.c.rollback()

    def cerrar(self):
        try:
            self.c.close()
        except Exception:
            pass


@contextmanager
def abrir():
    """Una conexion por pedido: clave para no agotar Neon."""
    if has_app_context():
        if "db" not in g:
            g.db = DB()
        db = g.db
        try:
            yield db
            db.commit()
        except Exception:
            db.rollback()
            raise
        return
    db = DB()
    try:
        yield db
        db.commit()
    except Exception:
        db.rollback()
        raise
    finally:
        db.cerrar()


def consulta(sql, params=()):
    with abrir() as db:
        return db.todos(sql, params)


def crear_esquema():
    with abrir() as db:
        for sentencia in ESQUEMA.split(";"):
            if sentencia.strip():
                db.ejecutar(sentencia)


def registrar_actividad(db, usuario_id, tipo, puntos, detalle=""):
    db.ejecutar(
        "INSERT INTO actividad (usuario_id, tipo, puntos, detalle, creado) VALUES (?, ?, ?, ?, ?)",
        (usuario_id, tipo, puntos, detalle, ahora()),
    )
    db.ejecutar(
        "UPDATE usuarios SET puntos = puntos + ? WHERE id = ?", (puntos, usuario_id)
    )


def _leer(nombre):
    ruta = os.path.join(CARPETA_FUENTES, nombre)
    if not os.path.exists(ruta):
        return None
    with open(ruta, encoding="utf-8") as f:
        return json.load(f)


def _cargar_temas(db):
    leyes = _leer("leyes.json") or {}
    for ley in leyes.get("leyes", []):
        db.ejecutar(
            """INSERT INTO temas (slug, tipo, titulo, resumen, categoria, subcategoria,
                   emoji, problema, evidencia, propuesta, urgencia, etapa, impacto,
                   estado_legal, fuente_url, verificado, creado)
               VALUES (?, 'ley', ?, ?, ?, ?, ?, ?, ?, ?, ?, 'en_debate', ?, ?, ?, ?, ?)
               ON CONFLICT (slug) DO NOTHING""",
            (
                ley.get("slug"), ley.get("titulo", ""), "",
                ley.get("categoria", "Gobierno"), ley.get("subcategoria", ""),
                ley.get("emoji", "⚖️"), ley.get("problema", ""), ley.get("evidencia", ""),
                ley.get("propuesta", ""), ley.get("impacto", "medio"),
                ley.get("impacto", "medio"), ley.get("estado", ""),
                ley.get("fuente_url"), 1 if ley.get("verificado") else 0, ahora(),
            ),
        )
    propuestas = _leer("propuestas.json") or {}
    for prop in propuestas.get("propuestas", []):
        db.ejecutar(
            """INSERT INTO temas (slug, tipo, titulo, resumen, categoria, subcategoria,
                   emoji, problema, evidencia, propuesta, datos_clave, urgencia, etapa,
                   impacto, estado_legal, fuente_url, verificado, creado)
               VALUES (?, 'propuesta', ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, 'medio', '', ?, ?, ?)
               ON CONFLICT (slug) DO NOTHING""",
            (
                prop.get("slug"), prop.get("titulo", ""), prop.get("resumen", ""),
                prop.get("categoria", "Social"), prop.get("subcategoria", ""),
                prop.get("emoji", "📌"), prop.get("resumen", ""),
                "; ".join(prop.get("datos_clave") or []), prop.get("propuesta", ""),
                json.dumps(prop.get("datos_clave") or [], ensure_ascii=False),
                prop.get("urgencia", "media"), prop.get("etapa", "propuesta"),
                (prop.get("fuentes") or [{}])[0].get("url"),
                1 if prop.get("verificado") else 0, ahora(),
            ),
        )


def _cargar_politicos(db):
    datos = _leer("politicos.json") or {}
    for p in datos.get("politicos", []):
        db.ejecutar(
            """INSERT INTO politicos (slug, nombre, cargo, camara, organismo, partido,
                   departamento, emoji, funciones, email_publico, telefono_oficina,
                   celular_publico, web, contacto_fuente_url, verificado, creado)
               VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
               ON CONFLICT (slug) DO NOTHING""",
            (
                p.get("slug"), p.get("nombre", ""), p.get("cargo", ""),
                p.get("camara", "Organismos"), p.get("organismo", ""),
                p.get("partido") or "", p.get("departamento") or "",
                p.get("emoji", "🏛️"), p.get("funciones", ""),
                p.get("email_publico"), p.get("telefono_oficina"),
                p.get("celular_publico"), p.get("web"), p.get("contacto_fuente_url"),
                1 if p.get("verificado") else 0, ahora(),
            ),
        )
        fila = db.uno("SELECT id FROM politicos WHERE slug = ?", (p.get("slug"),))
        if not fila:
            continue
        for act in p.get("actividades") or []:
            db.ejecutar(
                """INSERT INTO acciones (politico_id, titulo, descripcion, estado, fecha,
                       tema_categoria, fuente_url, creado)
                   VALUES (?, ?, ?, ?, ?, ?, ?, ?)""",
                (
                    fila["id"], act.get("titulo", ""), act.get("descripcion", ""),
                    act.get("estado", "pendiente"), act.get("fecha"),
                    act.get("tema", ""), act.get("fuente_url"), ahora(),
                ),
            )


def clave_admin():
    ruta = os.path.join(BASE, "datos", "clave_admin.txt")
    if os.environ.get("ADMIN_CLAVE"):
        return os.environ["ADMIN_CLAVE"]
    if os.path.exists(ruta):
        with open(ruta, encoding="utf-8") as f:
            return f.read().strip()
    clave = secrets.token_urlsafe(10)
    os.makedirs(os.path.dirname(ruta), exist_ok=True)
    with open(ruta, "w", encoding="utf-8") as f:
        f.write(clave)
    return clave


def sembrar():
    """Carga fuentes y crea el administrador. Es idempotente."""
    crear_esquema()
    with abrir() as db:
        if not db.valor("SELECT COUNT(*) FROM temas"):
            _cargar_temas(db)
        if not db.valor("SELECT COUNT(*) FROM politicos"):
            _cargar_politicos(db)
        if not db.valor("SELECT COUNT(*) FROM usuarios"):
            from werkzeug.security import generate_password_hash

            email = os.environ.get("ADMIN_EMAIL") or "admin@politicaeficiente.uy"
            db.ejecutar(
                """INSERT INTO usuarios (email, nombre, clave_hash, rol, puntos, creado)
                   VALUES (?, ?, ?, 'admin', 0, ?)""",
                (email, "Administración", generate_password_hash(clave_admin()), ahora()),
            )
        import desempeno

        desempeno.sembrar_criterios(db)
