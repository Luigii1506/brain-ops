# Style Guide — Biblia de estilo de la serie

## Voz

La voz de la colección es:
- **Clara**: sin ambigüedad, sin rodeos, sin frases que haya que releer
- **Culta**: vocabulario preciso, no simplificado, pero tampoco exhibicionista
- **Accesible**: un lector inteligente sin formación en el tema puede seguirla
- **Narrativa**: cuenta, no lista; mueve, no acumula
- **Interpretativa**: no solo dice qué pasó — dice qué significa
- **Elegante**: cada frase tiene peso, pero sin barroquismo
- **Intensa sin exagerar**: la prosa tiene energía pero nunca grita

## Prohibiciones de estilo

No escribir:
- como enciclopedia (datos sin tensión)
- como apuntes escolares (resúmenes planos)
- como paper académico (jerga, citas formales, tono neutro)
- como hilo de datos sin narrativa
- como texto épico vacío (grandilocuente pero hueco)
- como prosa barroca adornada (más forma que fondo)
- como resumen sin tesis (información sin interpretación)

## Tono

El tono es el de un ensayista que:
- sabe mucho pero no lo exhibe
- escribe como si explicara a alguien a quien respeta
- no teme interpretar, pero distingue hecho de opinión
- no necesita citas de autoridad para sostener un argumento
- alterna entre dato, explicación, tensión y reflexión

## Longitud

**Cada libro debe aspirar a ~5,000 palabras.** Puede desviarse moderadamente si el tema lo exige, pero nunca sin razón estructural clara.

- **Prólogo**: 200–400 palabras
- **Acto/bloque**: 400–800 palabras
- **Epílogo/legado**: 300–500 palabras
- **Reflexión**: 200–400 palabras (preguntas, no texto)
- **Guía de lectura**: sin límite (es referencia)

Un libro de menos de 3,500 palabras probablemente le falta profundidad — cada acto debería preguntarse si está desarrollando o solo mencionando.
Un libro de más de 7,000 probablemente necesita dividirse o tiene actos que se comen el balance del capítulo.

## Estructura del capítulo

```
---
type: book
subtype: output
tags: [libro, dominio, tema]
related: [entidades principales]
sources: []
---

> Navegación de serie

# Título del capítulo

> Subtítulo memorable — una línea que convierta el tema en algo vivo.

**Tesis:** Una afirmación potente que promete: "este capítulo no solo te contará qué pasó; te dirá qué significa."

---

## Prólogo — [Nombre evocador]

Abre el mundo del capítulo con fuerza. No empieza con dato: empieza con contexto cargado de sentido.

> 💭 **Pregunta provocadora** que enmarca todo lo que sigue.

---

## Acto I — [Nombre funcional]

Cada acto cumple una función: avanzar la historia, profundizar una idea, cambiar la escala, mostrar consecuencias.

> 💭 **Pregunta** que cierra el acto y obliga a pensar.

---

[...más actos según necesidad...]

---

## Epílogo — [Legado / consecuencias]

El tema sale del detalle y entra en una idea más grande.

> 💭 **Pregunta final** que conecta con el resto de la colección.

---

## Reflexión

- 🟡 Pregunta causa-efecto que integra el capítulo
- 🟡 Pregunta sobre método o fuentes
- 🔴 Contrafactual que fuerza comprensión profunda
- ⚫ Patrón cross-domain que conecta con otros libros
- ⚫ Explicación en una frase (prueba de comprensión)

---

## Guía de lectura

### [Categoría 1]
[[Entidad]] · [[Entidad]] · ...

### [Categoría N]
[[Entidad]] · [[Entidad]] · ...

---

> Navegación de serie
```

## Cómo introducir entidades

- Toda entidad importante se introduce con `[[wikilink]]` en su primera mención significativa
- No saturar un párrafo con más de 5-6 wikilinks — si hay más, redistribuir
- Presentar la entidad con contexto mínimo: "[[Brasidas]], un general espartano carismático" — no solo el nombre
- Nunca listar entidades sin función narrativa — si no mueven la comprensión, sobran

## Cómo cerrar cada acto

Cada acto termina con una pregunta `💭` que:
- no tiene respuesta obvia
- obliga al lector a pensar, no solo a recordar
- conecta el contenido del acto con una idea más amplia
- puede ser respondida de varias formas legítimas

No usar preguntas retóricas ("¿No es fascinante?"). Usar preguntas reales ("¿Qué dice X sobre Y?").

## Cómo hacer preguntas de reflexión

La sección final de Reflexión usa cuatro niveles:

| Icono | Nivel | Función | Ejemplo |
|-------|-------|---------|---------|
| 🟡 | Causa-efecto | Integrar el capítulo | "¿Por qué X produjo Y y no Z?" |
| 🟡 | Método/fuente | Pensar críticamente | "¿Qué cambia si miramos X en vez de Y?" |
| 🔴 | Contrafactual | Forzar comprensión | "¿Qué habría pasado si X nunca hubiera ocurrido?" |
| ⚫ | Cross-domain | Conectar colección | "¿Dónde más ves este patrón?" |
| ⚫ | Síntesis | Prueba de comprensión | "Explica la tesis en una frase" |

## Nivel de lirismo permitido

- Permitido: imágenes verbales que aumenten comprensión o intensidad ("murallas de madera" = trirremes)
- Permitido: frases con peso emocional en momentos clave (muertes, caídas, descubrimientos)
- Prohibido: metáforas extendidas que no aporten
- Prohibido: adjetivación excesiva ("el magnífico y extraordinario descubrimiento")
- Prohibido: dramatismo sin sustancia ("y entonces, todo cambió para siempre...")

Regla: el lirismo es sal. Poco mejora; mucho arruina.

## Nivel de análisis permitido

- Permitido: interpretar causas, consecuencias, patrones
- Permitido: comparar con otros temas de la colección
- Permitido: señalar contradicciones o paradojas
- Prohibido: largos excursos teóricos que detengan la narrativa
- Prohibido: análisis que requiera conocimiento previo especializado
- Prohibido: relativismo vacío ("hay muchas perspectivas sobre esto")

Regla: el análisis debe sentirse como parte de la narrativa, no como pausa académica.

## Densidad informativa

- Cada párrafo debe contener al menos un hecho, una explicación o una interpretación
- No más de 3 nombres nuevos por párrafo (salvo guías de lectura)
- Alternar constantemente entre dato → explicación → interpretación
- Si un párrafo solo tiene datos, falta interpretación
- Si un párrafo solo tiene análisis, faltan hechos concretos

## Idioma

Los libros se escriben en español. La prosa debe sonar natural en español — no como traducción del inglés. Evitar anglicismos innecesarios. Usar terminología técnica en su idioma original solo cuando sea el estándar del campo (e.g., "trade-off", "stasis").
