"""Crea (si falta) una base propia en el proyecto Neon que ya usa RAVE.

No imprime credenciales: solo host y nombre de base.
"""
import os
import re
import socket
import sys
from urllib.parse import urlparse, urlunparse

import psycopg2

ENV_RAVE = r"C:\Mis Documentos\_superacion\Codex\DisenioHumano - para prueba OpenCode\.env"
NUEVA = sys.argv[1] if len(sys.argv) > 1 else "politica_eficiente"


def leer_dsn():
    if os.environ.get("DATABASE_URL"):
        return os.environ["DATABASE_URL"].strip()
    with open(ENV_RAVE, encoding="utf-8", errors="ignore") as f:
        for linea in f:
            if linea.strip().startswith("DATABASE_URL="):
                return linea.split("=", 1)[1].strip().strip('"').strip("'")
    return ""


def con_database(dsn, base):
    partes = urlparse(dsn)
    return urlunparse(partes._replace(path="/" + base))


dsn = leer_dsn()
if not dsn:
    print("sin DATABASE_URL")
    sys.exit(1)

partes = urlparse(dsn)
base_actual = partes.path.lstrip("/")
print("host:", partes.hostname, flush=True)
print("base actual:", base_actual, flush=True)
print("params:", partes.query, flush=True)

ipv4 = None
for info in socket.getaddrinfo(partes.hostname, partes.port or 5432, socket.AF_INET, socket.SOCK_STREAM):
    ipv4 = info[4][0]
    break
print("ipv4:", ipv4, flush=True)
print("conectando...", flush=True)

c = psycopg2.connect(
    host=partes.hostname,
    hostaddr=ipv4,
    port=partes.port or 5432,
    user=partes.username,
    password=partes.password,
    dbname=base_actual,
    sslmode="require",
    connect_timeout=20,
    application_name="politica-eficiente-setup",
)
print("conectado", flush=True)
c.autocommit = True
cur = c.cursor()
cur.execute("SELECT version()")
print("servidor:", cur.fetchone()[0].split(",")[0])
cur.execute("SELECT datname FROM pg_database WHERE datname = %s", (NUEVA,))
existe = cur.fetchone()
if not existe:
    cur.execute(f'CREATE DATABASE "{NUEVA}"')
    print("base creada:", NUEVA)
else:
    print("la base ya existía:", NUEVA)
cur.execute("SELECT current_user")
print("usuario:", cur.fetchone()[0])
c.close()

nuevo = con_database(dsn, NUEVA)
print("dsn nuevo listo para:", urlparse(nuevo).hostname, "/", urlparse(nuevo).path.lstrip("/"))
with open("datos/dsn_neon.txt", "w", encoding="utf-8") as f:
    f.write(nuevo)
print("dsn guardado en datos/dsn_neon.txt (ignorado por git)")
