# Qwen Image 2.1 多視角測試 v01

- 輸入：`webgl-prototype/assets/character-atlas.png`（V11 八方向角色圖）
- 輸出：`turnaround-qwen-test-v01.png`
- 模型：`qwen_image_2.1_int8_convrot.safetensors`
- 文字編碼器：`qwen3vl_8b_int8_convrot.safetensors`
- VAE：`qwen_image_2.1_vae_bf16.safetensors`
- Seed：`2026110401`
- Steps：`15`
- Sampler／Scheduler：`euler`／`simple`
- 輸出尺寸：1248 × 832
- DGX 最高觀察溫度：67°C；完成後回落至 49°C

## 用途

作為高品質 3D 生成的四方向一致參考。此圖已明顯改善背景、相機高度、比例與服裝一致性，但手臂仍接近自然下垂，不是完整 A-pose；進入自動綁骨前仍須在 Blender 留意腋下與手臂拓樸。
