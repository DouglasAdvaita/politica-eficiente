"""Actualiza el sitio de forma automatica.

Corre los recopiladores disponibles y deja la base lista para servir.
Uso:
    python actualizar_sitio.py            # actualizacion completa
    python actualizar_sitio.py --solo-actuacion   # solo actividad parlamentaria
    python actualizar_sitio.py --dry       # no escribe en la base

Programar en Windows (una vez, como administrador):
    schtasks /Create /TN "PoliticaEficiente_Actualizar" /TR "python C:\\ruta\\actualizar_sitio.py" /SC DAILY /ST 03:00
"""
import subprocess
import sys
import os

ROOT = os.path.dirname(os.path.abspath(__file__))
PY = sys.executable

pasos = [
    ("Actividad parlamentaria", [PY, "traer_actuacion.py"]),
    ("Marcar importancia de acciones", [PY, "marcar_acciones.py"]),
]

dry = "--dry" in sys.argv
solo_act = "--solo-actuacion" in sys.argv

if solo_act:
    pasos = [pasos[0]]

for nombre, cmd in pasos:
    if dry and "traer_actuacion" in cmd[1]:
        cmd = cmd + ["--dry"]
    print("==>", nombre, flush=True)
    r = subprocess.run(cmd, cwd=ROOT)
    if r.returncode != 0:
        print("FALLO:", nombre, "codigo", r.returncode, flush=True)
        sys.exit(r.returncode)

print("Actualizacion terminada.")
print("Nota: 'Lo ultimo que hicieron los cargos' viene de datos/fuentes/politicos.json")
print("(importar_politicos.py). Para automatizarlo hace falta un recopilador de")
print("actividad parlamentaria hacia la tabla 'acciones', todavia no implementado.")
