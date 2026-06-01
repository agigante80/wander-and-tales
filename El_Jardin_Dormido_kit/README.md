# El Jardín Dormido — Juego de rol para niños

Kit de un juego de rol cooperativo para **2 jugadores** (un adulto y su hijo/a), en
español, pensado para jugar en casa con **figuras de Lego** sobre un mapa imprimible
y **dados de rol (d20, d12, d10)**.

Este repositorio es un **punto de continuación**: contiene los PDF finales ya
generados, los scripts de Python que los producen, y los archivos de contexto para
seguir trabajando desde Claude CLI / Claude Code.

## Concepto del juego (resumen)

- **Tono:** mágico y amable. **Nadie muere y nadie pierde.** No hay villanos reales,
  solo cosas que arreglar y amigos por conocer. Se "gana" siendo listo y amable.
- **Mecánica central:** resolver puzles con magia, no combate.
- **Cuatro escuelas de magia**, cada una resuelve puzles a su manera:
  - **Luz** — revela lo escondido, lee mensajes secretos.
  - **Crecer** — plantas, puentes, caminos.
  - **Cambio** — transforma un objeto en otro.
  - **Voz** — habla con animales y objetos.
- **Energía:** cada jugador tiene **5 estrellas** (fichas de Lego). Gastar magia
  consume estrellas; se recuperan al pasar de parada o al ayudar al otro.
- **Cooperación:** si uno falla una tirada, el otro puede ayudar, o combinan magias.

## Los dados (importante)

- **d20 = Dado Mágico** (principal). Igualar o superar el "Número Mágico":
  Fácil = 6+, Normal = 10+, Difícil = 14+.
- **d12 = Dado de Ayuda.** Cuando un jugador ayuda al otro: con 7+ se supera el reto
  aunque el d20 se quede corto.
- **d10 = Dado Sorpresa.** En cada parada se tira y se consulta una tabla de sorpresas
  (1–10). *(El usuario mencionó un "dado de 9"; se confirmó que es un d10.)*

## La aventura: "El Jardín Dormido"

El Gran Jardín se ha quedado dormido y todo el reino se vuelve gris. Los dos pequeños
magos cruzan el jardín desde la **Salida** hasta el **Corazón del Jardín** resolviendo
3 puzles:

1. **Puerta de Enredaderas** (fácil) — abrir un nudo de hojas (Crecer/Cambio/Voz).
2. **Cantero de Flores** — ordenar 4 flores por color con la rima
   *"Primero el sol, luego el mar, después la fresa y a volar"* →
   **amarillo, azul, rojo, blanco**.
3. **Fuente Parlanchina** (normal) — la fuente está triste; con magia de Voz pide que
   le canten o le cuenten un chiste, y vuelve a fluir.

**Final feliz:** en el Corazón no hay un malo, sino un **duendecillo solitario** que
durmió el jardín porque quería compañía. Al ofrecerle amistad, el jardín despierta.

## Contenido del kit (PDFs finales en `/pdfs`)

| Archivo | Qué es |
|---|---|
| `01_mapa_y_reglas.pdf` | Mapa imprimible (A4 horizontal) + guía del adulto con reglas para 2 jugadores. |
| `02_fichas_de_personaje.pdf` | 2 fichas (una por jugador): nombre, magia, 5 estrellas, dibujo de la figura Lego, poder especial, mochila. |
| `03_banco_de_ideas.pdf` | Poderes por magia, objetos mágicos, criaturas, lugares, mini-retos y recompensas. |
| `04_el_mundo_y_la_historia.pdf` | Ambientación: el mundo, quiénes son los niños, qué pasa, lugares, habitantes y texto para leer en voz alta. |

Ver `CONTENT.md` para el texto completo de cada documento.

## Cómo regenerar los PDFs (desde Claude CLI)

Requisitos: Python 3 con `reportlab`, `cairosvg`, `pypdf` (solo el mapa usa SVG).

```bash
pip install reportlab cairosvg pypdf
cd scripts
python build_01_mapa_y_reglas.py   # genera el mapa (SVG->PDF) + reglas, fusionados
python build_02_fichas.py
python build_03_banco_de_ideas.py
python build_04_mundo.py
```

Nota: `build_01` espera un `mapa.svg` en el directorio (incluido en `scripts/`).
Los scripts escriben en rutas tipo `/mnt/user-data/outputs/`; al usarlos en local,
edita las rutas de salida al inicio/fin de cada script.

## Estado y pendientes

Ver `STATUS.md` para el estado actual, decisiones tomadas e ideas siguientes
(ilustraciones del mapa, más aventuras, cartas de criaturas, etc.).
