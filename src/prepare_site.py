"""Prepare a self-contained static studio for the project's dedicated Pages branch."""
from pathlib import Path
import json, shutil
ROOT=Path(__file__).resolve().parents[1]
BUILD=(ROOT/'build').resolve()
SITE=BUILD/'site'
SITE.mkdir(exist_ok=True)
for name in ('index.html','style.css','app.js'):
    shutil.copy2(ROOT/'preview'/name,SITE/name)
shutil.copytree(ROOT/'preview/vendor',SITE/'vendor',dirs_exist_ok=True)
reference=ROOT/'reference/rgirtophalf.png'
if reference.exists():
    shutil.copy2(reference,SITE/'reference.png')
d=json.loads((ROOT/'preview/progress.json').read_text())
latest=SITE/'build/latest'
latest.mkdir(parents=True,exist_ok=True)
prefix='GPT6AstraPro_ColabDev_Blender_RgirlBust'
for name in (prefix+'.glb',prefix+'_portrait.png'):
    shutil.copy2(BUILD/'latest'/name,latest/name)
for revision in (BUILD/'revisions').glob('r*'):
    target=SITE/'build/revisions'/revision.name
    target.mkdir(parents=True,exist_ok=True)
    for image in revision.glob('*.png'):
        shutil.copy2(image,target/image.name)
    for name in ('build-report.json','config.json'):
        if (revision/name).exists():
            shutil.copy2(revision/name,target/name)
release='https://github.com/ecooxai/GPT6AstraPro-ColabDev-Blender-RgirlBust/releases/download/portrait-study/'
for item in d['files']:
    if item['url'].endswith(('.blend','.zip')):
        item['url']=release+Path(item['url']).name
(SITE/'progress.json').write_text(json.dumps(d,indent=2))
(SITE/'.nojekyll').touch()
print(json.dumps({'site':str(SITE),'revision':d['revision'],'score':d['score']}))
