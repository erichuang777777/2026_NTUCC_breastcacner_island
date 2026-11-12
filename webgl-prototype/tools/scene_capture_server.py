"""Local-only export server. Run from any directory; original sources are read-only."""
import argparse
import hashlib
import json
from http.server import SimpleHTTPRequestHandler, ThreadingHTTPServer
from pathlib import Path
from urllib.parse import urlsplit

ROOT = Path(__file__).resolve().parents[2]
ART = ROOT / 'art-source'
SHOT_IDS = [s['id'] for s in json.loads((ROOT / 'scene/shots.json').read_text())['shots']]
BASE_ALLOWED = {'exports/taiwan-study-scene-v01.glb', 'captures/shots-capture.json',
           'captures/export-manifest.json'} | {f'captures/web/{s}.png' for s in SHOT_IDS}

PROPS_ALLOWED = {f'captures/web-props/{s}.png' for s in SHOT_IDS} | {'captures/web-props/stats.json'}

LOOKDEV_ALLOWED = {f'captures/web-lookdev/{s}.png' for s in SHOT_IDS}


def injected_source(source, lookdev=False, props=False):
    if props and not lookdev:
        raise ValueError("--props requires --lookdev")
    source = source.replace('function animate(now){',
        'function animate(now){if(window.__captureFreeze)return;')
    if lookdev:
        source += '\nwindow.__captureLookdev = true;\n'
        source += (ROOT / 'webgl-prototype/tools/lookdev_hook.js').read_text()
    if props:
        marker = 'const batches=new Map(),originals=[];'
        if source.count(marker) != 1:
            raise ValueError('props obstacle injection requires the static batching marker')
        source = source.replace(marker, (ROOT / 'webgl-prototype/tools/props_obstacles_hook.js').read_text() + '\n' + marker)
        source += '\n' + (ROOT / 'webgl-prototype/tools/props_scatter_hook.js').read_text()
    return source + '\n' + (ROOT / 'webgl-prototype/tools/scene_capture_hook.js').read_text()


class Handler(SimpleHTTPRequestHandler):
    def __init__(self, *args, **kwargs):
        super().__init__(*args, directory=str(ROOT), **kwargs)

    def do_GET(self):
        path = urlsplit(self.path).path
        if path == '/webgl-prototype/taiwan-study.js':
            source = (ROOT / path.lstrip('/')).read_text()
            source = injected_source(source, getattr(self.server, 'lookdev', False), getattr(self.server, 'props', False))
            data = source.encode()
            self.send_response(200)
            self.send_header('Content-Type', 'text/javascript; charset=utf-8')
            self.send_header('Content-Length', str(len(data)))
            self.end_headers()
            self.wfile.write(data)
        elif path.startswith('/api/'):
            self.send_error(404, 'Capture server has no production API')
        else:
            super().do_GET()

    def do_POST(self):
        # No arbitrary-path writes, cross-origin posts, or production mutations.
        origin = self.headers.get('Origin')
        if origin != f'http://{self.headers.get("Host")}':
            self.send_error(403)
            return
        relative = urlsplit(self.path).path.removeprefix('/__capture/')
        size = int(self.headers.get('Content-Length', '0'))
        if not self.path.startswith('/__capture/') or relative not in (PROPS_ALLOWED if getattr(self.server, 'props', False) else LOOKDEV_ALLOWED if getattr(self.server, 'lookdev', False) else BASE_ALLOWED) or not 0 < size <= 2**31:
            self.send_error(400)
            return
        target = ART / relative
        target.parent.mkdir(parents=True, exist_ok=True)
        remaining = size
        temporary = target.with_suffix(target.suffix + '.partial')
        try:
            with temporary.open('wb') as out:
                while remaining:
                    chunk = self.rfile.read(min(remaining, 1024 * 1024))
                    if not chunk:
                        raise EOFError('Incomplete upload')
                    out.write(chunk)
                    remaining -= len(chunk)
            temporary.replace(target)
        except Exception:
            temporary.unlink(missing_ok=True)
            raise
        self.send_response(204)
        self.end_headers()


if __name__ == '__main__':
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--port', type=int, default=8767)
    parser.add_argument('--lookdev', action='store_true', help='Preview lighting and postprocessing; save only four PNGs')
    parser.add_argument('--props', action='store_true', help='Add v02 prop scatter; requires --lookdev')
    args = parser.parse_args()
    if args.props and not args.lookdev:
        parser.error('--props requires --lookdev')
    if not args.lookdev:
        ART.joinpath('captures').mkdir(parents=True, exist_ok=True)
        sources = {str(p.relative_to(ROOT)): hashlib.sha256(p.read_bytes()).hexdigest()
                   for p in (ROOT / 'webgl-prototype').glob('*.js')}
        sources.update({str(p.relative_to(ROOT)): hashlib.sha256(p.read_bytes()).hexdigest()
                        for p in (ROOT / 'scene').glob('*.json')})
        ART.joinpath('captures/source-hashes.json').write_text(json.dumps(sources, indent=2))
    print(f'Open http://127.0.0.1:{args.port}/webgl-prototype/taiwan-study.html', flush=True)
    server = ThreadingHTTPServer(('127.0.0.1', args.port), Handler)
    server.lookdev = args.lookdev
    server.props = args.props
    server.serve_forever()
