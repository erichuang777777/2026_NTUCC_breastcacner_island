"""Move only identified historical outputs; preserve references and current authoring sources."""
from pathlib import Path
import hashlib,json,shutil
ROOT=Path(__file__).resolve().parents[2]
WEB=ROOT/'webgl-prototype';DEST=ROOT/'archive/2026-11-11-v20'
records=[]
def move(path):
    if not path.exists():return
    relative=path.relative_to(ROOT);target=DEST/relative
    if target.exists():raise RuntimeError('Archive destination already exists: '+str(target))
    target.parent.mkdir(parents=True,exist_ok=True)
    digest=hashlib.sha256(path.read_bytes()).hexdigest() if path.is_file() else None
    size=path.stat().st_size if path.is_file() else sum(p.stat().st_size for p in path.rglob('*') if p.is_file())
    shutil.move(str(path),str(target));records.append(dict(source=str(relative),archive=str(target.relative_to(ROOT)),bytes=size,sha256=digest))
# Screenshots at the web root are historic QA output, not runtime media.
# All design references under visual-references/ and editable component sources stay in place.
for p in sorted(WEB.glob('*.png')):move(p)
for folder in [WEB,WEB/'dist']:
    for name in ['index.html','app.js','styles.css','hope-study.html','hope-study.js']:
        move(folder/name)
for name in ['scene-v18','crowd-v19']:move(WEB/'reviews'/name)
for name in ['HOPE-STUDY.md','TAIWAN-STUDY.md']:move(WEB/name)
# Keep only assets used by the active viewer in the deployable tree; retain all source assets as references.
active_assets={'ntucc-blender-v07.glb','poster-lighthouse-tower-v01.glb','ntucc-campus-reference.jpg','characters','film-character-reference'}
for p in sorted((WEB/'dist/assets').iterdir()):
    if p.name not in active_assets:move(p)
for p in sorted((WEB/'dist/assets/characters').iterdir()):
    if p.name!='v05':move(p)
move(ROOT/'README_本地開發與建模套件.md')
(DEST/'manifest.json').write_text(json.dumps(records,ensure_ascii=False,indent=2))
(DEST/'README.md').write_text('# 歷史檔案封存\n\n日期：2026-11-11\n\n舊版頁面、程式、驗收截圖及不再使用的部署模型均搬移至此，未刪除。原始路徑與檔案 SHA-256 見 manifest.json。before/ 是本次變更前的備份。\n\nvisual-references/、原始建模素材與可編輯來源保留原處；dist 僅保留當前網頁使用的模型。還原個別檔案時依 manifest 的 source 路徑搬回，請先檢查該路徑是否已有新版。\n')
print(json.dumps(dict(moved=len(records),bytes=sum(r['bytes'] for r in records)),ensure_ascii=False))
