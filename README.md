# easyOrg

easyOrg organiza fotos y videos en una estructura cronologica segura sin modificar su contenido multimedia. El mismo core se reutiliza desde CLI y GUI.

## Que hace

- escanea imagenes y videos de forma recursiva;
- no sigue enlaces simbolicos;
- resuelve la fecha con prioridad: metadata, nombre, filesystem, `SIN_FECHA`;
- simula antes de copiar o mover;
- organiza por `Año/Mes` o `Año/Mes/Semana`;
- no sobrescribe nombres: resuelve colisiones de forma determinista;
- copia con validacion de existencia y tamaño;
- mueve mediante `copy -> validate -> delete`;
- permite cancelacion controlada;
- registra mensajes simples y cronologicos para CLI y GUI.

## Plataformas

- Windows 10/11
- Ubuntu / Debian
- Parrot OS
- Raspberry Pi OS ARM64

## Requisitos

- Python 3.12 o superior para ejecucion desde codigo fuente
- ExifTool
  - Windows: binario portable en `tools/exiftool/windows/` o `tools/exiftool/`
  - Linux: portable en `tools/exiftool/linux/` o `tools/exiftool/`, o `exiftool` en `PATH`
  - Linux puede ofrecer instalacion asistida con `apt` solo con consentimiento del usuario

## CLI

Ejemplo interactivo:

```bash
python -m easyorg
```

Ejemplo directo:

```bash
python -m easyorg --source /ruta/origen --destination /ruta/destino --mode copy --organization year-month --yes
```

Opciones principales:

- `--mode copy|move`
- `--organization year-month|year-month-week`
- `--yes`
- `--delete-sources-after-copy`
- `--gui`

## GUI

Ejecuta:

```bash
python -m easyorg --gui
```

La GUI usa `tkinter`, mantiene el trabajo pesado fuera del hilo principal y muestra actividad, progreso, cancelacion y resumen.

## Packaging

Linux:

```bash
python scripts/build_linux.py
```

Windows:

```bash
python scripts/build_windows.py
```

El build Windows usa PyInstaller y genera salida en `dist/`.

## GitHub Releases

El repositorio incluye un workflow para publicar el ejecutable de Windows como asset descargable en GitHub Releases.

Flujo previsto:

```bash
git tag v1.0.0
git push origin v1.0.0
```

Cuando se publica un tag con formato `v*`, GitHub Actions:

- ejecuta los tests;
- construye `easyOrg.exe` en Windows;
- empaqueta `dist/easyOrg/` en un zip;
- adjunta ese zip a la Release correspondiente.

## Seguridad

- nunca modifica metadata interna;
- nunca borra un original antes de validar su copia;
- no hace deduplicacion ni hashes en v1;
- no hace rollback global;
- la eliminacion de originales tras `copy` solo se ofrece cuando no hubo fallos.

## Estructura de salida

```text
easyOrg_YYYY-MM-DD/
├── 2024/
│   └── 03 - Marzo/
│       └── Semana 3/
└── SIN_FECHA/
```

## Limitaciones conocidas

- el repositorio prepara la estructura para ExifTool portable, pero no incluye binarios reales;
- la validacion automatica cubre tests, CLI y builds locales; la comprobacion manual multiplataforma final depende del entorno donde se despliegue.
