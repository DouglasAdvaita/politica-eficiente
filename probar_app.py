import os
import sys

RAIZ = os.path.dirname(os.path.abspath(__file__))
sys.path.insert(0, RAIZ)
os.chdir(RAIZ)

RUTA_PRUEBA = os.path.join(RAIZ, "_prueba.db")
for sufijo in ("", "-journal", "-wal", "-shm"):
    try:
        os.remove(RUTA_PRUEBA + sufijo)
    except OSError:
        pass
os.environ["POLITICA_DB"] = RUTA_PRUEBA

import app as mod
import db as dbm

mod.app.config["TESTING"] = True
c = mod.app.test_client()

for r in ["/", "/temas", "/mapa", "/politicos", "/registro", "/ingresar", "/salud"]:
    resp = c.get(r)
    print(r, resp.status_code, len(resp.data))

with dbm.abrir() as db:
    tema = db.uno("SELECT slug FROM temas LIMIT 1")
    pol = db.uno("SELECT slug, email_publico FROM politicos WHERE email_publico IS NOT NULL LIMIT 1")
    con_acciones = db.uno("SELECT COUNT(*) AS n FROM politicos WHERE id IN (SELECT politico_id FROM acciones)")["n"]
print("tema", tema, "pol", pol)

for r in [f"/tema/{tema['slug']}"]:
    resp = c.get(r)
    print(r, resp.status_code, len(resp.data))
if pol:
    resp = c.get(f"/politico/{pol['slug']}")
    print("politico", resp.status_code, len(resp.data))

resp = c.post("/registro", data={
    "nombre": "Prueba Ciudadana", "email": "prueba@ejemplo.uy",
    "clave": "clave12345", "departamento": "Montevideo",
    "intereses": ["Salud", "Educacion"],
}, follow_redirects=True)
print("registro", resp.status_code)

resp = c.post(f"/tema/{tema['slug']}/votar", data={"valor": "1"}, follow_redirects=True)
print("voto", resp.status_code, "Voto registrado" in resp.get_data(as_text=True))

resp = c.post(f"/tema/{tema['slug']}/opinar", data={"texto": "Me parece un tema central."}, follow_redirects=True)
print("opinion", resp.status_code, "Me parece un tema central" in resp.get_data(as_text=True))

for r in ["/perfil", "/configuracion"]:
    resp = c.get(r)
    print(r, resp.status_code)

resp = c.post(f"/politico/{pol['slug']}/solicitar", follow_redirects=True) if pol else None
print("solicitar", resp.status_code if resp else "sin cargos")
with dbm.abrir() as db:
    sol = db.uno("SELECT token, estado FROM solicitudes_vinculo ORDER BY id DESC LIMIT 1")
print("solicitud", sol)
if sol:
    resp = c.get(f"/vincular/{sol['token']}", follow_redirects=True)
    print("vincular", resp.status_code)
    with dbm.abrir() as db:
        print("vinculo en base", db.uno("SELECT usuario_id, nombre FROM politicos WHERE slug = ?", (pol["slug"],)))
    resp = c.post(f"/tema/{tema['slug']}/opinar", data={"texto": "Postura del cargo desde la app."}, follow_redirects=True)
    with dbm.abrir() as db:
        fila = db.uno("SELECT politico_id FROM opiniones ORDER BY id DESC LIMIT 1")
    print("opinion con cargo", resp.status_code, fila)

c.get("/salir")
with dbm.abrir() as db:
    admin = db.uno("SELECT email FROM usuarios WHERE rol='admin'")
resp = c.post("/ingresar", data={"email": admin["email"], "clave": dbm.clave_admin()}, follow_redirects=True)
print("login admin", resp.status_code)
resp = c.get("/admin")
print("/admin", resp.status_code, len(resp.data))

for r in ["/mapa?camara=Senadores", "/mapa?categoria=Salud", "/temas?tipo=ley&orden=urgencia"]:
    resp = c.get(r)
    print(r, resp.status_code, len(resp.data))
