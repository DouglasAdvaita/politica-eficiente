"""Glosario de términos difíciles, en lenguaje simple.

El filtro `glosario` envuelve la primera aparición de cada término en el texto
de un tema con una ventana emergente. No reemplaza ni resume: solo explica.
"""
import html
import re

GLOSARIO = {
    "gasto tributario": "Dinero que el Estado deja de recaudar por exoneraciones y regímenes especiales. No aparece como gasto en el presupuesto, pero reduce los ingresos.",
    "exoneración": "Excepción legal que libera a alguien de pagar un impuesto. También se llama beneficio tributario.",
    "déficit fiscal": "Cuando el Estado gasta más de lo que recauda en un año. Se cubre con deuda o con reservas.",
    "PIB": "Producto Interno Bruto: el valor de todo lo que produce el país en un año. Se usa como medida de referencia para comparar cifras.",
    "reglamentación": "Decreto que explica cómo se aplica una ley. Sin reglamento, muchos artículos no se pueden ejecutar.",
    "derogar": "Dejar sin efecto una norma. No es lo mismo que modificarla: la derogación la elimina del ordenamiento.",
    "sanción": "Castigo previsto por una norma para quien la incumple. También se usa para la aprobación de una ley por el Parlamento; el contexto indica cuál.",
    "presunción de inocencia": "Regla según la cual nadie es culpable hasta que una sentencia firme lo declare. Impide castigar por sospechas.",
    "medidas cautelares": "Decisiones judiciales provisorias para proteger a una persona o asegurar un proceso mientras se resuelve el caso.",
    "tasa de prisionalización": "Cantidad de personas presas por cada 100.000 habitantes. Permite comparar países con distinta población.",
    "reincidencia": "Volver a cometer un delito después de haber sido condenado por otro.",
    "femicidio": "Homicidio de una mujer por razones de género. En Uruguay se tipificó como agravante del homicidio.",
    "interseccionalidad": "Idea de que una persona puede sufrir varias discriminaciones a la vez (por género, etnia, discapacidad, territorio) y que se refuerzan entre sí.",
    "autonomía fiscal": "Capacidad de un organismo o gobierno de recaudar y decidir sus propios recursos, sin depender de una partida ajena.",
    "licitación pública": "Procedimiento por el que el Estado compra bienes o servicios, con reglas y ofertas comparables.",
    "cupo": "Porcentaje de puestos reservado por ley para un grupo determinado.",
    "ajustes razonables": "Cambios en el entorno o en la forma de trabajar que permiten a una persona con discapacidad desempeñarse en igualdad de condiciones.",
    "primera infancia": "Etapa de 0 a 5 años, donde se concentran cuidados, estimulación y detección temprana.",
    "desvinculación": "Abandono del sistema educativo por parte de un estudiante matriculado.",
    "valorización": "Recuperar materiales de los residuos para volver a usarlos, en lugar de enterrarlos o quemarlos.",
    "responsabilidad extendida": "Regla que obliga al fabricante a hacerse cargo de un producto cuando termina su vida útil.",
    "inseguridad alimentaria": "Situación en que un hogar reduce la cantidad o la calidad de lo que come por falta de dinero u otros recursos.",
    "canasta básica": "Conjunto de bienes y servicios que se considera mínimo para vivir. Su costo se usa para medir pobreza y precios.",
    "aprobación ficta": "Cuando un proyecto se considera aprobado porque la autoridad no respondió en plazo, aunque hubiera objeciones técnicas.",
    "sumario": "Investigación administrativa interna para determinar si un funcionario cometió una falta y qué sanción corresponde.",
    "preaviso": "Aviso obligatorio con anticipación antes de iniciar una huelga o un lockout.",
    "lockout": "Cierre patronal: decisión del empleador de paralizar la actividad como medida de presión.",
    "subsidio": "Ayuda económica del Estado para abaratar un servicio o sostener un ingreso.",
    "IRAE": "Impuesto a las Rentas de las Actividades Económicas: el principal tributo que pagan las empresas.",
    "hacinamiento": "Más personas de las que el lugar admite, con servicios e infraestructura insuficientes.",
    "partida": "Monto concreto que el presupuesto asigna a un organismo, programa u obra.",
}

ALIASES = {
    "exoneraciones": "exoneración",
    "sanciones": "sanción",
    "femicidios": "femicidio",
    "cupos": "cupo",
    "sumarios": "sumario",
    "licitaciones": "licitación pública",
    "subsidios": "subsidio",
    "partidas": "partida",
}

_DEFINICIONES = {clave.lower(): valor for clave, valor in GLOSARIO.items()}
_DEFINICIONES.update(
    {variante: GLOSARIO[canonica] for variante, canonica in ALIASES.items()}
)
_TERMINOS = sorted(set(GLOSARIO) | set(ALIASES), key=len, reverse=True)
_PATRON = re.compile(
    r"(?<![\wáéíóúüñ])(" + "|".join(re.escape(t) for t in _TERMINOS) + r")(?![\wáéíóúüñ])",
    re.IGNORECASE,
)


def marcar(texto, limite=6):
    """Devuelve el texto escapado, con hasta `limite` términos explicados."""
    if not texto:
        return ""
    salida = html.escape(str(texto))
    partes, ultimo, usados = [], 0, 0
    for m in _PATRON.finditer(salida):
        if usados >= limite:
            break
        definicion = _DEFINICIONES.get(m.group(1).lower())
        if not definicion:
            continue
        partes.append(salida[ultimo:m.start()])
        partes.append(
            '<span class="palabra" tabindex="0" data-tip="%s">%s</span>'
            % (html.escape(definicion, quote=True), m.group(0))
        )
        ultimo = m.end()
        usados += 1
    partes.append(salida[ultimo:])
    return "".join(partes)
