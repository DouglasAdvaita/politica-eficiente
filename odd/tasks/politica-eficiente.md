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
- Mismo camino que RAVE: git, Render (gunicorn + `render.yaml`), estética neón, APK después.
- SQL con `?` traducido a `%s`: el mismo esquema corre en SQLite y Postgres/Neon.
- Sin datos personales inventados. Todo contacto lleva fuente y marca de verificación.
- La app **no es vinculante**: informa, ordena y compara; no reemplaza ningún órgano del Estado.

## Diseño UX/UI (estudio)
**Principio rector:** que la persona entienda en 5 segundos qué está mirando y qué puede hacer.
Tres capas, siempre en el mismo orden: *qué pasa* → *qué puedo hacer* → *qué se está haciendo*.

1. **Jerarquía visual.** Fondo azul-noche, paneles elevados, un solo acento fuerte por pantalla.
   El neón (verde agua) marca acción y dato positivo; rosa/rojo, conflicto o descuido; ámbar,
   advertencia o dato sin verificar. Nunca dos acentos compitiendo en la misma tarjeta.
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
- [ ] T13 — Despliegue en Render con Neon · criterio: URL pública responde y `/salud` dice `postgres`.
- [ ] T14 — Ruta de aprobación por instrumento (ley, decreto, resolución, ordenanza) · criterio: cada tema muestra instrumento, vía y pasos con estado.
- [ ] T15 — APK Android (WebView, actualización por internet) · criterio: instala, abre la app y detecta versión nueva.
- [ ] T16 — Correo real por SMTP y verificación de dominio del cargo · criterio: aviso enviado y enlace funcional desde el correo.
- [ ] T17 — Carga de actividades desde fuentes oficiales (IMPO, Parlamento) · criterio: importación repetible sin duplicados.

## Evidencia
- `python probar_app.py` → `/`, `/temas`, `/mapa`, `/politicos`, `/registro`, `/ingresar`, `/salud`,
  `/tema/<slug>`, `/politico/<slug>`, `/perfil`, `/configuracion`, `/admin` y `/mapa` con filtros: **200**.
- Registro, voto y opinión: 200 y el texto aparece en el tema.
- Vínculo completo: solicitud creada, token abierto, `politicos.usuario_id = 2`, opinión posterior con `politico_id = 2`.
- Base sembrada: 17 leyes + 18 propuestas (11 categorías), 30 cargos y 30 actividades.
- Revisión visual en Firefox: portada, mapa (con 40 cuentas demo), ficha de cargo, listado y detalle de tema.
- `demo.py crear` / `demo.py limpiar`: datos de demostración para ver el mapa con volumen.

## Progreso
- Sesión 1 (2026-11-04): esqueleto completo, datos de leyes, propuestas y cargos, mapa SVG, brecha,
  desempeño con confianza por cantidad de datos, vínculo por correo, UX/UI aplicada y revisada en pantalla.
  Falta el primer commit (T12) y el despliegue (T13).

## Próximo paso
Primer commit local, después repo remoto y despliegue en Render con Neon.
