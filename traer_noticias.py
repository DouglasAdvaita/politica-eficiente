"""Recolecta noticias recientes de cada cargo publico desde Google News RSS y las
guarda en la base (SQLite local o Neon/Postgres via DATABASE_URL).

Cada noticia guarda titulo, medio, fecha y enlace tal cual llegan del RSS. Se
deduplica por URL. La correlacion con el cargo se hace por nombre y queda en el
campo `estado`:

  - aceptada:    aparece nombre de pila + apellido, o los dos apellidos, o un
                 apellido que es unico entre los 148 cargos (p. ej. "Orsi").
  - por_revisar: solo un apellido comun (posible homonimo), se decide a mano.
  - descartada:  no menciona a la persona.

Este script NO escribe en la linea de tiempo: solo junta los registros crudos.
La correlacion final y la subida a hitos se hace con `procesar_noticias.py`.

Uso:
    python traer_noticias.py             # todos los cargos
    python traer_noticias.py --solo 5    # prueba con los primeros 5
    python traer_noticias.py --sin-bio   # solo los que no tienen biografia
"""
import os
import re
import subprocess
import sys
import threading
import time
import unicodedata
import urllib.parse
from email.utils import parsedate_to_datetime

import db as dbm

CURL = "curl.exe" if os.name == "nt" else "curl"
UA = "Mozilla/5.0 (compatible; PoliticaEficiente/0.1; +proyecto civico)"
INTERVALO = 1.0
_LOCK = threading.Lock()
_ULTIMO = [0.0]
RSS = "https://news.google.com/rss/search?q={q}&hl=es-419&gl=UY&ceid=UY:es-419"
POR_PERSONA = 15


def _plano(texto):
    return "".join(c for c in unicodedata.normalize("NFD", texto or "")
                   if unicodedata.category(c) != "Mn").lower()


def _tokens(nombre):
    basura = {"de", "del", "la", "las", "los", "y", "e", "da", "do", "dos", "das"}
    return [t for t in re.split(r"[\s\-]+", _plano(nombre)) if len(t) > 2 and t not in basura]


def _get(url):
    for intento in range(4):
        with _LOCK:
            falta = _ULTIMO[0] + INTERVALO - time.time()
            if falta > 0:
                time.sleep(falta)
            _ULTIMO[0] = time.time()
        try:
            out = subprocess.run([CURL, "-sL", "-m", "30", "-A", UA, url],
                                 capture_output=True, timeout=45)
            if out.returncode == 0 and out.stdout:
                return out.stdout.decode("utf-8", "replace")
        except Exception:
            pass
        time.sleep(3 * (intento + 1))
    return ""


def _limpio(t):
    t = (t or "").replace("&amp;", "&").replace("&quot;", '"').replace("&#39;", "'")
    t = t.replace("&lt;", "<").replace("&gt;", ">").replace("&nbsp;", " ")
    return re.sub(r"\s+", " ", t).strip()


def _items(xml):
    salida = []
    for bloque in re.findall(r"<item>(.*?)</item>", xml, re.S):
        t = re.search(r"<title>(.*?)</title>", bloque, re.S)
        l = re.search(r"<link>(.*?)</link>", bloque, re.S)
        d = re.search(r"<pubDate>(.*?)</pubDate>", bloque, re.S)
        s = re.search(r"<source[^>]*>(.*?)</source>", bloque, re.S)
        if not t or not l:
            continue
        salida.append({
            "titulo": _limpio(t.group(1)),
            "url": l.group(1).strip(),
            "fecha": d.group(1).strip() if d else "",
            "medio": _limpio(s.group(1)) if s else "",
        })
    return salida


def _fecha_iso(pub):
    try:
        dt = parsedate_to_datetime(pub)
        return dt.date().isoformat(), dt.year
    except Exception:
        return "", None


def clasificar(nombre, titulo, apellido_conteo):
    """Devuelve 'aceptada', 'por_revisar' o 'descartada'."""
    tokens = _tokens(nombre)
    if not tokens:
        return "descartada"
    plano = _plano(titulo)
    pila, apellidos = tokens[0], tokens[1:]
    if not apellidos:
        return "por_revisar" if pila in plano else "descartada"
    if pila in plano and any(a in plano for a in apellidos):
        return "aceptada"
    if len(apellidos) >= 2 and all(a in plano for a in apellidos):
        return "aceptada"
    for a in apellidos:
        if a in plano:
            return "aceptada" if apellido_conteo.get(a, 0) == 1 else "por_revisar"
    return "descartada"


def recolectar(limite=None, solo_sin_bio=False):
    dbm.crear_esquema()
    todos = dbm.consulta("SELECT id, slug, nombre FROM politicos")
    apellido_conteo = {}
    for t in todos:
        for a in _tokens(t["nombre"])[1:]:
            apellido_conteo[a] = apellido_conteo.get(a, 0) + 1

    if solo_sin_bio:
        gente = dbm.consulta(
            "SELECT p.id, p.slug, p.nombre FROM politicos p "
            "LEFT JOIN biografias b ON b.politico_id = p.id "
            "WHERE b.id IS NULL ORDER BY p.nombre")
    else:
        gente = todos
    if limite:
        gente = gente[:limite]

    nuevas = 0
    with dbm.abrir() as db:
        for i, g in enumerate(gente, 1):
            nombre = g["nombre"]
            q = urllib.parse.quote(f'"{nombre}" Uruguay')
            xml = _get(RSS.format(q=q))
            items = _items(xml) if xml else []
            a = r = d = 0
            for it in items[:POR_PERSONA]:
                estado = clasificar(nombre, it["titulo"], apellido_conteo)
                if estado == "descartada":
                    d += 1
                    continue
                fecha, anio = _fecha_iso(it["fecha"])
                cur = db.ejecutar(
                    """INSERT INTO noticias (url, titulo, medio, fecha, anio, politico_id,
                           estado, creado)
                       VALUES (?, ?, ?, ?, ?, ?, ?, ?)
                       ON CONFLICT (url) DO NOTHING""",
                    (it["url"], it["titulo"], it["medio"], fecha, anio,
                     g["id"] if estado == "aceptada" else None, estado, dbm.ahora()),
                )
                if cur.rowcount:
                    nuevas += 1
                    if estado == "aceptada":
                        a += 1
                    else:
                        r += 1
            db.commit()
            print(f"[{i}/{len(gente)}] {nombre}: {a} nuevas, {r} por revisar, "
                  f"{d} descartadas", flush=True)
    print(f"\ntotal nuevas en noticias: {nuevas}")


if __name__ == "__main__":
    sys.stdout.reconfigure(encoding="utf-8", errors="replace")
    limite = None
    if "--solo" in sys.argv:
        limite = int(sys.argv[sys.argv.index("--solo") + 1])
    recolectar(limite=limite, solo_sin_bio="--sin-bio" in sys.argv)
