"""Recolecta biografias de legisladores y cargos del Ejecutivo desde la Wikipedia
en espanol.

Genera datos/fuentes/biografias.json. Cada dato queda atado al articulo del
que sale: la app lo muestra como fuente secundaria y con enlace para auditar.
No inventa nada: si un dato no aparece en el articulo, queda vacio.

Uso:
    python traer_biografias.py            # todos los legisladores
    python traer_biografias.py --solo 5   # prueba con los primeros 5
"""
import json
import os
import re
import subprocess
import sys
import threading
import time
import unicodedata
import urllib.parse

BASE = os.path.dirname(os.path.abspath(__file__))
FUENTES = os.path.join(BASE, "datos", "fuentes")
CACHE = os.path.join(BASE, "datos", "cache_wikipedia")
SALIDA = os.path.join(FUENTES, "biografias.json")
API = "https://es.wikipedia.org/w/api.php"
UA = "PoliticaEficiente/0.1 (proyecto civico; datos publicos con fuente)"
INTERVALO = 1.0
_LOCK = threading.Lock()
_ULTIMO = [0.0]

ARCHIVOS = ("politicos.json", "senadores.json", "diputados_a_f.json",
            "diputados_g_o.json", "diputados_p_z.json", "diputados_faltantes.json")

MESES = ("enero|febrero|marzo|abril|mayo|junio|julio|agosto|setiembre|septiembre|"
         "octubre|noviembre|diciembre")
RE_NAC = re.compile(r"\(([^()]{2,60}?),\s*(\d{1,2} de (?:" + MESES + r") de (\d{4}))\)")
RE_NAC_SOLA = re.compile(r"\((\d{1,2} de (?:" + MESES + r") de (\d{4}))\)")
ROLES = ("polític", "ministr", "intendente", "senador", "senadora", "diputad", "fiscal",
         "canciller", "jerarca", "subsecretari", "secretari", "presidencia", "vicepresident")
RE_PROF = re.compile(r"es (?:un|una) ([^.]{3,160}?) uruguay[oa]", re.I)
RE_ANIO = re.compile(r"\b(1[89]\d\d|20[0-2]\d)\b")

CLAVES_HITO = (
    "elect", "senador", "senadora", "diputad", "ministr", "intendente", "asumi",
    "candidat", "fundó", "fundo", "ingresó", "militó", "presidente", "subsecretari",
    "director", "directora", "edil", "junta", "partido", "gobierno", "secretari",
    "delegad", "representante", "renunci", "designad", "nombrad", "promulg",
    "votó", "voto", "ley", "embajador", "rector", "gerente", "presidi",
)
CLAVES_FAMILIA = ("hijo", "hija", "padre", "madre", "hermano", "hermana", "esposa",
                  "esposo", "pareja", "casó", "casado", "casada", "matrimonio",
                  "divorci", "viudo", "viuda", "nieto", "abuelo", "tío", "primo")
CLAVES_AMISTAD = ("amigo", "amiga", "amistad", "compañero de fórmula", "mentor",
                  "discípulo", "referente político")
CLAVES_VINCULO_POL = ("hijo del", "hija del", "sobrino", "sobrina", "hermano del",
                      "hermana del", "esposa del", "esposo de la", "viuda de")
RUIDO = ("== Referencias ==", "== Enlaces externos ==", "== Véase también ==",
         "== Notas ==", "== Bibliografía ==")
_RUTA_BUSQUEDAS = os.path.join(CACHE, "busquedas.json")
_BUSQUEDAS = {}
if os.path.exists(_RUTA_BUSQUEDAS):
    with open(_RUTA_BUSQUEDAS, encoding="utf-8") as _f:
        _BUSQUEDAS = json.load(_f)


def _get(params):
    """curl anda en segundos donde urllib espera IPv6 y tarda 15 s.

    Wikipedia limita rafagas: una peticion por segundo como maximo y
    reintentos con espera creciente. Si aun asi falla, devuelve {} y el
    recolector sigue con la siguiente persona.
    """
    params = dict(params, format="json")
    url = API + "?" + urllib.parse.urlencode(params)
    for intento in range(6):
        with _LOCK:
            falta = _ULTIMO[0] + INTERVALO - time.time()
            if falta > 0:
                time.sleep(falta)
            _ULTIMO[0] = time.time()
        try:
            out = subprocess.run(
                ["curl.exe", "-s", "-m", "30", "-A", UA, "-w", "\n__CODIGO__%{http_code}", url],
                capture_output=True, timeout=45,
            )
            crudo = out.stdout.decode("utf-8", "replace")
            cuerpo, _, codigo = crudo.rpartition("__CODIGO__")
            if codigo.strip() == "200" and cuerpo.strip().startswith("{"):
                return json.loads(cuerpo)
        except Exception:
            pass
        time.sleep(6 * (intento + 1))
    print("  aviso: Wikipedia no respondio; se salta esta consulta", flush=True)
    return {}


def _plano(texto):
    return "".join(c for c in unicodedata.normalize("NFD", texto or "")
                   if unicodedata.category(c) != "Mn").lower()


def _tokens(nombre):
    basura = {"de", "del", "la", "las", "los", "y", "e", "da", "do", "dos", "das"}
    return [t for t in re.split(r"[\s\-]+", _plano(nombre)) if len(t) > 2 and t not in basura]


def _puntaje_titulo(nombre, titulo):
    """Exige dos coincidencias y algun apellido en el titulo.

    Evita el error tipico de agarrar a otra persona que comparte un apellido
    comun (por ejemplo un Lopez cualquiera para Gonzalo Civila Lopez).
    """
    tokens = _tokens(nombre)
    if not tokens:
        return 0
    titulo_plano = _plano(titulo)
    coincidencias = sum(1 for t in tokens if t in titulo_plano)
    if not any(a in titulo_plano for a in tokens[1:]):
        return 0
    return coincidencias


def titulos_candidatos(nombre):
    """Variantes razonables del nombre, con acentos y mayusculas como titula Wikipedia."""
    palabras = [p for p in re.split(r"\s+", nombre.strip()) if p]
    if not palabras:
        return []
    particulas = {"de", "del", "la", "las", "los", "y", "e", "da", "do", "dos", "das"}
    variantes = [" ".join(palabras)]
    if len(palabras) >= 3 and palabras[-2].lower() not in particulas:
        sin_materno = " ".join(palabras[:-1])
        variantes += [sin_materno, sin_materno + " (político)"]
        corto = palabras[0] + " " + palabras[-2]
        variantes += [corto, corto + " (político)"]
    if len(palabras) == 2:
        variantes.append(palabras[0] + " " + palabras[1] + " (político)")
    # Titulos con particula en minuscula ("Alfredo de Mattos").
    minuscula = " ".join(p.lower() if p.lower() in particulas else p for p in palabras)
    variantes.append(minuscula)
    limpias, vistas = [], set()
    for v in variantes:
        v = re.sub(r"\s+", " ", v).strip()
        if v and v.lower() not in vistas:
            vistas.add(v.lower())
            limpias.append(v)
    return limpias


def por_titulo(nombre):
    """Prueba los titulos probables de una vez y devuelve el texto si existe."""
    candidatos = titulos_candidatos(nombre)
    if not candidatos:
        return None, ""
    for c in candidatos:
        ruta = _ruta_cache(c)
        if os.path.exists(ruta):
            with open(ruta, encoding="utf-8") as f:
                texto = f.read()
            if texto:
                return c, texto
    j = _get({"action": "query", "prop": "extracts|pageprops", "explaintext": 1,
              "redirects": 1, "titles": "|".join(candidatos)})
    paginas = j.get("query", {}).get("pages", {})
    orden = {c.lower(): i for i, c in enumerate(candidatos)}
    for pagina in sorted(paginas.values(),
                         key=lambda p: orden.get((p.get("title") or "").lower(), 99)):
        if pagina.get("missing") is not None:
            continue
        texto = pagina.get("extract") or ""
        if texto:
            _guardar_cache(pagina.get("title") or "", texto)
            return pagina.get("title"), texto
    return None, ""


def buscar(nombre, partido=""):
    """Una consulta por persona; la del partido queda como respaldo."""
    clave = f"{nombre}|{partido}"
    with _LOCK:
        if clave in _BUSQUEDAS:
            return list(_BUSQUEDAS[clave])
    consultas = [f'"{nombre}" Uruguay']
    if partido:
        consultas.append(f'"{nombre}" "{partido}"')
    consultas.append(f"{nombre} Uruguay político")
    consultas.append(f'"{nombre}"')
    titulos = []
    for consulta in consultas:
        j = _get({"action": "query", "list": "search", "srsearch": consulta, "srlimit": 6})
        if not j:
            continue
        titulos = [x["title"] for x in j.get("query", {}).get("search", [])]
        if any(_puntaje_titulo(nombre, t) >= 2 for t in titulos):
            break
    with _LOCK:
        _BUSQUEDAS[clave] = titulos
        with open(_RUTA_BUSQUEDAS, "w", encoding="utf-8") as f:
            json.dump(_BUSQUEDAS, f, ensure_ascii=False)
    return titulos


def _ruta_cache(titulo):
    return os.path.join(CACHE, re.sub(r"[^A-Za-z0-9_-]+", "_", titulo) + ".txt")


def _guardar_cache(titulo, texto):
    os.makedirs(CACHE, exist_ok=True)
    with open(_ruta_cache(titulo), "w", encoding="utf-8") as f:
        f.write(texto)


def extracto(titulo):
    ruta = _ruta_cache(titulo)
    if os.path.exists(ruta):
        with open(ruta, encoding="utf-8") as f:
            return f.read()
    j = _get({"action": "query", "prop": "extracts", "explaintext": 1,
              "redirects": 1, "titles": titulo})
    paginas = list(j.get("query", {}).get("pages", {}).values())
    texto = (paginas[0].get("extract", "") if paginas else "") or ""
    if not texto:
        return ""
    _guardar_cache(titulo, texto)
    return texto


def _limpio(texto):
    texto = (texto or "").replace("\u200b", "").replace("\xa0", " ")
    for marca in RUIDO:
        texto = texto.split(marca)[0]
    texto = re.sub(r"=+[^=\n]{1,80}=+", " ", texto)
    texto = re.sub(r"\[\d+\]", "", texto)
    texto = re.sub(r"[ \t]+", " ", texto)
    texto = re.sub(r"\n{2,}", "\n\n", texto)
    return texto.strip()


def oraciones(texto):
    texto = _limpio(texto)
    texto = re.sub(r"\s+", " ", texto)
    return [s.strip(" .;\u200b") for s in re.split(r"(?<=[.!?])\s+", texto) if s.strip()]


def _valida(titulo, texto, nombre, apellido):
    if not texto or len(texto) < 400:
        return False
    if "puede referirse a" in texto[:300].lower():
        return False
    if _puntaje_titulo(nombre, titulo) < 2:
        return False
    primera = _plano(titulo.split()[0]) if titulo.split() else ""
    if primera not in _tokens(nombre):
        return False
    inicio = _plano(texto[:500])
    tokens = _tokens(nombre)
    if not any(a in inicio for a in tokens[1:]) or not any(t in inicio for t in tokens[:-2] or tokens[:1]):
        return False
    # Con dos nombres de pila (Juan Pedro) no alcanza con que aparezca uno:
    # asi no se confunde a la persona con su padre o con un homonimo.
    pila = tokens[:-2]
    if len(pila) >= 2 and sum(1 for t in pila if t in inicio) < 2:
        return False
    # El segundo apellido evita homonimos con apellido comun (William Martinez
    # futbolista no es William Martinez Zaquierez).
    if len(tokens) >= 3 and tokens[-1] not in inicio:
        return False
    bajo = _plano(texto[:1200])
    return ("uruguay" in bajo or "uruguayo" in bajo or "uruguaya" in bajo) and \
        any(_plano(r) in _plano(texto[:800]) for r in ROLES)


def extraer(nombre, titulo, partido=""):
    texto = extracto(titulo)
    url = "https://es.wikipedia.org/wiki/" + urllib.parse.quote(titulo.replace(" ", "_"))
    intro = _limpio(texto.split("\n\n")[0]) if texto else ""
    nac = RE_NAC.search(intro) or RE_NAC.search(texto[:1500])
    lugar = fecha = None
    if nac:
        lugar, fecha = nac.group(1), nac.group(2)
    else:
        sola = RE_NAC_SOLA.search(intro) or RE_NAC_SOLA.search(texto[:1500])
        if sola:
            fecha = sola.group(1)
    prof = RE_PROF.search(intro)
    anio_nac = int(re.search(r"(\d{4})", fecha).group(1)) if fecha else None
    frases = oraciones(texto)
    resumen = ". ".join(frases[:2])[:700] if frases else ""

    formacion = None
    for o in frases:
        bajo = _plano(o)
        if len(o) <= 240 and ("universidad" in bajo or "facultad" in bajo) and any(
                k in bajo for k in ("estudi", "gradu", "egresad", "recibi", "curs")):
            formacion = o
            break

    vinculos, textos_vinculo = [], set()
    for o in frases:
        if len(o) > 260:
            continue
        bajo = _plano(o)
        tipo = None
        if any(c in bajo for c in CLAVES_AMISTAD) or any(c in bajo for c in CLAVES_VINCULO_POL):
            tipo = "vinculo"
        elif any(c in bajo for c in CLAVES_FAMILIA):
            tipo = "familiar"
        if tipo:
            vinculos.append({"tipo": tipo, "descripcion": o})
            textos_vinculo.add(o)

    piso = anio_nac or 1935
    hitos, vistos = [], set()
    for o in frases:
        if len(o) < 25 or len(o) > 280 or o in textos_vinculo:
            continue
        m = RE_ANIO.search(o)
        if not m:
            continue
        anio = int(m.group(1))
        if anio < piso or anio > time.localtime().tm_year + 1:
            continue
        bajo = _plano(o)
        if not any(c in bajo for c in CLAVES_HITO):
            continue
        if fecha and fecha in o:
            continue
        clave = (anio, bajo[:50])
        if clave in vistos:
            continue
        vistos.add(clave)
        hitos.append({"anio": anio, "texto": o[0].upper() + o[1:] + ("" if o.endswith(".") else ".")})
    hitos.sort(key=lambda h: (h["anio"], h["texto"]))

    return {
        "articulo": titulo,
        "url": url,
        "nacimiento_fecha": fecha,
        "nacimiento_lugar": lugar,
        "profesion": prof.group(1).strip() if prof else None,
        "formacion": formacion,
        "resumen": resumen,
        "hitos": hitos[:16],
        "vinculos": vinculos[:8],
        "_largo_articulo": len(texto),
    }


def legisladores():
    vistos, filas = set(), []
    for archivo in ARCHIVOS:
        ruta = os.path.join(FUENTES, archivo)
        if not os.path.exists(ruta):
            continue
        with open(ruta, encoding="utf-8") as f:
            datos = json.load(f)
        for p in datos.get("politicos") or datos.get("faltantes") or []:
            slug = p.get("slug")
            if not slug or slug in vistos:
                continue
            vistos.add(slug)
            filas.append({"slug": slug, "nombre": p.get("nombre", ""),
                          "partido": p.get("partido") or "",
                          "camara": p.get("camara", "")})
    return filas


def _procesar(p):
    nombre, partido = p["nombre"], p["partido"]
    try:
        titulo, texto = por_titulo(nombre)
        if titulo and _valida(titulo, texto, nombre, ""):
            datos = extraer(nombre, titulo, partido)
            datos.update({"slug": p["slug"], "nombre": nombre})
            return datos, None, [titulo]
        candidatos = buscar(nombre, partido)
        candidatos = sorted(set(candidatos), key=lambda t: -_puntaje_titulo(nombre, t))
        probados = 0
        for titulo in candidatos:
            if _puntaje_titulo(nombre, titulo) < 2:
                continue
            probados += 1
            if probados > 3:
                break
            texto = extracto(titulo)
            if _valida(titulo, texto, nombre, ""):
                datos = extraer(nombre, titulo, partido)
                datos.update({"slug": p["slug"], "nombre": nombre})
                return datos, None, candidatos
        return None, f"sin articulo validado (candidatos: {candidatos[:3]})", candidatos
    except Exception as e:  # noqa: BLE001 - una persona rota no frena a las demas
        return None, f"error: {type(e).__name__}", []


def recolectar(limite=None):
    from concurrent.futures import ThreadPoolExecutor, as_completed

    gente = legisladores()
    if limite:
        gente = gente[:limite]
    salida, fallos = [None] * len(gente), []
    with ThreadPoolExecutor(max_workers=2) as pool:
        futuros = {pool.submit(_procesar, p): i for i, p in enumerate(gente)}
        listos = 0
        for futuro in as_completed(futuros):
            i = futuros[futuro]
            datos, motivo, candidatos = futuro.result()
            listos += 1
            if datos:
                salida[i] = datos
                print(f"[{listos}/{len(gente)}] {datos['nombre']}: {datos['articulo']} "
                      f"({len(datos['hitos'])} hitos, {len(datos['vinculos'])} vinculos)", flush=True)
            else:
                fallos.append({"slug": gente[i]["slug"], "nombre": gente[i]["nombre"],
                               "motivo": motivo})
                print(f"[{listos}/{len(gente)}] {gente[i]['nombre']}: {motivo}", flush=True)
    salida = [d for d in salida if d]

    contenido = {
        "fuente": "Wikipedia en español",
        "licencia": "CC BY-SA 4.0",
        "advertencia": ("Datos tomados de articulos de Wikipedia y atribuidos en cada ficha. "
                        "Es fuente secundaria: debe contrastarse con el Parlamento o el IMPO."),
        "generado": time.strftime("%Y-%m-%dT%H:%M:%S"),
        "legisladores": salida,
        "sin_articulo": fallos,
    }
    with open(SALIDA, "w", encoding="utf-8") as f:
        json.dump(contenido, f, ensure_ascii=False, indent=1)
    print(f"\nguardado {SALIDA}: {len(salida)} con articulo, {len(fallos)} sin articulo")


if __name__ == "__main__":
    sys.stdout.reconfigure(encoding="utf-8", errors="replace")
    limite = None
    if "--solo" in sys.argv:
        limite = int(sys.argv[sys.argv.index("--solo") + 1])
    recolectar(limite)
