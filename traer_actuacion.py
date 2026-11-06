"""Trae la actuacion parlamentaria oficial de cada legislador.

La ficha del Parlamento expone un JSON con cada hecho: proyectos presentados,
pedidos de informes, informes en comision y exposiciones, con fecha y enlace
al documento. Se guardan solo los hechos con contenido, no el trámite menor
(convocatorias, intervenciones o firmas).

Uso:
    python traer_actuacion.py --dry
    python traer_actuacion.py
    python traer_actuacion.py --solo 5
"""
import html
import json
import re
import subprocess
import sys
import unicodedata
from urllib.parse import quote

import db as dbm
import traer_legisladores as leg

UA = leg.UA
BASE = leg.BASE
DESDE = "2025-02-15"
HASTA = "2030-02-14"

ACCIONES = (
    ("Presenta el proyecto de ley", "Presentó un proyecto de ley"),
    ("Presenta el proyecto de resolución", "Presentó un proyecto de resolución"),
    ("Solicita pedido de informes", "Pidió informes"),
    ("Informante en la comisión", "Fue informante en la comisión"),
)

PROPIOS = {"banco", "previsión", "social", "caja", "profesional", "código", "penal",
           "ley", "artículo", "ministerio", "intendencia", "poder", "judicial",
           "legislativo", "república", "estado", "nacional", "consejo", "comisión",
           "cámara", "senado", "diputados", "tribunal", "corte", "fiscalía",
           "instituto", "agencia", "servicio", "dirección", "programa"}

ACRONIMOS = {"MSP", "MTSS", "MIDES", "MI", "MA", "MTOP", "MEC", "ANEP", "UTU",
             "OSE", "BPS", "BROU", "ANTEL", "ANCAP", "IRAE", "IVA", "PIB",
             "URCDP", "ARCE", "INAU", "ASSE", "OPP", "MVOT", "MGAP", "INEFOP", "N"}


def _get_json(url):
    ps = ("$ProgressPreference='SilentlyContinue'; "
          "[Console]::OutputEncoding=[System.Text.Encoding]::UTF8; "
          f"(Invoke-WebRequest -UseBasicParsing -TimeoutSec 60 -Headers @{{'User-Agent'='{UA}'}} "
          f"'{url}').Content")
    out = subprocess.run(["powershell", "-NoProfile", "-Command", ps],
                         capture_output=True, timeout=90)
    texto = out.stdout.decode("utf-8", "replace").strip()
    if not texto.startswith("["):
        return []
    try:
        return json.loads(texto)
    except ValueError:
        return []


def _limpio(markup):
    enlaces = re.findall(r'href="([^"]+)"', markup or "")
    texto = re.sub(r"<[^>]+>", " ", markup or "")
    texto = " ".join(html.unescape(texto).split())
    return texto, (enlaces[0] if enlaces else "")


def _frase(texto):
    """Pasa un título en mayúsculas a frase, conservando siglas."""
    palabras = (texto or "").split()
    if not palabras:
        return ""
    con_mayus = [p for p in palabras if p.isupper() and len(re.sub(r"[^\w]", "", p)) >= 2]
    if len(con_mayus) < max(2, len(palabras) * 0.4):
        return texto
    salida = []
    for p in palabras:
        limpio = re.sub(r"[^\w]", "", p)
        if limpio in ACRONIMOS:
            salida.append(p)
        elif p.isupper() and limpio.lower() in PROPIOS:
            salida.append(p[:1].upper() + p[1:].lower())
        elif p.isupper():
            salida.append(p.lower())
        else:
            salida.append(p)
    frase = " ".join(salida)
    return frase[:1].upper() + frase[1:]


def _hecho(registro):
    texto, enlace = _limpio(registro.get("Texto", ""))
    fecha = registro.get("Fecha", "")
    m = re.match(r"(\d{2})-(\d{2})-(\d{4})", fecha)
    if not m:
        return None
    anio = int(m.group(3))
    etiqueta = None
    for prefijo, valor in ACCIONES:
        if texto.lower().startswith(prefijo.lower()):
            etiqueta = valor
            break
    if not etiqueta:
        return None
    # El asunto va después del último ";".
    asunto = texto.split(";")[-1].strip() if ";" in texto else ""
    asunto = re.split(r"\s+Se da cuenta", asunto)[0]
    asunto = re.sub(r"\s*tomo\s+\d+.*$", "", asunto, flags=re.I)
    asunto = re.sub(r"\s*d\.s\.\s*\d+.*$", "", asunto, flags=re.I)
    asunto = re.sub(r"\s*Carpeta[:.]?\s*\S+\s*", " ", asunto).strip(" .;")
    if asunto:
        partes = [_frase(p.strip()) for p in asunto.split(" - ")]
        cuerpo = "%s: %s." % (etiqueta, " - ".join(partes))
    else:
        cuerpo = "%s." % etiqueta
    cuerpo = re.sub(r"\s+", " ", cuerpo)
    return anio, cuerpo, enlace


def _url(idleg):
    return ("%s/camarasycomisiones/legisladores/%d/actuacion-legislador/json"
            "?Fecha_desde=%s&Fecha_hasta=%s&_format=json"
            % (BASE, idleg, quote(DESDE), quote(HASTA)))


def main(dry=False, limite=None):
    dbm.crear_esquema()
    listado = leg.mapado()
    indice = {}
    for nombre, idleg in listado:
        indice[leg._plano(nombre)] = (idleg, nombre)

    with dbm.abrir() as db:
        gente = db.todos("SELECT id, nombre FROM politicos ORDER BY nombre")
    if limite:
        gente = gente[:limite]
    total = 0
    for g in gente:
        plano = leg._plano(g["nombre"])
        idleg, mejor = None, 0.0
        tokens_p = set(leg._tokens(g["nombre"]))
        for clave, (ident, visible) in indice.items():
            partes = [p.strip() for p in clave.split(",")]
            armado = leg._plano(partes[1] + " " + partes[0]) if len(partes) == 2 else clave
            if plano == armado:
                idleg = ident
                break
            tokens_c = set(leg._tokens(armado))
            if not tokens_p or not tokens_c:
                continue
            comunes = len(tokens_p & tokens_c)
            puntaje = comunes / max(len(tokens_p), len(tokens_c))
            if comunes >= 2 and puntaje >= 0.7 and puntaje > mejor:
                idleg, mejor = ident, puntaje
        if not idleg:
            continue
        registros = _get_json(_url(idleg))
        if not registros:
            print("%-40s sin datos" % g["nombre"][:40], flush=True)
            continue
        nuevos = 0
        hechos = [h for h in (_hecho(r) for r in registros) if h]
        if len(hechos) > 60:
            hechos = hechos[-60:]   # los 60 hechos mas recientes
        try:
            with dbm.abrir() as db:   # una conexion por legislador: si se corta, no pierde el resto
                for anio, texto, enlace in hechos:
                    enlace = enlace or ("%s/camarasycomisiones/legisladores/%d" % (BASE, idleg))
                    if db.uno("SELECT id FROM hitos WHERE politico_id = ? AND texto = ?",
                              (g["id"], texto)):
                        continue
                    if not dry:
                        db.ejecutar(
                            "INSERT INTO hitos (politico_id, anio, texto, fuente_url, creado) "
                            "VALUES (?, ?, ?, ?, ?)",
                            (g["id"], anio, texto, enlace, dbm.ahora()))
                    nuevos += 1
        except Exception as e:
            print("%-40s error: %s" % (g["nombre"][:40], str(e)[:60]), flush=True)
            continue
        total += nuevos
        print("%-40s %3d hechos nuevos" % (g["nombre"][:40], nuevos), flush=True)
    print("total nuevos:", total)


if __name__ == "__main__":
    sys.stdout.reconfigure(encoding="utf-8", errors="replace")
    lim = None
    if "--solo" in sys.argv:
        lim = int(sys.argv[sys.argv.index("--solo") + 1])
    main(dry="--dry" in sys.argv, limite=lim)
