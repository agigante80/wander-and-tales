from reportlab.lib.pagesizes import A4
from reportlab.lib.units import mm
from reportlab.lib.colors import HexColor, white
from reportlab.pdfgen import canvas
from reportlab.lib.styles import ParagraphStyle
from reportlab.platypus import Paragraph, Frame

W,H=A4
c=canvas.Canvas("/home/claude/banco1.pdf",pagesize=A4)
CREAM=HexColor("#fef9ef");GREEN=HexColor("#4ea24a");DARK=HexColor("#3a5a32")
c.setFillColor(CREAM);c.rect(0,0,W,H,fill=1,stroke=0)
c.setFillColor(GREEN);c.rect(0,H-24*mm,W,24*mm,fill=1,stroke=0)
c.setFillColor(white);c.setFont("Helvetica-Bold",17)
c.drawString(15*mm,H-15*mm,"Banco de Ideas - El Jardin Dormido")
c.setFont("Helvetica",9);c.drawString(15*mm,H-21*mm,"Poderes, objetos y mas (elige o invéntate los tuyos)")
st=ParagraphStyle("s",fontName="Helvetica",fontSize=8.3,leading=10.6,textColor=DARK)
def P(h):return Paragraph(h,st)
html=(
"<b>PODERES - LUZ:</b> ojo de luciernaga (ilumina pistas), mirada de sol (lee mensajes secretos), "
"destello amable (calma criaturas), brujula brillante, cortina de luz, faro guia, arcoiris puente.<br/>"
"<b>PODERES - CRECER:</b> mano jardinera (planta-puente), salto de hiedra, escudo de hojas (nadie se hace dano), "
"semilla veloz, trampolin de musgo, flor paraguas (refugio), raices amigas.<br/>"
"<b>PODERES - CAMBIO:</b> toque transformador (piedra en llave), mini-maxi (agranda/encoge), color camaleon, "
"truco del agua (hielo/niebla), llave comodin, puente de piedras, eco de espejo.<br/>"
"<b>PODERES - VOZ:</b> charla animal, susurro de objetos (pregunta que necesitan), cancion calmante, "
"eco buscador, orden amistosa, cuentachistes (abre puertas grunonas), llamada de amigos.<br/><br/>"
"<b>OBJETOS por magia:</b> <b>Luz:</b> linterna de estrellas, lupa arcoiris, gafas de noche, vela eterna. "
"<b>Crecer:</b> semilla saltarina, regadera infinita, guantes gigantes, maceta de bolsillo. "
"<b>Cambio:</b> varita de tiza, guante cambiacolor, dado transformador, cubo de hielo magico. "
"<b>Voz:</b> caracola parlante, silbato de animales, megafono de hojas, cuaderno que escucha.<br/>"
"<b>OBJETOS para cualquiera:</b> capa de la valentia, brujula de la amistad, frasco de purpurina, "
"mapa que se dibuja solo, llave maestra de juguete, campanita de pistas, espejo de bolsillo, "
"cuaderno de secretos, bolsa sin fondo, piedra de la suerte.<br/>"
"<i>Recarga:</i> cada objeto se usa una vez por aventura; se recarga ayudando o resolviendo un puzle.<br/><br/>"
"<b>CRIATURAS amistosas:</b> duende solitario (solo quiere un amigo), gato de niebla (da pistas), "
"buho bibliotecario (acertijos), tortuga puente, hada de las pistas, raton mensajero.<br/>"
"<b>LUGARES magicos:</b> cueva de los ecos, puente de setas, lago espejo, columpio de nubes, "
"biblioteca de hojas, claro de las luciernagas.<br/>"
"<b>MINI-RETOS:</b> seguir el rastro de petalos, encontrar la pareja de piedras, ordenar sonidos, "
"adivinanza del guardian, laberinto de flores, memoria de estrellas.<br/>"
"<b>RECOMPENSAS felices:</b> pegatina de estrella, un baile, un abrazo y un gracias, una pista, "
"una semilla nueva, recuperar todas las estrellas.")
Frame(14*mm,12*mm,W-28*mm,H-40*mm,leftPadding=6,rightPadding=6,topPadding=4,
      bottomPadding=4,showBoundary=0).addFromList([P(html)],c)
c.save()
import base64
b=open("/home/claude/banco1.pdf","rb").read()
open("/mnt/user-data/outputs/Banco_de_Ideas.pdf","wb").write(b)
enc=base64.b64encode(b).decode();assert base64.b64decode(enc)==b
open("/home/claude/banco1_b64.txt","w").write(enc)
print("bytes",len(b),"b64",len(enc))
