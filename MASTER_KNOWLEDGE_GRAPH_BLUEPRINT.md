# DOCUMENTO MAESTRO — EVOLUCIÓN DEL KNOWLEDGE GRAPH PERSONAL
## Proyecto: segundo cerebro narrativo, histórico, científico y simbólico

> Este documento define la dirección, arquitectura, taxonomía, migración y prioridades de un knowledge graph personal en Obsidian.
> El objetivo no es crear una enciclopedia genérica, sino un segundo cerebro que permita aprender, retener, conectar y explicar con claridad los temas que más importan al autor.
> Claude Code debe usar este documento como blueprint operativo para proponer y ejecutar cambios en la base de conocimiento.

---

# 1. MISIÓN DEL PROYECTO

## 1.1 Finalidad central
Este knowledge graph existe para convertirse en un **segundo cerebro personal**: una representación externa del tipo de mente que el autor quiere tener.

Ese segundo cerebro ideal debe:

- conocer profundamente los temas de interés del autor
- no olvidar lo importante
- mostrar relaciones entre dominios
- permitir explicar los temas con claridad a otra persona
- ayudar a aprender mejor, retener mejor y formar criterio propio
- servir como base para futuras síntesis narrativas, rutas de estudio, libros y exploraciones guiadas por LLMs

## 1.2 Qué NO es este proyecto
Este proyecto NO es:

- una enciclopedia neutral sin punto de vista
- una wiki genérica de datos sueltos
- un sistema hecho solo para RAG
- un archivo pasivo de notas sin arquitectura
- un catálogo indiscriminado de curiosidades

## 1.3 Qué SÍ es este proyecto
Este proyecto SÍ es:

- una base de conocimiento personal con valor académico
- una inteligencia narrativa orientada a comprensión
- una estructura viva para estudiar historia, ciencia, religión, filosofía, esoterismo y ML/AI
- una herramienta para pensar mejor y recordar mejor
- una base navegable que otra persona podría recorrer para entender “cómo piensa” su autor

---

# 2. CRITERIO DE ÉXITO

## 2.1 Qué significa “dominar” un tema
En este sistema, dominar un tema significa principalmente:

- poder explicarlo con claridad a otra persona
- entender por qué importa
- ver sus relaciones con otros temas
- comprender su historia, su estructura y su contexto
- poder escribir o enseñar sobre él con profundidad razonable

## 2.2 Evidencia de dominio
Un tema se considera más cercano al dominio cuando:

- puede explicarse sin perder el hilo
- tiene una narrativa inteligible
- tiene conexiones claras con otras entidades
- tiene una cronología o estructura conceptual clara
- puede convertirse en una nota o libro narrativo coherente

---

# 3. DOMINIOS PRIORITARIOS

## 3.1 Núcleo principal del proyecto
Los dominios núcleo del sistema son:

1. Historia
2. Ciencia

## 3.2 Dominios importantes orbitando el núcleo
Estos dominios rodean y enriquecen el núcleo principal:

3. Religión y mitología
4. Esoterismo / misterio / tradiciones simbólicas
5. Filosofía
6. ML/AI

## 3.3 Orden de importancia real
- Historia = prioridad máxima
- Ciencia = prioridad máxima
- Religión / mitología = alta prioridad como capa simbólica e histórica
- Esoterismo = alta prioridad como tradición simbólica e intelectual, con epistemología explícita
- Filosofía = importante, pero como herramienta de pensamiento y puente entre religión/ciencia
- ML/AI = importante, pero no debe absorber la energía principal en esta etapa

---

# 4. ESTADO ACTUAL DEL GRAFO

## 4.1 Volumen aproximado
- ~1,047 notas en la carpeta de conocimiento

## 4.2 Dominios detectados actualmente
Aproximadamente:
- filosofía
- historia
- religión
- machine learning
- ciencia
- algunas notas sin domain asignado

## 4.3 Forma actual del sistema
Actualmente el grafo está compuesto principalmente por:

- entidades
- conceptos
- eventos
- lugares
- obras
- organizaciones
- notas MOC
- notas libro

## 4.4 Método actual de construcción
El flujo actual es aproximadamente:

1. crear entidades
2. crear MOCs
3. crear libros narrativos

Esto es útil, pero debe evolucionar.

## 4.5 Diagnóstico del estado actual
Fortalezas:
- misión clara
- materia prima abundante
- taxonomía inicial sólida
- método narrativo valioso
- uso disciplinado y frecuente

Debilidades:
- muchas relaciones siguen implícitas por links
- `related` plano tiene demasiado peso
- no hay schema mínimo fuerte por subtype
- faltan predicados intelectuales, históricos y simbólicos clave
- faltan dominios estratégicos: biología, química, historia medieval-moderna, esoterismo formal
- falta capa epistemológica explícita
- hay notas sin `domain`
- el sistema todavía depende demasiado del criterio variable del LLM

---

# 5. TESIS DE REDISEÑO

El knowledge graph debe evolucionar de:

**vault interesante con muchas entidades**

a

**knowledge graph narrativo, tipado, epistemológicamente claro, durable y mantenible de por vida**

Para lograrlo, el sistema debe organizarse en 5 capas:

## 5.1 Capa 1 — Entidades
Notas atómicas: personas, eventos, conceptos, civilizaciones, obras, símbolos, etc.

## 5.2 Capa 2 — Relaciones tipadas
Las relaciones no deben vivir solo en prosa o en `related`. Deben poder expresarse formalmente.

## 5.3 Capa 3 — Estructura
MOCs, cronologías, rutas, mapas de dominio, notas puente, comparativas.

## 5.4 Capa 4 — Narrativa
Los libros narrativos son síntesis de alto nivel construidas sobre las capas anteriores.

## 5.5 Capa 5 — Epistemología
Debe quedar explícito si una nota representa algo científico, histórico, religioso, mítico, esotérico, filosófico o especulativo.

---

# 6. PRINCIPIOS RECTORES DEL SISTEMA

## 6.1 Principio narrativo
El sistema debe priorizar comprensión por causalidad, secuencia y tensión, no solo acumulación de datos.

## 6.2 Principio de explicabilidad
Toda entidad importante debe poder responder:
- qué es
- por qué importa
- qué conecta
- en qué narrativa entra

## 6.3 Principio de arquitectura antes que volumen
A partir de ahora, no debe crecer primero por cantidad de notas, sino por calidad estructural:
1. arquitectura
2. relaciones
3. huecos estratégicos
4. notas puente
5. narrativa

## 6.4 Principio de distinción epistemológica
No mezclar en el mismo plano:
- ciencia verificada
- historia documentada
- tradición religiosa
- mito
- esoterismo
- especulación

Pueden convivir, pero deben distinguirse explícitamente.

## 6.5 Principio de valor de existencia
Una nota nueva debe justificar su existencia:
- ¿qué explica?
- ¿qué conecta?
- ¿qué narrativa necesita?
- ¿qué hueco cierra?

---

# 7. ARQUITECTURA OBJETIVO

## 7.1 Tipos macro de notas
El sistema debe organizarse alrededor de tres clases mayores de notas:

### A. Notas base
Entidades atómicas del mundo:
- persona
- civilización
- imperio
- concepto
- teoría
- deidad
- guerra
- libro
- símbolo
- tradición esotérica
- etc.

### B. Notas estructurales
No representan “cosas del mundo”, sino orden:
- MOC de dominio
- MOC de civilización
- cronologías
- notas puente
- rutas de estudio
- comparativas
- listas de huecos
- mapas de relaciones

### C. Notas narrativas
- libros narrativos
- recorridos explicativos largos
- síntesis de un bloque maduro

## 7.2 Flujo ideal futuro
El flujo ideal debe ser:

1. crear o enriquecer entidades núcleo
2. agregar relaciones tipadas
3. construir MOC del bloque
4. construir cronología o secuencia
5. construir notas puente
6. construir libro narrativo

NO al revés.

---

# 8. TAXONOMÍA ACTUAL Y EXPANSIÓN NECESARIA

## 8.1 Taxonomía actual base
Actualmente existen grandes tipos como:
- entity
- concept
- work
- event
- place
- organization
- source
- topic
- disambiguation

Eso debe mantenerse, pero ampliarse.

## 8.2 Expansiones obligatorias — Historia
Agregar subtypes históricos faltantes:

- `historical_period`
- `dynasty`
- `era`
- `historical_process`

Ejemplos:
- Edad Media → `historical_period`
- Renacimiento → `historical_period`
- Dinastía Han → `dynasty`
- Feudalismo → `historical_process`

## 8.3 Expansiones obligatorias — Biología y medicina
Agregar:

- `organism`
- `cell`
- `gene`
- `biological_process`
- `anatomical_structure`
- `disease`
- `medical_condition`
- `medical_theory`

## 8.4 Expansiones obligatorias — Química
Agregar:

- `chemical_element`
- `compound`
- `molecule`
- `chemical_reaction`

## 8.5 Expansiones obligatorias — Matemáticas
Agregar:

- `mathematical_object`
- `theorem`
- `constant`
- `function`
- `proof_method`
- `mathematical_field`

## 8.6 Expansiones obligatorias — Lenguaje y texto
Agregar:

- `language`
- `script`
- `sacred_text`
- `esoteric_text`

## 8.7 Expansiones obligatorias — Esoterismo
Agregar:

- `esoteric_tradition`
- `ritual`
- `symbolic_system`
- `divination_system`
- `occult_movement`
- `mystical_concept`

## 8.8 Criterio
Claude Code debe proponer una taxonomía revisada que:

- no rompa lo ya existente innecesariamente
- amplíe lo suficiente para cubrir los dominios reales del autor
- preserve claridad
- evite hiperfragmentación inútil

---

# 9. RELACIONES NUEVAS RECOMENDADAS

## 9.1 Problema actual
`related` no es suficiente. El grafo necesita predicados con sentido.

## 9.2 Relaciones intelectuales
Agregar:

- `reacted_against`
- `developed`
- `extended`
- `synthesized`
- `refuted`
- `criticized`
- `inspired`
- `derived_from`

## 9.3 Relaciones históricas
Agregar:

- `belongs_to_period`
- `contemporary_of`
- `emerged_from`
- `transformed_into`
- `ruled_by`
- `centered_on`
- `continuation_of`

## 9.4 Relaciones religiosas, míticas y esotéricas
Agregar:

- `worshipped_by`
- `worshipped`
- `associated_with`
- `symbolizes`
- `used_in`
- `practiced_by`
- `interpreted_as`
- `appears_in`

## 9.5 Relaciones de obra
Agregar:

- `depicts`
- `describes`
- `argues_for`
- `argues_against`
- `written_in`
- `based_on`

## 9.6 Relaciones científicas
Agregar:

- `explains`
- `measured_by`
- `studied_in`
- `part_of_system`
- `precedes_in_process`
- `depends_on`

## 9.7 Participación genérica
Agregar un predicado general:
- `participated_in`

para no depender solo de `fought_in`.

## 9.8 Uso estratégico de `related`
`related` debe quedar como:
- fallback temporal
- relación blanda
- conexión todavía no tipada

NO como relación principal permanente.

---

# 10. CAPA EPISTEMOLÓGICA

## 10.1 Problema
Este sistema quiere abarcar ciencia, religión, mito, filosofía y esoterismo.
Si no se marca la naturaleza epistemológica de cada nota, el sistema se vuelve confuso.

## 10.2 Campos obligatorios recomendados
Agregar gradualmente:

- `epistemic_mode`
- `certainty_level`
- `tradition`

## 10.3 Valores sugeridos para `epistemic_mode`
- `historical`
- `scientific`
- `religious`
- `mythological`
- `esoteric`
- `philosophical`
- `speculative`

## 10.4 Valores sugeridos para `certainty_level`
- `well_supported`
- `tradition_based`
- `symbolic`
- `contested`
- `speculative`

## 10.5 Sentido
Esto NO es para censurar ni jerarquizar moralmente los dominios.
Es para distinguir con claridad:

- qué es una afirmación histórica
- qué es una teoría científica
- qué es una creencia religiosa
- qué es una estructura simbólica
- qué es una tradición esotérica
- qué es una hipótesis o misterio abierto

---

# 11. DOMINIOS PRIORITARIOS DE EXPANSIÓN

## 11.1 Historia — prioridad máxima
La historia es el eje principal del proyecto.

### 11.1.1 Objetivo
Construir grandes bloques narrativos conectados por una columna cronológica mínima.

### 11.1.2 Bloques históricos obligatorios
- cosmología y formación del mundo
- primeras civilizaciones
- Egipto
- Mesopotamia
- Grecia
- Roma
- Persia
- India antigua
- China antigua
- Mesoamérica
- Bizancio
- Edad Media
- Islam clásico / Edad de Oro islámica
- Renacimiento
- Reforma
- Revolución Científica
- Ilustración
- Revoluciones modernas
- siglo XIX
- siglo XX
- historia contemporánea

### 11.1.3 Criterio operativo
No intentar escribir una historia lineal total desde ya.
Construir:
- bloques fuertes
- cronología madre mínima
- notas puente entre bloques

## 11.2 Ciencia — prioridad máxima
La ciencia debe expresar esta cadena:

**cosmos → materia → estrellas → elementos → Tierra → vida → mente → civilización**

### 11.2.1 Subdominios prioritarios
Orden sugerido:
1. cosmología
2. física
3. biología
4. química
5. neurociencia
6. geología
7. psicología
8. medicina general

### 11.2.2 Alcance de medicina y psicología
No se busca nivel profesional clínico.
Se busca:
- comprensión general
- relación cuerpo / mente / vida
- conexión con ciencia, historia y filosofía

## 11.3 Religión y mitología
Debe evolucionar de “colección de dioses y mitos” a “sistema simbólico e histórico”.

Modelar mejor:
- cosmogonías
- funciones simbólicas
- cultos
- rituales
- textos
- relación entre religión, poder y sociedad

## 11.4 Filosofía
Debe usarse como:
- herramienta para pensar mejor
- puente entre ciencia y religión
- historia de ideas
- entrenamiento de criterio

## 11.5 Esoterismo
Debe convertirse en un dominio formal, no accesorio.

### 11.5.1 Alcance
Incluir:
- hermetismo
- gnosticismo
- cábala
- tarot
- alquimia
- simbolismo
- sociedades secretas
- ocultismo moderno

### 11.5.2 Forma de tratarlo
Principalmente como:
- tradición simbólica e intelectual
- campo de investigación y misterio
- puente entre religión y ciencia en la historia de las ideas

Con epistemología explícita.

## 11.6 ML/AI
Mantener y consolidar, pero no convertirlo en la prioridad expansiva central de esta etapa.

---

# 12. GRANDES HUECOS ESTRATÉGICOS

Claude Code debe asumir como huecos estratégicos prioritarios:

## 12.1 Hueco histórico Roma → modernidad
Es el hueco más importante porque rompe la continuidad entre:
- Antigüedad
- filosofía medieval
- Renacimiento
- Reforma
- Ilustración

Debe atacarse con prioridad.

## 12.2 Biología
El sistema actual salta demasiado rápido de cosmos/Tierra a humanos.
Debe completarse la capa de vida.

## 12.3 Química
Necesaria para conectar:
- física
- biología
- cosmología
- alquimia / historia de la ciencia

## 12.4 Civilizaciones no occidentales
Se necesita más solidez en:
- India
- China
- Mesoamérica
- Persia

## 12.5 Esoterismo estructurado
Actualmente es un interés fuerte sin infraestructura suficiente.

---

# 13. COLUMNA VERTEBRAL HISTÓRICA

## 13.1 Propuesta
Crear una nota estructural maestra:
`Historia del mundo — columna vertebral`

Esta nota NO debe ser una enciclopedia.
Debe ser un mapa de:
- grandes periodos
- transiciones
- bloques civilizatorios
- puntos de contacto

## 13.2 Función
Servirá para:
- orientar navegación
- ubicar cronológicamente bloques
- construir notas puente
- evitar islas temporales

## 13.3 Complementos
Además de la columna vertebral, cada gran bloque debe tener:

- MOC del bloque
- cronología del bloque
- entidades núcleo
- conceptos núcleo
- eventos núcleo
- notas puente
- libro narrativo final

---

# 14. NOTAS PUENTE OBLIGATORIAS

El sistema necesita muchas más notas puente.
Estas notas explican transiciones, herencias, tensiones y conexiones causales.

## 14.1 Ejemplos históricos
- De Roma al feudalismo
- Del mundo clásico al cristianismo imperial
- De la Antigüedad tardía al mundo medieval
- Del mundo clásico al Islam medieval
- Del feudalismo al Renacimiento
- De la escolástica al humanismo
- De la Reforma a la modernidad política
- De la alquimia a la química

## 14.2 Ejemplos científicos
- De la cosmología a la formación de elementos
- De la química a la biología
- De la evolución a la aparición del humano
- Del cerebro a la mente
- De la estadística al machine learning

## 14.3 Ejemplos simbólicos
- Del mito a la filosofía
- Religión y poder en las primeras civilizaciones
- Hermetismo entre religión, ciencia y simbolismo
- Alquimia como protoquímica y lenguaje espiritual

## 14.4 Regla
Cada dominio fuerte debe tener de 3 a 10 notas puente mínimas.

---

# 15. LIBROS NARRATIVOS

## 15.1 Rol correcto del libro
El libro NO debe ser la fuente de verdad.
Debe ser la síntesis narrativa final construida sobre estructura madura.

## 15.2 Pipeline ideal
Un libro solo debe escribirse cuando existan al menos:

- entidades clave del bloque
- relaciones tipadas suficientes
- MOC del bloque
- cronología mínima
- varias notas puente

## 15.3 Estructura deseable de un libro
Cada libro puede mantener el formato compacto actual, pero debe apoyarse en:

- tesis
- prólogo
- capítulos
- hilo causal
- tensión narrativa
- personajes o fuerzas principales
- transición final hacia otros bloques

## 15.4 Decisión
Conservar el método de libros, pero moverlo al final del pipeline de maduración.

---

# 16. SCHEMAS MÍNIMOS POR SUBTYPE

Claude Code debe diseñar schemas mínimos razonables por subtype.
No deben ser rígidos al punto de romper el flujo, pero sí lo bastante claros para evitar inconsistencia.

## 16.1 Person
Campos sugeridos:
- `type`
- `subtype`
- `name`
- `domain`
- `subdomain`
- `era`
- `tradition`
- `born`
- `died`
- `nationality`
- `occupation`
- `epistemic_mode`
- `why_it_matters`
- relaciones relevantes (`influenced_by`, `influenced`, etc.)

## 16.2 Event
Campos sugeridos:
- `type`
- `subtype`
- `name`
- `domain`
- `period` o `date`
- `start_date`
- `end_date`
- `participants`
- `location`
- `outcome`
- `caused_by`
- `significance`
- `epistemic_mode`

## 16.3 Civilization / polity / empire
Campos sugeridos:
- `type`
- `subtype`
- `name`
- `domain`
- `time_range`
- `region`
- `capital`
- `key_figures`
- `defining_traits`
- `predecessor`
- `successor`
- `epistemic_mode`

## 16.4 Concept
Campos sugeridos:
- `type`
- `subtype`
- `name`
- `domain`
- `field`
- `concise_definition`
- `why_it_matters`
- `originated`
- `originated_by`
- `epistemic_mode`
- `certainty_level`

## 16.5 Esoteric tradition
Campos sugeridos:
- `type`
- `subtype`
- `name`
- `domain`
- `origin`
- `historical_context`
- `core_symbols`
- `principal_texts`
- `main_practices`
- `influenced_by`
- `influenced`
- `epistemic_mode`
- `certainty_level`

## 16.6 Work
Campos sugeridos:
- `type`
- `subtype`
- `name`
- `author`
- `published`
- `genre`
- `language`
- `depicts`
- `argues_for`
- `argues_against`
- `epistemic_mode`

## 16.7 Place
Campos sugeridos:
- `type`
- `subtype`
- `name`
- `region`
- `continent`
- `civilizational_context`
- `epistemic_mode`

---

# 17. REGLAS EDITORIALES

## 17.1 Regla de creación de entidades
No crear una entidad nueva salvo que cumpla al menos una de estas:
- es nodo clave de un dominio
- cierra un hueco importante
- es necesaria para una cronología
- es necesaria para una nota puente
- es necesaria para un libro narrativo
- conecta fuertemente varios subdominios

## 17.2 Regla de justificación
Toda nota debe dejar claro:
- qué es
- por qué importa
- qué conecta
- en qué narrativa entra

## 17.3 Regla contra el bloat
Evitar:
- notas casi vacías
- entidades sin contexto
- notas creadas solo por completismo
- duplicación de nombres o conceptos sin clara necesidad

## 17.4 Regla de claridad
Priorizar:
- claridad
- navegabilidad
- profundidad razonable
- valor explicativo

por encima de:
- completismo ciego
- hiperatomización innecesaria

## 17.5 Regla de consistencia terminológica
Claude Code debe revisar convenciones de naming para reducir ambigüedad:
- singular vs plural
- idioma principal
- forma canónica de imperios, periodos, escuelas, conceptos
- disambiguaciones útiles

---

# 18. ESTRATEGIA DE MIGRACIÓN

Claude Code NO debe intentar una refactorización destructiva de una sola vez.
Debe proponer una migración gradual por campañas.

## 18.1 Campaña 1 — Consolidación estructural
Objetivos:
- completar `domain` en notas faltantes
- revisar `subdomain`
- proponer taxonomía expandida
- diseñar schemas mínimos
- introducir capa epistemológica
- definir nuevas relaciones tipadas
- preparar estrategia de migración desde `related`

Entregables:
- propuesta de taxonomía v2
- propuesta de relaciones v2
- propuesta de schemas v2
- lista de notas mal clasificadas o sin dominio

## 18.2 Campaña 2 — Hueco Roma → modernidad
Objetivos:
- Edad Media
- Bizancio
- Islam clásico
- Renacimiento
- Reforma
- Revolución Científica
- Ilustración

Entregables:
- MOCs de estos bloques
- cronologías mínimas
- listas de entidades faltantes
- notas puente obligatorias

## 18.3 Campaña 3 — Cadena de la vida
Objetivos:
- biología básica
- química básica
- neurociencia introductoria
- medicina general

Entregables:
- taxonomía biológica/química mínima
- entidades núcleo
- mapa de conexiones cosmos → vida → mente

## 18.4 Campaña 4 — Civilizaciones no occidentales
Objetivos:
- India
- China
- Mesoamérica
- Persia más fuerte

Entregables:
- bloques históricos comparables a Grecia/Roma/Egipto

## 18.5 Campaña 5 — Dominio esotérico
Objetivos:
- hermetismo
- gnosticismo
- cábala
- alquimia
- tarot
- simbolismo
- ocultismo moderno

Entregables:
- taxonomía esotérica mínima
- relaciones simbólicas y de influencia
- marco epistemológico claro

## 18.6 Campaña 6 — Fortalecimiento narrativo
Objetivos:
- más notas puente
- macro-libros por bloque
- comparativas civilizatorias
- mejor conexión entre historia, ciencia, religión y simbolismo

---

# 19. MÉTRICAS DE AVANCE

Claude Code debe ayudar a medir progreso con métricas útiles, no solo contando notas.

## 19.1 Métricas recomendadas
- porcentaje de notas con `domain`
- porcentaje de notas con `subdomain`
- porcentaje de notas con schema mínimo válido
- porcentaje de notas con relaciones tipadas
- cantidad de notas puente por dominio
- cantidad de MOCs maduros por dominio
- cantidad de cronologías estructurales
- cantidad de libros construidos sobre bloques maduros

## 19.2 Métrica cualitativa principal
La métrica más importante es:
**¿puede el sistema explicar bien este dominio?**

---

# 20. PAPEL DEL LLM

## 20.1 Qué debe hacer el LLM
El LLM debe asistir en:
- detectar huecos
- proponer entidades faltantes
- convertir prosa en estructura
- sugerir relaciones tipadas
- generar borradores de notas
- generar preguntas de estudio
- generar libros narrativos a partir de estructura madura
- revisar consistencia

## 20.2 Qué NO debe decidir solo
El LLM NO debe decidir sin supervisión:
- taxonomía final
- jerarquía epistemológica final
- prioridades estratégicas del proyecto
- naming canónico en casos ambiguos
- afirmaciones históricas/científicas delicadas sin revisión

## 20.3 Regla
El LLM es copiloto estructural y narrativo.
No es árbitro absoluto de verdad.

---

# 21. ENTREGABLES QUE CLAUDE CODE DEBE PRODUCIR

Claude Code no debe responder solo con teoría.
Debe producir entregables concretos y accionables.

## 21.1 Entregables principales
1. propuesta de taxonomía expandida
2. propuesta de relaciones nuevas
3. propuesta de schema mínimo por subtype
4. plan de migración gradual
5. lista de notas sin `domain`
6. lista de subtypes insuficientes o ambiguos
7. propuesta de capa epistemológica
8. propuesta de MOCs estructurales faltantes
9. lista de notas puente prioritarias
10. lista de campañas por dominio

## 21.2 Entregables por campaña
Cada campaña debe producir:
- objetivo
- rationale
- entidades núcleo
- conceptos núcleo
- eventos núcleo
- relaciones críticas
- MOC requerido
- cronología requerida
- notas puente requeridas
- libro final opcional o recomendado

---

# 22. PRIMERA TAREA CONCRETA PARA CLAUDE CODE

## 22.1 Objetivo inmediato
No empezar creando entidades nuevas a ciegas.
Primero hacer un diagnóstico estructural riguroso del vault actual.

## 22.2 Diagnóstico que debe ejecutar
Claude Code debe revisar y entregar:

### A. Diagnóstico taxonómico
- qué types y subtypes existen realmente
- cuáles están infraespecificados
- cuáles sobran o están solapados
- cuáles faltan

### B. Diagnóstico de metadatos
- qué porcentaje tiene `domain`
- qué porcentaje tiene `subdomain`
- qué porcentaje tiene campos mínimos razonables
- qué campos están dispersos o inconsistentes

### C. Diagnóstico relacional
- cuánto depende el sistema de `related`
- qué relaciones deberían tiparse primero
- qué dominios tienen más prosa relacional sin estructura

### D. Diagnóstico de cobertura
- fortalezas actuales
- huecos críticos
- dominios sobrepoblados pero poco conectados
- dominios subdesarrollados

### E. Diagnóstico narrativo
- qué bloques ya están suficientemente maduros para libro
- cuáles necesitan primero estructura y no narrativa

---

# 23. SEGUNDA TAREA CONCRETA PARA CLAUDE CODE

Después del diagnóstico, Claude Code debe proponer una **arquitectura v2** del sistema:

- taxonomía v2
- relaciones v2
- frontmatter v2
- capa epistemológica v2
- flujo de construcción v2
- orden de campañas v2

Sin ejecutar cambios destructivos hasta validación.

---

# 24. TERCERA TAREA CONCRETA PARA CLAUDE CODE

Tras validación, Claude Code debe iniciar una implementación gradual empezando por:

1. completar `domain` faltantes
2. estandarizar `subdomain`
3. introducir `epistemic_mode` y `certainty_level` donde más valor dé
4. proponer migración parcial de `related`
5. identificar el bloque histórico Roma → modernidad
6. generar backlog de biología / química / esoterismo

---

# 25. DECISIONES DE DISEÑO IMPORTANTES

## 25.1 Sobre la historia
La historia no debe modelarse como una línea única obligatoria.
Debe modelarse como:
- grandes bloques narrativos
- conectados por una cronología madre y notas puente

## 25.2 Sobre la filosofía
La filosofía no es solo un dominio de autores.
Es una caja de herramientas para pensar, interpretar ciencia y religión, y construir criterio.

## 25.3 Sobre la religión
La religión debe modelarse como:
- historia
- simbolismo
- cosmovisión
- sistema social

## 25.4 Sobre el esoterismo
El esoterismo debe tratarse como dominio formal y serio, principalmente como:
- tradición simbólica e intelectual
- campo histórico-cultural
- espacio de investigación y misterio

Pero con distinción epistemológica explícita frente a la ciencia.

## 25.5 Sobre los libros
Los libros narrativos se conservan, pero se subordinan a la estructura madura del grafo.

---

# 26. ORDEN RECOMENDADO DE EJECUCIÓN

## 26.1 Primero
Consolidación estructural:
- taxonomy
- metadata
- schemas
- epistemology
- relations

## 26.2 Segundo
Hueco histórico central:
- Edad Media
- Islam clásico
- Renacimiento
- Reforma
- Ilustración

## 26.3 Tercero
Biología + química

## 26.4 Cuarto
India + China + Mesoamérica + Persia

## 26.5 Quinto
Esoterismo formal

## 26.6 Sexto
Libros narrativos grandes construidos sobre bloques maduros

---

# 27. RESULTADO ESPERADO A LARGO PLAZO

Si este blueprint se ejecuta bien, el knowledge graph debe volverse capaz de:

- explicar un tema con claridad
- mostrar conexiones profundas entre dominios
- ofrecer rutas de estudio
- generar cronologías
- generar comparativas
- producir libros narrativos mejores
- servir de base para conversación inteligente con LLMs
- representar una inteligencia personal coherente y durable

---

# 28. INSTRUCCIÓN FINAL PARA CLAUDE CODE

Usa este documento como blueprint maestro.

Tu trabajo no es solo agregar notas.
Tu trabajo es ayudar a transformar este vault en una **inteligencia personal estructurada**.

Prioriza:
- claridad estructural
- relaciones tipadas
- consistencia taxonómica
- huecos estratégicos
- notas puente
- narrativa construida sobre arquitectura sólida
- distinción epistemológica entre ciencia, historia, religión, mito, filosofía y esoterismo

No optimices por volumen bruto.
Optimiza por comprensión, explicabilidad, navegación, conexión y durabilidad.

---

# 29. PRÓXIMO PASO INMEDIATO

Comienza por generar un informe con estas 10 secciones:

1. Resumen ejecutivo del estado actual del vault
2. Taxonomía real detectada
3. Problemas taxonómicos
4. Estado de metadatos
5. Estado de relaciones
6. Huecos estratégicos por dominio
7. Propuesta de taxonomía v2
8. Propuesta de relaciones v2
9. Propuesta de campañas
10. Plan de implementación gradual sin romper el sistema

Ese informe será la base de la siguiente iteración.

---