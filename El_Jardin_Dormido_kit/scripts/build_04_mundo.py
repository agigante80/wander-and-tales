from reportlab.lib.pagesizes import A4
from reportlab.lib.units import mm
from reportlab.lib.colors import HexColor, white
from reportlab.pdfgen import canvas
from reportlab.lib.styles import ParagraphStyle
from reportlab.platypus import Paragraph, Frame

W,H=A4
c=canvas.Canvas("/home/claude/mundo.pdf",pagesize=A4)
CREAM=HexColor("#fef9ef");GREEN=HexColor("#4ea24a");DARK=HexColor("#3a5a32")
TEAL=HexColor("#2bb3a3");PINK=HexColor("#d36fb0");BLUE=HexColor("#3f8fd6")
GOLD=HexColor("#f2a93b");PURP=HexColor("#8a6fd6")

body=ParagraphStyle("b",fontName="Helvetica",fontSize=9.4,leading=13,textColor=DARK)
ital=ParagraphStyle("i",fontName="Helvetica-Oblique",fontSize=9.6,leading=13.6,textColor=DARK)

def bg(title,sub):
    c.setFillColor(CREAM);c.rect(0,0,W,H,fill=1,stroke=0)
    c.setStrokeColor(HexColor("#9ccf8a"));c.setLineWidth(3);c.setDash(2,12)
    c.roundRect(8*mm,8*mm,W-16*mm,H-16*mm,10,fill=0,stroke=1);c.setDash()
    c.setFillColor(GREEN);c.roundRect(14*mm,H-30*mm,W-28*mm,16*mm,8,fill=1,stroke=0)
    c.setFillColor(white);c.setFont("Helvetica-Bold",18);c.drawCentredString(W/2,H-23*mm,title)
    c.setFont("Helvetica",9);c.drawCentredString(W/2,H-28.5*mm,sub)

def head(x,y,t,col):
    c.setFillColor(col);c.setFont("Helvetica-Bold",13);c.drawString(x,y,t)
def block(x,y,w,h,p):
    Frame(x,y,w,h,leftPadding=2,rightPadding=2,topPadding=2,bottomPadding=2,
          showBoundary=0).addFromList([p],c)

M=15*mm; CW=W-30*mm

# ---- PAGE 1: EL MUNDO ----
bg("El Mundo de El Jardin Dormido","La historia: donde estais y que esta pasando")

head(M,H-40*mm,"Un mundo donde la magia solo ayuda",GREEN)
block(M,H-66*mm,CW,24*mm,Paragraph(
 "Muy lejos, en lo alto de una colina verde, hay un reino tranquilo donde la magia nunca sirve "
 "para hacer dano: sirve para <b>crecer, curar, transformar y hablar</b> con las cosas. Aqui nadie "
 "pelea ni pierde; los problemas se resuelven con ingenio, paciencia y un poco de amabilidad. "
 "El corazon de este reino es un jardin enorme y magico: el <b>Gran Jardin</b>.",body))

head(M,H-74*mm,"Donde estais vosotros",TEAL)
block(M,H-100*mm,CW,24*mm,Paragraph(
 "Sois dos <b>pequenos magos aprendices</b> de la <b>Casa de los Pequenos Magos</b>, una casita "
 "junto a la entrada del Gran Jardin. Cada uno esta aprendiendo su propia magia (Luz, Crecer, "
 "Cambio o Voz) y, aunque todavia sois pequenos, ya teneis vuestra mochila, vuestra estrella de "
 "energia y muchas ganas de ayudar. Hoy os toca vuestra primera gran aventura.",body))

head(M,H-108*mm,"Que esta pasando",PINK)
block(M,H-138*mm,CW,28*mm,Paragraph(
 "Algo raro ha ocurrido: el Gran Jardin se ha quedado <b>dormido</b>. Las flores cerraron sus "
 "petalos, la fuente dejo de cantar y hasta los animalitos bostezan sin parar. Mientras el jardin "
 "duerma, todo el reino se queda gris y silencioso. Nadie sabe muy bien por que ha pasado... pero "
 "alguien tiene que ir a despertarlo con cuidado y carino.",body))

head(M,H-146*mm,"Vuestra mision",GOLD)
block(M,H-176*mm,CW,28*mm,Paragraph(
 "Cruzar el Gran Jardin desde la <b>Salida</b> hasta el <b>Corazon del Jardin</b>, resolviendo un "
 "pequeno puzle en cada parada (la puerta de enredaderas, el cantero de flores y la fuente "
 "parlanchina). Cada puzle que resolveis despierta un pedacito del jardin. Trabajais en equipo: "
 "cuando uno no llega, el otro ayuda, y juntos siempre encontrais una manera.",body))

head(M,H-184*mm,"La regla de este mundo",PURP)
block(M,H-206*mm,CW,20*mm,Paragraph(
 "Aqui <b>nadie muere y nadie pierde</b>. No hay malos de verdad, solo cosas que arreglar y amigos "
 "por conocer. Se gana siendo <b>listo y amable</b>: pensando, probando ideas y ayudandoos.",body))
c.showPage()

# ---- PAGE 2: LUGARES, HABITANTES, EL SECRETO ----
bg("El Mundo - Lugares y habitantes","Por donde pasareis y a quien conocereis")

head(M,H-40*mm,"Los lugares del Gran Jardin",TEAL)
block(M,H-92*mm,CW,50*mm,Paragraph(
 "&bull; <b>La Salida:</b> la puerta de la Casa de los Pequenos Magos, donde empieza el camino dorado.<br/>"
 "&bull; <b>La Puerta de Enredaderas:</b> un arco de hojas que se ha cerrado con un nudo verde.<br/>"
 "&bull; <b>El Cantero de Flores:</b> un parterre de flores de colores que hay que ordenar bien.<br/>"
 "&bull; <b>La Fuente Parlanchina:</b> una fuente que antes cantaba y ahora esta callada y triste.<br/>"
 "&bull; <b>El Corazon del Jardin:</b> el centro magico donde late la vida de todo el reino. Si "
 "despierta, despierta el jardin entero.",body))

head(M,H-100*mm,"Quien vive en el jardin",PINK)
block(M,H-140*mm,CW,38*mm,Paragraph(
 "El jardin esta lleno de criaturas amables: un <b>gato de niebla</b> que aparece y desaparece "
 "dando pistas, un <b>buho bibliotecario</b> que adora los acertijos, mariposas mensajeras, una "
 "<b>tortuga puente</b> y muchas flores que hablan bajito. Ninguna quiere haceros dano; algunas "
 "solo necesitan que las escucheis o que jugueis con ellas.",body))

head(M,H-148*mm,"El secreto del jardin (para el adulto)",GOLD)
block(M,H-188*mm,CW,38*mm,Paragraph(
 "Quien durmio el jardin no fue un villano, sino un <b>duendecillo solitario</b> que vive en el "
 "Corazon. Se sentia muy solo y penso que, si todo se dormia, alguien vendria a hacerle compania. "
 "Por eso, al final del camino no hay una batalla: hay un duende timido que solo queria un amigo. "
 "Cuando los ninos lo descubren y le ofrecen su amistad, el jardin se despierta de golpe, lleno de "
 "color, y todos celebran juntos. <b>Final feliz.</b>",body))

head(M,H-196*mm,"Para empezar (leelo en voz alta)",GREEN)
block(M,H-222*mm,CW,24*mm,Paragraph(
 "\"Esta manana os despertasteis y todo el reino estaba en silencio. Desde la ventana de la Casa de "
 "los Pequenos Magos vesteis el Gran Jardin quieto y grisaceo, como dormido. Cogeis vuestra mochila, "
 "os mirais el uno al otro y decis a la vez: -Vamos a despertarlo-. El camino dorado os espera...\"",ital))
c.showPage()
c.save()

import base64
b=open("/home/claude/mundo.pdf","rb").read()
open("/mnt/user-data/outputs/El_Mundo_y_la_Historia.pdf","wb").write(b)
enc=base64.b64encode(b).decode();assert base64.b64decode(enc)==b
open("/home/claude/mundo_b64.txt","w").write(enc)
print("bytes",len(b),"b64",len(enc))
