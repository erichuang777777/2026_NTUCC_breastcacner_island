"""Create full-resolution side-by-side comparisons; requires Pillow."""
import json
from pathlib import Path
from PIL import Image, ImageDraw

ART = Path(__file__).resolve().parents[1]
shots = json.loads((ART / 'captures/shots-capture.json').read_text())['shots']
(ART / 'compare').mkdir(exist_ok=True)
for shot in shots:
    name = shot['id'] + '.png'
    with Image.open(ART / 'captures/web' / name) as web, Image.open(ART / 'renders' / name) as render:
        assert web.size == render.size == (1920, 1080), f'{name}: unexpected dimensions'
        result = Image.new('RGB', (3840, 1120), '#202020')
        result.paste(web, (0, 40))
        result.paste(render, (1920, 40))
        draw = ImageDraw.Draw(result)
        draw.text((12, 12), f'{shot["id"]} | WEB / ACES', fill='white')
        draw.text((1932, 12), 'BLENDER / EEVEE / AgX', fill='white')
        result.save(ART / 'compare' / name)
print('Comparisons written; visual review is still required.')
