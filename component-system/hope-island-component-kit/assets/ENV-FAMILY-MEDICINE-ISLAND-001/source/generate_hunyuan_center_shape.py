import time
from pathlib import Path
import torch
from PIL import Image
from hy3dgen.shapegen import Hunyuan3DDiTFlowMatchingPipeline

ROOT=Path("/workspace")
image=Image.open(ROOT/"family-medicine-center-input-v01.png").convert("RGBA")
pipeline=Hunyuan3DDiTFlowMatchingPipeline.from_pretrained("tencent/Hunyuan3D-2",subfolder="hunyuan3d-dit-v2-0",variant="fp16")
started=time.time()
mesh=pipeline(image=image,num_inference_steps=50,octree_resolution=384,num_chunks=20000,generator=torch.manual_seed(68021),output_type="trimesh")[0]
output=ROOT/"family-medicine-center-hunyuan-shape-v01.glb";mesh.export(output)
print(f"output={output}");print(f"elapsed_seconds={time.time()-started:.1f}")
