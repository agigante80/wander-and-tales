from reportlab.lib.pagesizes import A4
from reportlab.lib.units import mm
from reportlab.lib.colors import HexColor, white
from reportlab.pdfgen import canvas
import math

W, H = A4  # portrait
c = canvas.Canvas("/home/claude/fichas.pdf", pagesize=A4)

CREAM=HexColor("#fef9ef"); SKY=HexColor("#eaf7e1"); GREEN=HexColor("#4ea24a")
DARK=HexColor("#3a5a32"); TEAL=HexColor("#2bb3a3"); PINK=HexColor("#d36fb0")
BLUE=HexColor("#3f8fd6"); GOLD=HexColor("#f2a93b"); SUN=HexColor("#ffd95e")
PURP=HexColor("#b18cff"); LEAF=HexColor("#6fbf73"); BROWN=HexColor("#9c6b3f")

def star(cx, cy, r, fill, stroke):
    pts=[]
    for i in range(10):
        ang=math.radians(-90+i*36)
        rad=r if i%2==0 else r*0.45
        pts.append((cx+rad*math.cos(ang), cy+rad*math.sin(ang)))
    p=c.beginPath(); p.moveTo(*pts[0])
    for pt in pts[1:]: p.lineTo(*pt)
    p.close()
    c.setFillColor(fill); c.setStrokeColor(stroke); c.setLineWidth(1.5)
    c.drawPath(p, fill=1, stroke=1)

def ficha(player_label, accent):
    # background
    c.setFillColor(CREAM); c.rect(0,0,W,H,fill=1,stroke=0)
    c.setStrokeColor(HexColor("#9ccf8a")); c.setLineWidth(4); c.setDash(2,12)
    c.roundRect(8*mm,8*mm,W-16*mm,H-16*mm,10,fill=0,stroke=1); c.setDash()

    # little sun top-right + flowers
    c.setFillColor(SUN); c.circle(W-30*mm, H-30*mm, 9*mm, fill=1, stroke=0)
    c.setStrokeColor(SUN); c.setLineWidth(2.5)
    for a in range(0,360,45):
        x1=W-30*mm+math.cos(math.radians(a))*13*mm; y1=H-30*mm+math.sin(math.radians(a))*13*mm
        x2=W-30*mm+math.cos(math.radians(a))*16*mm; y2=H-30*mm+math.sin(math.radians(a))*16*mm
        c.line(x1,y1,x2,y2)

    # title banner
    c.setFillColor(accent); c.roundRect(18*mm, H-38*mm, W-36*mm, 18*mm, 8, fill=1, stroke=0)
    c.setFillColor(white); c.setFont("Helvetica-Bold", 22)
    c.drawCentredString(W/2, H-30*mm, "Mi Ficha de Mago/a")
    c.setFont("Helvetica", 10)
    c.drawCentredString(W/2, H-36*mm, player_label)

    y = H-52*mm
    # NAME
    c.setFillColor(DARK); c.setFont("Helvetica-Bold", 13)
    c.drawString(20*mm, y, "Mi nombre de mago/a:")
    c.setStrokeColor(accent); c.setLineWidth(1.5)
    c.line(75*mm, y-1*mm, W-20*mm, y-1*mm)

    # MAGIC SCHOOL
    y -= 14*mm
    c.setFillColor(accent); c.setFont("Helvetica-Bold", 13)
    c.drawString(20*mm, y, "Mi magia (marca una):")
    schools=[("Luz","revela lo escondido",GOLD),
             ("Crecer","plantas, puentes, caminos",GREEN),
             ("Cambio","convierte un objeto en otro",PURP),
             ("Voz","habla con animales y objetos",BLUE)]
    y -= 9*mm
    for i,(name,desc,col) in enumerate(schools):
        yy = y - i*9*mm
        c.setStrokeColor(col); c.setLineWidth(2); c.setFillColor(white)
        c.circle(24*mm, yy, 3*mm, fill=1, stroke=1)
        c.setFillColor(col); c.setFont("Helvetica-Bold", 11)
        c.drawString(30*mm, yy-1.2*mm, name)
        c.setFillColor(DARK); c.setFont("Helvetica", 10)
        c.drawString(52*mm, yy-1.2*mm, "- "+desc)

    # ENERGY STARS
    y -= 4*9*mm + 8*mm
    c.setFillColor(accent); c.setFont("Helvetica-Bold", 13)
    c.drawString(20*mm, y, "Mi energia magica (colorea al gastar):")
    y -= 12*mm
    for i in range(5):
        star(28*mm + i*22*mm, y, 8*mm, white, accent)

    # DRAW LEGO FIGURE
    y -= 20*mm
    c.setFillColor(accent); c.setFont("Helvetica-Bold", 13)
    c.drawString(20*mm, y, "Dibuja tu figura de Lego:")
    c.setStrokeColor(accent); c.setLineWidth(1.5); c.setDash(4,4)
    c.roundRect(20*mm, y-48*mm, 80*mm, 44*mm, 8, fill=0, stroke=1); c.setDash()

    # SPECIAL POWER + box on the right of the drawing box
    c.setFillColor(accent); c.setFont("Helvetica-Bold", 13)
    c.drawString(108*mm, y, "Mi poder especial:")
    c.setFillColor(DARK); c.setFont("Helvetica", 9)
    c.drawString(108*mm, y-6*mm, "(invéntalo: p.ej. 'hablo con las")
    c.drawString(108*mm, y-11*mm, "mariposas' o 'hago crecer puentes')")
    c.setStrokeColor(accent); c.setLineWidth(1.2)
    for k in range(3):
        c.line(108*mm, y-18*mm-k*9*mm, W-20*mm, y-18*mm-k*9*mm)

    # FRIENDS / NOTES
    yb = y-48*mm
    c.setFillColor(accent); c.setFont("Helvetica-Bold", 13)
    c.drawString(20*mm, yb-8*mm, "Cosas magicas que llevo (mochila):")
    c.setStrokeColor(accent); c.setLineWidth(1.2)
    for k in range(3):
        c.line(20*mm, yb-16*mm-k*9*mm, W-20*mm, yb-16*mm-k*9*mm)

    # footer flowers
    for i,(col) in enumerate([PINK,GOLD,BLUE,PURP,PINK,GREEN]):
        fx=25*mm+i*32*mm
        c.setFillColor(col); c.circle(fx, 18*mm, 2.6*mm, fill=1, stroke=0)
        c.setFillColor(HexColor("#fff3b0")); c.circle(fx, 18*mm, 1.2*mm, fill=1, stroke=0)
    c.setFillColor(DARK); c.setFont("Helvetica-Oblique", 9)
    c.drawCentredString(W/2, 12*mm, "El Jardin Dormido  -  recuerda: aqui nadie pierde, solo se busca otra ruta")
    c.showPage()

ficha("Jugador 1  (el adulto)", TEAL)
ficha("Jugador 2  (tu hijo)", PINK)
c.save()

import base64
b=open("/home/claude/fichas.pdf","rb").read()
open("/mnt/user-data/outputs/Fichas_de_Personaje.pdf","wb").write(b)
enc=base64.b64encode(b).decode(); assert base64.b64decode(enc)==b
open("/home/claude/fichas_b64.txt","w").write(enc)
print("bytes",len(b),"b64",len(enc))
