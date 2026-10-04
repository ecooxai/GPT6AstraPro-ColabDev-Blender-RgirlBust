"""Original procedural upper-body portrait. No external mesh, image texture or hair assets.
All shapes are authored here; reference is never loaded by Blender.
Front is -Y, up is Z. Units are artistic portrait units, not measured anatomy.
"""
import bpy, math, random, json, sys, argparse, os, time
from pathlib import Path
from mathutils import Vector, Matrix
from mathutils.geometry import delaunay_2d_cdt
import bmesh
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
scene.eevee.use_gtao=True;scene.eevee.gtao_distance=.09;scene.eevee.gtao_factor=.92
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
bump=nt.nodes.new('ShaderNodeBump');bump.inputs['Strength'].default_value=.08;bump.inputs['Distance'].default_value=.006;nt.links.new(noise.outputs['Fac'],bump.inputs['Height']);nt.links.new(bump.outputs['Normal'],p.inputs['Normal'])
plain_skin=mat('SKIN | ears neck and chest',CFG.get('skin','E8B2A0'),.49,sub=.085)
for node in [noise]: pass
nose_dark=mat('Nostrils | soft occlusion','59352D',.75)
lip=mat('LIPS | natural rose','BB7472',.38,sub=.055)
lip_light=mat('Lips | soft wet highlights','D79189',.31,sub=.06)
lip_seam=mat('Lips | subtle central separation','6E3E3D',.64)
crease=mat('Skin | subtle warm crease','BA8271',.61)
waterline=mat('Lid margin | muted rose','D2A89A',.44,sub=.04)
lashmat=mat('Lashes | dark brown','241714',.53)
browmat=mat('Brows | individual tapered hairs','513B30',.72)
white=mat('Sclera | warm ivory','F0E1D7',.27,sub=.025)
nt=white.node_tree;vc=nt.nodes.new('ShaderNodeVertexColor');vc.layer_name='ScleraTint';nt.links.new(vc.outputs['Color'],nt.nodes.get('Principled BSDF').inputs['Base Color'])
irismat=mat('Iris | original radial vertex pigment','573725',.26)
nt=irismat.node_tree;col=nt.nodes.new('ShaderNodeVertexColor');col.layer_name='IrisPigment';nt.links.new(col.outputs['Color'],nt.nodes.get('Principled BSDF').inputs['Base Color'])
pupil=mat('Pupils | near black','080707',.19)
catchmat=mat('Corneal catchlight','FFF9EF',.09)
pc=catchmat.node_tree.nodes.get('Principled BSDF');pc.inputs['Emission Color'].default_value=(.7,.65,.6,1);pc.inputs['Emission Strength'].default_value=.05
for ocular_material in [white,irismat]:
 p=ocular_material.node_tree.nodes.get('Principled BSDF');p.inputs['Coat Weight'].default_value=.10;p.inputs['Coat Roughness'].default_value=.09;p.inputs['Roughness'].default_value=.29;p.inputs['Specular IOR Level'].default_value=.14
hairmats=[]
for name,c in [('espresso','241A19'),('walnut','30211E'),('warm strands','3E2C26'),('cool sheen','382C2B'),('fine glints','4A3631')]:
 m=mat('HAIR | '+name,c,CFG.get('hair_roughness',.38));p=m.node_tree.nodes.get('Principled BSDF');p.inputs['Anisotropic'].default_value=.55;p.inputs['Specular IOR Level'].default_value=.20
 hairmats.append(m)
fibermats=[]
for original in hairmats:
 m=original.copy();m.name=original.name+' | fine fiber';m.shadow_method='NONE';m.node_tree.nodes.get('Principled BSDF').inputs['Specular IOR Level'].default_value=.15;fibermats.append(m)
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
HEAD=[(3.10,.015,-.22,.32),(3.17,.25,-.57,.48),(3.29,.43,-.73,.61),(3.46,.62,-.81,.70),(3.64,.78,-.82,.79),(3.88,.92,-.80,.88),(4.12,1.015,-.79,.93),(4.37,1.045,-.765,.95),(4.62,1.04,-.735,.96),(4.87,1.03,-.75,.95),(5.12,1.015,-.79,.94),(5.42,1.01,-.78,.93),(5.67,.93,-.71,.85),(5.89,.70,-.51,.64),(6.06,.35,-.22,.35),(6.12,.008,.07,.09)]
NOSE=[(3.83,0,.12),(3.90,.10,.17),(3.975,.31,.185),(4.055,.43,.17),(4.13,.40,.145),(4.28,.29,.12),(4.48,.20,.115),(4.70,.11,.13),(4.91,0,.16)]

def face_y(x,z):
 w=interp(HEAD,z);f=interp(HEAD,z,2);b=interp(HEAD,z,3);cy=(f+b)/2;dep=(b-f)/2
 power=2+.40*exp(-((z-4.65)/.42)**2)+.15*exp(-((z-4.15)/.30)**2)
 y=cy-dep*max(0,1-(abs(x)/max(w,.01))**power)**(1/power)
 y-=.075*gauss(x,z,0,3.35,.37,.20)
 y-=.042*gauss(x,z,0,3.61,.38,.22)
 for s in [-1,1]:
  y-=.061*gauss(x,z,s*.62,4.23,.32,.23)
  y-=.025*gauss(x,z,s*.44,4.49,.30,.125)
  y+=.018*gauss(x,z,s*.46,4.66,.34,.18)
  y-=.068*gauss(x,z,s*.45,4.94,.39,.14)
 y-=CFG.get('nose_depth',1.0)*interp(NOSE,z)*exp(-(x/interp(NOSE,z,2))**2)
 for s in [-1,1]:y-=.078*gauss(x,z,s*.173,3.987,.090,.062)
 y-=.027*gauss(x,z,0,4.047,.125,.094)+.019*gauss(x,z,0,3.964,.046,.046)
 y-=.02*(gauss(x,z,-.059,3.80,.025,.09)+gauss(x,z,.059,3.80,.025,.09))
 return y

def complexion(x,z):
 base=rgb(CFG.get('skin','E8B5A0'));blush=rgb('D88F87');nosecol=rgb('E0A18D')
 k=.34*sum(gauss(x,z,s*.64,4.22,.28,.22) for s in [-1,1]);k+=.16*gauss(x,z,0,4.04,.24,.11)
 color=tuple(base[i]*(1-k)+blush[i]*k for i in range(3))
 t=(abs(x)-.15)/.60
 if 0<t<1:
  center=4.958+.044*sin(t*pi*.92)-.025*t;shade=.20*exp(-((z-center)/.037)**2)*sin(pi*t)**.35;root=rgb('73584C');color=tuple(color[i]*(1-shade)+root[i]*shade for i in range(3))
 return color

# Constrained triangulation in the frontal (theta, z) parameter domain.
# Both eye loops are actual holes. Their outer lid vertices will be welded into this face mesh.
NU=144;M=170;NLOOP=128
polygons=[]
for sign in [-1,1]:
 polygon=[]
 for k in range(NLOOP):
  th=2*pi*k/NLOOP;q=CFG.get('eye_width',.245)*cos(th);h=(CFG.get('eye_up',.112) if sin(th)>0 else CFG.get('eye_low',.088))*sin(th)*abs(sin(th))**.85
  oq=q*(1.29+.03*sin(th));oh=h*(1.8 if h>0 else 1.95);x=sign*CFG.get('eye_x',.445)+oq;z=CFG.get('eye_z',4.66)+oh+.038*sign*oq
  polygon.append((math.asin(x/interp(HEAD,z)),z))
 polygons.append(polygon)
for sign in [-1,1]:
 polygon=[]
 for k in range(48):
  th=2*pi*k/48;x=sign*.137+.036*cos(th);z=3.951+.0115*sin(th)-sign*.16*(x-sign*.137)
  polygon.append((math.asin(x/interp(HEAD,z)),z))
 polygons.append(polygon)
bounds=[(min(v[0] for v in poly),max(v[0] for v in poly),min(v[1] for v in poly),max(v[1] for v in poly)) for poly in polygons]
def inside_eye(point):
 x,z=point
 for poly,box in zip(polygons,bounds):
  if not(box[0]<=x<=box[1] and box[2]<=z<=box[3]):continue
  inside=False;last=poly[-1]
  for current in poly:
   if (current[1]>z)!=(last[1]>z) and x<(last[0]-current[0])*(z-current[1])/(last[1]-current[1])+current[0]:inside=not inside
   last=current
  if inside:return True
 return False
points=[];edges=[]
for j in range(M+1):
 z=3.10+(6.12-3.10)*j/M
 for k in range(NU+1):
  point=(-pi/2+pi*k/NU,z)
  if not inside_eye(point):points.append(Vector(point))
for poly in polygons:
 start_index=len(points);points.extend(Vector(point) for point in poly)
 edges.extend((start_index+k,start_index+(k+1)%len(poly)) for k in range(len(poly)))
print('TRIANGULATING ORIGINAL FACE',len(points),'points',flush=True)
result=delaunay_2d_cdt(points,edges,[],0,0.000001,False)
vs=[];fs=[];cols=[]
for th,z in result[0]:
 x=interp(HEAD,z)*sin(th);vs.append((x,face_y(x,z),z));cols.append(complexion(x,z))
for face in result[2]:
 center=sum((result[0][i] for i in face),Vector((0,0)))/len(face)
 if not inside_eye(center):fs.append(tuple(face))
offset=len(vs)
for j in range(M+1):
 z=3.10+(6.12-3.10)*j/M;w=interp(HEAD,z);fr=interp(HEAD,z,2);ba=interp(HEAD,z,3)
 for k in range(NU+1):
  th=pi/2+pi*k/NU;x=w*sin(th);y=(fr+ba)/2-(ba-fr)/2*cos(th);vs.append((x,y,z));cols.append(rgb(CFG.get('skin','E8B5A0')))
for j in range(M):
 for k in range(NU):
  q=offset+j*(NU+1)+k;fs.append((q,q+1,q+NU+2,q+NU+1))
head=mesh('Face | original continuous orbital topology, nose and jaw',vs,fs,skin,True,cols)
# Mild lower face refinement remains in the continuous mesh, not a stack of primitives.

# Eyes: almond scleral patches with spherical depth, continuous sculpted skin lids.
EYEZ=CFG.get('eye_z',4.66);EYEX=CFG.get('eye_x',.445);EYER=CFG.get('eye_radius',.275);EYEY=CFG.get('eye_y',-.49);EW=CFG.get('eye_width',.315);UP=CFG.get('eye_up',.133);LOW=CFG.get('eye_low',.101)
def eyeco(s,q,h,extra=0):
 x=s*EYEX+q;z=EYEZ+h+.038*s*q
 y=EYEY-EYER+.078*(q/EW)**2+.026*(h/.12)**2+.16*s*q-.012*exp(-((((q-CFG.get('iris_look',-.010))**2+(h-.012)**2)/.020)**2))-extra
 return (x,y,z)
def eye_boundary(th):
 q=EW*cos(th);h=(UP if sin(th)>0 else LOW)*sin(th)*(abs(sin(th))**.85)
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
 sclera_colors=[]
 for point in v:
  q=point[0]-s*EYEX;k=.48*(min(1,abs(q/EW))**5);a=rgb('EEE1D8');b=rgb('D9A095');sclera_colors.append(tuple(a[j]*(1-k)+b[j]*k for j in range(3)))
 mesh('Eye '+side+' | spherical almond sclera',v,f,white,True,sclera_colors,'ScleraTint')
 # Real radial iris surface, no photograph or generated texture.
 v=[];f=[];c=[];IR=CFG.get('iris_radius',.112);PUP=.050
 for r in range(15):
  rad=IR*r/14
  for k in range(144):
   th=2*pi*k/144;q=rad*cos(th)+CFG.get('iris_look',-.010);h=rad*sin(th)+.012
   limit=max(0,1-(q/EW)**2)**.925;h=max(-LOW*limit+.00015,min(UP*limit-.00015,h))
   v.append(eyeco(s,q,h,.004))
   if rad<PUP*.96:color=rgb('0B0908')
   else:
    phase=.5+.23*sin(th*41+.4*sin(th*11))+.14*sin(th*77+rad*230)+.1*sin(th*113-rad*90)
    strength=(.26+.48*phase)*(1-.6*exp(-((rad-IR)/.009)**2))
    inner=exp(-((rad-.066)/.018)**2)
    color=tuple(lin(min(.85,vv*strength)) for vv in (.38+.06*inner,.245+.02*inner,.166))
   c.append(color)
 for r in range(14):
  for k in range(144):f.append((r*144+k,r*144+(k+1)%144,(r+1)*144+(k+1)%144,(r+1)*144+k))
 mesh('Eye '+side+' | 144-ray brown iris and pupil',v,[tuple(reversed(face)) for face in f],irismat,True,c,'IrisPigment')
 # Lid tissue lofts into underlying anatomical face. Outer vertices meet face exactly.
 v=[];f=[];c=[]
 for r in range(9):
  t=r/8
  for k in range(128):
   th=2*pi*k/128;q,h=eye_boundary(th);ix,iy,iz=eyeco(s,q,h,.007)
   oq=q*(1.29+.03*sin(th));oh=h*(1.8 if h>0 else 1.95);ox=s*EYEX+oq;oz=EYEZ+oh+.038*s*oq;oy=face_y(ox,oz)
   x=ix*(1-t)+ox*t;z=iz*(1-t)+oz*t;y=iy*(1-t)+oy*t-.003*sin(pi*t)
   v.append((x,y,z));base=complexion(x,z);warm=rgb('DCA18F');blend=.15*(1-t)
   c.append(tuple(base[j]*(1-blend)+warm[j]*blend for j in range(3)))
 for r in range(8):
  for k in range(128):f.append((r*128+k,r*128+(k+1)%128,(r+1)*128+(k+1)%128,(r+1)*128+k))
 mesh('Eye '+side+' | upper and lower anatomical lids',v,[tuple(reversed(face)) for face in f],skin,True,c)
 for upper in [True,False]:
  pts=[]
  for k in range(65):
   th=pi*k/64 if upper else pi+pi*k/64;q,h=eye_boundary(th);pts.append(eyeco(s,q,h,.010))
  tube('Eye '+side+(' | upper lash roots' if upper else ' | lower waterline'),pts,.0045 if upper else .0035,lashmat if upper else waterline,True,6,False)
 # A fine orbital fold lies directly on the upper-lid tissue surface.
 pts=[]
 for k in range(48):
  th=pi*(.10+.80*k/47);q,h=eye_boundary(th);ix,iy,iz=eyeco(s,q,h,.007);oq=q*(1.29+.03*sin(th));oh=h*1.8;ox=s*EYEX+oq;oz=EYEZ+oh+.038*s*oq;oy=face_y(ox,oz);t=.56
  pts.append((ix*(1-t)+ox*t,iy*(1-t)+oy*t-.003*sin(pi*t)-.0015,iz*(1-t)+oz*t))
 tube('Eye '+side+' | delicate upper fold',pts,.0022,crease,True,5)
 # Individual lashes are fine, not a solid strip.
 for k in range(45):
  u=-.94+1.88*(k+random.random()*.75)/45;q=EW*u;h=UP*(sqrt(max(0,1-u*u))**1.85);p=Vector(eyeco(s,q,h,.015));le=.022+.021*(.5+.5*u*s)
  tube('Lash '+side+str(k),[p,p+Vector((u*.014,-.025,.008)),p+Vector((u*.031,-.045,le))],random.uniform(.0010,.0016),lashmat,True,4,True,8)
 for k in range(17):
  u=-.8+1.6*(k+random.random()*.7)/17;q=EW*u;h=-LOW*(sqrt(1-u*u)**1.85);p=Vector(eyeco(s,q,h,.010))
  tube('Lower lash '+side+str(k),[p,p+Vector((u*.014,-.016,-.018)),p+Vector((u*.025,-.020,-.019))],random.uniform(.0007,.0011),browmat,True,4,True,7)
 # Catchlights are small pieces of 3D corneal geometry, not image dots.
 for q,h,rr in [(-.029,.035,.008),(.030,-.024,.003)]:
  loc=eyeco(s,q,h,.012);sphere('Eye '+side+' | corneal catchlight',loc,(rr,.003,rr*.8),catchmat,True,20,12)
 # Brows composed of hundreds of thin original hairs with a soft root silhouette.
 for k in range(340):
  t=random.random();x=s*(.15+.60*t);z=4.958+.044*sin(t*pi*.92)-.025*t+random.uniform(-.024,.023);y=face_y(x,z)-.012
  le=random.uniform(.019,.037);dx=s*(.021+.029*t)
  end=(x+dx,y-.008,z+le*(1-.7*t))
  tube('Brow '+side+f' | hair {k:03d}',[(x,y,z),(x+dx*.45,y-.008,z+le*.6),end],random.uniform(.0008,.0014),browmat,True,4,True,6)
# Genuine recessed nostril chambers, continuous with the cut facial openings.
for sign in [-1,1]:
 v=[];f=[]
 for j in range(5):
  t=j/4
  for k in range(48):
   th=2*pi*k/48;x=sign*.137+.036*cos(th)*(1-.13*t);z=3.951+.0115*sin(th)*(1-.13*t)-sign*.16*(x-sign*.137);y=face_y(x,z)+.055*t;z+=.010*t
   v.append((x,y,z))
 for j in range(4):
  for k in range(48):f.append((j*48+k,j*48+(k+1)%48,(j+1)*48+(k+1)%48,(j+1)*48+k))
 f.append(tuple(4*48+k for k in range(48)))
 mesh('Nostril | inset anatomical chamber '+str(sign),v,f,nose_dark,True)
 pts=[]
 for k in range(26):
  t=k/25;x=sign*(.213+.023*sin(pi*t));z=4.027-.073*t;pts.append((x,face_y(x,z)-.001,z))
 tube('Nose | subtle alar fold '+str(sign),pts,.0016,crease,True,5)
# Lip surfaces with cupid bow and soft integration into surrounding skin.
MW=CFG.get('mouth_width',.278);MZ=CFG.get('mouth_z',3.625)
def mouthline(u):return MZ-.012*abs(u)+.007*cos(u*pi)
def upperlip(u):return (1-u*u)**.75*(.055+.014*exp(-((abs(u)-.34)/.23)**2)-.006*exp(-(u/.16)**2))
def lowerlip(u):return .098*(max(0,1-u*u)**.80)
lip_surfaces=[]
for source in [lip,lip_light]:
 m=source.copy();m.name=source.name+' | feathered edge';nt=m.node_tree;vc=nt.nodes.new('ShaderNodeVertexColor');vc.layer_name='LipTint';nt.links.new(vc.outputs['Color'],nt.nodes.get('Principled BSDF').inputs['Base Color']);lip_surfaces.append(m)
for top in [True,False]:
 vs=[];fs=[];colors=[]
 for i in range(81):
  u=-1+2*i/80;x=MW*u;line=mouthline(u);extent=upperlip(u) if top else -lowerlip(u)
  for j in range(11):
   t=j/10;z=line+extent*t;edge=face_y(x,z)-.007
   bulge=(.070 if top else .084)*sin(pi*t*.92)*(max(0,1-u*u)**.6)+.021*(1-t)*(1-u*u)
   vs.append((x,edge-bulge,z))
   blend=max(0,(t-.65)/.35)**.6;sc=complexion(x,z);lc=rgb('BC7975' if top else 'D38D84');colors.append(tuple(lc[k]*(1-blend)+sc[k]*blend for k in range(3)))
 for i in range(80):
  for j in range(10):q=i*11+j;fs.append((q,q+11,q+12,q+1))
 mesh('Mouth | '+('sculpted cupid bow' if top else 'soft lower lip'),vs,fs if top else [tuple(reversed(face)) for face in fs],lip_surfaces[0 if top else 1],True,colors,'LipTint')
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
NECK=[(1.73,.82,-.40,.42),(1.96,.77,-.34,.44),(2.19,.65,-.28,.40),(2.42,.48,-.27,.36),(2.77,.43,-.24,.345),(3.13,.42,-.225,.35),(3.48,.44,-.20,.36),(3.64,.39,-.12,.35)]
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
sys.path.insert(0,str(ROOT/'src'))
from garment_surface import create_garment_surface
garment_width,shirt_y=create_garment_surface(TORSO,interp,gauss)
v=[];f=[];NN=224;MM=150
for j in range(MM+1):
 z=-.14+2.94*j/MM;w=garment_width(z);fr=interp(TORSO,z,2);ba=interp(TORSO,z,3)
 opening=.44*max(0,(z-1.90)/.90);theta0=math.asin(min(.98,opening/w))
 for k in range(NN+1):
  th=theta0+(2*pi-2*theta0)*k/NN;x=w*sin(th);y=shirt_y(x,z,front=cos(th)>0)
  if cos(th)<=0:y+=.006*sin(15*z+3*x)
  v.append((x,y,z))
for j in range(MM):
 for k in range(NN):f.append((j*(NN+1)+k,j*(NN+1)+k+1,(j+1)*(NN+1)+k+1,(j+1)*(NN+1)+k))
f.append(tuple(range(NN,-1,-1)))
ob=mesh('Shirt | tailored closed torso with open neckline',v,f,shirt);mod=ob.modifiers.new('Cotton thickness','SOLIDIFY');mod.thickness=.014
# Stitching follows the continuous torso-and-sleeve surface.
for sign in [-1,1]:
 points=[]
 for k in range(44):
  t=k/43;z=2.33-.88*t;x=sign*(1.46+.12*sin(pi*t));points.append((x,shirt_y(x,z)-.003,z))
 tube('Shirt | tailored sleeve seam '+str(sign),points,.0035,seammat,False,5)
# Folded collar leaves, softly curved four-sided textile surfaces.
def collar_patch(s):
 A=Vector((s*.43,-.23,2.75));B=Vector((s*.64,-.23,2.55));C=Vector((s*.78,-.45,1.99));D=Vector((s*.19,-.50,2.10))
 v=[];f=[]
 for i in range(21):
  u=i/20
  for j in range(21):
   t=j/20;p=(1-t)*((1-u)*A+u*B)+t*((1-u)*D+u*C)
   p.y-=.075*sin(pi*u)*sin(pi*t);p.z+=.045*sin(pi*u)*sin(pi*t)
   v.append(tuple(p))
 for i in range(20):
  for j in range(20):q=i*21+j;f.append((q,q+21,q+22,q+1))
 ob=mesh('Collar | folded cotton leaf '+str(s),v,[tuple(reversed(face)) for face in f] if s>0 else f,shirt);mod=ob.modifiers.new('Collar cloth thickness','SOLIDIFY');mod.thickness=.023
 smooth(ob,1)
 # Restrained perimeter stitching, mostly covered by the falling hair.
 tube('Collar | edge stitching '+str(s),[D+Vector((s*.02,-.007,.012)),C+Vector((-s*.02,-.007,.017)),B+Vector((-s*.015,-.01,-.018))],.0035,seammat,False,5,False,52)
collar_patch(-1);collar_patch(1)
# Collar stand wraps fully around the back of the neck.
v=[];f=[]
for j in range(2):
 for k in range(97):
  th=1.20+(2*pi-2.40)*k/96;z=2.70+.03*cos(th)+j*.12;v.append((.485*sin(th),.04-.31*cos(th),z))
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
# Original ivory button at the open collar.
bpy.ops.mesh.primitive_cylinder_add(vertices=32,radius=.044,depth=.014,location=(.435,-.335,2.48),rotation=(pi/2+.12,0,-.10))
ob=bpy.context.object;ob.name='Collar | ivory neck-opening button';put(ob);ob.data.materials.append(buttonmat)
bevel=ob.modifiers.new('Soft collar button rim','BEVEL');bevel.width=.006;bevel.segments=3
print('CLOTHING BUILT',flush=True)

# Hair. A closed scalp shell supports layered, volumetric swept locks.
# Every fiber below is authored 3D geometry; no cards, scanned hair, or photo textures.
def scalp_point(th,t):
 bottom=(4.83+.79*max(0,cos(th))**.40) if cos(th)>=0 else (4.83-.90*(-cos(th))**.8);z=6.205-(6.205-bottom)*t**.84+(.008*sin(37*th)+.005*sin(83*th))*min(1,t)**10;hz=min(6.118,z-.060)
 w=interp(HEAD,hz)+.056;fr=interp(HEAD,hz,2)-.075;ba=interp(HEAD,hz,3)+.064
 return Vector((w*sin(th)+.16*(1-min(1,t))**3,(fr+ba)/2-(ba-fr)/2*cos(th),z))
v=[];f=[];HS=192;HR=64
for j in range(HR+1):
 for k in range(HS):v.append(tuple(scalp_point(2*pi*k/HS,j/HR)))
for j in range(HR):
 for k in range(HS):f.append((j*HS+k,j*HS+(k+1)%HS,(j+1)*HS+(k+1)%HS,(j+1)*HS+k))
mesh('Hair | nonintersecting original scalp foundation',v,[tuple(reversed(face)) for face in f],hairmats[0],True)
# Crown fibers sit on the actual scalp surface, never on an approximate ellipsoid.
for k in range(680):
 angle=2*pi*(k+.27)/680;pts=[]
 for j in range(48):
  t=.012+.998*j/47;th=angle+.28*sin(pi*min(1,t))*(1-min(1,t));point=scalp_point(th,t);normal=Vector((point.x,point.y-.04,max(.04,point.z-4.7)*.7)).normalized();point+=normal*.006;pts.append(point)
 tube('Hair fiber | crown meridian %04d'%k,pts,random.uniform(.0012,.0019),fibermats[random.choice([0,0,1,1,3])],True,4)
# Original tiny hairs soften the forehead transition without any alpha texture.
for k in range(180):
 angle=-1.08+2.16*(k+random.random())/180;points=[]
 for j in range(12):
  point=scalp_point(angle,.89+.11*j/11);point+=Vector((0,-.004,0));points.append(point)
 tip=points[-1];length=random.uniform(.022,.064);points.extend([tip+Vector((-.014,-.004,-length*.52)),tip+Vector((-.020,-.004,-length))])
 tube('Hair fiber | natural fine hairline %03d'%k,points,random.uniform(.0006,.0010),fibermats[random.choice([0,1,3])],True,3)
# Back hair volume is closed around the ends; fine locks live above this surface.
v=[];f=[];HC=96;HZ=60
for layer in [0,1]:
 for j in range(HZ+1):
  t=j/HZ
  for k in range(HC+1):
   th=1.25+(4.78-1.25)*k/HC;bottom=.96+.16*cos(2*th)+.035*sin(11*th);z=4.57+(bottom-4.57)*t
   wid=1.14+.16*sin(pi*t)-.17*t**5;dep=.99-.23*t
   x=(wid-.065*layer)*sin(th);y=.10-(dep-.065*layer)*cos(th);v.append((x,y,z))
S=(HZ+1)*(HC+1)
for layer in [0,1]:
 for j in range(HZ):
  for k in range(HC):
   q=layer*S+j*(HC+1)+k;face=(q,q+1,q+HC+2,q+HC+1);f.append(tuple(reversed(face)) if layer==0 else face)
for j in range(HZ):
 for k in [0,HC]:
  q=j*(HC+1)+k;f.append((q,q+HC+1,q+HC+1+S,q+S))
for k in range(HC):
 q=HZ*(HC+1)+k;f.append((q,q+S,q+1+S,q+1))
mesh('Hair | full back volume and closed ends',v,f,hairmats[0],True)

FIBERS=CFG.get('fibers_per_lock',11)
def lock(name,points,width,depth=.035,fibers=FIBERS,mati=0):
 ps=sample(points,56)
 # Project into a continuous skull-to-hair envelope, with no hard height transition.
 for point in ps:
  fine=('wisp' in name or 'fringe' in name or 'cheek frame' in name);clearance=.039 if fine else .115
  hz=min(6.112,max(3.2,point.z-.065));wh=interp(HEAD,hz)+clearance;fr=interp(HEAD,hz,2)-(.036 if fine else .140);ba=interp(HEAD,hz,3)+clearance;cyh=(fr+ba)/2;rh=(ba-fr)/2
  if name.startswith('rear curtain'):
   t=max(0,min(1,(4.57-point.z)/3.85));wb=1.14+.16*sin(pi*t)-.17*t**5+.067;rb=.99-.23*t+.060;a=max(0,min(1,(4.98-point.z)/.72));a=a*a*(3-2*a);w=wh*(1-a)+wb*a;ry=rh*(1-a)+rb*a;cy=cyh*(1-a)+.10*a;weight=1
  else:
   w=wh;ry=rh;cy=cyh;weight=max(0,min(1,(point.z-4.05)/.75));weight=weight*weight*(3-2*weight)
  if weight>0:
   distance=sqrt((point.x/w)**2+((point.y-cy)/ry)**2)
   if distance>.02:
    need=1/distance;scale=.5*(1+need+sqrt((1-need)**2+.00020));scale=1+(scale-1)*weight;point.x*=scale;point.y=cy+(point.y-cy)*scale
 for _ in range(2):ps=[ps[0]]+[(ps[i-1]+2*ps[i]+ps[i+1])/4 for i in range(1,len(ps)-1)]+[ps[-1]]
 v=[];f=[];frames=[];old=None
 for i,p in enumerate(ps):
  t=i/(len(ps)-1);tangent=(ps[min(len(ps)-1,i+1)]-ps[max(0,i-1)]).normalized()
  normal=Vector((p.x*.46,p.y-.12,max(.03,p.z-5.08)*.66)).normalized()
  side=tangent.cross(normal).normalized();normal=side.cross(tangent).normalized()
  if old is not None and side.dot(old)<0:side=-side;normal=-normal
  old=side
  taper=(.48+.52*sin(min(1,t*1.35)*pi/2))*(max(.0008,1-t**4)**.80)
  wi=width*taper;di=depth*(.50+.50*sin(pi*t))*(max(.03,1-t**6)**.65)
  frames.append((p,side,normal,wi,di))
  for j in range(10):
   th=2*pi*j/10;v.append(tuple(p+side*(wi*cos(th))+normal*(di*sin(th))))
  if i:
   for j in range(10):f.append(((i-1)*10+j,(i-1)*10+(j+1)%10,i*10+(j+1)%10,i*10+j))
 f.append(tuple(range(9,-1,-1)));f.append(tuple((len(ps)-1)*10+j for j in range(10)))
 mesh('Hair lock | '+name,v,[tuple(reversed(face)) for face in f],hairmats[mati],True)
 for k in range(fibers):
  off=-.92+1.84*(k+.5)/fibers;phase=random.random()*6.28;pts=[]
  for i,(p,side,n,wi,di) in enumerate(frames):
   t=i/(len(frames)-1);wav=.0019*sin(phase+t*35)*sin(pi*t);q=p+side*(off*wi+wav)+n*(di*sqrt(max(0,1-off*off))+.002)
   pts.append(q)
  tube('Hair fiber | '+name+' '+str(k),pts,random.uniform(.0013,.0023)*(.43 if ('wisp' in name or 'fringe' in name) else 1),fibermats[random.choices([0,1,2,3,4],[.16,.37,.21,.23,.03])[0]],True,4)
# Back and side curtain, descending from crown around the whole skull.
for k in range(66):
 th=1.15+(4.79-1.15)*k/65;st=sin(th);ct=cos(th);jitter=random.uniform(-.035,.035);bottom=random.uniform(.44,1.00)+.13*ct
 points=[(.18+.08*st,.08-.13*ct,6.16),(.80*st,-.73*ct+.10,5.81),(1.095*st,-.95*ct+.10,4.93),(1.135*st,-.94*ct+.10,3.99),(1.24*st,-.84*ct+.09,3.13),(1.28*st+.055*sin(k*.8),-.82*ct+.07,2.37),(1.40*st+.04*sin(k),-.78*ct,1.51),(1.25*st+.05*sin(k),-.73*ct-.02,bottom)]
 lock('rear curtain %02d'%k,points,.080+random.random()*.040,.032,8,random.choice([0,0,1,3]))
# Prominent long front layers, separately sculpted on each side.
for s in [-1,1]:
 for k in range(30):
  t=k/29;ofs=(t-.5)*.78
  if s<0:
   points=[(.19-.04*t,-.18-.13*t,6.16-.025*t),(-.36,-.57-.03*t,6.09-.12*t),(-.88,-.68-.03*t,5.60-.23*t),(-1.10+ofs*.2,.015-.04*t,4.82),(-1.10+ofs*.35,.09-.06*t,3.86),(-1.13+ofs*.55,-.48-.18*t,2.91),(-1.20+ofs,-.58-.16*t,2.13),(-1.45+ofs*.8,-.64-.13*t,1.26),(-1.52+ofs*.5,-.66-.12*t,.74),(-1.02+ofs*.76,-.65-.08*t,-.03+.39*t+.055*sin(k*1.6))]
  else:
   points=[(.23+.04*t,-.17-.12*t,6.15-.02*t),(.71,-.57-.05*t,5.93-.06*t),(1.045,-.62-.03*t,5.24),(1.08+ofs*.1,-.42-.09*t,4.42),(1.11+ofs*.3,-.34-.10*t,3.55),(1.23+ofs*.55,-.47-.12*t,2.77),(1.37+ofs,-.61-.16*t,2.12),(1.55+ofs*.8,-.66-.13*t,1.49),(1.46+ofs*.8,-.69-.14*t,.94),(.96+ofs*.82,-.63-.1*t,.18+.32*t+.08*sin(k*1.3))]
  for j,point in enumerate(points):
   if point[2]<3.1:
    u=max(0,min(1,(3.1-point[2])/3.25));wave=.11*sin(pi*u)*sin(2*pi*u+k*.23);points[j]=(point[0]+s*wave,point[1]+.035*sin(pi*u)*sin(2*pi*u+k*.17),point[2])
  lock(('left' if s<0 else 'right')+' front fall %02d'%k,points,.055+random.random()*.035,.027,14,random.choice([0,1,1,3]))
# Short crown sweeps follow the off-center part and tuck behind the left ear.
for sgn in [-1,1]:
 for k in range(38):
  t=k/37
  if sgn<0:
   points=[(.22,.32-.81*t,6.19-.035*t),(-.22-.09*t,-.24-.58*t,6.10-.23*t),(-.69,-.32-.50*t,5.82-.44*t),(-1.04,-.17-.35*t,5.21-.37*t),(-1.11,.10-.035*t,4.53+.23*t)]
  else:
   points=[(.25,.32-.82*t,6.18-.025*t),(.63,-.20-.56*t,6.02-.19*t),(1.01,-.19-.53*t,5.58-.38*t),(1.14,-.10-.31*t,4.80-.20*t)]
  lock(('left' if sgn<0 else 'right')+' crown sweep %02d'%k,points,.036+random.random()*.012,.018,8,random.choice([0,0,1,3]))
# Wispy separate bangs: many narrow original bundles, not a few broad cards.
for k in range(14):
 t=k/13
 points=[(.22+.17*t,-.54+.05*t,6.06-.045*t),(.10-.14*t,-.80-.014*t,5.70-.085*t),(-.07-.23*t,-.846-.010*t,5.29-.10*t),(-.17-.39*t+.015*sin(k),-.87+.05*t,4.91+.09*sin(k*1.8)**2)]
 lock('wispy swept fringe %02d'%k,points,random.uniform(.0025,.0045),.0025,3,random.choice([0,0,1,3]))
for k in range(7):
 t=k/6
 points=[(.36+.025*t,-.67,5.94),(.43-.05*t,-.828,5.56),(.38-.085*t,-.857,5.20),(.22-.11*t,-.879,4.93+.14*t)]
 lock('central separated wisp %02d'%k,points,random.uniform(.0025,.0032),.002,3,0)
# A few thin face-framing pieces soften the edge near the left ear.
for k in range(5):
 t=k/4
 points=[(-.52-.08*t,-.84,5.63),(-.74-.07*t,-.93,5.22),(-.93-.04*t,-.84,4.63),(-1.00-.02*t,-.63,4.05),(-.96+.03*t,-.55,3.63)]
 lock('fine cheek frame %02d'%k,points,.008,.006,4,1)
# Irregular flyaways follow original guide splines and are intentionally restrained.
for k in range(65):
 s=random.choice([-1,1]);z=random.uniform(3.2,5.8);x=s*(1.09+.055*sin(z*3));y=random.uniform(-.45,.12)
 points=[(x,y,z),(x+s*.09,y-.035,z-.20),(x+s*.13,y-.02,z-.49),(x+s*.10,y+.01,z-.75)]
 tube('Hair | flyaway %03d'%k,points,random.uniform(.0008,.0013),fibermats[random.choice([1,3])],True,3,True,22)
# Narrow natural scalp part, almost entirely occluded by roots.
partmat=mat('Hair part | shaded scalp','72554A',.70)
tube('Hair | narrow off-center scalp part',[(.19,.42,6.105),(.22,.20,6.168),(.25,-.05,6.175),(.27,-.28,6.124),(.29,-.48,6.045)],.0045,partmat,True,6,True,48)
print('HAIR BUILT',flush=True)
# The upper cranium is fuller than the initial blockout; the face itself is unchanged.
for ob in head_objs:
 if ob.type=='MESH':
  for vertex in ob.data.vertices:
   if vertex.co.z>5.30:vertex.co.z+=CFG.get('crown_fullness',.34)*((vertex.co.z-5.30)/.905)**2
 if ob.name.startswith('Ear'):
  meanx=ob.location.x+sum(v.co.x for v in ob.data.vertices)/len(ob.data.vertices)*ob.scale.x;ob.location.x+=(.055 if meanx>0 else -.055);ob.location.y-=.018
for ob in head_objs:
 if ob.name.startswith('Ear'):
  mean_x=ob.matrix_world.translation.x+sum(v.co.x for v in ob.data.vertices)/len(ob.data.vertices)*ob.scale.x
  sign=1 if mean_x>0 else -1
  pivot=Vector((sign*1.07,.035,4.40))
  transform=Matrix.Translation(pivot)@Matrix.Rotation(sign*.34,4,'Z')@Matrix.Translation(-pivot)
  ob.matrix_world=transform@ob.matrix_world
# Pose is applied coherently to the complete head, ears, lids and hair.
root=bpy.data.objects.new('Head pose | soft reference tilt',None);CHAR.objects.link(root);root.location=(0,0,3.72)
bpy.context.view_layer.update()
for ob in head_objs:
 matrix=ob.matrix_world.copy();ob.parent=root;ob.matrix_parent_inverse=root.matrix_world.inverted();ob.matrix_world=matrix
root.rotation_euler.y=CFG.get('head_tilt',.095);root.rotation_euler.z=CFG.get('head_turn',.015)

body_root=bpy.data.objects.new('Body pose | gentle counter-lean',None);CHAR.objects.link(body_root);body_root.location=(0,0,2.85);bpy.context.view_layer.update()
for ob in list(CHAR.objects):
 if ob.type=='MESH' and ob.parent is None:
  matrix=ob.matrix_world.copy();ob.parent=body_root;ob.matrix_parent_inverse=body_root.matrix_world.inverted();ob.matrix_world=matrix
body_root.rotation_euler.y=CFG.get('body_tilt',-.055)

# Batch original geometry without changing its appearance. The procedural source retains every guide.
bpy.context.view_layer.update()
authored_object_count=len(CHAR.objects)
groups={}
for ob in list(CHAR.objects):
 if ob.type=='MESH' and len(ob.data.materials)==1:
  groups.setdefault((ob.data.materials[0].name,ob.parent.name if ob.parent else ''),[]).append(ob)
for key,objects in groups.items():
 if len(objects)<2:continue
 bpy.ops.object.select_all(action='DESELECT')
 for ob in objects:
  bpy.context.view_layer.objects.active=ob
  for modifier in list(ob.modifiers):bpy.ops.object.modifier_apply(modifier=modifier.name)
  ob.select_set(True)
 bpy.context.view_layer.objects.active=objects[0];bpy.ops.object.join();objects[0].name='Batched | '+key[0]
 if key[0]==skin.name:
  bm=bmesh.new();bm.from_mesh(objects[0].data);bmesh.ops.remove_doubles(bm,verts=list(bm.verts),dist=.00006);bmesh.ops.recalc_face_normals(bm,faces=list(bm.faces));bm.normal_update();bm.to_mesh(objects[0].data);bm.free();objects[0].data.update()
  print('Continuous face and lid boundaries welded',flush=True)
print('GEOMETRY BATCHED',authored_object_count,'to',len(CHAR.objects),flush=True)

# Studio is independent of the character export.
bg=mat('STUDIO | warm charcoal backdrop','282525',.92)
bpy.ops.mesh.primitive_plane_add(size=200,location=(0,3.1,3),rotation=(pi/2,0,0));ob=bpy.context.object;ob.name='Studio seamless backdrop';put(ob,stage=True);ob.data.materials.append(bg);backdrop=ob
nt=bg.node_tree;nt.nodes.clear();out=nt.nodes.new('ShaderNodeOutputMaterial');em=nt.nodes.new('ShaderNodeEmission');uv=nt.nodes.new('ShaderNodeTexCoord');sub=nt.nodes.new('ShaderNodeVectorMath');sub.operation='SUBTRACT';sub.inputs[1].default_value=(.497,.507,0);nt.links.new(uv.outputs['UV'],sub.inputs[0]);mul=nt.nodes.new('ShaderNodeVectorMath');mul.operation='MULTIPLY';mul.inputs[1].default_value=(100,100,0);nt.links.new(sub.outputs['Vector'],mul.inputs[0]);length=nt.nodes.new('ShaderNodeVectorMath');length.operation='LENGTH';nt.links.new(mul.outputs['Vector'],length.inputs[0]);ramp=nt.nodes.new('ShaderNodeValToRGB');ramp.color_ramp.elements[0].position=0;ramp.color_ramp.elements[0].color=(*rgb('514442'),1);ramp.color_ramp.elements[1].position=1.45;ramp.color_ramp.elements[1].color=(*rgb('08090A'),1);nt.links.new(length.outputs['Value'],ramp.inputs['Fac']);nt.links.new(ramp.outputs['Color'],em.inputs['Color']);nt.links.new(em.outputs[0],out.inputs['Surface'])
def area(name,loc,target,power,size,color,size_y=None):
 data=bpy.data.lights.new(name,'AREA');data.energy=power;data.color=color;data.shape='DISK' if size_y is None else 'RECTANGLE';data.size=size
 if size_y:data.size_y=size_y
 ob=bpy.data.objects.new(name,data);STAGE.objects.link(ob);ob.location=loc;ob.rotation_euler=(Vector(target)-ob.location).to_track_quat('-Z','Y').to_euler();data.use_shadow=True
area('Key | large soft portrait window',(-3.5,-5.3,7.0),(0,0,4),CFG.get('key_power',950),4.0,(1.0,.89,.82))
area('Fill | cool frontal silk',(3.5,-4.2,4.7),(0,0,3.8),CFG.get('fill_power',330),3.4,(.84,.90,1.0))
area('Hair rim | cool high strip',(2.8,1.2,7.2),(0,0,4.3),360,2.6,(.88,.91,1.0),1.7)
area('Hair separation | warm left',(-3.1,1.0,5.5),(0,0,3.7),260,2.6,(1,.81,.71),3.2)
area('Eye card | subtle frontal catchlight',(-.9,-5.1,5.4),(0,-.5,4.5),55,1.0,(1,.97,.91),.6)
# Typography is real Blender text placed above the character.
titlemat=mat('Studio typography | warm silver','BABCB2',.70)
def textline(name,text,z,size):
 curve=bpy.data.curves.new(name,'FONT');curve.body=text;curve.align_x='CENTER';curve.size=size;curve.space_character=1.15;curve.extrude=0
 ob=bpy.data.objects.new(name,curve);STAGE.objects.link(ob);ob.data.materials.append(titlemat);ob.location=(0,-.05,z);ob.rotation_euler=(pi/2,0,0)
textline('Title | model identity','GPT-6 ASTRA PRO',6.97,.125)
textline('Subtitle | development tools','COLABDEV  /  BLENDER EEVEE',6.77,.065)
camdata=bpy.data.cameras.new('Portrait camera');camera=bpy.data.objects.new('Portrait camera',camdata);STAGE.objects.link(camera);scene.camera=camera
camera.data.type='ORTHO';camera.data.ortho_scale=7.55;camera.data.lens=85
camera.data.clip_start=.05;camera.data.clip_end=200
VIEWS={'front':((0,-15,3.8),(0,0,3.45)), 'three-quarter':((8,-13,4.2),(0,0,3.45)), 'side':((14,-1.7,4.1),(0,0,3.45)), 'back':((0,15,4.0),(0,0,3.45)), 'face':((0,-15,4.55),(0,-.15,4.63))}
# Save an editable .blend, then render fast EEVEE review images.
for idx,name in enumerate(args.views.split(',')):
 location,target=VIEWS[name];camera.location=location;camera.rotation_euler=(Vector(target)-camera.location).to_track_quat('-Z','Y').to_euler();camera.data.ortho_scale=3.35 if name=='face' else 7.55
 if name=='face':scene.render.resolution_x=800;scene.render.resolution_y=960
 else:scene.render.resolution_x=CFG.get('width',720 if args.quality=='draft' else 1000);scene.render.resolution_y=CFG.get('height',1080 if args.quality=='draft' else 1500)
 if name!='front':
  for o in STAGE.objects:
   if o.type=='FONT':o.hide_render=True
 else:
  for o in STAGE.objects:
   if o.type=='FONT':o.hide_render=False
 backdrop.location=Vector(target)+(Vector(target)-camera.location).normalized()*3.2;backdrop.rotation_euler=camera.rotation_euler
 scene.render.filepath=str(REV/(name+'.png'))
 print('RENDERING',name,scene.render.filepath,flush=True);bpy.ops.render.render(write_still=True)
# Reset the editable scene to the front portrait composition.
camera.location=VIEWS['front'][0];camera.rotation_euler=(Vector(VIEWS['front'][1])-camera.location).to_track_quat('-Z','Y').to_euler();camera.data.ortho_scale=7.55
for o in STAGE.objects:
 if o.type=='FONT':o.hide_render=False
scene.render.resolution_x=1000;scene.render.resolution_y=1500;scene.render.filepath=str(LATEST/(PREFIX+'_portrait.png'))
backdrop.location=Vector(VIEWS['front'][1])+(Vector(VIEWS['front'][1])-camera.location).normalized()*3.2;backdrop.rotation_euler=camera.rotation_euler
scene['asset_origin']='Original math-authored meshes, fibers, procedural materials; no reference texture.'
scene['review_revision']=args.revision
bpy.ops.wm.save_as_mainfile(filepath=str(REV/(PREFIX+'.blend')))
if args.export:
 print('EXPORTING GLB',flush=True)
 bpy.ops.object.select_all(action='DESELECT')
 for ob in CHAR.objects:ob.select_set(True)
 bpy.context.view_layer.objects.active=next(o for o in CHAR.objects if o.type=='MESH')
 try:
  bpy.ops.export_scene.gltf(filepath=str(REV/(PREFIX+'.glb')),export_format='GLB',use_selection=True,export_apply=True,export_yup=True,export_animations=False,export_cameras=False,export_lights=False,export_texcoords=False,export_normals=True,export_colors=True,export_materials='EXPORT')
 except Exception as e:
  print('GLB_EXPORT_ERROR',repr(e),flush=True)
stats={'revision':args.revision,'objects':len(CHAR.objects),'authored_objects_before_batching':authored_object_count,'mesh_polygons':sum(len(o.data.polygons) for o in CHAR.objects if o.type=='MESH'),'mesh_vertices':sum(len(o.data.vertices) for o in CHAR.objects if o.type=='MESH'),'source':'all original procedural geometry','renderer':scene.render.engine,'config':CFG}
(REV/'build-report.json').write_text(json.dumps(stats,indent=2))
print('BUILD_DONE',json.dumps(stats),flush=True)
