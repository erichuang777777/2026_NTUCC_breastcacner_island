import time
from pathlib import Path

import torch
from PIL import Image
from hy3dgen.shapegen import Hunyuan3DDiTFlowMatchingPipeline

ROOT = Path("/work")
INPUT = ROOT / "character-hunyuan-input-v02.png"
OUTPUT = ROOT / "chr-visitor-hunyuan-shape-v02.glb"

image = Image.open(INPUT).convert("RGBA")
pipeline = Hunyuan3DDiTFlowMatchingPipeline.from_pretrained(
    "tencent/Hunyuan3D-2",
    subfolder="hunyuan3d-dit-v2-0",
    variant="fp16",
)

started = time.time()
mesh = pipeline(
    image=image,
    num_inference_steps=40,
    octree_resolution=384,
    num_chunks=20000,
    generator=torch.manual_seed(20261105),
    output_type="trimesh",
)[0]
mesh.export(OUTPUT)
print(f"output={OUTPUT}")
print(f"elapsed_seconds={time.time() - started:.1f}")
