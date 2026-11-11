from __future__ import annotations

import argparse
from pathlib import Path

import torch
from PIL import Image

from hy3dgen.rembg import BackgroundRemover
from hy3dgen.shapegen import Hunyuan3DDiTFlowMatchingPipeline
from hy3dgen.texgen import Hunyuan3DPaintPipeline


def load_rgba(path: Path, remover: BackgroundRemover) -> Image.Image:
    image = Image.open(path).convert("RGBA")
    alpha = image.getchannel("A")
    if alpha.getextrema() == (255, 255):
        image = remover(image)
    return image


def main() -> None:
    parser = argparse.ArgumentParser(description="Generate the Hope Island patient GLB from canonical views.")
    parser.add_argument("--atlas", type=Path, help="4x2 atlas ordered front, front-right, right, back-right / back, back-left, left, front-left")
    parser.add_argument("--front", type=Path)
    parser.add_argument("--left", type=Path)
    parser.add_argument("--back", type=Path)
    parser.add_argument("--right", type=Path)
    parser.add_argument("--output", type=Path, default=Path("output/patient_headscarf_raw.glb"))
    parser.add_argument("--seed", type=int, default=20261031)
    parser.add_argument("--steps", type=int, default=50)
    parser.add_argument("--octree-resolution", type=int, default=380)
    args = parser.parse_args()

    args.output.parent.mkdir(parents=True, exist_ok=True)
    remover = BackgroundRemover()
    if args.atlas:
        atlas = Image.open(args.atlas).convert("RGBA")
        cell_width, cell_height = atlas.width // 4, atlas.height // 2
        def atlas_cell(index: int) -> Image.Image:
            column, row = index % 4, index // 4
            return atlas.crop((column * cell_width, row * cell_height, (column + 1) * cell_width, (row + 1) * cell_height))
        images = {"front": atlas_cell(0), "right": atlas_cell(2), "back": atlas_cell(4), "left": atlas_cell(6)}
    else:
        paths = {"front": args.front, "left": args.left, "back": args.back, "right": args.right}
        if any(path is None for path in paths.values()):
            parser.error("Provide --atlas or all of --front --left --back --right")
        images = {name: load_rgba(path, remover) for name, path in paths.items()}

    shape_pipeline = Hunyuan3DDiTFlowMatchingPipeline.from_pretrained(
        "tencent/Hunyuan3D-2mv",
        subfolder="hunyuan3d-dit-v2-mv",
        variant="fp16",
    )
    paint_pipeline = Hunyuan3DPaintPipeline.from_pretrained("tencent/Hunyuan3D-2")

    generator = torch.Generator(device="cuda").manual_seed(args.seed)
    mesh = shape_pipeline(
        image=images,
        num_inference_steps=args.steps,
        octree_resolution=args.octree_resolution,
        num_chunks=20000,
        generator=generator,
        output_type="trimesh",
    )[0]
    mesh = paint_pipeline(mesh, image=images["front"])
    mesh.export(args.output)
    print(args.output.resolve())


if __name__ == "__main__":
    main()
