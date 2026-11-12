# Hunyuan3D 角色 v08

這一版保留 Hunyuan3D 形狀，將貼圖轉成語意純色色塊，另以參考圖重建臉部貼花，建立骨架並重定向 v05 的八個動作。輸入朝向、臉部對位與動畫形變仍須由協調者在沙箱外執行 Blender 並檢查渲染。

## 執行

從專案根目錄執行；以下使用 macOS Blender 路徑，可換成實際的 Blender 5.2.3 執行檔。

```sh
# 純 NumPy 測試，不啟動 Blender。
/Applications/Blender.app/Contents/Resources/5.2/python/bin/python3.13 art-source/characters/scripts/test_cast_v08_math.py

# Blender 內部的演算法自我檢查，不需要模型。
/Applications/Blender.app/Contents/MacOS/Blender --background --python-exit-code 1 --python art-source/characters/scripts/build_cast_v08_hunyuan.py -- --self-check

# 先建病友與護理師；參數必須使用網頁 role id。
/Applications/Blender.app/Contents/MacOS/Blender --background --python-exit-code 1 --python art-source/characters/scripts/build_cast_v08_hunyuan.py -- visitor nurse

# 完整六位。
/Applications/Blender.app/Contents/MacOS/Blender --background --python-exit-code 1 --python art-source/characters/scripts/build_cast_v08_hunyuan.py

# 六位全部完成後產出四張檢查圖。
/Applications/Blender.app/Contents/MacOS/Blender --background --python-exit-code 1 --python art-source/characters/scripts/render_cast_v08.py
```

`--python-exit-code 1` 讓 Python 例外傳回非零結束碼。腳本會重設 Blender 場景，請使用獨立背景程序。尚未完成的 GLB 留為 `.pending.glb`；通過輸出合約檢查才取代正式檔案。逐角色更新 manifest，單一角色重跑保留其他角色的紀錄。請勿同時執行多個建置程序寫入同一個輸出資料夾。

| 網頁 role id／輸出 | 原始檔前綴 | v05 顯示 style |
|---|---|---|
| visitor | patient | scarf |
| scarf | visitor | short |
| doctor | doctor | short |
| nurse | nurse | bob |
| surgeon | surgeon | cap |
| scrub | scrubnurse | mask：body、cap、mask |

每個前綴需要 `raw/<prefix>-rgba.png`、`raw/<prefix>-textured.glb`。高面數 `-shape.glb` 留作原始資料，建置不使用它。建置前會一次列出所選角色缺少的檔案。本次撰寫時六張 PNG 已存在，六個 textured GLB 尚未到位。

## 輸出

全部位於 `art-source/characters/`，不會複製到網頁目錄。

- `export/v08-hunyuan/{visitor,scarf,doctor,nurse,surgeon,scrub}.glb`：一個 `cast_body` 網格、多材質、一個骨架。
- `export/v08-hunyuan/<role>-face.png`：512 × 512 臉部貼圖，也會內嵌於 GLB。
- `export/v08-hunyuan/<role>-report.json`、`manifest.json`：三角形數、位元組、材質與面數、動作、實際調色盤、骨頭位置、碰撞診斷及待人工驗證狀態。
- `renders/v08-lineup-front.png`、`v08-lineup-three-quarter.png`：左至右為病友、陪伴者、醫師、護理師、刷手服醫師、手術室護理師。v08 在前，v05 在後排，橫向錯開以減少遮擋。front 為正面方位、相機略俯視；three-quarter 將每位角色旋轉 35°。
- `renders/v08-pose-check.png`：上排病友、下排護理師；左至右為 idle 第 1 格、walk 第 1 格、第 8 格、wave 中段。各格獨立烘成靜態快照。
- `renders/v08-panorama.png`：僅六位 v08，相機距離目標點 12 單位、俯角 30°。暖米白棚景、AgX、面光源柔和陰影，不是網頁島嶼場景截圖。

## 集中參數與處理方式

所有主要調整放在建置腳本頂部。`ROLE_PARAMS[role]` 覆寫共用 `PARAMS`，`PALETTE_OVERRIDES[role]` 可指定語意色彩的十六進位值。

1. **正規化**：glTF 匯入器先完成 Y-up → Blender Z-up。`rotation_degrees=(0,0,0)` 預設輸入正面經匯入後為 -Y；若反向，將該角色設為 `(0,0,180)`。幾何本身無法可靠推斷哪面是臉，因此不偽稱自動辨識正反。總高 `HEIGHT=1.57`，最低點為 z=0；取最低 10% 高度的腳部 bbox 中點置中。第一個模型診斷印出原始／正規化 bbox、旋轉及預期朝向。
2. **取色**：Lab k-means，10 群、最多 30,000 樣本、35 輪、固定 seed 8。頂部 `PALETTES` 已由現有六張 PNG 自動取色，依初始語意色相／明度錨點對應而得；建置仍會重新取色，輸出實際結果。每個角色保留 8–10 個語意材質；相同 RGB 可能對應不同部位。遮罩優先使用 alpha；若近乎全不透明，排除近白背景並列警告。白鞋若被背景判斷吃掉，可手動設定 `reference_bbox`。
3. **色塊**：每個三角形取 7 個 UV 點，以面積加權得面平均色，找最近 Lab 色。上衣、褲子、鞋、頭飾另加高度限制，避免同色制服全部變成同一材質。鄰面嚴格多數決 3 輪；少於 18 面的小島併入鄰接較大區塊。中央臉部橢圓內被誤判成 hair／accent 的眼眉改回 skin，避免貼花留洞。純色材質把 sRGB 轉成線性色；布料 roughness 0.8、皮膚 0.55、鞋／鞋底 0.6。
4. **臉部**：選擇 skin、法線 y < -0.30、高度 0.77–0.97 H、中心左右 0.16 H 的面，改為 `skin_face`。以原始 T-pose 的 x／z bbox 對齊參考圖剪影，裁切頭部並重採樣至 512 × 512，寫入 `FaceUV`。正投影在放下手臂之前完成。`face_uv_scale`、`face_uv_offset` 是對位調整；`face_reference_rect`／`reference_bbox` 是原圖像素座標 `[left,bottom,right,top]`，原點在**左下角**。口罩材質不覆蓋成臉部。
5. **減面**：collapse 目標 19,000 三角形，最多三輪；匯出硬上限 24,000。材質邊界、開放邊界及臉部以頂點群組與 factor 1000 強烈保護，保留 UV。這是權重保護，**不是拓樸硬鎖**；需檢查接縫、臉部與衣領。沒有使用只對 dissolve 有意義的 delimit 冒充 collapse 邊界保護。
6. **骨架**：16 骨，省略 eye.L/R；父子關係沿用 v05。肩高初值 0.685 H，由外側手臂剖面微調；肩寬單側 0.135 H；肘／腕位於肩到手尖的 49%／85%。頸 0.755 H、髖 0.39 H、膝 0.215 H、踝 0.055 H；腿部 x／y 由膝剖面中位數估計。先執行自動權重；例外或任何未加權頂點觸發最近骨段距離的四骨混合權重。統一限制四個影響、正規化權重。T-pose 兩臂向下旋轉，與垂直保留 12°，套用變形修改器、再套用新靜止姿勢並恢復修改器。手掌沿手臂一起旋轉，掌面是否朝內仍須從圖確認。
7. **動作**：讀取唯讀 v05 visitor GLB 的八個 action；以來源／目標 rest basis 轉換局部旋轉與位移，逐格重採樣為新 action，保持八個名稱。這比直接套用不同 bone roll 的曲線穩健，但不是 IK 重定向；身形差異仍可能造成穿插、腳滑。rest、idle 首格及 walk 全段會用 BVH 檢查前臂／手對軀幹、左右腿表面交叉，印出影格與交叉數，寫入報告。此檢查不能保證排除完全包覆、腋下皺摺或所有自碰撞，亦不會偷偷修改來源動作。可調整 `rest_abduction`、`shoulder_width` 或關節比例後重建。
8. **匯出**：驗證單一 `cast_body` 網格、八個 action 及三角形硬上限；一般 PNG／glTF，不依賴網頁尚未設定的 Draco／KTX 解碼器。單檔 1,500,000 bytes 為目標，超標印警告並標示 `size_target_met=false`，不假稱通過。可先下調 `TARGET_TRIANGLES`，重建並確認臉部品質。

## 協調者優先檢查

1. 朝向是否為 -Y、腳底是否貼地，正面圖是否左右顛倒。輸入不是標準朝向時先改 `rotation_degrees`，再評估其他結果。
2. 臉部眼睛、眉毛、嘴巴是否落在正確位置；參考圖與 Hunyuan 形狀比例不同時，單靠剪影 bbox 對齊不保證吻合。檢查 `skin_face` 面數與輸出的 PNG。
3. 同色區域是否正確區分：粉色外套／頭巾、深色制服／髮色、綠色帽子／衣褲、口罩。取色群數固定，細小配件可能被大面積主色吃掉；需要時調整錨點、override 或島面數門檻。
4. 放下雙臂後的腋下、袖口、手掌方向與側身間距；有 backpack 的病友尤其容易讓自動權重跨區。檢查 `weights` 是否退回 `nearest_segment`。
5. walk 第 1／8 格及完整循環、wave 中段；BVH 報告為篩檢，渲染才是必要的視覺驗收。前排與後排的身高差是實際尺寸，不另縮放 v05。
6. 最後確認實際 GLB 大小、材質名稱與動畫名稱。所有 `visual_validation` 初始保持 pending；未經人工檢查不應當成已驗收資產。

## 本次驗證範圍

已用 Blender 隨附 Python／NumPy 執行獨立測試：Lab 黑白與紅色基準、RGB 解析、鄰面多數決、小島合併、孤立面與輸入不可變性。三支 Python 檔均經語法解析。六張參考圖已實際解碼並產生初版調色盤。

依任務限制，未啟動 Blender；尚未驗證 Blender 5.2.3 實際執行、自動權重、材質／動作匯出、GLB 體積或渲染結果。匯出參數參考 [Blender glTF API](https://docs.blender.org/api/dev/bpy.ops.export_scene.html)，版本差異以協調者實際執行為準。
