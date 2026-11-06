"""Trae la ficha oficial de cada legislador desde el Parlamento.

La ficha no tiene una biografia redactada, pero si datos verificables: distrito,
partido, comisiones en las que actua, grupos de amistad y a quien suplanto.
Cada dato se guarda como hito con la fecha de la legislatura y el enlace oficial.

Uso:
    python traer_legisladores.py --dry     # muestra lo que encontraria
    python traer_legisladores.py           # guarda los hitos
    python traer_legisladores.py --todos   # incluye a quienes ya tienen hitos
"""
import os
import re
import subprocess
import sys
import unicodedata

import db as dbm

BASE = "https://parlamento.gub.uy"
LISTADO = BASE + "/sobreelparlamento/legisladores"
UA = ("Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 "
      "(KHTML, like Gecko) Chrome/124.0 Safari/537.36")
CURL = "curl.exe" if os.name == "nt" else "curl"
ANIO = 2025


def _plano(texto):
    texto = "".join(c for c in unicodedata.normalize("NFD", texto or "")
                    if unicodedata.category(c) != "Mn")
    return re.sub(r"\s+", " ", texto).strip().lower()


def _tokens(texto):
    basura = {"de", "del", "la", "las", "los", "y", "e", "da", "do", "dos", "das"}
    return [t for t in re.split(r"[\s,]+", _plano(texto)) if len(t) > 2 and t not in basura]


def _get(url):
    """Pide la pagina con cara de navegador; curl queda como respaldo."""
    try:
        import subprocess as sp
        import tempfile
        destino = os.path.join(tempfile.gettempdir(), "pe_legislador.html")
        ps = ("$ProgressPreference='SilentlyContinue'; "
              "[Console]::OutputEncoding=[System.Text.Encoding]::UTF8; "
              f"(Invoke-WebRequest -UseBasicParsing -TimeoutSec 40 -Headers @{{'User-Agent'='{UA}'}} "
              f"'{url}').Content | Out-File -FilePath '{destino}' -Encoding utf8")
        sp.run(["powershell", "-NoProfile", "-Command", ps],
               capture_output=True, timeout=60)
        if os.path.exists(destino):
            html = open(destino, encoding="utf-8-sig", errors="replace").read()
            if len(html) > 3000 and "403 ERROR" not in html:
                return html
    except Exception:
        pass
    out = subprocess.run([CURL, "-sL", "-m", "40", "-A", UA, url], capture_output=True)
    return out.stdout.decode("utf-8", "replace")


def _lineas(html):
    cuerpo = re.search(r"<main.*?</main>", html, re.S)
    texto = cuerpo.group(0) if cuerpo else html
    texto = re.sub(r"<script.*?</script>|<style.*?</style>", " ", texto, flags=re.S)
    texto = re.sub(r"<[^>]+>", "\n", texto)
    filas = [" ".join(l.split()) for l in texto.splitlines()]
    return [f for f in filas if f]


def mapado():
    """Devuelve [(nombre_visible, id)] del listado oficial."""
    html = _get(LISTADO)
    pares = re.findall(
        r'href="[^"]*/camarasycomisiones/legisladores/(\d+)"[^>]*>\s*([^<]+?)\s*</a>',
        html, re.S)
    vistos = {}
    for pid, nombre in pares:
        nombre = " ".join(nombre.split())
        if nombre and pid not in vistos:
            vistos[pid] = nombre
    return [(n, int(i)) for i, n in vistos.items()]


def _titulo(texto):
    menores = {"de", "del", "la", "las", "los", "y", "e", "con", "en", "a", "por", "el",
               "departamento"}
    palabras = []
    for i, p in enumerate((texto or "").split()):
        bajo = p.lower()
        palabras.append(bajo if (i and bajo in menores) else bajo[:1].upper() + bajo[1:])
    return " ".join(palabras)


def _ficha(idleg):
    lineas = _lineas(_get(BASE + "/camarasycomisiones/legisladores/%d" % idleg))
    datos = {"cargo": "", "comisiones": [], "grupos": [], "suplanto": ""}
    for i, linea in enumerate(lineas):
        if "por el Lema" in linea and not datos["cargo"]:
            datos["cargo"] = linea
        if linea == "Comisiones en las que actúa":
            j = i + 1
            while j + 2 < len(lineas) and lineas[j] != "Grupos de Amistad Interparlamentarios":
                if lineas[j] == "-->":
                    j += 1
                    continue
                nombre, rol, cuerpo = lineas[j], lineas[j + 1], lineas[j + 2]
                if rol in ("Miembro", "Presidente", "Presidenta", "Secretario",
                           "Secretaria", "Vicepresidente", "Vicepresidenta"):
                    datos["comisiones"].append((nombre, rol, cuerpo))
                    j += 3
                else:
                    j += 1
        if linea == "Grupos de Amistad Interparlamentarios":
            j = i + 1
            while j < len(lineas) and lineas[j] != "Ficha":
                if lineas[j].startswith("URUGUAY"):
                    datos["grupos"].append(lineas[j])
                j += 1
        if linea == "Suplantó a" and not datos["suplanto"]:
            nombre = lineas[i + 1] if i + 1 < len(lineas) else ""
            if nombre.endswith(",") and i + 2 < len(lineas):
                nombre += " " + lineas[i + 2]
            datos["suplanto"] = nombre.replace(" ,", ",").strip()
    return datos


def _hitos(idleg, datos):
    enlace = BASE + "/camarasycomisiones/legisladores/%d" % idleg
    salida = []
    cargo = datos["cargo"].replace("por el Lema ", "por el ")
    if cargo:
        texto = ("Asumió en la Legislatura L (2025-2030): %s." % _titulo(cargo))
        salida.append((ANIO, texto, enlace))
    if datos["suplanto"]:
        salida.append((ANIO, "Ocupó la banca que dejó %s." % _titulo(datos["suplanto"]), enlace))
    for nombre, rol, cuerpo in datos["comisiones"]:
        salida.append((2026, "Integra la comisión %s (%s) como %s."
                       % (_titulo(nombre), _titulo(cuerpo), rol.lower()), enlace))
    for grupo in datos["grupos"]:
        salida.append((2026, "Integra el Grupo de Amistad Interparlamentario %s."
                       % _titulo(grupo), enlace))
    return salida


def main(todos=False, dry=False, limite=None):
    dbm.crear_esquema()
    listado = mapado()
    print("legisladores en el listado oficial:", len(listado), flush=True)
    if not listado:
        print("no se pudo leer el listado")
        return
    indice = {}
    for nombre, idleg in listado:
        indice[_plano(nombre)] = (idleg, nombre)

    with dbm.abrir() as db:
        if todos:
            gente = db.todos("SELECT id, nombre FROM politicos ORDER BY nombre")
        else:
            gente = db.todos(
                "SELECT p.id, p.nombre FROM politicos p WHERE NOT EXISTS "
                "(SELECT 1 FROM hitos h WHERE h.politico_id = p.id) ORDER BY p.nombre")
        guardados = 0
        sin_match = []
        if limite:
            gente = gente[:limite]
        for g in gente:
            nombre = g["nombre"]
            plano = _plano(nombre)
            idleg = None
            tokens_p = set(_tokens(nombre))
            mejor = 0.0
            for clave, (ident, visible) in indice.items():
                # "Apellido, Nombre" contra "Nombre Apellido"
                partes = [p.strip() for p in clave.split(",")]
                if len(partes) == 2:
                    armado = _plano(partes[1] + " " + partes[0])
                else:
                    armado = clave
                if plano == armado:
                    idleg, mejor = ident, 1.0
                    break
                tokens_c = set(_tokens(armado))
                if not tokens_p or not tokens_c:
                    continue
                comunes = len(tokens_p & tokens_c)
                puntaje = comunes / max(len(tokens_p), len(tokens_c))
                if comunes >= 2 and puntaje >= 0.7 and puntaje > mejor:
                    idleg, mejor = ident, puntaje
            if not idleg:
                sin_match.append(nombre)
                continue
            datos = _ficha(idleg)
            hitos = _hitos(idleg, datos)
            print("%-42s id=%-6s %s" % (nombre[:42], idleg,
                                        " | ".join(str(h[1])[:60] for h in hitos[:2])), flush=True)
            if dry:
                continue
            for anio, texto, enlace in hitos:
                existe = db.uno(
                    "SELECT id FROM hitos WHERE politico_id = ? AND texto = ?",
                    (g["id"], texto))
                if existe:
                    continue
                db.ejecutar(
                    "INSERT INTO hitos (politico_id, anio, texto, fuente_url, creado) "
                    "VALUES (?, ?, ?, ?, ?)",
                    (g["id"], anio, texto, enlace, dbm.ahora()))
                guardados += 1
        print("hitos guardados:", guardados)
        if sin_match:
            print("sin ficha oficial:", len(sin_match), "->", ", ".join(sin_match))


if __name__ == "__main__":
    sys.stdout.reconfigure(encoding="utf-8", errors="replace")
    limite = None
    if "--solo" in sys.argv:
        limite = int(sys.argv[sys.argv.index("--solo") + 1])
    main(todos="--todos" in sys.argv, dry="--dry" in sys.argv, limite=limite)
