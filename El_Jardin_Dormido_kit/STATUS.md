# Estado del proyecto y handoff para Claude CLI

## Resumen de la sesión

Partimos de la idea de un juego de rol para niños donde **nadie muere, se usa magia y
se resuelven puzles**, jugable **en 2** (un padre y su hijo), con **Lego** para objetos
y personajes y **dados d20 / d12 / d10**. Construimos un kit completo en 4 PDFs y los
guardamos (parcialmente) en una carpeta de Google Drive.

## Decisiones de diseño tomadas

- **2 jugadores** cooperativos; el adulto hace de guía y también juega.
- **Sin combate, sin perder.** Mecánicas de ayuda y de combinar magias para que nunca
  haya un punto muerto.
- **Dados:** d20 principal (Número Mágico 6/10/14), d12 de ayuda (umbral 7+), d10 de
  sorpresa (tabla 1–10). Se confirmó que el tercer dado es un **d10** (no un "d9").
- **Lego** como componente físico: figuras = jugadores en el mapa; piezas sueltas = las
  5 estrellas de energía; construcciones libres = objetos (llave, flores, fuente...).
- **Estilo visual** de los PDF: fondo crema (#fef9ef), verdes (#4ea24a), acentos teal/
  rosa/azul/dorado/morado, tipografía sans, marco punteado, tono infantil y cálido.

## Estado de los entregables

| Documento | PDF generado | En Google Drive |
|---|---|---|
| Mapa + Reglas | ✅ | ✅ subido |
| Fichas de personaje | ✅ | ✅ subido |
| El Mundo y la Historia | ✅ | ✅ subido |
| Banco de Ideas | ✅ (versión 1 página) | ❌ no subido (fallaba por tamaño) |

### Notas sobre Google Drive
- Carpeta: **"Juego de Rol - Fichas e Historia"**
  (id `1nrLfGBDZw2Kfylk_nvIGEyXPsqoRdQM7`).
- La subida de archivos grandes vía la herramienta de Drive fallaba/truncaba; por eso el
  Banco de Ideas se redujo a 1 página. Si continúas en local, sube ese PDF manualmente.
- Quedaron **2 archivos "Untitled" corruptos** en la raíz del Drive del usuario (de
  intentos fallidos). Recomendación: borrarlos a mano.

## Restricciones técnicas aprendidas
- Mantener los PDF **pequeños** (fuentes estándar Helvetica, sin incrustar; vectores en
  vez de imágenes) facilita subirlos. `qpdf` ayuda a recomprimir.
- El mapa se dibuja como SVG (`scripts/mapa.svg`) y se convierte con `cairosvg`, luego se
  fusiona con la página de reglas usando `pypdf`.

## Ideas para las próximas sesiones (no hechas aún)
- **Ilustrar el mapa** con dibujos más ricos o iconos por parada.
- **Más aventuras** además de "El Jardín Dormido" (mismo motor, nuevo escenario): p.ej.
  "El Lago que se Olvidó de Cantar", "La Biblioteca de Hojas".
- **Cartas de criaturas** imprimibles (gato de niebla, búho bibliotecario, etc.).
- **Hoja de pegatinas/recompensas** para marcar progreso.
- **Versión en inglés** del kit.
- **Tarjetas de puzle** físicas para cada parada.
- Un **PDF "todo en uno"** que fusione los 4 documentos (con pypdf) para imprimir de una vez.

## Cómo retomar en Claude CLI
1. Lee `README.md` (visión general) y `CONTENT.md` (texto completo de cada PDF).
2. Los scripts en `scripts/` regeneran cada PDF. Ajusta las rutas de salida (ahora
   apuntan a `/mnt/user-data/outputs/`) a tu carpeta local.
3. Para un cambio de texto, edita el script correspondiente o regénralo desde `CONTENT.md`.
