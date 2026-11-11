import time
from pathlib import Path

import trimesh
from PIL import Image
from hy3dgen.texgen import Hunyuan3DPaintPipeline

ROOT = Path("/workspace")
image = Image.open(ROOT / "reconstruction-center-input-v01.png").convert("RGBA")
loaded = trimesh.load(ROOT / "reconstruction-center-hunyuan-shape-v01.glb", force="scene")
mesh = loaded.to_geometry() if isinstance(loaded, trimesh.Scene) else loaded
pipeline = Hunyuan3DPaintPipeline.from_pretrained("tencent/Hunyuan3D-2")
started = time.time()
textured = pipeline(mesh, image=image)
output = ROOT / "reconstruction-center-hunyuan-textured-v01.glb"
textured.export(output)
print(f"output={output}")
print(f"elapsed_seconds={time.time() - started:.1f}")
