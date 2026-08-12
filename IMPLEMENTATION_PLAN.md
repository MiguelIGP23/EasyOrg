# easyOrg v1 — Plan maestro de implementación autónoma

## 0. Propósito de este documento

Este archivo es la **fuente de verdad principal** para implementar easyOrg v1 mediante un agente de programación integrado en un IDE como PyCharm.

El agente debe trabajar de forma progresiva, autónoma y segura, realizando:

1. análisis de la fase actual;
2. implementación;
3. tests;
4. corrección de errores;
5. validación;
6. commit;
7. push;
8. continuación automática a la siguiente fase.

El objetivo es que el desarrollador tenga que intervenir lo mínimo posible.

El agente **NO debe intentar implementar todo el proyecto de una sola vez**.

Debe avanzar estrictamente por fases y no pasar a la siguiente hasta que la actual cumpla sus criterios de aceptación.

---

# 1. Objetivo del proyecto

**easyOrg** es una aplicación Python multiplataforma para organizar fotografías y vídeos de forma recursiva basándose en la fecha más fiable disponible.

Debe permitir:

- seleccionar un directorio origen;
- seleccionar un directorio destino padre;
- analizar recursivamente imágenes y vídeos;
- obtener su fecha real de captura/grabación cuando sea posible;
- utilizar fallbacks controlados cuando no exista;
- simular la operación antes de tocar archivos;
- copiar o mover;
- validar cada operación;
- organizar por:
  - Año / Mes
  - Año / Mes / Semana del mes;
- conservar los metadatos y timestamps originales en la medida de lo posible;
- no modificar nunca el contenido multimedia;
- funcionar mediante GUI y CLI;
- funcionar offline en Windows, Ubuntu, Parrot OS y Raspberry Pi OS en Raspberry Pi 5;
- utilizar ExifTool como motor principal de lectura de metadatos.

---

# 2. Principios obligatorios

El agente debe respetar siempre estas reglas:

1. Seguridad de los archivos por encima de velocidad.
2. Nunca modificar metadatos internos.
3. Nunca sobrescribir silenciosamente.
4. Nunca borrar un original antes de validar su copia.
5. Nunca seguir enlaces simbólicos.
6. Nunca crear carpetas vacías innecesarias.
7. Nunca introducir deduplicación en v1.
8. Nunca calcular hashes en v1 salvo cambio explícito de especificación.
9. GUI y CLI deben reutilizar el mismo núcleo.
10. La GUI no debe contener lógica de negocio.
11. El CLI no debe contener lógica de negocio.
12. Usar `pathlib`.
13. Usar type hints.
14. Preferir biblioteca estándar.
15. Añadir dependencias externas solo cuando estén justificadas.
16. No realizar cambios funcionales no contemplados en este documento.
17. No realizar `git push --force`.
18. No reescribir historial Git existente.
19. No borrar ramas remotas automáticamente.
20. No continuar a una fase nueva si los tests no pasan.

---

# 3. Plataformas objetivo

## 3.1 Windows

Objetivo:

- Windows 10
- Windows 11
- x86-64

Distribución final:

```text
easyOrg-Windows/
├── easyOrg.exe
└── tools/
    └── exiftool/
```

Debe funcionar:

- sin Python instalado;
- sin ExifTool instalado;
- sin conexión a Internet.

ExifTool se incluirá con la aplicación.

---

## 3.2 Linux

Compatibilidad prioritaria offline:

- Ubuntu
- Parrot OS
- Raspberry Pi OS ARM64 en Raspberry Pi 5
- Debian como objetivo compatible natural

Orden de búsqueda de ExifTool:

```text
ExifTool portable incluido
        ↓
ExifTool instalado en PATH
        ↓
gestor de paquetes disponible
        ↓
preguntar al usuario si desea instalar
        ↓
intentar instalación solo con consentimiento
        ↓
mostrar instrucciones manuales si falla
```

No ejecutar automáticamente comandos privilegiados sin consentimiento.

---

# 4. Arquitectura obligatoria

Estructura propuesta:

```text
easyOrg/
│
├── README.md
├── IMPLEMENTATION_PLAN.md
├── CHANGELOG.md
├── LICENSE
├── pyproject.toml
├── requirements.txt
├── .gitignore
│
├── src/
│   └── easyorg/
│       ├── __init__.py
│       ├── __main__.py
│       │
│       ├── core/
│       │   ├── __init__.py
│       │   ├── models.py
│       │   ├── scanner.py
│       │   ├── metadata.py
│       │   ├── date_resolver.py
│       │   ├── filename_date_parser.py
│       │   ├── planner.py
│       │   ├── organizer.py
│       │   ├── validator.py
│       │   ├── naming.py
│       │   ├── paths.py
│       │   ├── dependencies.py
│       │   ├── cancel.py
│       │   └── events.py
│       │
│       ├── cli/
│       │   ├── __init__.py
│       │   └── app.py
│       │
│       ├── gui/
│       │   ├── __init__.py
│       │   ├── app.py
│       │   ├── main_window.py
│       │   └── worker.py
│       │
│       └── utils/
│           ├── __init__.py
│           ├── sizes.py
│           ├── dates.py
│           └── platform.py
│
├── tools/
│   └── exiftool/
│
├── tests/
│   ├── unit/
│   ├── integration/
│   └── fixtures/
│
└── scripts/
    ├── build_windows.py
    └── build_linux.py
```

Puede ajustarse si hay una razón técnica clara, pero la separación:

```text
CORE
├── CLI
└── GUI
```

es obligatoria.

---

# 5. Modelo funcional

Flujo:

```text
Inicio
  ↓
Comprobar ExifTool
  ↓
Seleccionar origen
  ↓
Seleccionar destino padre
  ↓
Validar rutas
  ↓
Elegir Copiar / Mover
  ↓
Elegir Año/Mes o Año/Mes/Semana
  ↓
Escanear
  ↓
Leer metadatos
  ↓
Resolver fechas
  ↓
Construir plan
  ↓
Simulación
  ↓
Resumen
  ↓
Confirmación
  ↓
Crear easyOrg_AAAA-MM-DD
  ↓
Procesar
  ↓
Validar
  ↓
Resumen final
```

En modo copia:

```text
copiar
  ↓
validar
  ↓
mantener original
  ↓
al terminar preguntar si se desean eliminar originales
```

En modo mover:

```text
copiar
  ↓
validar
  ↓
eliminar original
```

---

# 6. Directorio de salida

El usuario selecciona un directorio padre.

easyOrg crea:

```text
easyOrg_AAAA-MM-DD
```

Si existe:

```text
easyOrg_AAAA-MM-DD_2
easyOrg_AAAA-MM-DD_3
...
```

Nunca reutilizar silenciosamente una carpeta de ejecución anterior.

---

# 7. Validación de rutas

Rechazar:

- origen == destino;
- destino dentro de origen;
- origen dentro de destino.

Usar rutas resueltas y normalizadas.

No confiar en comparación simple de strings.

---

# 8. Escaneo

- Recursivo.
- Solo directorios físicos.
- No seguir symlinks.
- Solo imágenes y vídeos.
- Ignorar archivos auxiliares.

Extensiones iniciales de imagen:

```text
.jpg
.jpeg
.png
.heic
.heif
.webp
.tif
.tiff
.gif
.bmp
.dng
.raw
.cr2
.cr3
.nef
.arw
.orf
.rw2
```

Vídeo:

```text
.mp4
.mov
.m4v
.avi
.mkv
.mts
.m2ts
.3gp
.webm
.mpg
.mpeg
```

Fuera de alcance:

```text
.pdf
.mp3
.flac
.xmp
.aae
.thm
documentos
```

---

# 9. Prioridad de fecha

Orden obligatorio:

```text
1. Fecha original de captura/grabación
2. Otras fechas internas multimedia fiables
3. Fecha inequívoca obtenida del nombre
4. Fecha de última modificación del filesystem
5. Fecha de creación del filesystem
6. SIN_FECHA
```

---

# 10. Fecha desde nombre

Aceptar únicamente patrones inequívocos.

Ejemplos válidos:

```text
IMG_20230417_153025.jpg
VID_20210821_121300.mp4
20200514_182223.jpg
Screenshot_20240322-194355.png
2024-03-18_12-42-31.jpg
```

No aceptar:

```text
foto_12_04_08.jpg
```

Validar siempre con `datetime`.

---

# 11. Organización

## Año / Mes

```text
2024/
├── 01 - Enero/
├── 02 - Febrero/
...
```

## Año / Mes / Semana

Semana del mes:

```text
1-7   → Semana 1
8-14  → Semana 2
15-21 → Semana 3
22-28 → Semana 4
29-31 → Semana 5
```

Fórmula:

```python
((day - 1) // 7) + 1
```

No crear carpetas vacías.

---

# 12. SIN_FECHA

```text
easyOrg_AAAA-MM-DD/
└── SIN_FECHA/
```

---

# 13. Colisiones de nombre

Nunca sobrescribir.

```text
IMG_001.jpg
IMG_001_2.jpg
IMG_001_3.jpg
```

La resolución debe ser determinista.

---

# 14. Copia

Usar preferentemente:

```python
shutil.copy2()
```

Después validar:

```text
destino existe
+
tamaño destino == tamaño origen
```

---

# 15. Movimiento seguro

No depender directamente de `shutil.move()`.

Implementar:

```text
copy
→ validate
→ delete source
```

Si la validación falla:

```text
NO borrar origen
```

---

# 16. Cancelación

GUI:

```text
Cancelar
```

CLI:

```text
Ctrl+C
```

Al cancelar:

1. terminar de forma segura la operación de archivo actual si es viable;
2. no comenzar nuevos archivos;
3. conservar todo lo ya procesado;
4. no hacer rollback global;
5. mostrar resumen final.

---

# 17. Simulación

Obligatoria antes de copiar/mover.

Debe mostrar:

```text
archivos encontrados
imágenes
vídeos
fecha desde metadata
fecha desde nombre
fecha desde filesystem
sin fecha
colisiones
tamaño total
espacio disponible
```

No modificar nada durante simulación.

---

# 18. Logging visible

No implementar niveles de logging formales como requisito funcional.

Emitir mensajes simples:

```text
[easyOrg] Iniciando...
[easyOrg] Buscando ExifTool...
[easyOrg] ExifTool encontrado.
[easyOrg] Escaneando...
[easyOrg] Leyendo metadatos...
[easyOrg] Preparando simulación...
```

No mostrar una línea por cada archivo salvo problemas.

El core debe emitir eventos/callbacks.

CLI los imprime.

GUI los muestra en un panel.

---

# 19. GUI

Usar:

```text
tkinter
ttk
```

Interfaz básica:

```text
Origen       [Buscar]
Destino      [Buscar]

Copiar / Mover
Año-Mes / Año-Mes-Semana

[Analizar]

Actividad:
...

[barra de progreso]

[Cancelar]
```

Las tareas pesadas nunca deben ejecutarse en el hilo Tkinter.

Usar:

```text
worker thread
→ queue
→ root.after()
→ GUI
```

---

# 20. CLI

Primera versión interactiva.

Debe ser completamente funcional antes de terminar la GUI.

---

# 21. Modelos

Usar dataclasses y enums.

Como mínimo:

```text
MediaType
DateSource
OperationMode
OrganizationMode
```

Modelos recomendados:

```text
MediaFile
PlannedOperation
OrganizationPlan
ScanStats
OperationResult
```

---

# 22. Estrategia Git autónoma

## Rama principal

La rama `main` debe mantenerse funcional.

## Rama de trabajo

Si el repositorio solo contiene este proyecto, el agente puede trabajar sobre:

```text
develop
```

Si `develop` no existe:

1. comprobar estado Git;
2. actualizar `main`;
3. crear `develop`;
4. realizar pushes allí.

No realizar merges automáticos a `main` salvo que el usuario lo haya autorizado explícitamente.

Si el usuario desea máxima simplicidad y solo existe `main`, se permite trabajar directamente en `main` únicamente si no existe historial de producción relevante.

Preferencia:

```text
main
└── develop
```

---

# 23. Protocolo Git obligatorio por fase

Cada fase debe terminar con:

```text
1. git status
2. ejecutar tests
3. ejecutar comprobaciones estáticas configuradas
4. revisar cambios
5. git add de archivos relevantes
6. git commit
7. git push
```

Nunca usar:

```text
git add .
```

a ciegas si existen archivos no revisados.

Preferir añadir rutas explícitas.

Nunca commitear:

```text
.venv/
venv/
__pycache__/
.idea/
dist/
build/
*.pyc
archivos multimedia personales
credenciales
tokens
```

---

# 24. Regla de commits

Un commit debe representar una unidad funcional coherente.

Formato recomendado:

```text
chore:
feat:
fix:
test:
refactor:
build:
docs:
```

Ejemplos:

```text
chore: initialize easyOrg project
feat: add media scanner
feat: add metadata date resolver
test: cover filename date parsing
fix: preserve source file on failed move
```

---

# 25. Regla de pushes

Después de cada fase correctamente validada:

```text
git push
```

No acumular muchas fases sin push.

Objetivo:

> Cada checkpoint funcional debe existir también en remoto.

Si el push falla:

1. no perder cambios;
2. mostrar el error;
3. reintentar solo si es un problema transitorio evidente;
4. si requiere autenticación/intervención, detener únicamente el push;
5. conservar commit local;
6. no rehacer la fase.

---

# 26. Regla de recuperación

Si una fase rompe tests:

```text
NO COMMIT
NO PUSH
NO CONTINUAR
```

El agente debe:

1. diagnosticar;
2. corregir;
3. volver a ejecutar tests;
4. continuar únicamente cuando todo pase.

Si después de varios intentos no puede resolverlo sin modificar la especificación:

```text
DETENER EJECUCIÓN
```

y dejar un informe claro.

No improvisar cambios funcionales importantes para “hacer pasar los tests”.

---

# 27. Regla de parada segura

El agente puede continuar automáticamente entre fases.

Debe detenerse si ocurre alguno de estos eventos:

- tests críticos siguen fallando;
- riesgo de pérdida de archivos;
- requiere credenciales;
- Git remoto rechaza por conflicto no trivial;
- habría que hacer force-push;
- dependencia externa presenta incompatibilidad grave;
- especificación es contradictoria;
- se requiere una decisión funcional no definida aquí.

No detenerse por pequeñas decisiones internas de implementación.

Debe resolverlas usando buenas prácticas.

---

# 28. Preflight antes de comenzar

Antes de modificar código:

1. leer `IMPLEMENTATION_PLAN.md`;
2. inspeccionar árbol del proyecto;
3. ejecutar `git status`;
4. identificar rama actual;
5. comprobar remoto;
6. ejecutar tests existentes;
7. comprobar versión de Python;
8. detectar sistema operativo;
9. no modificar nada todavía.

Si existen cambios locales no commiteados que no fueron generados por el agente:

- no sobrescribirlos;
- conservarlos;
- trabajar alrededor de ellos si es seguro;
- detenerse si existe riesgo de conflicto.

---

# 29. Secuencia autónoma completa

El agente debe ejecutar las fases siguientes en orden.

---

# FASE 0 — Inspección y preparación Git

## Objetivo

Preparar un entorno seguro.

## Tareas

- comprobar repositorio;
- crear `.gitignore` si falta;
- comprobar remoto;
- identificar rama;
- crear `develop` si procede;
- ejecutar tests existentes;
- registrar baseline.

## No implementar funcionalidad.

## Validación

```text
git status conocido
rama conocida
remoto conocido
baseline conocido
```

## Commit

Solo si fue necesario modificar infraestructura:

```text
chore: prepare repository for easyOrg development
```

Push.

---

# FASE 1 — Bootstrap del proyecto

## Tareas

- estructura `src`;
- paquetes Python;
- `pyproject.toml`;
- pytest;
- README mínimo;
- entrypoint básico;
- versión inicial.

Debe funcionar:

```bash
python -m easyorg
```

Resultado inicial:

```text
easyOrg
```

## Tests

Smoke test de importación.

## Commit

```text
chore: initialize easyOrg project structure
```

Push.

---

# FASE 2 — Modelos y utilidades

Implementar:

- enums;
- dataclasses;
- nombres de meses;
- cálculo de semana;
- formato de tamaños;
- creación de nombre `easyOrg_AAAA-MM-DD[_N]`.

## Tests obligatorios

Semana:

```text
1 → 1
7 → 1
8 → 2
14 → 2
15 → 3
21 → 3
22 → 4
28 → 4
29 → 5
31 → 5
```

Directorio base:

```text
easyOrg_2026-08-12
easyOrg_2026-08-12_2
easyOrg_2026-08-12_3
```

## Commit

```text
feat: add core models and utilities
```

Push.

---

# FASE 3 — Validación de rutas

Implementar:

- rutas normalizadas;
- igualdad;
- origen dentro de destino;
- destino dentro de origen;
- permisos básicos.

## Tests

Usar `tmp_path`.

## Commit

```text
feat: add source and destination path validation
```

Push.

---

# FASE 4 — Scanner multimedia

Implementar:

- recursividad;
- filtros;
- clasificación imagen/vídeo;
- ignorar symlinks;
- tamaño de archivos.

No leer metadata todavía.

## Tests

Directorios temporales anidados.

## Commit

```text
feat: add recursive media scanner
```

Push.

---

# FASE 5 — Parser de fechas en nombres

Implementar parser conservador.

## Tests válidos

```text
IMG_20230417_153025.jpg
VID_20210821_121300.mp4
20200514_182223.jpg
Screenshot_20240322-194355.png
2024-01-31_photo.jpg
```

## Tests inválidos

```text
foto_12_04_08.jpg
IMG_20231340.jpg
foto_final.jpg
123456.jpg
```

## Commit

```text
feat: add conservative filename date parser
```

Push.

---

# FASE 6 — Fechas del filesystem

Implementar:

- modificación;
- creación cuando exista;
- compatibilidad Windows/Linux;
- ausencia de birthtime.

No decidir prioridad completa todavía.

## Tests

Mocks cuando sea necesario.

## Commit

```text
feat: add filesystem date fallbacks
```

Push.

---

# FASE 7 — Resolución de ExifTool

Implementar localización:

```text
portable
→ PATH
→ instalación asistida
```

Primero construir la abstracción.

No integrar todavía lectura masiva de metadata.

Debe existir una clase/servicio claramente testeable.

## Linux

Prioridad de instalación v1:

```text
apt
```

Otros gestores pueden añadirse si resulta sencillo.

La instalación siempre requiere confirmación desde UI/CLI.

## Tests

Mockear subprocess.

## Commit

```text
feat: add ExifTool dependency resolver
```

Push.

---

# FASE 8 — Lectura de metadatos ExifTool

Implementar proveedor.

Objetivos:

- ejecución en lote;
- evitar proceso por archivo;
- salida JSON;
- normalización a estructura Python;
- errores por archivo sin abortar lote completo cuando sea posible.

No modificar metadata.

## Campos fotografía

Priorizar:

```text
DateTimeOriginal
CreateDate
```

más campos técnicamente justificados.

## Vídeo

Considerar:

```text
DateTimeOriginal
MediaCreateDate
TrackCreateDate
CreateDate
```

Definir orden de confianza explícito.

## Commit

```text
feat: integrate ExifTool metadata reader
```

Push.

---

# FASE 9 — DateResolver

Implementar política única:

```text
metadata primaria
metadata secundaria
filename
modification
creation
none
```

No duplicar esta lógica.

## Tests

Cubrir todos los caminos.

## Commit

```text
feat: add media capture date resolver
```

Push.

---

# FASE 10 — Planner

Construir `OrganizationPlan`.

No escribir archivos.

Implementar:

- Año/Mes;
- Año/Mes/Semana;
- SIN_FECHA;
- resolución de nombres;
- directorio base;
- operaciones previstas.

## Tests

Comprobar destinos exactos.

## Commit

```text
feat: add organization planner
```

Push.

---

# FASE 11 — Simulación y estadísticas

Calcular:

- total;
- imágenes;
- vídeos;
- metadata;
- filename;
- filesystem;
- sin fecha;
- colisiones;
- bytes;
- espacio disponible.

No tocar archivos.

## Validar espacio

Usar:

```python
shutil.disk_usage()
```

No permitir ejecutar si no hay espacio suficiente.

## Commit

```text
feat: add organization simulation and statistics
```

Push.

---

# FASE 12 — Motor de copia

Implementar copia segura con `copy2`.

Validación ligera:

```text
exists
size match
```

Errores individuales no abortan toda la ejecución.

## Tests críticos

- copia correcta;
- fallo de permisos simulado;
- tamaño distinto;
- destino desaparecido.

## Commit

```text
feat: add validated copy engine
```

Push.

---

# FASE 13 — Movimiento seguro

Implementar exclusivamente:

```text
copy
validate
delete source
```

## TEST CRÍTICO

Si la validación falla:

```text
origen debe seguir existiendo
```

No continuar hasta cubrir este comportamiento.

## Commit

```text
feat: add safe move workflow
```

Push.

---

# FASE 14 — Cancelación

Implementar token de cancelación.

Debe comprobarse antes de comenzar cada archivo nuevo.

## Tests

Cancelar tras N operaciones.

Comprobar:

- procesados correctos;
- pendientes intactos;
- originales seguros.

## Commit

```text
feat: add controlled operation cancellation
```

Push.

---

# FASE 15 — Eventos y progreso

Crear mecanismo común.

Core no debe imprimir ni tocar widgets.

Eventos mínimos:

```text
message
progress
summary
```

## Commit

```text
feat: add shared progress event system
```

Push.

---

# FASE 16 — CLI completo

Implementar:

- dependencia;
- origen;
- destino;
- modo;
- organización;
- análisis;
- resumen;
- confirmación;
- ejecución;
- cancelación;
- resumen final;
- eliminación opcional de originales tras copia.

El CLI debe ser funcional de extremo a extremo.

## Test manual obligatorio

Ejecutar con fixtures temporales.

## Commit

```text
feat: add interactive CLI workflow
```

Push.

---

# FASE 17 — End-to-end CLI

Antes de GUI, ejecutar una prueba completa con contenido artificial.

Casos:

```text
COPY Año/Mes
COPY Año/Mes/Semana
MOVE
colisiones
SIN_FECHA
cancelación
```

Corregir cualquier defecto.

## Commit

Solo si hubo cambios:

```text
fix: stabilize end-to-end CLI workflow
```

Push.

---

# FASE 18 — GUI base

Implementar Tkinter.

Controles:

- origen;
- destino;
- copiar/mover;
- estructura;
- analizar;
- actividad;
- progreso;
- cancelar.

No implementar aún threading complejo si no es necesario para construir layout.

## Commit

```text
feat: add initial Tkinter interface
```

Push.

---

# FASE 19 — Worker GUI no bloqueante

Implementar:

```text
thread
queue
root.after()
```

Nunca actualizar widgets desde worker.

Probar:

- ventana movible durante análisis;
- progreso;
- cancelación;
- mensajes.

## Commit

```text
feat: add non-blocking GUI workers
```

Push.

---

# FASE 20 — Flujo GUI completo

Conectar GUI con core.

Debe permitir flujo completo equivalente a CLI.

Diálogos:

- confirmación de ejecución;
- instalación ExifTool;
- eliminación de originales;
- errores estructurales.

## Commit

```text
feat: complete GUI organization workflow
```

Push.

---

# FASE 21 — Gestión de eliminación tras COPY

Implementar únicamente después de que copia esté validada.

Default:

```text
NO
```

No borrar directorios vacíos.

Si existe algún resultado fallido, ser conservador.

## Tests

Cobertura específica.

## Commit

```text
feat: add optional source cleanup after validated copy
```

Push.

---

# FASE 22 — ExifTool portable Linux

Preparar integración portable compatible con:

- Ubuntu;
- Parrot;
- Raspberry Pi OS.

Comprobar funcionamiento offline.

Fallback:

```text
portable
→ PATH
→ apt
```

No instalar sin permiso.

## Commit

```text
build: add portable ExifTool support for Linux
```

Push.

---

# FASE 23 — ExifTool Windows

Preparar distribución Windows.

Resolver rutas tanto:

- desarrollo;
- PyInstaller.

## Commit

```text
build: bundle ExifTool for Windows
```

Push.

---

# FASE 24 — Packaging Windows

Configurar PyInstaller.

Objetivo:

```text
easyOrg.exe
```

GUI funcional sin Python.

Opcional:

```text
easyOrg-cli.exe
```

si no complica demasiado mantenimiento.

## Prueba obligatoria

Probar ejecutable fuera del entorno virtual.

## Commit

```text
build: add Windows standalone packaging
```

Push.

---

# FASE 25 — Packaging Linux

Primero priorizar ejecución estándar Python.

Después evaluar PyInstaller.

No bloquear v1 si empaquetado Linux universal resulta poco fiable.

Compatibilidad más importante que un único binario.

## Commit

```text
build: add Linux distribution workflow
```

Push.

---

# FASE 26 — Suite de integración

Crear fixtures no personales.

Cubrir:

- JPEG con fecha;
- JPEG sin fecha;
- vídeo;
- filename;
- SIN_FECHA;
- colisión;
- rutas anidadas.

## Commit

```text
test: add end-to-end integration coverage
```

Push.

---

# FASE 27 — Robustez

Probar:

- archivo desaparece tras simulación;
- permiso denegado;
- destino se queda sin espacio;
- ExifTool falla;
- metadata corrupta;
- nombre extraño;
- Unicode;
- extensiones en mayúsculas;
- rutas largas;
- carpetas ocultas;
- cancelación repetida.

No añadir nuevas features.

## Commit

```text
fix: harden filesystem and metadata edge cases
```

Push.

---

# FASE 28 — Documentación

Actualizar README.

Debe explicar:

- qué hace;
- plataformas;
- instalación;
- GUI;
- CLI;
- ExifTool;
- seguridad;
- estructura de carpetas;
- limitaciones.

## Commit

```text
docs: complete easyOrg user documentation
```

Push.

---

# FASE 29 — Release candidate

Ejecutar:

```text
tests unitarios
tests integración
smoke CLI
smoke GUI
```

Generar build Windows.

No modificar funcionalidades.

Corregir solo defectos.

## Commit

```text
fix: prepare easyOrg v1 release candidate
```

Push.

---

# FASE 30 — Cierre v1

Comprobar criterios de aceptación.

Actualizar:

```text
CHANGELOG.md
versión
README
```

Crear commit:

```text
chore: prepare easyOrg v1.0.0
```

Push.

No crear tag ni release remoto automáticamente salvo que el usuario haya autorizado previamente esa acción.

---

# 30.1 Criterios de aceptación definitivos

easyOrg v1 está terminada cuando:

- escanea imágenes/vídeos recursivamente;
- no sigue symlinks;
- obtiene metadata con ExifTool;
- prioriza fecha real;
- usa filename antes del filesystem;
- soporta SIN_FECHA;
- organiza Año/Mes;
- organiza Año/Mes/Semana;
- no crea carpetas vacías;
- crea `easyOrg_AAAA-MM-DD[_N]`;
- no sobrescribe;
- simula antes;
- muestra resumen;
- valida espacio;
- copia conservando timestamps;
- valida existencia+tamaño;
- mueve mediante copy/validate/delete;
- puede cancelar;
- muestra resumen tras cancelar;
- nunca modifica metadata;
- CLI funciona sin GUI;
- GUI no se bloquea;
- Windows funciona offline;
- Ubuntu funciona offline;
- Parrot funciona offline;
- Raspberry Pi 5 funciona offline;
- otros Unix tienen fallback;
- no se elimina un original si la copia falla.

---

# 31. Auditoría automática al final de cada fase

Antes de commit:

```text
[ ] tests pasan
[ ] no hay traceback
[ ] no hay TODO crítico
[ ] no hay rutas locales
[ ] no hay secretos
[ ] no hay multimedia personal
[ ] no hay venv
[ ] no hay __pycache__
[ ] no hay .idea salvo decisión explícita
[ ] no hay build/dist accidental
[ ] imports limpios
[ ] type hints razonables
[ ] comportamiento coincide con plan
```

---

# 32. Auditoría de seguridad para fases destructivas

Antes de considerar completa cualquier fase que pueda borrar archivos:

```text
[ ] el original solo se elimina después de validación
[ ] fallo de copia conserva original
[ ] excepción conserva original
[ ] cancelación conserva pendientes
[ ] no existe ruta que borre antes de validar
[ ] tests cubren esos casos
```

Si cualquiera falla:

```text
NO COMMIT
NO PUSH
```

---

# 33. Política de cambios no previstos

Si el agente encuentra una mejora no descrita:

### Puede implementarla automáticamente si:

- es interna;
- no cambia UX;
- no cambia comportamiento esperado;
- reduce duplicación;
- aumenta seguridad;
- no añade dependencia innecesaria.

Ejemplo:

```text
refactor interno
helper reutilizable
mejor type hint
```

### Debe detenerse si:

- cambia comportamiento;
- añade una nueva feature;
- elimina compatibilidad;
- modifica prioridad de fechas;
- cambia cómo se borran originales;
- cambia estructura de salida;
- introduce una nueva dependencia pesada.

---

# 34. Política de dependencias

Antes de añadir una dependencia Python externa:

1. comprobar si biblioteca estándar resuelve el problema;
2. justificar necesidad;
3. fijar versión razonable;
4. documentarla;
5. añadirla al mecanismo de instalación correspondiente.

No añadir frameworks innecesarios.

---

# 35. Política de código

Preferencias:

```text
PEP 8
pathlib
dataclasses
Enum
type hints
funciones pequeñas
servicios con responsabilidades claras
```

Evitar:

```text
god classes
estado global
imports circulares
except Exception: pass
print dentro del core
os.path cuando pathlib sea suficiente
```

---

# 36. Manejo de errores

Errores por archivo:

```text
registrar
continuar
```

Errores estructurales:

```text
detener
```

Ejemplos estructurales:

- ExifTool imposible de obtener;
- origen inválido;
- destino inválido;
- sin permisos;
- espacio insuficiente.

---

# 37. Comportamiento ante conflicto Git

Si `git push` es rechazado porque el remoto tiene nuevos commits:

1. no hacer force push;
2. ejecutar fetch;
3. inspeccionar diferencia;
4. si puede integrar sin conflicto mediante rebase/merge seguro, hacerlo;
5. ejecutar tests otra vez;
6. push;
7. si existe conflicto no trivial, detener y documentar.

---

# 38. Comportamiento ante interrupción del agente

Como cada fase termina en commit + push, el proyecto debe poder reanudarse.

Al reiniciar:

1. leer este documento;
2. ejecutar preflight;
3. localizar última fase completada usando Git y código;
4. verificar tests;
5. continuar desde la primera fase incompleta.

No repetir fases ya completas salvo corrección necesaria.

---

# 39. Archivo de estado opcional

El agente puede mantener:

```text
AGENT_STATUS.md
```

con:

```text
Última fase completada
Commit
Tests
Siguiente fase
Problemas conocidos
```

Actualizarlo al final de cada fase.

Si se utiliza, debe estar versionado.

Ejemplo:

```text
Fase completada: 12 — Motor de copia
Commit: abc1234
Tests: 84 passed
Siguiente: 13 — Movimiento seguro
Problemas conocidos: ninguno
```

Esto se recomienda para facilitar recuperación autónoma.

---

# 40. Regla de continuidad automática

Una vez iniciado con una instrucción del usuario equivalente a:

> Implementa easyOrg siguiendo IMPLEMENTATION_PLAN.md de forma autónoma.

el agente está autorizado a:

- ejecutar fases consecutivas;
- crear/modificar código;
- ejecutar tests;
- crear commits;
- hacer pushes;
- continuar sin pedir confirmación después de cada fase.

Debe detenerse únicamente bajo las reglas de parada definidas en este documento.

---

# 41. Prompt recomendado para el agente

Usar:

```text
Lee IMPLEMENTATION_PLAN.md completo antes de modificar nada.

Implementa easyOrg v1 siguiendo estrictamente ese documento.

Trabaja de forma autónoma y progresiva, fase por fase, comenzando por la primera que aún no esté completada.

Para cada fase:

1. inspecciona el código existente;
2. implementa únicamente el alcance de esa fase;
3. crea o actualiza sus tests;
4. ejecuta toda la suite de tests relevante;
5. corrige cualquier fallo;
6. comprueba git status y revisa los cambios;
7. realiza un commit coherente;
8. haz push al remoto;
9. actualiza AGENT_STATUS.md si existe;
10. continúa automáticamente a la siguiente fase.

No avances si los tests fallan.

No hagas force-push.

No borres ni sobrescribas cambios ajenos no commiteados.

No cambies la especificación funcional.

Detente únicamente cuando se cumpla alguna de las reglas de parada del documento o cuando easyOrg v1 esté completado.
```

---

# 42. Fuera de alcance v1

No implementar:

- deduplicación;
- hashes;
- reconocimiento facial;
- GPS;
- clasificación por cámara;
- edición EXIF;
- transcodificación;
- audio;
- documentos;
- XMP/AAE;
- limpieza de directorios vacíos;
- rollback global;
- cloud;
- base de datos;
- watcher;
- daemon;
- servicio en background.

---

# 43. Mejoras futuras

Posibles v2+:

- documentos;
- audio;
- GPS;
- dispositivo/cámara;
- configuración persistente;
- historial;
- manifiestos JSON;
- modo CLI no interactivo;
- automatización;
- deduplicación opcional;
- hashes opcionales;
- rollback mediante manifiesto;
- watcher.

No condicionar v1 a estas funcionalidades.

---

# 44. Resultado esperado

Ejemplo:

```text
FotosDesordenadas/
├── DCIM/
├── movil/
├── whatsapp/
├── viajes/
└── videos/
```

easyOrg:

```text
easyOrg_2026-08-12/
├── 2019/
│   └── 08 - Agosto/
├── 2020/
├── 2021/
├── 2022/
└── SIN_FECHA/
```

O:

```text
easyOrg_2026-08-12/
└── 2026/
    └── 08 - Agosto/
        ├── Semana 1/
        ├── Semana 2/
        └── Semana 4/
```

El contenido multimedia debe permanecer fiel al original.

---

# 45. Definición de éxito del desarrollo autónomo

El plan se considera correctamente seguido si:

1. cada fase puede rastrearse a uno o varios commits;
2. cada checkpoint relevante existe en remoto;
3. ninguna fase posterior depende de código roto;
4. las operaciones destructivas están testeadas;
5. el agente puede reanudar el trabajo desde Git sin depender de memoria de conversación;
6. easyOrg v1 cumple todos los criterios de aceptación;
7. el usuario no necesita supervisar cada cambio individual para mantener seguridad razonable.

