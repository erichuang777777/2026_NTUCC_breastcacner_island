import time
from pathlib import Path

import torch
from PIL import Image

from hy3dgen.shapegen import Hunyuan3DDiTFlowMatchingPipeline


ROOT = Path("/workspace")
INPUT = ROOT / "imaging-pavilion-input-v01.png"
OUTPUT = ROOT / "imaging-pavilion-hunyuan-shape-v01.glb"

image = Image.open(INPUT).convert("RGBA")
pipeline = Hunyuan3DDiTFlowMatchingPipeline.from_pretrained(
    "tencent/Hunyuan3D-2",
    subfolder="hunyuan3d-dit-v2-0",
    variant="fp16",
)

started = time.time()
mesh = pipeline(
    image=image,
    num_inference_steps=50,
    octree_resolution=384,
    num_chunks=20000,
    generator=torch.manual_seed(62002),
    output_type="trimesh",
)[0]
mesh.export(OUTPUT)
print(f"output={OUTPUT}")
print(f"elapsed_seconds={time.time() - started:.1f}")
