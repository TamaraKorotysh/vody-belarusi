import json, math, numpy as np
K=16; CX,CY=28.0,53.7; KX=math.cos(math.radians(53.7))
def P(lon,lat): return ((lon-CX)*KX*K,(CY-lat)*K)
def inv(x,z): return (x/(KX*K)+CX, CY-z/K)
big=np.load("dem/big.npy"); zt,x0,y0=map(int,open("dem/meta.txt").read().split())
def dem(lon,lat):
    px=((lon+180)/360*2**zt-x0)*256; r=np.radians(lat)
    py=((1-np.log(np.tan(r)+1/np.cos(r))/np.pi)/2*2**zt-y0)*256
    ix=np.clip(px.astype(int),0,big.shape[1]-2); iy=np.clip(py.astype(int),0,big.shape[0]-2)
    fx=px-ix; fy=py-iy
    return (big[iy,ix]*(1-fx)*(1-fy)+big[iy,ix+1]*fx*(1-fy)+big[iy+1,ix]*(1-fx)*fy+big[iy+1,ix+1]*fx*fy)
G=json.load(open("geo_ll.json",encoding="utf8"))
border=[P(*p) for p in G["border"]]
bx=np.array([p[0] for p in border]); bz=np.array([p[1] for p in border])
xmin,xmax,zmin,zmax=bx.min()-1,bx.max()+1,bz.min()-1,bz.max()+1
STEP=0.2
nx=int((xmax-xmin)/STEP)+1; nz=int((zmax-zmin)/STEP)+1
gx,gz=np.meshgrid(xmin+np.arange(nx)*STEP, zmin+np.arange(nz)*STEP)
lon,lat=inv(gx,gz)
# average a few samples per cell for smoothness
h=np.zeros_like(gx)
for dx in (-.07,0,.07):
    for dz in (-.07,0,.07):
        l2,a2=inv(gx+dx,gz+dz); h+=dem(l2,a2)
h/=9
# light blur
for _ in range(1):
    hp=np.pad(h,1,mode="edge"); h=(hp[1:-1,1:-1]*4+hp[:-2,1:-1]+hp[2:,1:-1]+hp[1:-1,:-2]+hp[1:-1,2:])/8
print("grid",nx,nz,h.min(),h.max())
def inside(xs,zs):
    xs=np.asarray(xs); zs=np.asarray(zs); c=np.zeros(xs.shape,bool)
    x1,z1=bx,bz; x2,z2=np.roll(bx,-1),np.roll(bz,-1)
    for i in range(len(bx)):
        cond=((z1[i]>zs)!=(z2[i]>zs)) & (xs < (x2[i]-x1[i])*(zs-z1[i])/((z2[i]-z1[i]) or 1e-12)+x1[i])
        c^=cond
    return c
W={"Днепр":1.25,"Припять":1.1,"Западная Двина":1.1,"Неман":1.1,"Березина":.95,"Сож":.95,"Западный Буг":.85,"Вилия":.85,"Птичь":.65,"Свислочь":.6}
from collections import defaultdict
W=defaultdict(lambda:.3,W);W.update({k:.42 for k in ["Ясельда","Мухавец","Случь","Лань","Уборть","Друть","Ипуть","Беседь","Проня","Ведрич","Дисна","Улла","Лучоса","Нарев","Лесная","Зельвянка","Котра","Оресса","Гайна","Щара","Горынь"] if k not in W});W.update({"Щара":.65,"Горынь":.7,"Стырь":.6,"Друть":.6,"Ипуть":.6,"Ясельда":.55,"Случь":.5,"Беседь":.55,"Уборть":.55,"Мухавец":.5,"Нарев":.5,"Зельвянка":.48,"Котра":.45})
rivers={}; lakes={}
for f in G["water"]["features"]:
    n=f["properties"]["name"]
    if f["properties"]["kind"]=="river":
        segs=[]
        for line in f["geometry"]["coordinates"]:
            pts=np.array([P(*p) for p in line]); ins=inside(pts[:,0],pts[:,1])
            dd=np.sqrt(((pts[:,None,0]-bx[None,:])**2+(pts[:,None,1]-bz[None,:])**2).min(axis=1)); ins=ins|(dd<0.9)
            cur=[]
            for p,i in zip(pts,ins):
                if i: cur.append(p)
                else:
                    if len(cur)>1: segs.append(np.array(cur))
                    cur=[]
            if len(cur)>1: segs.append(np.array(cur))
        def dens(a):
            out=[a[0]]
            for p in a[1:]:
                q=out[-1]; L=np.hypot(*(p-q)); k=int(L/0.45)
                for j in range(1,k+1): out.append(q+(p-q)*j/(k+1))
                out.append(p)
            return np.array(out)
        segs=[dens(s) for s in segs]
        lens=[np.r_[0,np.cumsum(np.hypot(*np.diff(s,axis=0).T))] for s in segs]
        segs=[(s,l) for s,l in zip(segs,lens) if l[-1]>1.5]
        segs.sort(key=lambda t:-t[1][-1])
        if not segs: print('skip',n); continue
        main,ml=segs[0]; out=[]
        # chain main pieces: order main-ish segments by their start along flow is unknown; use nearest point on longest
        for s,l in segs:
            if s is main: off=0
            else:
                d=np.hypot(main[:,0]-s[0,0],main[:,1]-s[0,1]); j=d.argmin(); off=ml[j]
            out.append([[round(float(x),2),round(float(z),2),round(float(off+dd),2)] for (x,z),dd in zip(s,l)])
        D=max(p[2] for o in out for p in o)
        rivers[n]={"w":W[n],"D":round(D,2),"lines":out}
        print(n,len(out),round(D,1),sum(len(o) for o in out))
    else:
        polys=[]
        for poly in f["geometry"]["coordinates"]:
            polys.append([[[round(a,2) for a in P(*p)] for p in ring] for ring in poly])
        lakes[n]=polys
cities=[["Минск",27.5618,53.9025,1],["Гомель",31.0132,52.4239,1],["Витебск",30.207,55.193,1],["Гродно",23.8343,53.6835,1],["Могилёв",30.343,53.909,1],["Брест",23.6852,52.0938,1],["Бобруйск",29.2281,53.145,2],["Барановичи",26.0184,53.1323,2],["Борисов",28.5118,54.2241,2],["Пинск",26.1025,52.1114,2],["Солигорск",27.542,52.7841,2],["Орша",30.4294,54.5108,2],["Мозырь",29.2676,52.0495,2],["Лида",25.3023,53.8916,2],["Новополоцк",28.6452,55.5349,2],["Молодечно",26.8389,54.3073,2],["Полоцк",28.7682,55.4855,2],["Жлобин",30.0368,52.8909,2],["Жодино",28.3224,54.0963,2],["Речица",30.386,52.3718,2],["Слуцк",27.552,53.0277,2],["Светлогорск",29.7484,52.633,2],["Кобрин",24.3543,52.2086,3],["Слоним",25.3193,53.0927,3],["Волковыск",24.4582,53.1647,3],["Сморгонь",26.4013,54.4818,3],["Калинковичи",29.3314,52.1286,3],["Горки",30.9811,54.2895,3],["Рогачёв",30.0532,53.082,3],["Новогрудок",25.8216,53.5942,3],["Осиповичи",28.6382,53.3085,3],["Берёза",24.9845,52.5346,3],["Дзержинск",27.1315,53.6852,3],["Вилейка",26.9145,54.4881,3],["Кричев",31.7066,53.6952,3],["Лунинец",26.7978,52.2452,3],["Ивацевичи",25.3386,52.7091,3],["Марьина Горка",28.1478,53.5117,3]]
cities=[[n,*[round(v,2) for v in P(x,y)],r] for n,x,y,r in cities]
hq=np.round(h).astype(int)
out={"grid":{"x0":round(float(xmin),2),"z0":round(float(zmin),2),"step":STEP,"nx":nx,"nz":nz,"h":hq.flatten().tolist()},
     "border":[[round(x,2),round(z,2)] for x,z in border],"rivers":rivers,"lakes":lakes,"cities":cities}
s=json.dumps(out,ensure_ascii=False,separators=(",",":")); open("d3.json","w",encoding="utf8").write(s); print(len(s))
