import time
from pathlib import Path

import trimesh
from PIL import Image

from hy3dgen.texgen import Hunyuan3DPaintPipeline


ROOT = Path("/workspace")
INPUT_IMAGE = ROOT / "imaging-island-terrain-input-v01.png"
INPUT_MESH = ROOT / "imaging-island-terrain-hunyuan-shape-v01.glb"
OUTPUT = ROOT / "imaging-island-terrain-hunyuan-textured-v01.glb"

image = Image.open(INPUT_IMAGE).convert("RGBA")
loaded = trimesh.load(INPUT_MESH, force="scene")
mesh = loaded.to_geometry() if isinstance(loaded, trimesh.Scene) else loaded

pipeline = Hunyuan3DPaintPipeline.from_pretrained("tencent/Hunyuan3D-2")
started = time.time()
textured = pipeline(mesh, image=image)
textured.export(OUTPUT)
print(f"output={OUTPUT}")
print(f"elapsed_seconds={time.time() - started:.1f}")
