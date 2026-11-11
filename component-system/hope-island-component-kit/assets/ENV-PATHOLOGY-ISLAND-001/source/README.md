# 病理診斷島低模來源

正式來源由 Blender 5.2 LTS 建立；`build_blender.py` 依 `component.yaml` 的固定尺度重建 `.blend` 並匯出 GLB。

```bash
blender --background --factory-startup --python source/build_blender.py
```

輸出：`source/model.blend` 與 `export/env-pathology-island-001.glb`

舊的 `generate_glb.mjs` 留作無 Blender 環境的低模重建備援。病理小屋、共用環境道具與角色維持獨立資產。
