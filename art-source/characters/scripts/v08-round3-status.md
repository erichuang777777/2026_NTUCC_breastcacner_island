# v08 第 3 輪執行狀態

2026-11-12：程式與純 NumPy 檢查已完成，**新 GLB 與渲染尚未產生**。已查看第 2 輪的 `v08-face-check.png` 與 `v08-lineup-front.png`。所有本輪寫入均在 `art-source/characters/`，未 commit。

## 已完成

- 移除投影貼花產生流程；成功重建各角色時會刪除該角色舊 `*-face.png`，驗證 GLB 不含 `skin_face` 或任何影像。
- `v08_face_geometry.py`：讀取 v05 visitor GLB 靜止網格，依材質及焊接後的連通塊分類，結果列於 `v08-v05-components.json`。實際來源眉毛／上睫毛是 `hair`，高光是 `shoe`，因此依位置額外抽取，排除真正鞋子、耳內與手指細節。完整五官為 6,472 三角面。
- `PARAMS`／`ROLE_PARAMS`：可調 75° 正面角度、髮際線曲率、臉寬、耳朵範圍、清色範圍、平滑輪數、眼高（頭高 45%，預留眉毛空間）、眼距（臉寬 38%）、表面偏移（1.8 mm）。帽子、頭巾與口罩面受保護。
- 全臉與耳朵改為 skin，前方髮際線以下的 hair 清為 skin；固定臉部邊界做 45 輪 Laplacian 平滑，混合 0.4 的擬合橢球前表面，邊界仍固定。
- 五官以一致尺度對齊；沿 -Y 對臉部 BVH 射線投影，以整組剛性平移保留形狀。眼睛的眼白、虹膜、瞳孔、高光、睫毛共同定位，以保留前後層次。投影覆蓋不足 90% 直接停止，避免輸出漏貼五官。
- 眉毛獨立 `brow` 材質，顏色取角色 hair。scrub 排除嘴與腮紅，保留原口罩色塊。新增 eye.L／eye.R，父節點 head、方向沿用 v05；眼部純權重 1，其他部件綁 head。
- 移除原 UV 與舊法線、焊接重複位置後，身體先做 2 輪 Corrective Smooth；總三角面 24,000 的預算先扣除五官。所有面平滑，材質交界不設銳邊，真正大於 40° 的折角才設銳邊；臉部不設銳邊。
- 渲染全部重新匯入匯出後的 GLB。`v08-face-check.png` 改為正面／3/4 兩排，每個角色並列 v08／v05。另匯出 `export/v08-hunyuan/regions/*.glb`，供 `v08-face-region.png` 顯示實際選區：橘色臉、藍色耳、紫色下巴／清色。

## 已通過

使用 Blender 隨附 Python（不啟動 Blender）執行：

```sh
/Applications/Blender.app/Contents/Resources/5.2/python/bin/python3.13 -B art-source/characters/scripts/test_cast_v08_math.py
```

包含實際 GLB 連通塊／眼中心／五官面數、口罩排除、75° 選區、頭飾保護、耳朵、下巴清色、固定平滑邊界、色彩數學及修改腳本語法。

## 阻礙與沙箱外執行

本輪實際執行 build，Blender 5.2.3 仍在 Python 啟動前的 Metal 裝置偵測崩潰（exit 139），紀錄為 `v08-round3-build.log`。目前 `export/v08-hunyuan/*.glb` 與 `renders/v08-*` 仍是第 2 輪；未把舊圖當成本輪驗證，也未執行渲染腳本覆寫它們。

需協調者在可啟動 Blender 的環境依序執行（第一支成功才執行第二支）：

```sh
/Applications/Blender.app/Contents/MacOS/Blender --background --python art-source/characters/scripts/build_cast_v08_hunyuan.py
/Applications/Blender.app/Contents/MacOS/Blender --background --python art-source/characters/scripts/render_cast_v08.py
```

尚待驗證：Blender API 實際執行、六人髮際線／耳朵選區、投影覆蓋率、五官凸出程度、臉部形狀、GLB 法線與眨眼效果。參數尚未經本輪渲染校準；此狀態不代表換臉已驗收。
