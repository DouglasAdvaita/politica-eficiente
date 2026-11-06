# Política Eficiente

## Objetivo
Una app web (y luego APK) donde cualquier persona entiende qué pasa en la política uruguaya:
qué temas preocupan, qué opinan y votan los ciudadanos, qué hacen los cargos públicos y dónde
se cruzan o se ignoran esas dos cosas. Con datos con fuente, gamificación y foros.

## Problema
La información política está dispersa, en lenguaje técnico y sin comparación entre lo que la
gente pide y lo que se hace. No existe un lugar único, abierto y verificable donde seguir un
tema, ver la actividad de cada cargo y medir el desvío.

## Pedido textual
> Se me ocurre que podría estar bueno hacer una app de código abierto que tenga un agestuon pública de cambios y mejoras sociales a las leyes actuales y gestión política que la gente pueda enterarse, opinar y votar para que en el futuro pueda cuando tenga mucho peso de usuarios ser adoptada por algún político que pueda marcar que si haría de las propuestas y que durante su gestión se pueda ir viendo lo que hace y cuando y verificado por los usuarios o de alguna forma pública y a partir de eso que el programa asigne o determine si está trabajando o no o si debe continuar en el cargo según un criterio de configuración para los cargos. Debería considerarse como son las dinámicas de autorización política y su posible evolución futura si es por decretos, leyes u otras operativas. Ponlo en un proyecto local en Codex con el nombre Política eficiente (pero que seguirá el mismo camino que @Rave de git, render, neón, apk) La app debe tener temas relevantes para el usuario que pueda seguir. Debe tener un aprecarga de leyes que actualmente son ineficaces (esto es un estudio largo de algún su agente) o presentar propuestas a temas sociales relevantes actualmente (otro sub agente para determinar los) presentados por categorías y subcategorías de forma lúdica como gamificación y con emojis descriptivos. El usuario tendrá puntos, niveles y contadores de actividad para estimularse a contribuir con votos y opiniones. Por ahora será en una dB local pero transferible luego a neón. Estudiarlo con diseño UX/UI. Que aparezcan los políticos y directores de organismos públicos con sus cel y correos y funciones para contacto y sus actividades (otro sub agente para cargar esa tarea). La app debe tener un servidor SVG que permita ver y filtrar políticos y tareas públicas actuales, pendientes y en proceso y líneas vinculantes que ayuden a ver la dinámica actual y que quede claro a qué se le da prioridad y que se descuida y que cosas los usuarios les preocupa en comparación con lo que se hace, algo como líneas de diferentes colores para políticos y usuarios (los usuarios todos representados por diferentes grosores de línea sobre el total. Ej 100 político a la derecha en 4 columnas de 25 (pueden ser filtrados por senadores, diputados, ministros, etc, como rectángulos con nombre, una sección de temas de interés 20 en la izquierda y abajo al medio los usuarios por sus categorías (simple, muy activo, con intereses, etc) y líneas entre estos y los temas. Los usuarios que serán muchos se suman para aumentar grosores, ej si el 100% de un grupo apoyará poner Max grosor y el nro de pmusuarios de esa categoría que le interesó. Las líneas de los políticos pueden ser de colores según a favor o en contra. Debe incluir un apartado de foros para discutir cada tema que se abra al debate por usuario o político. En realidad un político debe poder ingresar como usuario a su elemento cuando quiera solicitarlo para poder votar desde adentro de la app (siendo validado por el administrador dándole un link por correo que permita que el tenga un usuario (de político) asociado a su nombre que tiene una parte automática de lo que el sistema encuentra de su actividad pública y su usuario controlar sus voluntades y acciones. El sistema de poder mostrar lo más claramente y gráfico lo que está pasando con leches, decretos y actividades de la política, para ver y entender la dinámica del país, que sea atractivo y jerarquizado como para que la población prefiera informarse por esta vía como elemento claro de visualización de la actividad política del país.

## Decisiones tomadas con el usuario
- País: **Uruguay**. Cargos: presidente y ministros, senadores, diputados, intendentes y directores de organismos.
- Contacto: **solo canales oficiales publicados**. Celular únicamente si el propio cargo u organismo lo publicó, con URL de fuente.
- Ingreso: **orientado al público general**. Toda persona se registra como ciudadano.
- Vínculo de un cargo: un usuario común lo solicita desde la ficha del cargo; el sistema manda un
  enlace al **correo público del cargo**; quien controle ese correo confirma. El político conserva
  su cuenta común y queda asociado al cargo. El administrador puede aprobar o rechazar.

## Alcance
- **Incluye:** app Flask, SQLite local portable a Neon, registro e ingreso, temas (leyes y propuestas),
  votos, foros, gamificación, directorio de cargos, actividades, vínculo de cargos por correo,
  mapa SVG con filtros, panel de brechas, desempeño configurable, panel de administración.
- **No incluye todavía:** APK Android, envío real de correo (queda guardado si no hay SMTP),
  carga automática de actividades desde fuentes oficiales, verificación de identidad del político
  más allá del correo público, moderación automática de foros.

## Restricciones
- Rutas: `C:\Mis Documentos\_superacion\Codex\PoliticaEficiente`.
- Mismo camino que RAVE: git, Render (gunicorn + `render.yaml`), estética clara y sobria (grises,
  color solo para el estado de gestión), APK después.
- SQL con `?` traducido a `%s`: el mismo esquema corre en SQLite y Postgres/Neon.
- Sin datos personales inventados. Todo contacto lleva fuente y marca de verificación.
- **Sin datos ficticios en pantalla.** Si no hay usuarios, votos o noticias, la sección no se muestra;
  no se dibujan líneas de ejemplo ni se explica por qué falta.
- **Neutralidad editorial con contraste obligatorio.** Ninguna cifra se muestra sola: cada dato va con
  su universo comparable (por ejemplo, muertes por feminicidio frente al total de homicidios, siniestros
  de tránsito y suicidios del mismo período) y con la fuente de cada número.
- Lo que no está en un registro oficial se muestra como **testimonio o tendencia de redes**, con fecha,
  volumen y la aclaración de que no es una muestra representativa.
- Una tesis discutida (denuncias falsas, injerencia extranjera, sesgo de una ley) puede aparecer siempre
  que esté **atribuida** a quien la sostiene, con la evidencia disponible y la posición contraria. No se
  presenta como hecho ni se le inventan cifras.
- La app **no es vinculante**: informa, ordena y compara; no reemplaza ningún órgano del Estado.

## Diseño UX/UI (estudio)
**Principio rector:** que la persona entienda en 5 segundos qué está mirando y qué puede hacer.
Tres capas, siempre en el mismo orden: *qué pasa* → *qué puedo hacer* → *qué se está haciendo*.

1. **Jerarquía visual.** Fondo claro (blanco y grises), texto oscuro y negritas en el dato
   relevante. El color se reserva para lo que exige atención: verde/ámbar/rojo de semáforo para el
   estado de gestión, nunca como decoración. Los cargos se muestran en gris oscuro y los emojis de
   tema, desaturados.
2. **Lectura por tarjetas.** Cada tema entra por emoji + título + una línea de resumen + barra de
   apoyo + contadores. El emoji funciona como ancla memorizable, no como decoración.
3. **Votar sin fricción.** Dos botones grandes (👍 / 👎) siempre visibles en el detalle, con el
   estado actual marcado. Sin cuenta, el botón lleva a registrarse y vuelve al mismo tema.
4. **Gamificación visible pero sobria.** Puntos y nivel en la barra superior; progreso al siguiente
   nivel en el perfil; historial con el motivo de cada punto. No hay rankings públicos agresivos.
5. **El mapa como pieza central.** Se lee de izquierda a derecha: temas → líneas → cargos, con la
   ciudadanía abajo al medio. Grosor = peso; color = postura; punteado = actividad sin postura.
   Leyenda fija y texto de "cómo leerlo" al lado, porque un gráfico sin guía no se entiende.
6. **Brecha explícita.** Debajo del mapa, dos barras por categoría (ciudadanía vs. cargos) y una
   etiqueta en palabras: *descuida*, *parejo*, *sobre-atende*. Es la conclusión, no el dato crudo.
7. **Móvil primero en el contenido.** Una columna, botones de 44 px, mapa con scroll horizontal
   contenido y tipografía mínima de 14 px. El APK reutilizará estas mismas pantallas en WebView.
8. **Accesibilidad.** Contraste alto, foco visible, textos alternativos en SVG, navegación completa
   por teclado y formularios con etiqueta real (no placeholder como etiqueta).
9. **Tono.** Neutro y concreto. Se describe el problema con evidencia; nunca se insulta ni se
   atribuye intención. Lo no verificado se muestra como "sin verificar", no se esconde.
10. **Vacíos.** Cuando no hay datos, se explica qué falta y cómo colaborar; nunca una pantalla muda.

## Dinámicas de autorización política (análisis)
En Uruguay un cambio puede entrar por varias puertas, y la app debe mostrarlo porque el peso
político y el tiempo de cada una son distintos:

| Instrumento | Quién lo aprueba | Particularidad |
|---|---|---|
| Ley | Parlamento; promulgación del Poder Ejecutivo | Mayoría simple; algunas materias piden 2/3 |
| Ley de urgente consideración | Poder Ejecutivo + Parlamento | 30 días; el Parlamento puede derogar artículos |
| Decreto reglamentario | Poder Ejecutivo (presidente + ministros) | No crea derechos nuevos; detalla cómo se aplica una ley |
| Resolución | Ministerio o directorio de ente autónomo | Operativa diaria; muy poco visible |
| Ordenanza / decreto departamental | Intendencia + Junta Departamental | Competencia departamental |
| Iniciativa popular | 2% del electorado | Puede presentar proyecto de ley |
| Referéndum derogatorio | 25% del electorado en un año | Deroga una ley vigente |
| Plebiscito constitucional | Mayoría de votantes | Reforma la Constitución |

**Evolución probable:** más datos abiertos y parlamento abierto, seguimiento de promesas con
indicadores, presupuestos participativos digitales y auditoría ciudadana. El límite es claro: una
app puede medir y presionar, pero no sustituir la validez jurídica de un acto administrativo.
Riesgos a cubrir más adelante: captura por grupos organizados, cuentas falsas, sesgo de la
muestra (quien usa la app no es el país) y protección de datos personales.

**Cómo lo modela la app (diseño):** cada tema debería llevar `instrumento` (ley, decreto,
resolución, ordenanza, iniciativa, plebiscito), `via` (parlamento, ejecutivo, intendencia,
ciudadanía) y una `ruta` de pasos con estado. Hoy se guarda `tipo` (ley/propuesta), `etapa` y
`urgencia`; la ruta completa queda como tarea T14.

## Modelo de datos
`usuarios`, `politicos`, `solicitudes_vinculo`, `temas`, `votos`, `opiniones`, `acciones`,
`posiciones`, `actividad`, `avisos`, `config`. Esquema portable (TEXT/INTEGER/SMALLINT) y
`DATABASE_URL` cambia SQLite por Neon sin reescribir consultas.

## Tareas
- [x] T1 — Proyecto Flask + SQLite con capa portable a Postgres · criterio: `/salud` responde `sqlite` y el esquema se crea solo.
- [x] T2 — Registro e ingreso de ciudadanía · criterio: alta con correo único, clave de 8+, sesión persistente.
- [x] T3 — Gamificación (puntos, niveles, grupos, historial) · criterio: registro +10, voto +2, opinión +5 y el perfil muestra nivel y progreso.
- [x] T4 — Precarga de leyes ineficaces y propuestas sociales · criterio: 17 leyes y 18 propuestas con categoría, emoji y fuente.
- [x] T5 — Foro por tema con distinción de cargos verificados · criterio: publicar opinión y verla en el hilo con su autor.
- [x] T6 — Directorio de cargos y organismos con contacto oficial · criterio: ficha con funciones, contacto con fuente y actividades. (30 cargos, 26 con contacto verificado, 0 celulares públicos)
- [x] T7 — Vínculo de cargo por enlace al correo público · criterio: solicitud, token de 7 días, confirmación y aprobación desde admin. (probado: usuario 2 quedó asociado a Carolina Cosse y su opinión sale con `politico_id`)
- [x] T8 — Mapa SVG con filtros por cámara y categoría · criterio: 4 columnas de cargos, temas a la izquierda, grupos abajo y grosores por porcentaje.
- [x] T9 — Panel de brechas ciudadanía vs. cargos · criterio: dos barras por categoría y etiqueta en palabras.
- [x] T10 — Desempeño configurable del cargo · criterio: puntaje 0-100 y veredicto según umbrales editables en admin.
- [x] T11 — Estudio UX/UI aplicado · criterio: estilos, plantillas y guía de lectura del mapa.
- [x] T12 — Commit inicial y repo remoto · criterio: commit `18375cf` y `origin` en https://github.com/DouglasAdvaita/politica-eficiente
- [x] T13 — Despliegue en Render con Neon · criterio: URL pública responde y `/salud` dice `postgres`.
  Hecho: https://politica-eficiente.onrender.com (servicio `politica-eficiente`, región Ohio, free tier).
  `/salud` → {"ok": true, "base": "postgres"}. Mapa, flujos, cargos y temas verificados en vivo.
  Base de datos: Neon `politica_eficiente`, sembrada con 148 cargos, 35 temas y 25 flujos.
- [ ] T14 — Ruta de aprobación por instrumento (ley, decreto, resolución, ordenanza) · criterio: cada tema muestra instrumento, vía y pasos con estado.
- [ ] T15 — APK Android (WebView, actualización por internet) · criterio: instala, abre la app y detecta versión nueva.
- [ ] T16 — Correo real por SMTP y verificación de dominio del cargo · criterio: aviso enviado y enlace funcional desde el correo.
- [ ] T17 — Carga de actividades desde fuentes oficiales (IMPO, Parlamento) · criterio: importación repetible sin duplicados.
- [x] T18 — Completar todos los senadores y diputados · criterio: 30 senadores + 99 diputados con cargo, partido, contacto oficial con fuente y actividades.
  Hecho: 99 diputados y los 30 senadores electos (27 en ejercicio + 3 que están en ministerios, con la
  aclaración de que su banca la ejerce un suplente). Total 148 cargos. Contacto: 99/99 diputados y
  27/28 senadores con correo institucional; sin teléfonos porque las fichas no los publican.
- [ ] T19 — Biografía, familia, vínculos y amistades documentadas de cada legislador · criterio: cada dato con fuente y una línea de tiempo de su vida; si no hay artículo enciclopédico, la biografía se arma con las noticias de lo que impulsó, votó o protagonizó, cada hecho con fecha y enlace. (En curso: 76 de 148 cargos con Wikipedia — 61 legisladores y 15 del Ejecutivo/Intendencias —, 522 hitos y 101 vínculos; faltan 72 por noticias.)
- [ ] T20 — Transcripciones del Parlamento · criterio: sesiones del Senado y de Diputados descargadas, buscables y enlazadas al tema que tratan.
- [ ] T21 — Línea de tiempo de noticias con contraste de datos · criterio: cada noticia con cifras comparables, causas y fuentes; sin afirmaciones sin respaldo.
- [ ] T24 — Comparador de muertes y volumen en redes · criterio: feminicidios, homicidios, siniestros y suicidios en la misma escala y período, y conteo de menciones por tema en redes con fecha y método.
- [x] T25 — Flujos de capital del Estado · criterio: Sankey con ingresos y gastos en % del PIB, panel de claves y comparación por país. (25 flujos, 24 comparaciones, 4 países)
- [ ] T22 — Contexto y preguntas abiertas por tema · criterio: cada propuesta explica cómo se llegó a la situación y plantea 2 a 4 preguntas que el ciudadano debe poder responder.
- [ ] T23 — Glosario con ventanas emergentes · criterio: palabras difíciles (subsidio, derogar, sanción, presunción de inocencia) con explicación simple al pasar el mouse o tocar.
- [ ] T26 — Comparador visual de actividad e iniciativas · criterio: comparar acciones importantes y no importantes de cada cargo, y la evolución de una iniciativa o tema en el tiempo, con la misma escala y la fuente de cada hecho.
- [ ] T27 — Semáforo de gestión por proceso · criterio: cada tema tiene un proceso con hitos y una calificación ciudadana e interna; verde, ámbar o rojo miden si la gestión y su evolución son adecuadas, no si el problema es grave; sin datos suficientes no se colorea.
- [ ] T28 — Contexto, lenguaje sencillo y política de fuentes · criterio: cada tema muestra el contexto faltante, traduce los términos difíciles y marca banderas rojas; ninguna fuente (medio masivo u oficial) se toma como verdad a priori y el sentir popular se registra como inteligencia colectiva, con control explícito de bots y contenido generado por IA.
- [ ] T29 — Recolector de noticias con actualización diaria · criterio: un cron diario junta noticias de cada cargo desde Google News RSS y las guarda crudas con fecha, medio y enlace, deduplicadas por URL; la correlación con la biografía del cargo se procesa aparte, con revisión manual de las ambiguas.

## Evidencia
- `python probar_app.py` → `/`, `/temas`, `/mapa`, `/politicos`, `/registro`, `/ingresar`, `/salud`,
  `/tema/<slug>`, `/politico/<slug>`, `/perfil`, `/configuracion`, `/admin` y `/mapa` con filtros: **200**.
- Registro, voto y opinión: 200 y el texto aparece en el tema.
- Vínculo completo: solicitud creada, token abierto, `politicos.usuario_id = 2`, opinión posterior con `politico_id = 2`.
- Base sembrada: 17 leyes + 18 propuestas (11 categorías), 30 cargos y 30 actividades.
- Revisión visual en Firefox: portada, mapa (con 40 cuentas demo), ficha de cargo, listado y detalle de tema.
- `demo.py crear` / `demo.py limpiar`: datos de demostración para ver el mapa con volumen.
- `python importar_politicos.py` → 30 cargos actualizados sin duplicar (3 diputados, 3 intendentes,
  8 organismos, 10 poder ejecutivo, 6 senadores).
- T18: **99 diputados** cargados (96 + 3 faltantes detectados por auditoría), todos con correo
  institucional y fuente. Los cargos del Ejecutivo mandan sobre la banca: quien asume un ministerio
  queda con ese cargo y no se duplica como legislador.
- T19: `traer_biografias.py` busca el artículo, valida identidad (apellidos, nombre de pila,
  mención de Uruguay y de un cargo o actividad política) y rechaza homónimos (deportistas,
  periodistas). Incluye cargos del Ejecutivo y las Intendencias. `importar_biografias.py` carga sin
  duplicar. Resultado: **76 biografías, 522 hitos y 101 vínculos**. Los artículos se guardan en
  `datos/cache_wikipedia/` (fuera de git).
- Neon: consulta directa confirma 76 biografías, 522 hitos y 101 vínculos, con el enlace de fuente
  de cada ficha.
- T29: `traer_noticias.py` junta noticias crudas (título, medio, fecha, enlace) en la tabla
  `noticias` y las clasifica por nombre (aceptada / por_revisar / descartada); `procesar_noticias.py`
  las correlaciona a la línea de tiempo del cargo y las sube a `hitos` sin duplicar. Cron diario en
  `.github/workflows/noticias.yml`. Probado local: 38 noticias de 3 cargos, promovidas y
  re-promovidas sin duplicados.
- Ficha de Pablo Abdala revisada en pantalla (captura 1200 px): resumen, nacimiento, profesión,
  familia, línea de tiempo y nota de fuente secundaria. Se corrigió la línea para que el año no
  quede pisado por el punto.
- Commit `b464186` subido a `origin/main`. Neon ya tiene los 63 registros. La ficha pública sigue
  con el código anterior: Render no tomó el commit en los primeros 25 minutos.
- Administrador de la app: `admin@politicaeficiente.uy` era un buzón inventado. `cambiar_admin.py`
  pasó el administrador al correo real del usuario (local: cuenta existente promovida y la genérica
  degradada; Neon: cuenta genérica renombrada) y alineó la clave con `ADMIN_CLAVE`. Login verificado
  en SQLite y en Postgres. El correo no se escribe en el repo: va por `ADMIN_EMAIL` en el entorno.

## Progreso
- Sesión 1 (2026-11-04): esqueleto completo, datos de leyes, propuestas y cargos, mapa SVG, brecha,
  desempeño con confianza por cantidad de datos, vínculo por correo, UX/UI aplicada y revisada en pantalla.
  Repo público y base Neon `politica_eficiente` sembrada.
- Sesión 2 (2026-11-05): app probada contra Postgres, una conexión por pedido, `/salud` en postgres.
  Se quitaron todos los datos de demostración de la interfaz: sin usuarios ni votos, el mapa no dibuja
  sección ciudadana ni brecha. Se agregaron T18 a T24. Falta el servicio de Render.
- Sesión 3 (2026-11-05): login de Render completado y formulario del Blueprint abierto (nombre y rama
  cargados). T18 en curso con cuatro estudios en paralelo e importador idempotente listo.
- Sesión 4 (2026-11-05): T19 con recolector de Wikipedia, validación de homónimos, tablas
  `biografias`, `hitos` y `vinculos`, ficha con línea de tiempo y carga en Neon. Decisión del
  usuario: las 64 fichas sin artículo se armarán con noticias (hechos, iniciativas, votos) y cada
  hecho con fecha y enlace; queda pedido el comparador visual de actividad (T26).
- Sesión 5 (2026-11-05): rediseño a fondo claro: blancos y grises, negritas en lo relevante,
  cargos en gris oscuro, emojis de tema desaturados y color reservado al semáforo de estado. Se
  ajustaron mapa y flujos. Verificado en pantalla a 1280 y a 420 px. Se agregaron T27 (semáforo de
  gestión por proceso) y T28 (contexto, lenguaje sencillo y política de fuentes). Además se
  extendieron las biografías al Ejecutivo y las Intendencias, con validación que descarta
  homónimos (futbolistas, periodistas): 76 biografías.

- Sesión 6 (2026-11-06): recolector de noticias diario (T29) en dos etapas — recolección automática
  por GitHub Actions (Google News RSS) + correlación/procesamiento manual con criterio editorial —,
  con la tabla `noticias` y el cron `.github/workflows/noticias.yml`. Probado contra SQLite.

## Próximo paso
1. Cargar el secreto `NEON_DATABASE_URL` en GitHub (Settings → Secrets → Actions) para que el cron
   escriba en Neon, y correr una primera pasada que pueble las noticias.
2. Revisar y correlacionar las noticias `por_revisar` y las aceptadas con su biografía (proceso manual).
3. Completar las 72 biografías sin artículo con noticias fechadas y enlazadas.
4. T26: comparador visual de acciones e iniciativas.
- [x] T30 - Ficha editorial obligatoria por tema: todo tema muestra fecha, responsable que lo inicia, critica de coherencia del relato e indice de personas y organismos con emoji justificado; importador idempotente a SQLite y Neon. (35 de 35 temas, commit a06e35d)
- [x] T23 - Glosario con ventanas emergentes: 30 terminos en lenguaje simple, pagina /glosario y palabras explicadas al pasar el mouse en los textos del tema. (commit 6523bcd)
- [x] T22 - Contexto y preguntas abiertas: cada uno de los 35 temas explica como se llego a la situacion, que dato falta y 3 preguntas que el ciudadano puede responder. (commit 40ac43b)
- [ ] T28 - Contexto, lenguaje sencillo y politica de fuentes: hecho el contexto faltante, el glosario y las banderas rojas; falta el control explicito de bots e IA en el sentir popular.
- [x] T26 - Comparador visual de actividad: pagina /comparador con acciones por importancia (alta, media, baja), estado y evolucion anual de los hechos registrados, cada uno con su fuente. (commit 503a243)
- [~] T19 - Biografia y linea de tiempo: los 148 cargos tienen al menos un hito. Los 32 diputados sin cobertura de prensa se completaron con la ficha oficial del Parlamento (banca, comisiones, grupos de amistad y suplencia), con enlace a cada ficha; falta familia y vinculos de esos 32.
- [x] Base local primero: politica.db en SQLite para desarrollo (rapido, sin red) y Neon solo como destino de publicacion; copiar_db.py --bajar / --subir reemplaza tablas en ambos sentidos. _run_local.py usa SQLite por defecto y --neon solo si se pide. (commit 3ecac17)
- [~] T17 - Actividades desde fuentes oficiales: traer_legisladores.py (ficha, comisiones, suplencias) y traer_actuacion.py (proyectos, pedidos de informes e informes en comision desde el JSON del Parlamento), idempotentes y con enlace a cada documento.
- [x] T27 - Semaforo de gestion por tema: cada uno de los 35 temas muestra estado (al dia, parcial, incumplida o sin datos), motivo concreto y fecha; el color mide avance hacia el objetivo, no gravedad, y queda gris cuando no hay datos publicos. (commit pendiente)
- [x] T28 - Contexto, lenguaje sencillo y politica de fuentes: contexto faltante, glosario, banderas rojas y control explicito de automatizacion en el foro (texto identico descartado 24 h y tope de 4 opiniones cada 5 minutos por cuenta, sin moderacion por IA).
- [x] T17 - Carga desde fuentes oficiales: traer_legisladores.py y traer_actuacion.py importan ficha, comisiones, suplencias, proyectos, pedidos de informes e informes en comision desde el Parlamento; repetibles sin duplicar (dedupe por texto) y con enlace a cada documento. (1.578 proyectos y 984 pedidos de informes en local)
