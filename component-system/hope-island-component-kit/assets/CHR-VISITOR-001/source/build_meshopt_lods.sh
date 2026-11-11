#!/usr/bin/env bash
set -euo pipefail

root_dir="$(cd "$(dirname "$0")/.." && pwd)"
source_model="$root_dir/export/chr-visitor-hunyuan-textured-v02.glb"

npx --yes gltfpack -i "$source_model" -o "$root_dir/export/chr-visitor-hunyuan-meshopt-lod0-v03.glb" -si 0.4 -se 0.002 -sv -kn -km
npx --yes gltfpack -i "$source_model" -o "$root_dir/export/chr-visitor-hunyuan-meshopt-lod1-v03.glb" -si 0.2 -se 0.005 -sv -kn -km
npx --yes gltfpack -i "$source_model" -o "$root_dir/export/chr-visitor-hunyuan-meshopt-lod2-v03.glb" -si 0.08 -se 0.012 -sv -kn -km
