# 階段 1 審查：網頁場景 → Blender 同鏡位渲染

日期：2026-11-11。審查者：協調 session。

## 執行方式

Codex 撰寫工具（`webgl-prototype/tools/scene_capture_*`、`art-source/scripts/*`）。Codex 沙箱無法啟動本機伺服器、瀏覽器與 Blender（Blender exit 139），因此由協調 session 在沙箱外執行：

1. `python3 webgl-prototype/tools/scene_capture_server.py --port 8767`
2. 無頭 Chromium（Playwright，chromium-1248）開啟擷取頁並按「匯出 GLB 與四個鏡位」。
3. `Blender --background --python art-source/scripts/assemble_scene.py`
4. `art-source/scripts/compare_shots.py`（需 Pillow）

產物（不進 git）：`art-source/exports/taiwan-study-scene-v01.glb`（77 MB、394 個網格）、`art-source/captures/web/*.png`、`art-source/renders/*.png`、`art-source/compare/*.png`、`art-source/blend/taiwan-study-assembly-v01.blend`。

## 結論

**幾何與鏡位：通過。** 四個鏡位的島形、醫院、燈塔、建築與道具位置完全一致。軸向探針誤差 0；醫院與燈塔的螢幕投影誤差小於 0.001 像素。

**外觀：未通過。** Blender 畫面整體偏灰綠、對比低，夜間尤其明顯。

| 差異 | 原因 | 證據 |
|---|---|---|
| 島上覆蓋一層半透明薄膜 | `capture_151_Mesh`（31×59 平面，覆蓋全島，Alpha 由非貼圖節點控制，BLENDED）在網頁有遮罩，匯入 Blender 後變成整片半透明 | 隱藏後重渲 S04，島上色彩明顯恢復 |
| 夜間雲朵是白色、海面偏亮 | 擷取只保存發光強度，未保存網頁 `setNight` 改變的基本顏色（雲、海、環境物件） | S03、S04 對照 |
| 整體環境光過強、對比低 | 半球光以 World 灰色背景近似（0.8，強度 0.58），EEVEE 的 World 間接光比 Three.js 半球光更平均；加上 ACES 與 AgX 差異 | `blend` 的 World 設定 |
| 缺角色 | 120 個 SkinnedMesh 未匯出（本階段預期） | `export-manifest.json` |
| 缺星星、燈塔光束、海岸泡沫 | Sprite、Points、Line、ShaderMaterial 未匯出（本階段預期） | `export-manifest.json`：Sprite 28、LineLoop 3、Points 1 |

## 下一步（階段 2a，僅 Blender 端）

1. 匯出時保存每個材質的日夜基本顏色與透明度，Blender 依鏡位還原。
2. 正確轉換 `capture_151_Mesh` 這類遮罩材質，或在 Blender 端排除並記錄。
3. 重新校準半球光近似、太陽與補光強度，使 S01 白天先與網頁一致，再處理夜間。
4. 匯出角色（SkinnedMesh 以站立姿勢烘焙），讓鏡位中有人物。

網頁改用 AgX（階段 2b）要等另一個修改 `webgl-prototype/` 的 Codex session 結束，避免衝突。
