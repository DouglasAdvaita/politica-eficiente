import os
from urllib.parse import urlparse

import psycopg2

RUTA = "datos/dsn_neon.txt"
with open(RUTA, encoding="utf-8") as f:
    dsn = f.read().strip()

partes = urlparse(dsn)
c = psycopg2.connect(
    host=partes.hostname,
    hostaddr=__import__("socket").getaddrinfo(partes.hostname, 5432, __import__("socket").AF_INET)[0][4][0],
    port=5432,
    user=partes.username,
    password=partes.password,
    dbname="neondb",
    sslmode="require",
    connect_timeout=20,
)
c.autocommit = True
cur = c.cursor()
cur.execute("SELECT datname FROM pg_database WHERE datname = 'politica_eficiente_test'")
if cur.fetchone():
    cur.execute(
        "SELECT pg_terminate_backend(pid) FROM pg_stat_activity "
        "WHERE datname = 'politica_eficiente_test' AND pid <> pg_backend_pid()"
    )
    cur.execute("DROP DATABASE politica_eficiente_test")
    print("base de prueba eliminada")
else:
    print("no existía la base de prueba")
cur.execute("SELECT datname FROM pg_database WHERE datname LIKE 'politica%'")
print("bases:", [f[0] for f in cur.fetchall()])
c.close()
