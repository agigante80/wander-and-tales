from reportlab.lib.pagesizes import A4, landscape
from reportlab.lib.units import mm
from reportlab.lib.colors import HexColor, white
from reportlab.pdfgen import canvas
from reportlab.lib.styles import ParagraphStyle
from reportlab.platypus import Paragraph, Frame

W, H = landscape(A4)
c = canvas.Canvas("/home/claude/kit_small.pdf", pagesize=landscape(A4))

CREAM=HexColor("#fef9ef"); SKY=HexColor("#eaf7e1"); GREEN=HexColor("#4ea24a")
DARK=HexColor("#3a5a32"); TEAL=HexColor("#2bb3a3"); PINK=HexColor("#d36fb0")
BLUE=HexColor("#3f8fd6"); GOLD=HexColor("#f2a93b"); PATH=HexColor("#e9d8a6")
LEAF=HexColor("#6fbf73"); LEAF2=HexColor("#5fb463"); BROWN=HexColor("#9c6b3f")
SUN=HexColor("#ffd95e")

# ================= PAGE 1 : MAP =================
c.setFillColor(SKY); c.rect(0,0,W,H,fill=1,stroke=0)
c.setStrokeColor(HexColor("#9ccf8a")); c.setLineWidth(4); c.setDash(2,12)
c.roundRect(8*mm,8*mm,W-16*mm,H-16*mm,10,fill=0,stroke=1); c.setDash()

# sun
c.setFillColor(SUN); c.circle(32*mm,170*mm,14*mm,fill=1,stroke=0)
c.setStrokeColor(SUN); c.setLineWidth(3)
import math
for a in range(0,360,45):
    x=32*mm+math.cos(math.radians(a))*20*mm; y=170*mm+math.sin(math.radians(a))*20*mm
    x2=32*mm+math.cos(math.radians(a))*25*mm; y2=170*mm+math.sin(math.radians(a))*25*mm
    c.line(x,y,x2,y2)

# winding path (in mm, y from bottom)
pts=[(40,40),(95,55),(120,95),(165,120),(205,150),(250,185)]
c.setStrokeColor(PATH); c.setLineWidth(46); c.setLineCap(1)
p=c.beginPath(); p.moveTo(pts[0][0]*mm,pts[0][1]*mm)
for (x,y) in pts[1:]: p.lineTo(x*mm,y*mm)
c.drawPath(p,stroke=1,fill=0)

def tree(x,y,s=1):
    c.setFillColor(BROWN); c.rect((x-2)*mm,(y-8)*mm,4*mm,10*mm,fill=1,stroke=0)
    c.setFillColor(LEAF); c.circle(x*mm,(y+3)*mm,9*s*mm,fill=1,stroke=0)
    c.setFillColor(LEAF2); c.circle((x-6)*mm,y*mm,6*s*mm,fill=1,stroke=0)
    c.setFillColor(LEAF2); c.circle((x+6)*mm,y*mm,6*s*mm,fill=1,stroke=0)
tree(70,120); tree(185,70); tree(245,140,0.8)

def flower(x,y,col):
    c.setFillColor(col); c.circle(x*mm,y*mm,2.4*mm,fill=1,stroke=0)
    c.setFillColor(HexColor("#fff3b0")); c.circle(x*mm,y*mm,1.1*mm,fill=1,stroke=0)
for (x,y,col) in [(130,55,PINK),(150,40,HexColor("#b18cff")),(225,105,PINK),
                  (45,110,BLUE),(255,150,PINK)]:
    flower(x,y,col)

# title banner
c.setFillColor(GREEN); c.roundRect(80*mm,182*mm,135*mm,18*mm,8,fill=1,stroke=0)
c.setFillColor(white); c.setFont("Helvetica-Bold",24)
c.drawCentredString(147*mm,191*mm,"El Jardin Dormido")
c.setFont("Helvetica",11); c.drawCentredString(147*mm,184.5*mm,"Un mapa de aventura magica")

def node(x,y,label1,label2,ring,fill,num=None,heart=False):
    c.setStrokeColor(ring); c.setLineWidth(5); c.setFillColor(white)
    c.circle(x*mm,y*mm,13*mm,fill=1,stroke=1)
    if num:
        c.setFillColor(fill); c.circle(x*mm,(y+3)*mm,6*mm,fill=1,stroke=0)
        c.setFillColor(white); c.setFont("Helvetica-Bold",15)
        c.drawCentredString(x*mm,(y+0.6)*mm,num)
    if heart:
        c.setFillColor(GOLD)
        hp=c.beginPath(); cx=x*mm; cy=(y+3)*mm
        hp.moveTo(cx,cy-5*mm)
        hp.curveTo(cx-7*mm,cy+3*mm,cx-3*mm,cy+7*mm,cx,cy+3*mm)
        hp.curveTo(cx+3*mm,cy+7*mm,cx+7*mm,cy+3*mm,cx,cy-5*mm)
        c.drawPath(hp,fill=1,stroke=0)
    c.setFillColor(ring); c.setFont("Helvetica-Bold",9)
    c.drawCentredString(x*mm,(y-20)*mm,label1)
    if label2: c.drawCentredString(x*mm,(y-24)*mm,label2)

node(40,40,"SALIDA","Empezais aqui",GREEN,GREEN,num=None)
c.setFillColor(GREEN); c.setFont("Helvetica-Bold",11); c.drawCentredString(40*mm,40.5*mm,"GO")
node(120,95,"Puerta de","Enredaderas",TEAL,TEAL,num="1")
node(165,120,"Cantero de","Flores",PINK,PINK,num="2")
node(205,150,"Fuente","Parlanchina",BLUE,BLUE,num="3")
node(250,185,"Corazon del","Jardin (META)",GOLD,GOLD,heart=True)

# legend (bottom-right, clear area)
lx=200*mm
c.setFillColor(white); c.roundRect(lx,12*mm,85*mm,42*mm,8,fill=1,stroke=0)
c.setFillColor(GREEN); c.setFont("Helvetica-Bold",11)
c.drawString(lx+4*mm,46*mm,"Como usar el mapa")
c.setFillColor(DARK); c.setFont("Helvetica",8.5)
c.drawString(lx+4*mm,38*mm,"Pon una figura Lego en cada circulo blanco")
c.drawString(lx+4*mm,33*mm,"(sois vosotros). El camino dorado os lleva")
c.drawString(lx+4*mm,28*mm,"del 1 al 4 resolviendo cada puzle.")
c.drawString(lx+4*mm,21*mm,"Construye los objetos (llave, flor...) con Lego.")
c.showPage()

# ================= PAGE 2 : RULES =================
c.setFillColor(CREAM); c.rect(0,0,W,H,fill=1,stroke=0)
c.setFillColor(GREEN); c.roundRect(15*mm,H-30*mm,W-30*mm,18*mm,8,fill=1,stroke=0)
c.setFillColor(white); c.setFont("Helvetica-Bold",19)
c.drawCentredString(W/2,H-22*mm,"El Jardin Dormido  -  Guia para el adulto (2 jugadores)")

def heading(x,y,t,col):
    c.setFillColor(col); c.setFont("Helvetica-Bold",13); c.drawString(x,y,t)
st=ParagraphStyle("s",fontName="Helvetica",fontSize=9.3,leading=12.6,textColor=DARK)
def block(x,y,w,h,html):
    Frame(x,y,w,h,leftPadding=4,rightPadding=4,topPadding=2,bottomPadding=2,
          showBoundary=0).addFromList([Paragraph(html,st)],c)

colW=(W-30*mm-10*mm)/2; Lx=15*mm; Rx=15*mm+colW+10*mm

heading(Lx,170*mm,"Preparar la partida",GREEN)
block(Lx,92*mm,colW,74*mm,
 "Imprimid el mapa de la otra pagina. Cada jugador coloca una <b>figura de Lego</b> "
 "en el circulo <b>SALIDA</b>.<br/>Con Lego construid los objetos que aparezcan "
 "(una llave, una flor, la fuente...).<br/><br/>"
 "Cada jugador elige una <b>magia</b> distinta (asi os complementais):<br/>"
 "&bull; <b>Luz</b>: revela lo escondido y lee mensajes secretos.<br/>"
 "&bull; <b>Crecer</b>: hace crecer plantas, puentes y caminos.<br/>"
 "&bull; <b>Cambio</b>: convierte un objeto en otro (piedra en llave).<br/>"
 "&bull; <b>Voz</b>: habla con animales y objetos para pedir pistas.<br/><br/>"
 "Cada jugador empieza con <b>5 estrellas de energia</b> (usad 5 piezas de Lego).")

heading(Lx,84*mm,"Vuestros dados",GREEN)
block(Lx,13*mm,colW,67*mm,
 "<b>Dado de 20 (d20) = Dado Magico.</b> El principal. Para superar un reto, tiralo "
 "e intenta <b>igualar o pasar el Numero Magico</b>:<br/>"
 "&bull; Facil = 6+ &nbsp;&bull; Normal = 10+ &nbsp;&bull; Dificil = 14+<br/><br/>"
 "<b>Dado de 12 (d12) = Dado de Ayuda.</b> Cuando un jugador ayuda al otro, tira el "
 "d12: con <b>7 o mas</b> el reto se supera aunque el d20 se quede corto.<br/><br/>"
 "<b>Dado de 10 (d10) = Dado Sorpresa.</b> Al llegar a cada parada, tiralo y mira la "
 "tabla de la derecha para una sorpresa.")

heading(Rx,170*mm,"Regla de oro: aqui nadie pierde",GOLD)
block(Rx,140*mm,colW,26*mm,
 "Si una tirada falla, podeis: (a) gastar <b>1 estrella</b> para repetir, o "
 "(b) <b>combinar las dos magias</b> una vez por parada para superar el reto sin "
 "tirar. Las estrellas se recuperan al pasar de parada o al ayudar.")

heading(Rx,134*mm,"Los 3 puzles (solucion para el adulto)",BLUE)
block(Rx,76*mm,colW,56*mm,
 "<b>1. Puerta de Enredaderas.</b> Cerrada con un nudo de hojas. Reto facil. "
 "<i>Solucion:</i> Crecer o Cambio para abrir un hueco, o Voz para pedirle a la "
 "planta que se aparte.<br/><br/>"
 "<b>2. Cantero de Flores.</b> Ordenar 4 flores por color con una rima. Di: "
 "<i>'Primero el sol, luego el mar, despues la fresa y a volar'</i> &rarr; "
 "<b>amarillo, azul, rojo, blanco</b>. Construid 4 flores Lego y que las ordene.<br/><br/>"
 "<b>3. Fuente Parlanchina.</b> Esta triste y no fluye. Reto normal. Pista: pregunta "
 "que necesita (Voz). Quiere que le canten o le cuenten un chiste; entonces brota agua.")

heading(Rx,70*mm,"Tabla del Dado Sorpresa (d10)",PINK)
block(Rx,13*mm,colW,54*mm,
 "<b>1</b> Una mariposa os da una pista gratis.<br/>"
 "<b>2</b> Recuperais 1 estrella de energia.<br/>"
 "<b>3</b> Aparece un gatito que ronronea (todo va bien).<br/>"
 "<b>4</b> Viento magico: el proximo reto es Facil.<br/>"
 "<b>5</b> Encontrais una semilla brillante (guardadla).<br/>"
 "<b>6</b> Un duendecillo hace una pregunta tonta y reis.<br/>"
 "<b>7</b> Llueve purpurina: os dais los cinco.<br/>"
 "<b>8</b> Un caracol sabio os deja repetir una tirada.<br/>"
 "<b>9</b> Brilla una luz: elegid vosotros la sorpresa.<br/>"
 "<b>10</b> Suena una cancion y todos bailan un turno.")

c.setFillColor(GOLD); c.setFont("Helvetica-Bold",11)
c.drawCentredString(W/2,10*mm,
 "FINAL: en el Corazon del Jardin (4) descubris que el 'malo' era un duende solo que "
 "queria un amigo. El jardin despierta. Fin feliz!")
c.showPage()
c.save()

import base64, os
b=open("/home/claude/kit_small.pdf","rb").read()
open("/mnt/user-data/outputs/El_Jardin_Dormido.pdf","wb").write(b)
enc=base64.b64encode(b).decode()
assert base64.b64decode(enc)==b
print("bytes",len(b),"b64len",len(enc))
open("/home/claude/b64.txt","w").write(enc)
