"""Fusiona los 4 PDFs del kit en un solo 'El_Jardin_Dormido_KIT.pdf'.
Ejecutar después de generar los PDFs individuales. Ajusta IN_DIR/OUT a tu ruta local."""
from pypdf import PdfReader, PdfWriter
IN_DIR = "../pdfs"
OUT = "El_Jardin_Dormido_KIT.pdf"
order = [
    "01_mapa_y_reglas.pdf",
    "04_el_mundo_y_la_historia.pdf",
    "02_fichas_de_personaje.pdf",
    "03_banco_de_ideas.pdf",
]
w = PdfWriter()
for f in order:
    for p in PdfReader(f"{IN_DIR}/{f}").pages:
        w.add_page(p)
with open(OUT, "wb") as fh:
    w.write(fh)
print("written", OUT)
