"""Politica Eficiente — app Flask.

Un lugar para entender que pasa en la politica uruguaya, opinar, votar y
comparar lo que preocupa a la gente con lo que hacen los cargos publicos.
"""
import json
import os
import smtplib
from email.message import EmailMessage

from flask import (
    Flask, abort, flash, g, redirect, render_template, request, session, url_for,
)
from markupsafe import Markup

import auth
import db as dbm
import desempeno
import flujos as flujosmod
import gamificacion
import mapa as mapamod

app = Flask(__name__)
app.secret_key = auth.clave_secreta()
app.config["MAX_CONTENT_LENGTH"] = 2 * 1024 * 1024


def enviar_aviso(db, para, asunto, cuerpo, enlace=None):
    """Guarda el aviso siempre; si hay SMTP configurado, tambien lo manda."""
    db.ejecutar(
        "INSERT INTO avisos (para, asunto, cuerpo, enlace, creado) VALUES (?, ?, ?, ?, ?)",
        (para, asunto, cuerpo, enlace, dbm.ahora()),
    )
    servidor = os.environ.get("SMTP_HOST")
    if not servidor:
        return False
    try:
        msg = EmailMessage()
        msg["Subject"] = asunto
        msg["From"] = os.environ.get("SMTP_FROM", "no-reply@politicaeficiente.uy")
        msg["To"] = para
        msg.set_content(cuerpo + ("\n\n" + enlace if enlace else ""))
        with smtplib.SMTP(servidor, int(os.environ.get("SMTP_PORT", 587))) as s:
            s.starttls()
            usuario = os.environ.get("SMTP_USER")
            if usuario:
                s.login(usuario, os.environ.get("SMTP_PASS", ""))
            s.send_message(msg)
        return True
    except Exception as e:  # noqa: BLE001 - no romper el flujo por un correo
        app.logger.warning("No se pudo enviar el correo: %s", e)
        return False


@app.context_processor
def inyectar():
    yo = auth.usuario_actual()
    if yo:
        yo["nivel"] = gamificacion.nivel(yo["puntos"])
        yo["grupo"] = gamificacion.datos_grupo(
            gamificacion.grupo(yo["puntos"], yo["acciones"], yo["intereses"] or "")
        )
    with dbm.abrir() as db:
        categorias = [
            f["categoria"]
            for f in db.todos(
                "SELECT categoria, COUNT(*) AS n FROM temas GROUP BY categoria ORDER BY n DESC"
            )
        ]
    return {
        "yo": yo,
        "categorias": categorias,
        "GRUPOS": gamificacion.GRUPOS,
        "ahora": dbm.ahora()[:10],
    }


@app.template_filter("fecha")
def filtro_fecha(texto):
    if not texto:
        return ""
    return str(texto)[:10]


NOMBRES_CATEGORIA = {
    "Educacion": "Educación",
    "Economia": "Economía",
}


@app.template_filter("corto")
def filtro_corto(texto, n=150):
    """Corta en un punto y aparte para no dejar frases a medias."""
    texto = " ".join(str(texto or "").split())
    if len(texto) <= n:
        return texto
    corte = texto.rfind(". ", 0, n)
    if corte > 60:
        return texto[: corte + 1]
    return texto[:n].rstrip() + "…"


@app.template_filter("cat")
def filtro_cat(valor):
    return NOMBRES_CATEGORIA.get(valor, valor)


@app.template_filter("datos")
def filtro_datos(texto):
    """Acepta la lista JSON de las propuestas o el texto separado por ';'."""
    if not texto:
        return []
    texto = str(texto).strip()
    if texto.startswith("["):
        try:
            return [str(x) for x in json.loads(texto)]
        except ValueError:
            return []
    return [parte.strip() for parte in texto.split(";") if parte.strip()]


@app.after_request
def cabeceras(resp):
    resp.headers.setdefault("X-Content-Type-Options", "nosniff")
    resp.headers.setdefault("Referrer-Policy", "same-origin")
    return resp


@app.teardown_appcontext
def cerrar_base(_excepcion=None):
    conexion = g.pop("db", None)
    if conexion is not None:
        conexion.cerrar()


def _slug_de_tema(slug):
    with dbm.abrir() as db:
        return db.uno("SELECT * FROM temas WHERE slug = ?", (slug,))


@app.route("/")
def inicio():
    with dbm.abrir() as db:
        totales = {
            "temas": db.valor("SELECT COUNT(*) FROM temas"),
            "politicos": db.valor("SELECT COUNT(*) FROM politicos"),
            "usuarios": db.valor("SELECT COUNT(*) FROM usuarios WHERE rol != 'admin'"),
            "opiniones": db.valor("SELECT COUNT(*) FROM opiniones"),
            "votos": db.valor("SELECT COUNT(*) FROM votos"),
            "acciones": db.valor("SELECT COUNT(*) FROM acciones"),
        }
        destacados = db.todos(
            """SELECT t.*, (SELECT COUNT(*) FROM votos v WHERE v.tema_id = t.id AND v.valor = 1) AS a_favor,
                      (SELECT COUNT(*) FROM votos v WHERE v.tema_id = t.id AND v.valor = -1) AS en_contra
               FROM temas t ORDER BY a_favor DESC, t.urgencia = 'alta' DESC LIMIT 6"""
        )
        ultimas = db.todos(
            """SELECT a.*, p.nombre, p.emoji FROM acciones a JOIN politicos p ON p.id = a.politico_id
               ORDER BY a.fecha DESC NULLS LAST LIMIT 5"""
        )
        brecha = mapamod.brecha(db)[:4]
    return render_template(
        "inicio.html", totales=totales, destacados=destacados, ultimas=ultimas, brecha=brecha
    )


@app.route("/registro", methods=["GET", "POST"])
def registro():
    if request.method == "POST":
        uid, error = auth.registrar(
            request.form.get("nombre"),
            request.form.get("email"),
            request.form.get("clave"),
            ",".join(request.form.getlist("intereses")),
            request.form.get("departamento", ""),
        )
        if error:
            flash(error, "error")
        else:
            session["usuario_id"] = uid
            flash("¡Bienvenido! Sumaste 10 puntos por registrarte.", "ok")
            return redirect(url_for("inicio"))
    return render_template("registro.html")


@app.route("/ingresar", methods=["GET", "POST"])
def ingresar():
    if request.method == "POST":
        uid, error = auth.ingresar(request.form.get("email"), request.form.get("clave"))
        if error:
            flash(error, "error")
        else:
            session["usuario_id"] = uid
            return redirect(request.args.get("volver") or url_for("inicio"))
    return render_template("ingresar.html")


@app.route("/salir")
def salir():
    session.clear()
    return redirect(url_for("inicio"))


@app.route("/temas")
def temas():
    categoria = request.args.get("categoria", "todas")
    tipo = request.args.get("tipo", "todos")
    orden = request.args.get("orden", "apoyo")
    where, params = [], []
    if categoria != "todas":
        where.append("t.categoria = ?")
        params.append(categoria)
    if tipo != "todos":
        where.append("t.tipo = ?")
        params.append(tipo)
    filtro = ("WHERE " + " AND ".join(where)) if where else ""
    orden_sql = {
        "apoyo": "a_favor DESC, a_favor + en_contra DESC",
        "debate": "opiniones DESC, a_favor DESC",
        "nuevos": "id DESC",
        "urgencia": "CASE urgencia WHEN 'alta' THEN 0 WHEN 'media' THEN 1 ELSE 2 END",
    }.get(orden, "a_favor DESC")
    with dbm.abrir() as db:
        filas = db.todos(
            f"""SELECT * FROM (
                   SELECT t.*,
                          (SELECT COUNT(*) FROM votos v WHERE v.tema_id = t.id AND v.valor = 1) AS a_favor,
                          (SELECT COUNT(*) FROM votos v WHERE v.tema_id = t.id AND v.valor = -1) AS en_contra,
                          (SELECT COUNT(*) FROM opiniones o WHERE o.tema_id = t.id) AS opiniones
                   FROM temas t {filtro}
                ) q ORDER BY {orden_sql}""",
            tuple(params),
        )
    return render_template(
        "temas.html", temas=filas, categoria=categoria, tipo=tipo, orden=orden
    )


@app.route("/tema/<slug>")
def tema(slug):
    with dbm.abrir() as db:
        t = db.uno(
            """SELECT t.*,
                  (SELECT COUNT(*) FROM votos v WHERE v.tema_id = t.id AND v.valor = 1) AS a_favor,
                  (SELECT COUNT(*) FROM votos v WHERE v.tema_id = t.id AND v.valor = -1) AS en_contra
               FROM temas t WHERE t.slug = ?""",
            (slug,),
        )
        if not t:
            abort(404)
        mi_voto = None
        yo = auth.usuario_actual()
        if yo:
            fila = db.uno(
                "SELECT valor FROM votos WHERE usuario_id = ? AND tema_id = ?",
                (yo["id"], t["id"]),
            )
            mi_voto = fila["valor"] if fila else None
        opiniones = db.todos(
            """SELECT o.*, u.nombre, u.puntos,
                      p.nombre AS politico_nombre, p.cargo AS politico_cargo
               FROM opiniones o JOIN usuarios u ON u.id = o.usuario_id
               LEFT JOIN politicos p ON p.id = o.politico_id
               WHERE o.tema_id = ? ORDER BY o.id DESC""",
            (t["id"],),
        )
        posicionados = db.todos(
            """SELECT p.*, pos.valor, pos.nota FROM posiciones pos
               JOIN politicos p ON p.id = pos.politico_id
               WHERE pos.tema_id = ? ORDER BY pos.valor DESC""",
            (t["id"],),
        )
        relacionados = db.todos(
            """SELECT slug, titulo, emoji, categoria FROM temas
               WHERE categoria = ? AND id != ? ORDER BY id DESC LIMIT 5""",
            (t["categoria"], t["id"]),
        )
        acciones = db.todos(
            """SELECT a.*, p.nombre, p.emoji FROM acciones a JOIN politicos p ON p.id = a.politico_id
               WHERE a.tema_categoria = ? ORDER BY a.fecha DESC NULLS LAST LIMIT 6""",
            (t["categoria"],),
        )
    return render_template(
        "tema.html", t=t, mi_voto=mi_voto, opiniones=opiniones,
        posicionados=posicionados, relacionados=relacionados, acciones=acciones,
    )


@app.route("/tema/<slug>/votar", methods=["POST"])
def votar(slug):
    yo = auth.usuario_actual()
    if not yo:
        return redirect(url_for("ingresar", volver=request.path.replace("/votar", "")))
    try:
        valor = 1 if int(request.form.get("valor", 0)) > 0 else -1
    except ValueError:
        abort(400)
    with dbm.abrir() as db:
        t = db.uno("SELECT id, titulo FROM temas WHERE slug = ?", (slug,))
        if not t:
            abort(404)
        previo = db.uno(
            "SELECT id, valor FROM votos WHERE usuario_id = ? AND tema_id = ?",
            (yo["id"], t["id"]),
        )
        if previo and previo["valor"] == valor:
            db.ejecutar("DELETE FROM votos WHERE id = ?", (previo["id"],))
            flash("Quité tu voto.", "ok")
        elif previo:
            db.ejecutar("UPDATE votos SET valor = ? WHERE id = ?", (valor, previo["id"]))
            flash("Cambiaste tu voto.", "ok")
        else:
            db.ejecutar(
                "INSERT INTO votos (usuario_id, tema_id, valor, creado) VALUES (?, ?, ?, ?)",
                (yo["id"], t["id"], valor, dbm.ahora()),
            )
            dbm.registrar_actividad(
                db, yo["id"], "voto", gamificacion.PUNTOS["voto"], f"Votó en {t['titulo']}"
            )
            flash(f"Voto registrado. +{gamificacion.PUNTOS['voto']} puntos.", "ok")
    return redirect(url_for("tema", slug=slug))


@app.route("/tema/<slug>/opinar", methods=["POST"])
@auth.requiere_sesion
def opinar(slug):
    texto = (request.form.get("texto") or "").strip()
    if len(texto) < 3:
        flash("Escribí al menos una frase.", "error")
        return redirect(url_for("tema", slug=slug))
    yo = auth.usuario_actual()
    with dbm.abrir() as db:
        t = db.uno("SELECT id, titulo FROM temas WHERE slug = ?", (slug,))
        if not t:
            abort(404)
        db.ejecutar(
            """INSERT INTO opiniones (tema_id, usuario_id, politico_id, texto, creado)
               VALUES (?, ?, ?, ?, ?)""",
            (t["id"], yo["id"], (yo.get("politico") or {}).get("id"), texto[:2000], dbm.ahora()),
        )
        dbm.registrar_actividad(
            db, yo["id"], "opinion", gamificacion.PUNTOS["opinion"], f"Opinión en {t['titulo']}"
        )
    flash(f"Opinión publicada. +{gamificacion.PUNTOS['opinion']} puntos.", "ok")
    return redirect(url_for("tema", slug=slug) + "#foro")


@app.route("/politicos")
def politicos():
    camara = request.args.get("camara", "todas")
    texto = (request.args.get("q") or "").strip()
    where, params = [], []
    if camara != "todas":
        where.append("camara = ?")
        params.append(camara)
    if texto:
        where.append("(nombre LIKE ? OR cargo LIKE ? OR organismo LIKE ?)")
        params += [f"%{texto}%"] * 3
    filtro = ("WHERE " + " AND ".join(where)) if where else ""
    with dbm.abrir() as db:
        filas = db.todos(
            f"""SELECT p.*, (SELECT COUNT(*) FROM acciones a WHERE a.politico_id = p.id) AS n_acciones,
                       (SELECT COUNT(*) FROM posiciones po WHERE po.politico_id = p.id) AS n_posiciones
                FROM politicos p {filtro}
                ORDER BY CASE camara WHEN 'Poder Ejecutivo' THEN 0 WHEN 'Senadores' THEN 1
                         WHEN 'Diputados' THEN 2 WHEN 'Intendencias' THEN 3 ELSE 4 END, nombre""",
            tuple(params),
        )
        camaras = [f["camara"] for f in db.todos("SELECT DISTINCT camara FROM politicos ORDER BY camara")]
        desempenos = desempeno.todos(db)
    for f in filas:
        f["desempeno"] = desempenos.get(f["id"])
    return render_template("politicos.html", politicos=filas, camara=camara, q=texto, camaras=camaras)


@app.route("/politico/<slug>")
def politico(slug):
    with dbm.abrir() as db:
        p = db.uno("SELECT * FROM politicos WHERE slug = ?", (slug,))
        if not p:
            abort(404)
        acciones = db.todos(
            """SELECT * FROM acciones WHERE politico_id = ?
               ORDER BY CASE estado WHEN 'en_proceso' THEN 0 WHEN 'pendiente' THEN 1 ELSE 2 END,
                        fecha DESC NULLS LAST""",
            (p["id"],),
        )
        posiciones = db.todos(
            """SELECT pos.*, t.titulo, t.emoji, t.slug FROM posiciones pos
               JOIN temas t ON t.id = pos.tema_id WHERE pos.politico_id = ?""",
            (p["id"],),
        )
        cuenta = db.uno("SELECT nombre, email, puntos FROM usuarios WHERE id = ?", (p["usuario_id"],)) if p["usuario_id"] else None
        mi_solicitud = None
        yo = auth.usuario_actual()
        if yo:
            mi_solicitud = db.uno(
                """SELECT * FROM solicitudes_vinculo WHERE politico_id = ? AND usuario_id = ?
                   AND estado = 'pendiente' ORDER BY id DESC LIMIT 1""",
                (p["id"], yo["id"]),
            )
        rendimiento = desempeno.de_politico(db, p["id"])
    return render_template(
        "politico.html", p=p, acciones=acciones, posiciones=posiciones,
        cuenta=cuenta, mi_solicitud=mi_solicitud, rendimiento=rendimiento,
    )


@app.route("/politico/<slug>/solicitar", methods=["POST"])
@auth.requiere_sesion
def solicitar_vinculo(slug):
    yo = auth.usuario_actual()
    with dbm.abrir() as db:
        p = db.uno("SELECT * FROM politicos WHERE slug = ?", (slug,))
        if not p:
            abort(404)
        if p["usuario_id"]:
            flash("Ese cargo ya tiene una cuenta vinculada.", "error")
            return redirect(url_for("politico", slug=slug))
        if not p["email_publico"]:
            flash("Ese cargo no tiene correo público verificado. Pedile al administrador que lo agregue.", "error")
            return redirect(url_for("politico", slug=slug))
        token = auth.crear_solicitud(p["id"], yo["id"])
        enlace = url_for("vincular", token=token, _external=True)
        enviar_aviso(
            db,
            p["email_publico"],
            "Vinculá tu cargo en Política Eficiente",
            f"Hola {p['nombre']}. La cuenta {yo['email']} pidió vincularse con tu cargo "
            f"({p['cargo']}). Si sos vos, abrí este enlace para confirmarlo. Vence en 7 días.",
            enlace,
        )
    flash("Te enviamos un enlace al correo público del cargo. Cuando lo abra, queda vinculado.", "ok")
    return redirect(url_for("politico", slug=slug))


@app.route("/vincular/<token>")
def vincular(token):
    sol, error = auth.resolver_solicitud(token, aprobar=True)
    if error:
        flash(error, "error")
        return redirect(url_for("inicio"))
    with dbm.abrir() as db:
        p = db.uno("SELECT nombre, cargo FROM politicos WHERE id = ?", (sol["politico_id"],))
        dbm.registrar_actividad(
            db, sol["usuario_id"], "vinculo", gamificacion.PUNTOS["vinculo"],
            f"Vinculó su cuenta con {p['cargo']}",
        )
    flash(f"Listo: tu cuenta quedó vinculada con {p['nombre']} ({p['cargo']}).", "ok")
    return redirect(url_for("politico", slug=dbm.consulta(
        "SELECT slug FROM politicos WHERE id = ?", (sol["politico_id"],))[0]["slug"]))


@app.route("/mapa")
def mapa():
    camara = request.args.get("camara", "todas")
    categoria = request.args.get("categoria", "todas")
    with dbm.abrir() as db:
        d = mapamod.datos(db, camara, categoria)
        brecha = mapamod.brecha(db)
        camaras = [f["camara"] for f in db.todos("SELECT DISTINCT camara FROM politicos ORDER BY camara")]
    dibujo = Markup(mapamod.svg(d))
    return render_template(
        "mapa.html", d=d, dibujo=dibujo, brecha=brecha, camaras=camaras,
        camara=camara, categoria=categoria,
    )


@app.route("/perfil")
@auth.requiere_sesion
def perfil():
    yo = auth.usuario_actual()
    with dbm.abrir() as db:
        historial = db.todos(
            "SELECT * FROM actividad WHERE usuario_id = ? ORDER BY id DESC LIMIT 40", (yo["id"],)
        )
        votos = db.todos(
            """SELECT v.valor, v.creado, t.titulo, t.emoji, t.slug FROM votos v
               JOIN temas t ON t.id = v.tema_id WHERE v.usuario_id = ? ORDER BY v.id DESC""",
            (yo["id"],),
        )
        opiniones = db.valor("SELECT COUNT(*) FROM opiniones WHERE usuario_id = ?", (yo["id"],))
        por_tipo = db.todos(
            "SELECT tipo, COUNT(*) AS n FROM actividad WHERE usuario_id = ? GROUP BY tipo", (yo["id"],)
        )
    return render_template(
        "perfil.html", historial=historial, votos=votos, opiniones=opiniones, por_tipo=por_tipo
    )


@app.route("/configuracion", methods=["GET", "POST"])
@auth.requiere_sesion
def configuracion():
    yo = auth.usuario_actual()
    if request.method == "POST":
        nombre = (request.form.get("nombre") or "").strip()
        intereses = ",".join(request.form.getlist("intereses"))
        with dbm.abrir() as db:
            db.ejecutar(
                "UPDATE usuarios SET nombre = ?, intereses = ?, departamento = ? WHERE id = ?",
                (nombre or yo["nombre"], intereses,
                 (request.form.get("departamento") or "").strip(), yo["id"]),
            )
        flash("Preferencias guardadas.", "ok")
        return redirect(url_for("configuracion"))
    with dbm.abrir() as db:
        solicitudes = db.todos(
            """SELECT s.*, p.nombre, p.cargo, p.slug FROM solicitudes_vinculo s
               JOIN politicos p ON p.id = s.politico_id WHERE s.usuario_id = ? ORDER BY s.id DESC""",
            (yo["id"],),
        )
        avisos = db.todos(
            "SELECT * FROM avisos WHERE para = ? ORDER BY id DESC LIMIT 10", (yo["email"],)
        )
    return render_template("configuracion.html", solicitudes=solicitudes, avisos=avisos)


@app.route("/admin")
@auth.requiere_admin
def admin():
    with dbm.abrir() as db:
        solicitudes = db.todos(
            """SELECT s.*, p.nombre AS politico, p.cargo, u.nombre AS usuario, u.email
               FROM solicitudes_vinculo s JOIN politicos p ON p.id = s.politico_id
               JOIN usuarios u ON u.id = s.usuario_id ORDER BY s.id DESC LIMIT 50"""
        )
        avisos = db.todos("SELECT * FROM avisos ORDER BY id DESC LIMIT 20")
        usuarios = db.todos(
            """SELECT id, nombre, email, rol, puntos, creado FROM usuarios
               ORDER BY puntos DESC LIMIT 30"""
        )
        resumen = {
            "temas": db.valor("SELECT COUNT(*) FROM temas"),
            "politicos": db.valor("SELECT COUNT(*) FROM politicos"),
            "usuarios": db.valor("SELECT COUNT(*) FROM usuarios"),
            "votos": db.valor("SELECT COUNT(*) FROM votos"),
            "sin_contacto": db.valor("SELECT COUNT(*) FROM politicos WHERE email_publico IS NULL"),
        }
        rendimientos = desempeno.todos(db)
        ranking = db.todos("SELECT id, nombre, emoji, cargo FROM politicos")
        for r in ranking:
            r["desempeno"] = rendimientos.get(r["id"])
        ranking.sort(key=lambda r: (r["desempeno"]["puntaje"] is None, -(r["desempeno"]["puntaje"] or 0)))
        cfg = desempeno.criterios(db)
    return render_template(
        "admin.html", solicitudes=solicitudes, avisos=avisos, usuarios=usuarios,
        resumen=resumen, ranking=ranking, criterios=cfg, CRITERIOS=desempeno.CRITERIOS,
    )


@app.route("/admin/criterios", methods=["POST"])
@auth.requiere_admin
def admin_criterios():
    with dbm.abrir() as db:
        for clave in desempeno.CRITERIOS:
            valor = (request.form.get(clave) or "").strip().replace(",", ".")
            try:
                numero = float(valor)
            except ValueError:
                continue
            db.ejecutar("UPDATE config SET valor = ? WHERE clave = ?", (str(numero), clave))
    flash("Criterios de desempeño actualizados.", "ok")
    return redirect(url_for("admin"))


@app.route("/admin/solicitud/<int:sid>/<accion>", methods=["POST"])
@auth.requiere_admin
def admin_solicitud(sid, accion):
    with dbm.abrir() as db:
        sol = db.uno("SELECT * FROM solicitudes_vinculo WHERE id = ?", (sid,))
        if not sol:
            abort(404)
        if accion == "aprobar":
            db.ejecutar("UPDATE politicos SET usuario_id = ? WHERE id = ?", (sol["usuario_id"], sol["politico_id"]))
            db.ejecutar(
                "UPDATE solicitudes_vinculo SET estado = 'aprobada', resuelto = ? WHERE id = ?",
                (dbm.ahora(), sid),
            )
            flash("Vínculo aprobado.", "ok")
        elif accion == "rechazar":
            db.ejecutar(
                "UPDATE solicitudes_vinculo SET estado = 'rechazada', resuelto = ? WHERE id = ?",
                (dbm.ahora(), sid),
            )
            flash("Solicitud rechazada.", "ok")
    return redirect(url_for("admin"))


@app.route("/flujos")
def flujos():
    anio = request.args.get("anio")
    anio = int(anio) if (anio or "").isdigit() else None
    with dbm.abrir() as db:
        d = flujosmod.datos(db, anio=anio)
        cl = flujosmod.claves(d)
        comparacion = d["comparacion"]
    dibujo = Markup(flujosmod.svg(d)) if d["hay_datos"] else ""
    return render_template(
        "flujos.html", d=d, dibujo=dibujo, claves=cl, comparacion=comparacion
    )


@app.route("/salud")
def salud():
    with dbm.abrir() as db:
        db.valor("SELECT COUNT(*) FROM temas")
    return {"ok": True, "base": "postgres" if dbm.ES_PG else "sqlite"}


@app.errorhandler(404)
def no_encontrado(_e):
    return render_template("404.html"), 404


if __name__ == "__main__":
    dbm.sembrar()
    app.run(host="127.0.0.1", port=int(os.environ.get("PORT", 5055)), debug=os.environ.get("FLASK_DEBUG") == "1")
else:
    dbm.sembrar()
