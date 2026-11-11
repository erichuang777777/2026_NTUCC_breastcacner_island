import time
from pathlib import Path

import trimesh
from PIL import Image
from hy3dgen.texgen import Hunyuan3DPaintPipeline


ROOT = Path("/work")
MESH = ROOT / "chr-visitor-hunyuan-shape-v02.glb"
IMAGE = ROOT / "character-hunyuan-input-v02.png"
OUTPUT = ROOT / "chr-visitor-hunyuan-textured-v02.glb"

pipeline = Hunyuan3DPaintPipeline.from_pretrained("tencent/Hunyuan3D-2")
image = Image.open(IMAGE).convert("RGBA")
loaded = trimesh.load(MESH, force="scene")
mesh = loaded.to_geometry() if isinstance(loaded, trimesh.Scene) else loaded
started = time.time()
textured = pipeline(mesh, image=image)
textured.export(OUTPUT)
print(f"output={OUTPUT}")
print(f"elapsed_seconds={time.time() - started:.1f}")
