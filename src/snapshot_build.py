"""Capture the exact original source used by a Blender build."""
from pathlib import Path
import hashlib, json, shutil, subprocess
from datetime import datetime, timezone

def capture_source(root: Path, revision: Path):
    if (revision/'build-report.json').exists():
        raise RuntimeError('This revision already has a completed build. Use a new revision number.')
    destination=revision/'source'
    destination.mkdir(parents=True,exist_ok=True)
    hashes={}
    for source in sorted((root/'src').iterdir()):
        if source.is_file() and source.suffix in ('.py','.json','.sh'):
            shutil.copy2(source,destination/source.name)
            hashes[source.name]=hashlib.sha256(source.read_bytes()).hexdigest()
    try:
        commit=subprocess.check_output(['git','rev-parse','HEAD'],cwd=root,text=True,timeout=5).strip()
    except Exception:
        commit='not recorded'
    digest=hashlib.sha256(json.dumps(hashes,sort_keys=True).encode()).hexdigest()
    report={'created':datetime.now(timezone.utc).isoformat(),'git_commit':commit,'sha256':digest,'files':hashes}
    (revision/'source-report.json').write_text(json.dumps(report,indent=2))
    return report
