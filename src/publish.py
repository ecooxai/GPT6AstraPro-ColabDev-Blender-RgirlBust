"""Publish one manually visually reviewed revision. Never invent automatic quality scores."""
from pathlib import Path
import json, argparse, shutil, datetime
p=Path(__file__).resolve().parents[1];b=(p/'build').resolve();prefix='GPT6AstraPro_ColabDev_Blender_RgirlBust'
a=argparse.ArgumentParser();a.add_argument('revision',type=int);a.add_argument('--score',type=float,required=True);a.add_argument('--title',required=True);a.add_argument('--review',required=True);args=a.parse_args()
rev=b/'revisions'/f'r{args.revision:03d}';latest=b/'latest';front=rev/'front.png'
assert front.exists(),f'Cannot publish a missing render: {front}'
for extension in ['.blend','.glb']:
 source=rev/(prefix+extension)
 if source.exists():
  temporary=latest/(prefix+extension+'.tmp')
  shutil.copy2(source,temporary)
  temporary.replace(latest/(prefix+extension))
shutil.copy2(front,latest/(prefix+'_portrait.png'))
manifest=p/'preview/progress.json';d=json.loads(manifest.read_text())
d.update(revision=args.revision,score=args.score,status=args.title,updated=datetime.datetime.now(datetime.timezone.utc).isoformat(timespec='seconds'),project=str(p),build=str(b),portrait=f'build/latest/{prefix}_portrait.png',portraitPath=str(latest/(prefix+'_portrait.png')))
glb=latest/(prefix+'.glb')
if glb.exists():d.update(model=f'build/latest/{prefix}.glb',modelPath=str(glb))
d['notes']='Single-reference reconstruction. All character geometry and materials are original. No reference-photo texture is used. The score is a subjective visual review, not an external similarity measurement. Requested iteration budget: 20,000; only completed, inspected revisions are counted.'
d['files']=[]
for filename,label in [(prefix+'.blend','Editable Blender scene'),(prefix+'.glb','Interactive 3D model · GLB'),(prefix+'_portrait.png','EEVEE portrait · PNG'),(prefix+'_source.zip','Source + project archive')]:
 f=latest/filename
 if f.exists():d['files'].append(dict(label=label,url='build/latest/'+filename,path=str(f),size=f'{f.stat().st_size/1048576:.1f} MB'))
d['iterations']=[i for i in d.get('iterations',[]) if i['id']!=args.revision]
d['iterations'].append(dict(id=args.revision,score=args.score,title=args.title,review=args.review,image=f'build/revisions/r{args.revision:03d}/front.png',path=str(front)))
d['iterations'].sort(key=lambda i:i['id'])
d['views']=[]
for view,label in [('face','Facial anatomy detail'),('three-quarter','Three-quarter inspection'),('side','Side silhouette'),('back','Rear hair construction')]:
 # Reuse last available view, but its source revision remains explicitly named in the path.
 found=sorted((b/'revisions').glob('r*/'+view+'.png'))
 if found:
  f=found[-1];relative=str(f.relative_to(b));d['views'].append(dict(label=label,url='build/'+relative,path=str(f)))
tmp=manifest.with_suffix('.tmp');tmp.write_text(json.dumps(d,indent=2));tmp.replace(manifest)
print(json.dumps({'published_revision':args.revision,'score':args.score,'reviewed_revisions':len(d['iterations']),'files':[f['label'] for f in d['files']]}))
