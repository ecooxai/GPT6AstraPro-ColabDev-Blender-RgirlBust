"""Original procedural upper-body portrait. No external mesh, image texture or hair assets.
All shapes are authored here; reference is never loaded by Blender.
Front is -Y, up is Z. Units are artistic portrait units, not measured anatomy.
"""
import bpy, math, random, json, sys, argparse, os, time
from pathlib import Path
from mathutils import Vector
from math import sin, cos, pi, sqrt, exp
ROOT=Path(__file__).resolve().parents[1]
args=sys.argv[sys.argv.index('--')+1:] if '--' in sys.argv else []
a=argparse.ArgumentParser(); a.add_argument('--revision',type=int,default=1);a.add_argument('--quality',default='draft');a.add_argument('--views',default='front');a.add_argument('--export',action='store_true');args=a.parse_args(args)
CFG=json.loads((ROOT/'src/config.json').read_text()) if (ROOT/'src/config.json').exists() else {}
random.seed(41)
REV=ROOT/'build/revisions'/f'r{args.revision:03d}';REV.mkdir(parents=True,exist_ok=True)
LATEST=ROOT/'build/latest';LATEST.mkdir(exist_ok=True)
PREFIX='GPT6AstraPro_ColabDev_Blender_RgirlBust'
bpy.ops.object.select_all(action='SELECT');bpy.ops.object.delete(use_global=False)
for data in list(bpy.data.materials): bpy.data.materials.remove(data)
scene=bpy.context.scene
scene.render.engine='BLENDER_EEVEE'
scene.render.resolution_x=CFG.get('width',720 if args.quality=='draft' else 1000)
scene.render.resolution_y=CFG.get('height',1080 if args.quality=='draft' else 1500)
scene.render.resolution_percentage=100
scene.render.image_settings.file_format='PNG';scene.render.film_transparent=False
scene.eevee.taa_render_samples=32 if args.quality=='draft' else 96
scene.eevee.use_gtao=True;scene.eevee.gtao_distance=.16;scene.eevee.gtao_factor=1.12
scene.eevee.use_soft_shadows=True;scene.eevee.use_ssr=True
scene.render.threads_mode='FIXED';scene.render.threads=10
try: scene.view_settings.view_transform='AgX';scene.view_settings.look='AgX - Medium High Contrast'
except Exception:
 try: scene.view_settings.view_transform='Filmic';scene.view_settings.look='Medium High Contrast'
 except Exception: scene.view_settings.view_transform='Standard'
scene.view_settings.exposure=CFG.get('exposure',0.1)
scene.render.image_settings.color_mode='RGBA'
scene.world.use_nodes=True;scene.world.node_tree.nodes['Background'].inputs[0].default_value=(.27,.25,.24,1);scene.world.node_tree.nodes['Background'].inputs[1].default_value=.32
CHAR=bpy.data.collections.new('CHARACTER | original geometry');scene.collection.children.link(CHAR)
STAGE=bpy.data.collections.new('STUDIO | EEVEE lights and presentation');scene.collection.children.link(STAGE)
head_objs=[]
def put(o,head=False,stage=False):
 for c in list(o.users_collection): c.objects.unlink(o)
 (STAGE if stage else CHAR).objects.link(o)
 if head:head_objs.append(o)
 return o

def lin(v): return v/12.92 if v<=.04045 else ((v+.055)/1.055)**2.4

def rgb(s):
 if isinstance(s,str): s=tuple(int(s[i:i+2],16)/255 for i in (0,2,4))
 return tuple(lin(v) for v in s)

def mat(name,color,rough=.45,metal=0,sub=0):
 m=bpy.data.materials.new(name);m.diffuse_color=(*rgb(color),1);m.use_nodes=True
 p=m.node_tree.nodes.get('Principled BSDF');p.inputs['Base Color'].default_value=m.diffuse_color;p.inputs['Roughness'].default_value=rough;p.inputs['Metallic'].default_value=metal
 if 'Subsurface Weight' in p.inputs:p.inputs['Subsurface Weight'].default_value=sub;p.inputs['Subsurface Radius'].default_value=(1,.48,.28);p.inputs['Subsurface Scale'].default_value=.07
 return m
skin=mat('SKIN | warm porcelain, procedural pores','E8B5A0',.48,sub=.085)
nt=skin.node_tree;p=nt.nodes.get('Principled BSDF')
vcol=nt.nodes.new('ShaderNodeVertexColor');vcol.layer_name='Complexion';nt.links.new(vcol.outputs['Color'],p.inputs['Base Color'])
noise=nt.nodes.new('ShaderNodeTexNoise');noise.inputs['Scale'].default_value=165;noise.inputs['Detail'].default_value=2.3;noise.inputs['Roughness'].default_value=.7
bump=nt.nodes.new('ShaderNodeBump');bump.inputs['Strength'].default_value=.15;bump.inputs['Distance'].default_value=.009;nt.links.new(noise.outputs['Fac'],bump.inputs['Height']);nt.links.new(bump.outputs['Normal'],p.inputs['Normal'])
plain_skin=mat('SKIN | ears neck and chest','E8B5A0',.49,sub=.085)
for node in [noise]: pass
nose_dark=mat('Nostrils | soft occlusion','703F35',.68)
lip=mat('LIPS | natural rose','BB7472',.38,sub=.055)
lip_light=mat('Lips | soft wet highlights','D79189',.31,sub=.06)
lip_seam=mat('Lips | subtle central separation','6E3E3D',.64)
crease=mat('Skin | subtle warm crease','BA8271',.61)
waterline=mat('Lid margin | muted rose','C99183',.44,sub=.04)
lashmat=mat('Lashes | dark brown','241714',.53)
browmat=mat('Brows | individual tapered hairs','45312A',.68)
white=mat('Sclera | warm ivory','F0E1D7',.27,sub=.025)
irismat=mat('Iris | original radial vertex pigment','573725',.26)
nt=irismat.node_tree;col=nt.nodes.new('ShaderNodeVertexColor');col.layer_name='IrisPigment';nt.links.new(col.outputs['Color'],nt.nodes.get('Principled BSDF').inputs['Base Color'])
pupil=mat('Pupils | near black','080707',.19)
catchmat=mat('Corneal catchlight','FFF9EF',.09)
pc=catchmat.node_tree.nodes.get('Principled BSDF');pc.inputs['Emission Color'].default_value=(.7,.65,.6,1);pc.inputs['Emission Strength'].default_value=.6
hairmats=[]
for name,c in [('espresso','241A19'),('walnut','30211E'),('warm strands','3E2C26'),('cool sheen','382C2B'),('fine glints','4A3631')]:
 m=mat('HAIR | '+name,c,CFG.get('hair_roughness',.38));p=m.node_tree.nodes.get('Principled BSDF');p.inputs['Anisotropic'].default_value=.45
 hairmats.append(m)
shirt=mat('SHIRT | white cotton, procedural weave','E5E7EB',.71)
nt=shirt.node_tree;p=nt.nodes.get('Principled BSDF');p.inputs['Sheen Weight'].default_value=.16
tex=nt.nodes.new('ShaderNodeTexNoise');tex.inputs['Scale'].default_value=220;tex.inputs['Detail'].default_value=2
bump=nt.nodes.new('ShaderNodeBump');bump.inputs['Strength'].default_value=.18;bump.inputs['Distance'].default_value=.007;nt.links.new(tex.outputs['Fac'],bump.inputs['Height']);nt.links.new(bump.outputs['Normal'],p.inputs['Normal'])
seammat=mat('Shirt | cotton topstitch','C7CED7',.77)
buttonmat=mat('Buttons | ivory nacre','E8E3D7',.27)
threadmat=mat('Button threads','B9B2A8',.68)

def mesh(name,vs,fs,m,head=False,colors=None,layer='Complexion',stage=False):
 me=bpy.data.meshes.new(name);me.from_pydata(vs,[],fs);me.update();ob=bpy.data.objects.new(name,me);put(ob,head,stage);ob.data.materials.append(m)
 for f in me.polygons:f.use_smooth=True
 if colors:
  ca=me.color_attributes.new(name=layer,type='FLOAT_COLOR',domain='POINT')
  for i,c in enumerate(colors):ca.data[i].color=(*c[:3],1)
 return ob

def smooth(ob,levels=1):
 mod=ob.modifiers.new('Smooth original topology','SUBSURF');mod.levels=levels;mod.render_levels=levels
 return ob

def sphere(name,loc,scale,m,head=False,segments=40,rings=24):
 bpy.ops.mesh.primitive_uv_sphere_add(segments=segments,ring_count=rings,location=loc);o=bpy.context.object;o.name=name;o.scale=scale;put(o,head);o.data.materials.append(m)
 for p in o.data.polygons:p.use_smooth=True
 return o

def sample(points,n=48):
 ps=[Vector(p) for p in points];out=[]
 for k in range(n):
  u=k/(n-1)*(len(ps)-1);i=min(int(u),len(ps)-2);t=u-i
  a=ps[max(0,i-1)];b=ps[i];c=ps[i+1];d=ps[min(len(ps)-1,i+2)]
  out.append(.5*((2*b)+(-a+c)*t+(2*a-5*b+4*c-d)*t*t+(-a+3*b-3*c+d)*t*t*t))
 return out

def tube(name,points,r,m,head=False,sides=6,taper=True,samples=None):
 ps=sample(points,samples) if samples else [Vector(p) for p in points];vs=[];fs=[];last=None
 for i,p in enumerate(ps):
  tangent=(ps[min(i+1,len(ps)-1)]-ps[max(0,i-1)]).normalized()
  ref=Vector((0,1,0)) if abs(tangent.y)<.95 else Vector((1,0,0))
  n=tangent.cross(ref).normalized();b=tangent.cross(n).normalized()
  rr=r*(max(.08,(1-(i/(len(ps)-1))**3)) if taper else 1)
  for j in range(sides):vs.append(tuple(p+rr*(cos(2*pi*j/sides)*n+sin(2*pi*j/sides)*b)))
  if i:
   for j in range(sides):fs.append(((i-1)*sides+j,(i-1)*sides+(j+1)%sides,i*sides+(j+1)%sides,i*sides+j))
 fs.append(tuple(range(sides-1,-1,-1)));fs.append(tuple((len(ps)-1)*sides+j for j in range(sides)))
 return mesh(name,vs,fs,m,head)

def interp(table,z,col=1):
 if z<=table[0][0]:return table[0][col]
 if z>=table[-1][0]:return table[-1][col]
 for i in range(len(table)-1):
  if table[i][0]<=z<=table[i+1][0]:
   a,b=table[i],table[i+1];t=(z-a[0])/(b[0]-a[0]);h=b[0]-a[0]
   prev=table[max(0,i-1)];nxt=table[min(len(table)-1,i+2)]
   m0=(b[col]-prev[col])/(b[0]-prev[0]);m1=(nxt[col]-a[col])/(nxt[0]-a[0])
   return (2*t**3-3*t*t+1)*a[col]+(t**3-2*t*t+t)*h*m0+(-2*t**3+3*t*t)*b[col]+(t**3-t*t)*h*m1

def gauss(x,z,cx,cz,wx,wz):return exp(-((x-cx)/wx)**2-((z-cz)/wz)**2)
HEAD=[(3.10,.015,-.22,.32),(3.17,.25,-.57,.48),(3.29,.48,-.73,.61),(3.46,.69,-.81,.70),(3.64,.83,-.82,.79),(3.88,.96,-.80,.88),(4.12,1.015,-.79,.93),(4.37,1.045,-.765,.95),(4.62,1.04,-.735,.96),(4.87,1.03,-.75,.95),(5.12,1.015,-.79,.94),(5.42,1.01,-.78,.93),(5.67,.93,-.71,.85),(5.89,.70,-.51,.64),(6.06,.35,-.22,.35),(6.12,.008,.07,.09)]
NOSE=[(3.83,0,.12),(3.90,.10,.17),(3.975,.31,.185),(4.055,.43,.17),(4.13,.40,.145),(4.28,.29,.12),(4.48,.20,.115),(4.70,.11,.13),(4.91,0,.16)]

def face_y(x,z):
 w=interp(HEAD,z);f=interp(HEAD,z,2);b=interp(HEAD,z,3);cy=(f+b)/2;dep=(b-f)/2
 y=cy-dep*sqrt(max(0,1-(x/max(w,.01))**2))
 y-=.075*gauss(x,z,0,3.35,.37,.20)
 y-=.042*gauss(x,z,0,3.61,.38,.22)
 for s in [-1,1]:
  y-=.074*gauss(x,z,s*.62,4.23,.32,.23)
  y+=.10*gauss(x,z,s*.46,4.66,.36,.19)
  y-=.068*gauss(x,z,s*.45,4.94,.39,.14)
 y-=CFG.get('nose_depth',1.0)*interp(NOSE,z)*exp(-(x/interp(NOSE,z,2))**2)
 for s in [-1,1]:y-=.10*gauss(x,z,s*.18,3.986,.097,.065)
 y-=.02*(gauss(x,z,-.059,3.80,.025,.09)+gauss(x,z,.059,3.80,.025,.09))
 return y

def complexion(x,z):
 base=rgb(CFG.get('skin','E8B5A0'));blush=rgb('DDA093');nosecol=rgb('E0A18D')
 k=.34*sum(gauss(x,z,s*.64,4.22,.28,.22) for s in [-1,1]);k+=.16*gauss(x,z,0,4.04,.24,.11)
 return tuple(base[i]*(1-k)+blush[i]*k for i in range(3))

vs=[];fs=[];cols=[];N=192;M=180
for j in range(M+1):
 z=3.10+(6.12-3.10)*j/M;w=interp(HEAD,z);f=interp(HEAD,z,2);b=interp(HEAD,z,3);cy=(f+b)/2;dep=(b-f)/2
 for k in range(N):
  th=2*pi*k/N;x=w*sin(th);y=cy-dep*cos(th)
  if cos(th)>0:y=face_y(x,z)
  vs.append((x,y,z));cols.append(complexion(x,z) if cos(th)>0 else rgb(CFG.get('skin','E8B5A0')))
for j in range(M):
 for k in range(N):fs.append((j*N+k,j*N+(k+1)%N,(j+1)*N+(k+1)%N,(j+1)*N+k))
head=mesh('Face | continuous original nose, cheeks, jaw and cranium',vs,fs,skin,True,cols)
# Mild lower face refinement remains in the continuous mesh, not a stack of primitives.

# Eyes: almond scleral patches with spherical depth, continuous sculpted skin lids.
EYEZ=CFG.get('eye_z',4.66);EYEX=CFG.get('eye_x',.445);EYER=.355;EYEY=CFG.get('eye_y',-.588);EW=CFG.get('eye_width',.315);UP=CFG.get('eye_up',.133);LOW=CFG.get('eye_low',.101)
def eyeco(s,q,h,extra=0):
 x=s*EYEX+q;z=EYEZ+h+.038*s*q
 y=EYEY-sqrt(max(.0001,EYER*EYER-q*q-h*h))-extra
 return (x,y,z)
def eye_boundary(th):
 q=EW*cos(th);h=(UP if sin(th)>0 else LOW)*sin(th)*(abs(sin(th))**.18)
 return q,h
for s in [-1,1]:
 side='L' if s<0 else 'R';v=[eyeco(s,0,0)];f=[]
 for r in range(1,17):
  for k in range(96):
   q,h=eye_boundary(2*pi*k/96);v.append(eyeco(s,q*r/16,h*r/16))
 for k in range(96):f.append((0,1+k,1+(k+1)%96))
 for r in range(1,16):
  a=1+(r-1)*96;b=1+r*96
  for k in range(96):f.append((a+k,b+k,b+(k+1)%96,a+(k+1)%96))
 mesh('Eye '+side+' | spherical almond sclera',v,f,white,True)
 # Real radial iris surface, no photograph or generated texture.
 v=[];f=[];c=[];IR=CFG.get('iris_radius',.121);PUP=.050
 for r in range(15):
  rad=IR*r/14
  for k in range(144):
   th=2*pi*k/144;q=rad*cos(th);h=rad*sin(th)
   v.append(eyeco(s,q,h,.004))
   if rad<PUP*.96:color=rgb('0B0908')
   else:
    phase=.5+.23*sin(th*41+.4*sin(th*11))+.14*sin(th*77+rad*230)+.1*sin(th*113-rad*90)
    strength=(.39+.7*phase)*(1-.6*exp(-((rad-IR)/.009)**2))
    inner=exp(-((rad-.066)/.018)**2)
    color=tuple(lin(min(.85,vv*strength)) for vv in (.38+.06*inner,.245+.02*inner,.166))
   c.append(color)
 for r in range(14):
  for k in range(144):f.append((r*144+k,r*144+(k+1)%144,(r+1)*144+(k+1)%144,(r+1)*144+k))
 mesh('Eye '+side+' | 144-ray brown iris and pupil',v,f,irismat,True,c,'IrisPigment')
 # Lid tissue lofts into underlying anatomical face. Outer vertices meet face exactly.
 v=[];f=[];c=[]
 for r in range(9):
  t=r/8
  for k in range(128):
   th=2*pi*k/128;q,h=eye_boundary(th);ix,iy,iz=eyeco(s,q,h,.007)
   oq=q*(1.29+.03*sin(th));oh=h*(1.8 if h>0 else 1.95);ox=s*EYEX+oq;oz=EYEZ+oh+.038*s*oq;oy=face_y(ox,oz)-.003
   x=ix*(1-t)+ox*t;z=iz*(1-t)+oz*t;y=iy*(1-t)+oy*t-.012*sin(pi*t)
   v.append((x,y,z));base=complexion(x,z);warm=rgb('DCA18F');blend=.15*(1-t)
   c.append(tuple(base[j]*(1-blend)+warm[j]*blend for j in range(3)))
 for r in range(8):
  for k in range(128):f.append((r*128+k,r*128+(k+1)%128,(r+1)*128+(k+1)%128,(r+1)*128+k))
 mesh('Eye '+side+' | upper and lower anatomical lids',v,f,skin,True,c)
 for upper in [True,False]:
  pts=[]
  for k in range(65):
   th=pi*k/64 if upper else pi+pi*k/64;q,h=eye_boundary(th);pts.append(eyeco(s,q,h,.010))
  tube('Eye '+side+(' | upper lash roots' if upper else ' | lower waterline'),pts,.0065 if upper else .005,lashmat if upper else waterline,True,6,False)
 # Upper orbital fold, restrained, interrupted at inner corner.
 pts=[]
 for k in range(48):
  q=-EW*.83+EW*1.66*k/47;h=UP*sqrt(max(0,1-(q/EW)**2))+.063;x=s*EYEX+q;z=EYEZ+h+.038*s*q
  y=.62*eyeco(s,q,min(h,UP))[1]+.38*face_y(x,z)-.011
  pts.append((x,y,z))
 tube('Eye '+side+' | delicate upper fold',pts,.004,crease,True,5)
 # Individual lashes are fine, not a solid strip.
 for k in range(31):
  u=-.94+1.88*k/30;q=EW*u;h=UP*(sqrt(max(0,1-u*u))**1.18);p=Vector(eyeco(s,q,h,.015));le=.034+.029*(.5+.5*u*s)
  tube('Lash '+side+str(k),[p,p+Vector((u*.014,-.025,.008)),p+Vector((u*.031,-.045,le))],.0023,lashmat,True,4,True,8)
 for k in range(13):
  u=-.8+1.6*k/12;q=EW*u;h=-LOW*sqrt(1-u*u);p=Vector(eyeco(s,q,h,.010))
  tube('Lower lash '+side+str(k),[p,p+Vector((u*.014,-.016,-.018)),p+Vector((u*.025,-.020,-.028))],.0015,browmat,True,4,True,7)
 # Catchlights are small pieces of 3D corneal geometry, not image dots.
 for q,h,rr in [(-.037,.045,.021),(.034,-.031,.007)]:
  loc=eyeco(s,q,h,.012);sphere('Eye '+side+' | corneal catchlight',loc,(rr,.003,rr*.8),catchmat,True,20,12)
 # Brows composed of hundreds of thin original hairs with a soft root silhouette.
 for k in range(175):
  t=random.random();x=s*(.15+.60*t);z=4.995+.075*sin(t*pi*.92)-.035*t+random.uniform(-.029,.025);y=face_y(x,z)-.012
  le=random.uniform(.033,.063);dx=s*(.029+.03*t)
  end=(x+dx,y-.008,z+le*(1-.7*t))
  tube('Brow '+side+f' | hair {k:03d}',[(x,y,z),(x+dx*.45,y-.008,z+le*.6),end],random.uniform(.0015,.0025),browmat,True,4,True,6)
# Nostrils and alar seams are small, warm and inset, with integrated nose surface above.
for s in [-1,1]:
 x=s*.153;z=3.958;y=face_y(x,z)-.008
 o=sphere('Nostril | recessed aperture '+str(s),(x,y,z),(.048,.009,.022),nose_dark,True,32,16);o.rotation_euler.y=s*.16
 pts=[]
 for k in range(24):
  t=k/23;x=s*(.198+.030*sin(pi*t));z=4.025-.080*t;pts.append((x,face_y(x,z)-.003,z))
 tube('Alar crease '+str(s),pts,.0035,crease,True,5)
# Lip surfaces with cupid bow and soft integration into surrounding skin.
MW=CFG.get('mouth_width',.305);MZ=CFG.get('mouth_z',3.625)
def mouthline(u):return MZ-.012*abs(u)+.007*cos(u*pi)
def upperlip(u):return (1-u*u)**.75*(.068+.027*exp(-((abs(u)-.34)/.20)**2)-.011*exp(-(u/.15)**2))
def lowerlip(u):return .112*(max(0,1-u*u)**.80)
for top in [True,False]:
 vs=[];fs=[]
 for i in range(81):
  u=-1+2*i/80;x=MW*u;line=mouthline(u);extent=upperlip(u) if top else -lowerlip(u)
  for j in range(11):
   t=j/10;z=line+extent*t;edge=face_y(x,z)-.007
   bulge=(.070 if top else .084)*sin(pi*t*.92)*(max(0,1-u*u)**.6)+.021*(1-t)*(1-u*u)
   vs.append((x,edge-bulge,z))
 for i in range(80):
  for j in range(10):q=i*11+j;fs.append((q,q+11,q+12,q+1))
 mesh('Mouth | '+('sculpted cupid bow' if top else 'soft lower lip'),vs,fs,lip if top else lip_light,True)
pts=[]
for i in range(90):
 u=-1+2*i/89;x=MW*u;z=mouthline(u);pts.append((x,face_y(x,z)-.030*(1-u*u)-.010,z))
tube('Mouth | fine relaxed separation',pts,.005,lip_seam,True,6,False)
# Fine lip ridges are actual subdued 3D striations.
for i in range(32):
 u=-.88+1.76*i/31;x=MW*u;zz=mouthline(u);points=[]
 for j in range(7):
  t=.20+.63*j/6;z=zz-lowerlip(u)*t;y=face_y(x,z)-.008-.084*sin(pi*t*.92)*(1-u*u)**.6-.021*(1-t)*(1-u*u)-.0008;points.append((x+.003*sin(j*.9+i),y,z))
 tube('Lip | natural fine ridge '+str(i),points,.0012,lip_light,True,4)
# Ears, complete on both sides, with helix and concha.
for s in [-1,1]:
 o=sphere('Ear | pinna '+str(s),(s*1.008,.045,4.39),(.158,.198,.398),plain_skin,True,48,32);o.rotation_euler.y=s*-.16
 sphere('Ear | concha '+str(s),(s*1.038,-.143,4.395),(.082,.013,.174),crease,True)
 pts=[]
 for i in range(65):
  t=2*pi*i/64;x=s*(1.017+.105*sin(t));z=4.40+.332*cos(t);y=-.125-.023*sin(t);pts.append((x,y,z))
 tube('Ear | helix rim '+str(s),pts,.033,plain_skin,True,8,False)
 tube('Ear | antihelix '+str(s),[(s*1.04,-.172,4.17),(s*1.075,-.179,4.32),(s*1.07,-.170,4.48),(s*1.03,-.165,4.61)],.024,plain_skin,True,8,True,36)
 sphere('Ear | tragus '+str(s),(s*.965,-.165,4.34),(.040,.038,.069),plain_skin,True)
print('ANATOMY BUILT',flush=True)
# Neck transitions into a closed upper chest, visible through the collar opening.
NECK=[(1.73,.82,-.40,.42),(1.96,.77,-.34,.44),(2.19,.65,-.28,.40),(2.42,.43,-.215,.36),(2.77,.34,-.175,.345),(3.13,.34,-.155,.35),(3.48,.38,-.12,.36),(3.64,.36,-.04,.35)]
v=[];f=[]
for j in range(65):
 z=1.73+(3.64-1.73)*j/64;w=interp(NECK,z);fr=interp(NECK,z,2);ba=interp(NECK,z,3)
 for k in range(96):
  th=2*pi*k/96;x=w*sin(th);y=(fr+ba)/2-(ba-fr)/2*cos(th)
  # Soft sternomastoid tendons are integral to the neck surface.
  if cos(th)>0:
   y-=.010*exp(-((abs(x)-(.17+.15*max(0,2.8-z)))/.045)**2)*exp(-((z-2.75)/.65)**2)
  v.append((x-.035,y,z))
for j in range(64):
 for k in range(96):f.append((j*96+k,j*96+(k+1)%96,(j+1)*96+(k+1)%96,(j+1)*96+k))
mesh('Neck | continuous throat and clavicular chest',v,f,plain_skin)

TORSO=[(-.14,1.56,-.535,.49),(.0,1.65,-.58,.54),(.35,1.68,-.61,.58),(.82,1.73,-.65,.60),(1.30,1.79,-.64,.58),(1.73,1.85,-.57,.54),(2.04,1.88,-.46,.49),(2.28,1.80,-.30,.41),(2.47,1.41,-.23,.34),(2.66,.66,-.18,.26),(2.80,.46,-.17,.22)]
def shirt_y(x,z):
 w=interp(TORSO,z);fr=interp(TORSO,z,2);ba=interp(TORSO,z,3)
 y=(fr+ba)/2-(ba-fr)/2*sqrt(max(.001,1-(x/max(.1,w))**2))
 # Low-amplitude fabric tensions originate near the placket, shoulder, and side seam.
 y-=.024*sin(13*z+4*x)*exp(-((abs(x)-.36)/.23)**2)
 y-=.026*sin(17*z-7*abs(x))*exp(-((abs(x)-1.45)/.24)**2)
 y-=.018*sin(19*z+3*x)*exp(-((z-.3)/.27)**2)
 return y
v=[];f=[];NN=160;MM=115
for j in range(MM+1):
 z=-.14+2.94*j/MM;w=interp(TORSO,z);fr=interp(TORSO,z,2);ba=interp(TORSO,z,3)
 for k in range(NN):
  th=2*pi*k/NN;x=w*sin(th);y=shirt_y(x,z) if cos(th)>0 else (fr+ba)/2-(ba-fr)/2*cos(th)
  if cos(th)<=0:y+=.009*sin(15*z+3*x)
  v.append((x,y,z))
for j in range(MM):
 for k in range(NN):
  ids=(j*NN+k,j*NN+(k+1)%NN,(j+1)*NN+(k+1)%NN,(j+1)*NN+k);cen=sum((Vector(v[a]) for a in ids),Vector())/4
  # A genuine V-shaped aperture. No flesh-colored painted insert.
  if cen.y<.04 and cen.z>1.90 and abs(cen.x)<.44*(cen.z-1.90)/.90:continue
  f.append(ids)
f.append(tuple(range(NN-1,-1,-1)))
ob=mesh('Shirt | tailored closed torso with open neckline',v,f,shirt);mod=ob.modifiers.new('Cotton thickness','SOLIDIFY');mod.thickness=.014
# Full sleeves, open lower bust crop but closed geometrical cut ends.
for s in [-1,1]:
 points=[(s*1.46,.035,2.28),(s*1.76,.07,2.06),(s*1.87,.08,1.65),(s*1.93,.075,1.04),(s*1.92,.075,.35),(s*1.88,.075,-.15)]
 ps=sample(points,55);v=[];f=[]
 for j,p in enumerate(ps):
  t=j/(len(ps)-1);rx=.33*(1-.13*t);ry=.34*(1-.10*t)
  for k in range(64):
   th=2*pi*k/64;fold=.010*sin(17*pi*t+3*th)*sin(pi*t)**2
   v.append((p.x+(rx+fold)*cos(th),p.y+(ry+fold)*sin(th),p.z))
 for j in range(len(ps)-1):
  for k in range(64):f.append((j*64+k,j*64+(k+1)%64,(j+1)*64+(k+1)%64,(j+1)*64+k))
 f.append(tuple(range(63,-1,-1)));f.append(tuple((len(ps)-1)*64+k for k in range(64)))
 mesh('Shirt | shoulder and sleeve '+str(s),v,f,shirt)
 pts=[]
 for k in range(40):
  t=k/39;z=2.26-.77*t;x=s*(1.54+.10*sin(t*pi));pts.append((x,shirt_y(x,z)-.008,z))
 tube('Shirt | set-in sleeve seam '+str(s),pts,.006,seammat,False,5)
# Folded collar leaves, softly curved four-sided textile surfaces.
def collar_patch(s):
 A=Vector((s*.37,-.19,2.75));B=Vector((s*.64,-.10,2.49));C=Vector((s*.73,-.43,1.98));D=Vector((s*.025,-.58,1.89))
 v=[];f=[]
 for i in range(21):
  u=i/20
  for j in range(21):
   t=j/20;p=(1-t)*((1-u)*A+u*B)+t*((1-u)*D+u*C)
   p.y-=.075*sin(pi*u)*sin(pi*t);p.z+=.045*sin(pi*u)*sin(pi*t)
   v.append(tuple(p))
 for i in range(20):
  for j in range(20):q=i*21+j;f.append((q,q+21,q+22,q+1))
 ob=mesh('Collar | folded cotton leaf '+str(s),v,f,shirt);mod=ob.modifiers.new('Collar cloth thickness','SOLIDIFY');mod.thickness=.023
 smooth(ob,1)
 # Restrained perimeter stitching, mostly covered by the falling hair.
 tube('Collar | edge stitching '+str(s),[D+Vector((s*.02,-.007,.012)),C+Vector((-s*.02,-.007,.017)),B+Vector((-s*.015,-.01,-.018))],.0035,seammat,False,5,False,52)
collar_patch(-1);collar_patch(1)
# Collar stand wraps fully around the back of the neck.
v=[];f=[]
for j in range(2):
 for k in range(97):
  th=.50+(2*pi-1.0)*k/96;z=2.70+.03*cos(th)+j*.12;v.append((.425*sin(th),.04-.27*cos(th),z))
for k in range(96):f.append((k,k+1,97+k+1,97+k))
ob=mesh('Collar | continuous rear neckband',v,f,shirt);mod=ob.modifiers.new('Collar band thickness','SOLIDIFY');mod.thickness=.018
# Soft front placket with three-dimensional buttons and stitching.
v=[];f=[]
for i in range(80):
 z=-.14+2.02*i/79;cx=.06+.065*cos(z*1.4)
 for j in range(7):
  x=cx+(.5-j/6)*.18;y=shirt_y(x,z)-.013-.011*sin(pi*j/6);v.append((x,y,z))
for i in range(79):
 for j in range(6):q=i*7+j;f.append((q,q+7,q+8,q+1))
mesh('Shirt | shaped front button placket',v,f,shirt)
for edge in [-1,1]:
 pts=[]
 for i in range(80):
  z=-.13+2.0*i/79;x=.06+.065*cos(z*1.4)+edge*.075;pts.append((x,shirt_y(x,z)-.029,z))
 tube('Shirt | fine placket stitching '+str(edge),pts,.0028,seammat,False,4,False)
for z in [1.58,.83,.08]:
 x=.06+.065*cos(z*1.4);y=shirt_y(x,z)-.039
 bpy.ops.mesh.primitive_cylinder_add(vertices=40,radius=.054,depth=.018,location=(x,y,z),rotation=(pi/2,0,0));o=bpy.context.object;o.name='Shirt | ivory four-hole button';put(o);o.data.materials.append(buttonmat)
 bevel=o.modifiers.new('Rounded mother-of-pearl edge','BEVEL');bevel.width=.008;bevel.segments=3
 for dx in [-.015,.015]:
  for dz in [-.015,.015]:sphere('Button | recessed thread hole',(x+dx,y-.014,z+dz),(.007,.003,.007),threadmat,False,16,8)
 for dz in [-.015,.015]:tube('Button | sewn cross-thread',[(x-.016,y-.019,z+dz),(x+.016,y-.019,z+dz)],.0027,shirt,False,5,False)
print('CLOTHING BUILT',flush=True)

# Hair. A closed scalp shell supports layered, volumetric swept locks.
# Every fiber below is authored 3D geometry; no cards, scanned hair, or photo textures.
v=[];f=[];HS=144;HR=44
for j in range(HR+1):
 for k in range(HS):
  th=2*pi*k/HS;maxphi=1.18+.70*(1-cos(th))/2+.16*abs(sin(th));phi=.008+(maxphi-.008)*j/HR
  x=1.11*sin(phi)*sin(th);y=.065-1.00*sin(phi)*cos(th);z=4.62+1.61*cos(phi)
  v.append((x,y,z))
for j in range(HR):
 for k in range(HS):f.append((j*HS+k,j*HS+(k+1)%HS,(j+1)*HS+(k+1)%HS,(j+1)*HS+k))
mesh('Hair | closed anatomical scalp foundation',v,f,hairmats[0],True)

FIBERS=CFG.get('fibers_per_lock',11)
def lock(name,points,width,depth=.035,fibers=FIBERS,mati=0):
 ps=sample(points,56);v=[];f=[];frames=[];old=None
 for i,p in enumerate(ps):
  t=i/(len(ps)-1);tangent=(ps[min(len(ps)-1,i+1)]-ps[max(0,i-1)]).normalized()
  if p.z>5.20:normal=Vector((p.x*.65,p.y-.1,(p.z-5.15)*.72)).normalized()
  else:normal=Vector((p.x*.38,p.y-.22,.03)).normalized()
  side=tangent.cross(normal).normalized();normal=side.cross(tangent).normalized()
  if old is not None and side.dot(old)<0:side=-side;normal=-normal
  old=side
  taper=(.48+.52*sin(min(1,t*1.35)*pi/2))*(max(.022,1-t**4)**.72)
  wi=width*taper;di=depth*(.50+.50*sin(pi*t))*(max(.03,1-t**6)**.65)
  frames.append((p,side,normal,wi,di))
  for j in range(10):
   th=2*pi*j/10;v.append(tuple(p+side*(wi*cos(th))+normal*(di*sin(th))))
  if i:
   for j in range(10):f.append(((i-1)*10+j,(i-1)*10+(j+1)%10,i*10+(j+1)%10,i*10+j))
 f.append(tuple(range(9,-1,-1)));f.append(tuple((len(ps)-1)*10+j for j in range(10)))
 mesh('Hair lock | '+name,v,f,hairmats[mati],True)
 for k in range(fibers):
  off=-.92+1.84*(k+.5)/fibers;phase=random.random()*6.28;pts=[]
  for i,(p,side,n,wi,di) in enumerate(frames):
   t=i/(len(frames)-1);wav=.0019*sin(phase+t*35)*sin(pi*t);q=p+side*(off*wi+wav)+n*(di*sqrt(max(0,1-off*off))+.002)
   pts.append(q)
  tube('Hair fiber | '+name+' '+str(k),pts,random.uniform(.0013,.0023),hairmats[random.choices([0,1,2,3,4],[.16,.37,.21,.23,.03])[0]],True,4)
# Back and side curtain, descending from crown around the whole skull.
for k in range(66):
 th=.66+(2*pi-1.32)*k/65;st=sin(th);ct=cos(th);jitter=random.uniform(-.035,.035);bottom=random.uniform(.44,1.00)+.13*ct
 points=[(.18+.08*st,.08-.13*ct,6.16),(.80*st,-.73*ct+.10,5.81),(1.095*st,-.95*ct+.10,4.93),(1.135*st,-.94*ct+.10,3.99),(1.24*st,-.84*ct+.09,3.13),(1.28*st+.055*sin(k*.8),-.82*ct+.07,2.37),(1.40*st+.04*sin(k),-.78*ct,1.51),(1.25*st+.05*sin(k),-.73*ct-.02,bottom)]
 lock('rear curtain %02d'%k,points,.080+random.random()*.040,.032,8,random.choice([0,0,1,3]))
# Prominent long front layers, separately sculpted on each side.
for s in [-1,1]:
 for k in range(18):
  t=k/17;ofs=(t-.5)*.37
  if s<0:
   points=[(.19-.04*t,-.18-.13*t,6.16-.025*t),(-.36,-.57-.03*t,6.09-.12*t),(-.88,-.68-.03*t,5.60-.23*t),(-1.035+ofs*.2,-.60-.06*t,4.82),(-1.06+ofs*.35,-.41-.15*t,3.86),(-1.13+ofs*.55,-.48-.18*t,2.91),(-1.20+ofs,-.58-.16*t,2.13),(-1.45+ofs*.8,-.64-.13*t,1.26),(-1.52+ofs*.5,-.66-.12*t,.74),(-1.25+ofs,-.67-.10*t,.30+.35*t)]
  else:
   points=[(.23+.04*t,-.17-.12*t,6.15-.02*t),(.71,-.57-.05*t,5.93-.06*t),(1.045,-.62-.03*t,5.24),(1.08+ofs*.1,-.42-.09*t,4.42),(1.11+ofs*.3,-.34-.10*t,3.55),(1.23+ofs*.55,-.47-.12*t,2.77),(1.37+ofs,-.61-.16*t,2.12),(1.55+ofs*.8,-.66-.13*t,1.49),(1.46+ofs*.8,-.69-.14*t,.94),(1.11+ofs,-.65-.1*t,.52+.27*t)]
  lock(('left' if s<0 else 'right')+' front fall %02d'%k,points,.055+random.random()*.035,.027,14,random.choice([0,1,1,3]))
# Swept forehead fringe, sparse enough to reveal the forehead.
for k in range(9):
 t=k/8
 points=[(.24+.16*t,-.62+.03*t,5.94-.055*t),(.19-.15*t,-.86-.015*t,5.67-.08*t),(-.07-.28*t,-.94-.02*t,5.23-.12*t),(-.18-.42*t,-.95+.04*t,4.92-.08*t)]
 lock('wispy swept fringe %02d'%k,points,.022+random.random()*.014,.014,10,random.choice([0,1,3]))
for k in range(5):
 t=k/4
 points=[(.42+.03*t,-.65,5.83),(.46-.06*t,-.90,5.52),(.39-.09*t,-.98,5.15),(.26-.10*t,-.98,4.84+.035*t)]
 lock('central separated wisp %02d'%k,points,.011+random.random()*.008,.010,6,0)
# A few thin face-framing pieces soften the edge near the left ear.
for k in range(8):
 t=k/7
 points=[(-.52-.08*t,-.84,5.63),(-.74-.07*t,-.93,5.22),(-.93-.04*t,-.84,4.63),(-1.00-.02*t,-.63,4.05),(-.96+.03*t,-.55,3.63)]
 lock('fine cheek frame %02d'%k,points,.013,.010,5,1)
# Irregular flyaways follow original guide splines and are intentionally restrained.
for k in range(65):
 s=random.choice([-1,1]);z=random.uniform(3.2,5.8);x=s*(1.09+.055*sin(z*3));y=random.uniform(-.45,.12)
 points=[(x,y,z),(x+s*.09,y-.035,z-.20),(x+s*.13,y-.02,z-.49),(x+s*.10,y+.01,z-.75)]
 tube('Hair | flyaway %03d'%k,points,random.uniform(.0008,.0013),hairmats[random.choice([1,3])],True,3,True,22)
# Narrow natural scalp part, almost entirely occluded by roots.
partmat=mat('Hair part | shaded scalp','A87763',.70)
tube('Hair | narrow off-center scalp part',[(.19,.42,6.105),(.22,.20,6.168),(.25,-.05,6.175),(.27,-.28,6.124),(.29,-.48,6.045)],.009,partmat,True,6,True,48)
print('HAIR BUILT',flush=True)
# Pose is applied coherently to the complete head, ears, lids and hair.
root=bpy.data.objects.new('Head pose | soft reference tilt',None);CHAR.objects.link(root);root.location=(0,0,3.72)
bpy.context.view_layer.update()
for ob in head_objs:
 matrix=ob.matrix_world.copy();ob.parent=root;ob.matrix_parent_inverse=root.matrix_world.inverted();ob.matrix_world=matrix
root.rotation_euler.y=CFG.get('head_tilt',.095);root.rotation_euler.z=CFG.get('head_turn',.015)

# Studio is independent of the character export.
bg=mat('STUDIO | warm charcoal backdrop','282525',.92)
bpy.ops.mesh.primitive_plane_add(size=200,location=(0,3.1,3),rotation=(pi/2,0,0));ob=bpy.context.object;ob.name='Studio seamless backdrop';put(ob,stage=True);ob.data.materials.append(bg)
def area(name,loc,target,power,size,color,size_y=None):
 data=bpy.data.lights.new(name,'AREA');data.energy=power;data.color=color;data.shape='DISK' if size_y is None else 'RECTANGLE';data.size=size
 if size_y:data.size_y=size_y
 ob=bpy.data.objects.new(name,data);STAGE.objects.link(ob);ob.location=loc;ob.rotation_euler=(Vector(target)-ob.location).to_track_quat('-Z','Y').to_euler();data.use_shadow=True
area('Key | large soft portrait window',(-3.5,-5.3,7.0),(0,0,4),CFG.get('key_power',950),4.0,(1.0,.89,.82))
area('Fill | cool frontal silk',(3.5,-4.2,4.7),(0,0,3.8),CFG.get('fill_power',330),3.4,(.84,.90,1.0))
area('Hair rim | cool high strip',(2.8,1.2,7.2),(0,0,4.3),780,2.6,(.88,.91,1.0),1.7)
area('Hair separation | warm left',(-3.1,1.0,5.5),(0,0,3.7),600,2.6,(1,.81,.71),3.2)
area('Eye card | subtle frontal catchlight',(-.9,-5.1,5.4),(0,-.5,4.5),55,1.0,(1,.97,.91),.6)
# Typography is real Blender text placed above the character.
titlemat=mat('Studio typography | warm silver','BABCB2',.70)
def textline(name,text,z,size):
 curve=bpy.data.curves.new(name,'FONT');curve.body=text;curve.align_x='CENTER';curve.size=size;curve.space_character=1.15;curve.extrude=0
 ob=bpy.data.objects.new(name,curve);STAGE.objects.link(ob);ob.data.materials.append(titlemat);ob.location=(0,-.05,z);ob.rotation_euler=(pi/2,0,0)
textline('Title | model identity','GPT-6 ASTRA PRO',6.72,.125)
textline('Subtitle | development tools','COLABDEV  /  BLENDER EEVEE',6.51,.065)
camdata=bpy.data.cameras.new('Portrait camera');camera=bpy.data.objects.new('Portrait camera',camdata);STAGE.objects.link(camera);scene.camera=camera
camera.data.type='ORTHO';camera.data.ortho_scale=7.30;camera.data.lens=85
camera.data.clip_start=.05;camera.data.clip_end=200
VIEWS={'front':((0,-15,3.8),(0,0,3.30)), 'three-quarter':((8,-13,4.2),(0,0,3.35)), 'side':((14,-1.7,4.1),(0,0,3.35)), 'back':((0,15,4.0),(0,0,3.35)), 'face':((0,-15,4.55),(0,-.15,4.63))}
# Save an editable .blend, then render fast EEVEE review images.
for idx,name in enumerate(args.views.split(',')):
 location,target=VIEWS[name];camera.location=location;camera.rotation_euler=(Vector(target)-camera.location).to_track_quat('-Z','Y').to_euler();camera.data.ortho_scale=3.35 if name=='face' else 7.30
 if name=='face':scene.render.resolution_x=800;scene.render.resolution_y=960
 else:scene.render.resolution_x=CFG.get('width',720 if args.quality=='draft' else 1000);scene.render.resolution_y=CFG.get('height',1080 if args.quality=='draft' else 1500)
 if name!='front':
  for o in STAGE.objects:
   if o.type=='FONT':o.hide_render=True
 else:
  for o in STAGE.objects:
   if o.type=='FONT':o.hide_render=False
 scene.render.filepath=str(REV/(name+'.png'))
 print('RENDERING',name,scene.render.filepath,flush=True);bpy.ops.render.render(write_still=True)
# Reset the editable scene to the front portrait composition.
camera.location=VIEWS['front'][0];camera.rotation_euler=(Vector(VIEWS['front'][1])-camera.location).to_track_quat('-Z','Y').to_euler();camera.data.ortho_scale=7.30
for o in STAGE.objects:
 if o.type=='FONT':o.hide_render=False
scene.render.resolution_x=1000;scene.render.resolution_y=1500;scene.render.filepath=str(LATEST/(PREFIX+'_portrait.png'))
scene['asset_origin']='Original math-authored meshes, fibers, procedural materials; no reference texture.'
scene['review_revision']=args.revision
bpy.ops.wm.save_as_mainfile(filepath=str(LATEST/(PREFIX+'.blend')))
if args.export:
 print('EXPORTING GLB',flush=True)
 bpy.ops.object.select_all(action='DESELECT')
 for ob in CHAR.objects:ob.select_set(True)
 bpy.context.view_layer.objects.active=head
 try:
  bpy.ops.export_scene.gltf(filepath=str(LATEST/(PREFIX+'.glb')),export_format='GLB',use_selection=True,export_apply=True,export_yup=True,export_animations=False,export_cameras=False,export_lights=False,export_texcoords=False,export_normals=True,export_colors=True,export_materials='EXPORT')
 except Exception as e:
  print('GLB_EXPORT_ERROR',repr(e),flush=True)
stats={'revision':args.revision,'objects':len(CHAR.objects),'mesh_vertices':sum(len(o.data.vertices) for o in CHAR.objects if o.type=='MESH'),'source':'all original procedural geometry','renderer':scene.render.engine,'config':CFG}
(REV/'build-report.json').write_text(json.dumps(stats,indent=2))
print('BUILD_DONE',json.dumps(stats),flush=True)
