"""Create an offline-capable review page using a supplied local Three.js package."""
import argparse
import hashlib
import json
import shutil
from pathlib import Path


def main():
    p = argparse.ArgumentParser(description=__doc__)
    p.add_argument('--model', required=True, type=Path)
    p.add_argument('--reference', required=True, type=Path)
    p.add_argument('--three-dir', required=True, type=Path)
    p.add_argument('--out', required=True, type=Path)
    p.add_argument('--label', default='肖像 3D 檢查')
    a = p.parse_args()
    if a.out.exists():
        p.error('輸出已存在；請使用新目錄')
    for f in [a.model, a.reference, a.three_dir/'build/three.module.js', a.three_dir/'examples/jsm/loaders/GLTFLoader.js', a.three_dir/'LICENSE']:
        if not f.is_file():
            p.error(f'缺少檔案：{f}')
    if a.reference.suffix.lower() not in ['.png', '.jpg', '.jpeg', '.webp']:
        p.error('不支援的原照格式')
    from audit_glb import audit
    audit(a.model)
    a.out.mkdir(parents=True)
    template = Path(__file__).resolve().parents[1]/'assets/preview'
    shutil.copytree(template, a.out, dirs_exist_ok=True)
    vendor = a.out/'vendor/three'
    for part in ['build', 'examples/jsm']:
        shutil.copytree(a.three_dir/part, vendor/part)
    shutil.copy2(a.three_dir/'LICENSE', vendor/'LICENSE')
    shutil.copy2(a.model, a.out/'model.glb')
    reference = 'reference'+a.reference.suffix.lower()
    shutil.copy2(a.reference, a.out/reference)
    settings = {'label': a.label, 'model': 'model.glb', 'reference': reference,
                'assetSHA256': hashlib.sha256(a.model.read_bytes()).hexdigest(),
                'referenceSHA256': hashlib.sha256(a.reference.read_bytes()).hexdigest(),
                'initialAngle': 0, 'rotation': [0, 0, 0],
                'camera': {'target': None, 'halfHeight': None},
                'photo': {'scale': 1, 'xPercent': 0, 'yPercent': 0},
                'hideInClay': [], 'note': '側後方依參考資料推估；此頁尚未完成同尺度相機校準。'}
    (a.out/'viewer.json').write_text(json.dumps(settings, ensure_ascii=False, indent=2)+'\n')
    print(f'python3 -m http.server 8002 --bind 127.0.0.1 --directory "{a.out.resolve()}"')
    print('若連接埠已被使用，選其他未使用的連接埠；不停止其他服務。')


if __name__ == '__main__':
    main()
