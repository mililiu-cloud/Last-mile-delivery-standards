# Renders region cards that mirror holiday-calendar.html (warehouse view) 1:1.
# Geometry/colors/fonts were read off the live page's computed styles.
import json, os
OUT=os.environ.get("HOLIDAY_OUT_DIR",os.getcwd())
from PIL import Image, ImageDraw, ImageFont

S = 2  # supersample scale
rows = json.load(open("parsed.json")); meta = json.load(open("meta.json"))
MON = ["","January","February","March","April","May","June","July","August","September","October","November","December"]
MLAB = "%s %d" % (MON[meta["month"]], meta["year"])
DOW = {"Monday":"Mon","Tuesday":"Tue","Wednesday":"Wed","Thursday":"Thu","Friday":"Fri","Saturday":"Sat","Sunday":"Sun"}

SANS="/usr/share/fonts/opentype/noto/NotoSansCJK-Regular.ttc"; SANS_B="/usr/share/fonts/opentype/noto/NotoSansCJK-Bold.ttc"
SERIF="/usr/share/fonts/opentype/noto/NotoSerifCJK-Regular.ttc"; SERIF_B="/usr/share/fonts/opentype/noto/NotoSerifCJK-Bold.ttc"
IDX=2  # SC face
_fc={}
def F(path,size):
    k=(path,size)
    if k not in _fc: _fc[k]=ImageFont.truetype(path,int(round(size*S)),index=IDX)
    return _fc[k]

BODY=(238,234,225); PAGE=(250,248,243); LINE=(228,225,216)
NAVY=(10,24,48); GOLD=(216,199,154)
HL_BG=(246,239,222); HL_BD=(228,211,166)
PILL_BG=(242,238,227); PILL_TX=(91,100,114)
HNAME=(138,106,38); HDATE=(59,66,80); HNOTE=(107,90,46); QUIET=(138,131,112); SRC=(91,100,114)

PW=760; SHELL_T=26; SHELL_B=30; SHELL_X=20; W=800
HDR_H=94.5; PAD_X=34; INNER=690
COL_W=223.33; GAP=10
CONTENT=COL_W-2*12-2*1  # text width inside a card

def note_for(dw, multi=False):
    if multi: return "Multi-day closure; pickup/delivery resumes after, allow +1-2 days from the last day"
    if dw in ("Saturday","Sunday"): return "Falls on a weekend; limited impact, but watch customs/pickup windows"
    if dw in ("Monday","Friday"):   return "Long weekend delay, transit time +1-2 days"
    return "Warehouse/carrier closure, transit time +1-2 days"

_m=ImageDraw.Draw(Image.new("RGB",(1,1)))
def tw(t,f): return _m.textlength(t,font=f)/S
def wrap(t,f,maxw):
    out=[];cur=""
    for w in t.split():
        c=(cur+" "+w).strip()
        if tw(c,f)<=maxw or not cur: cur=c
        else: out.append(cur); cur=w
    if cur: out.append(cur)
    return out

def card_lines(w):
    f=F(SANS,9.5)
    return [wrap(note_for(h["dow"], bool(h.get("date_end"))),f,CONTENT) for h in w["holidays"]]

def card_h(w,lines):
    y=29.5
    if w["holidays"]:
        for ls in lines: y += 6+1+6+13.5+1+12+2+12.825*len(ls)
    else:
        y += 6+14
    return y+11

def draw_card(d,x,y,h,item,lines):
    has=bool(item["holidays"])
    d.rounded_rectangle([x*S,y*S,(x+COL_W)*S,(y+h)*S],2*S,fill=HL_BG if has else (255,255,255),
                        outline=HL_BD if has else LINE,width=max(1,int(S)))
    fc=F(SERIF_B,14)
    d.text(((x+13)*S,(y+12.5)*S),item["wh"],font=fc,fill=NAVY,anchor="la")
    px=x+13+tw(item["wh"],fc)+6; fp=F(SANS_B,9.5)
    pw=tw(item["country"],fp)+12
    d.rounded_rectangle([px*S,(y+14)*S,(px+pw)*S,(y+29)*S],1*S,fill=PILL_BG)
    d.text(((px+6)*S,(y+21.5)*S),item["country"],font=fp,fill=PILL_TX,anchor="lm")
    cy=y+29.5
    if not has:
        d.text(((x+13)*S,(cy+6)*S),"No closures this month",font=F(SANS,10.5),fill=QUIET,anchor="la")
        return
    for h_,ls in zip(item["holidays"],lines):
        cy+=6
        for dx in range(0,int(CONTENT),6):  # dashed rule
            d.line([(x+13+dx)*S,cy*S,(x+13+min(dx+3,CONTENT))*S,cy*S],fill=HL_BD,width=max(1,int(S)))
        cy+=7
        d.text(((x+13)*S,cy*S),h_.get("name_en",h_["name"]),font=F(SANS_B,11.5),fill=HNAME,anchor="la"); cy+=14.5
        p=h_["date"].split("/")
        if h_.get("date_end"):
            p2=h_["date_end"].split("/")
            dtxt="%s %s-%s (%s-%s)"%(MON[int(p[1])][:3],int(p[2]),int(p2[2]),
                                     DOW.get(h_["dow"],h_["dow"]),DOW.get(h_["dow_end"],h_["dow_end"]))
        else:
            dtxt="%s %s (%s)"%(MON[int(p[1])][:3],int(p[2]),DOW.get(h_["dow"],h_["dow"]))
        d.text(((x+13)*S,cy*S),dtxt,font=F(SANS,10.5),fill=HDATE,anchor="la"); cy+=14
        for ln in ls:
            d.text(((x+13)*S,cy*S),ln,font=F(SANS,9.5),fill=HNOTE,anchor="la"); cy+=12.825

def render(region,whs,path):
    lines=[card_lines(w) for w in whs]
    nat=[card_h(w,l) for w,l in zip(whs,lines)]
    rowsz=[]
    for i in range(0,len(whs),3):
        rowsz.append(max(nat[i:i+3]))
    grid_h=sum(rowsz)+GAP*(len(rowsz)-1)
    grid_y=179.5
    src_y=grid_y+grid_h+16
    page_h=src_y+14.5+6+1
    H=SHELL_T+page_h+SHELL_B
    img=Image.new("RGB",(int(W*S),int(round(H*S))),BODY); d=ImageDraw.Draw(img)
    px0,py0=SHELL_X,SHELL_T
    d.rounded_rectangle([px0*S,py0*S,(px0+PW)*S,(py0+page_h)*S],2*S,fill=PAGE,outline=LINE,width=max(1,int(S)))
    # header gradient 135deg
    hx0,hy0,hx1,hy1=(px0+1),(py0+1),(px0+PW-1),(py0+1+HDR_H)
    gw,gh=int((hx1-hx0)*S),int((hy1-hy0)*S)
    g=Image.new("RGB",(gw,gh)); gd=ImageDraw.Draw(g)
    stops=[(0.0,(10,24,48)),(0.62,(16,35,63)),(1.0,(20,42,78))]
    for i in range(gw+gh):
        t=i/(gw+gh-1)
        for j in range(len(stops)-1):
            if stops[j][0]<=t<=stops[j+1][0]:
                f0,c0=stops[j]; f1,c1=stops[j+1]; k=(t-f0)/(f1-f0)
                col=tuple(int(c0[n]+(c1[n]-c0[n])*k) for n in range(3)); break
        gd.line([(i,0),(0,i)],fill=col)
    img.paste(g,(int(hx0*S),int(hy0*S)))
    X=px0+1+PAD_X
    # kicker with 3px letter-spacing
    fk=F(SANS_B,10.5); cx=X
    for ch in "PLAUD LOGISTICS · GLOBAL OPS":
        d.text((cx*S,(py0+29)*S),ch,font=fk,fill=GOLD,anchor="lm"); cx+=tw(ch,fk)+3
    d.text((X*S,(py0+57)*S),"Overseas Warehouse Holiday Calendar",font=F(SERIF,25),fill=(255,255,255),anchor="lm")
    d.text((X*S,(py0+121)*S),MLAB,font=F(SERIF_B,13),fill=NAVY,anchor="lm")
    fr=F(SANS_B,12); cx=X
    for ch in region.upper():
        d.text((cx*S,(py0+152)*S),ch,font=fr,fill=NAVY,anchor="lm"); cx+=tw(ch,fr)+1
    d.line([X*S,(py0+169)*S,(X+INNER)*S,(py0+169)*S],fill=GOLD,width=max(1,int(S)))
    for i,(w,l,nh) in enumerate(zip(whs,lines,nat)):
        r,c=divmod(i,3)
        x=X+c*(COL_W+GAP); y=py0+grid_y+sum(rowsz[:r])+GAP*r
        draw_card(d,x,y,rowsz[r],w,l)
    d.text((X*S,(py0+src_y+7)*S),
           'Source: Feishu "Holiday Schedule - Overseas Warehouses" sheet (filed by warehouse operators incl. 万邑通/谷仓) · Auto-synced %s'%meta["today"],
           font=F(SANS,10.5),fill=SRC,anchor="lm")
    img.save(path); print("saved",path,img.size)

out={}
for rn in ["Americas","EMEA","APAC"]:
    whs=[w for w in rows if w["region"]==rn]
    if any(w["holidays"] for w in whs):
        p=os.path.join(OUT,"holiday_%s.png"%rn.lower()); render(rn,whs,p); out[rn]=p
    else: print("skip",rn,"(no closures)")
json.dump(out,open(os.path.join(OUT,"images.json"),"w"))
