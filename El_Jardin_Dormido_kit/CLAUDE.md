# CLAUDE.md — instrucciones para Claude Code

Este proyecto es un **kit de juego de rol infantil en español** llamado
"El Jardín Dormido". Lee `README.md`, `CONTENT.md` y `STATUS.md` antes de empezar.

## Principios de diseño (no romper)
- Público: **niños**. Todo debe ser **amable y apropiado**: nadie muere, nadie pierde,
  no hay violencia ni villanos reales. Los conflictos se resuelven con ingenio y amistad.
- Juego **cooperativo para 2** (un adulto y un niño/a).
- Componentes físicos: **Lego** + dados **d20/d12/d10**. No introducir dados que el
  usuario no tiene (p.ej. nada de d6/d8 obligatorios; el d10 ya cubre la tabla sorpresa).
- Idioma de los entregables: **español** (los PDF evitan acentos en algunos textos por
  compatibilidad de fuente; al regenerar puedes usar acentos si la fuente lo soporta).

## Estilo de los PDF
- Generados con `reportlab` (y `cairosvg`+`pypdf` para el mapa).
- Paleta: crema `#fef9ef`, verde `#4ea24a`, teal `#2bb3a3`, rosa `#d36fb0`,
  azul `#3f8fd6`, dorado `#f2a93b`, morado `#8a6fd6`. Texto `#3a5a32`.
- Mantener los archivos **pequeños** (fuentes Helvetica estándar, sin incrustar).

## Flujo de trabajo
- Para editar un documento: modifica su script en `scripts/` o regéneralo desde el
  texto de `CONTENT.md`.
- Tras generar, revisa visualmente (rasterizar a PNG) antes de dar por bueno.
- `scripts/merge_all.py` fusiona los 4 PDFs en uno solo para imprimir.

## Cosas a vigilar
- Las rutas de salida en los scripts apuntan a `/mnt/user-data/outputs/`; cámbialas a
  rutas locales al ejecutar en CLI.
- `build_01_mapa_y_reglas.py` necesita `scripts/mapa.svg` en el mismo directorio.
