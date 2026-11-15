"""Create a local portrait study; preserve reference bytes, never overwrite."""
import argparse
import hashlib
import json
import re
import shutil
from pathlib import Path


def main():
    p = argparse.ArgumentParser(description=__doc__)
    p.add_argument('--out', required=True, type=Path)
    p.add_argument('--reference', required=True, type=Path)
    p.add_argument('--subject-id', required=True)
    p.add_argument('--source-note', required=True)
    a = p.parse_args()
    if not re.fullmatch(r'[a-z0-9][a-z0-9-]{0,63}', a.subject_id):
        p.error('subject-id 必須為小寫英文、數字與連字號')
    if not a.reference.is_file():
        p.error('找不到原照')
    if a.reference.suffix.lower() not in {'.jpg', '.jpeg', '.png', '.webp'}:
        p.error('請提供 JPEG、PNG 或 WebP 原照')
    if a.out.exists():
        p.error('輸出資料夾已存在；請使用新的研究目錄')
    a.out.mkdir(parents=True)
    for name in ['reference', 'source', 'versions', 'reviews']:
        (a.out / name).mkdir()
    target = a.out / 'reference' / ('portrait' + a.reference.suffix.lower())
    shutil.copy2(a.reference, target)
    data = {'subjectId': a.subject_id, 'reference': str(target.relative_to(a.out)),
            'referenceSHA256': hashlib.sha256(target.read_bytes()).hexdigest(),
            'sourceNote': a.source_note, 'sideBackEstimated': True,
            'modelUnits': 'not-calibrated', 'status': 'initialized',
            'versions': [], 'mainSceneIntegrated': False}
    (a.out / 'study.json').write_text(json.dumps(data, ensure_ascii=False, indent=2) + '\n')
    print(a.out.resolve() / 'study.json')


if __name__ == '__main__':
    main()
