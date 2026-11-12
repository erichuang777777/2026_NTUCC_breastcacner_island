# 階段 2b lookdev 第 2 輪修正

日期：2026-11-12。本輪已檢視協調者提供的 S01–S04 前後並排圖及概念圖，依白天灰暗、海色偏綠與夜間燈塔光暈過大修正。新參數尚待重新擷取驗收，未量測 fps。沿用 `lookdev-params-v01.json` 檔名，同步更新內容。

## 檔案與寫入範圍

| 檔案 | 用途 |
|---|---|
| `webgl-prototype/tools/lookdev_hook.js`（新增） | 頂端參數、AgX、光線、composer、AO、Bloom、景深、顯示空間調色與 render 包裝 |
| `webgl-prototype/tools/scene_capture_server.py`（修改） | `--lookdev` 注入順序與獨立 PNG 白名單；lookdev 不寫 source-hashes JSON |
| `webgl-prototype/tools/scene_capture_hook.js`（修改） | 保留原匯出分支，增加只擷取四張 PNG 的 lookdev 分支及動畫恢復 |
| `webgl-prototype/tools/test_lookdev.py`（新增） | 預設注入相容、輸出隔離、參數一致與組合模組語法檢查 |
| `webgl-prototype/tools/test_lookdev_render.mjs`（新增） | 用替身檢查 high／medium、遞迴防護、尺寸、日夜與錯誤復原 |
| `art-source/lookdev/lookdev-params-v01.json`（新增） | 與 hook 頂端物件相同的參數快照，供後續搬入共用設定 |
| `art-source/lookdev/README.md`（新增） | 本交付說明 |

未修改網頁既有原始碼、scene、specifications 或 reviews，未 commit。工作目錄原有其他 session 的修改不屬於這次交付。

## 協調者執行步驟

```sh
cd /Users/eric777/Desktop/Breastcancer_island_of_hope
python3 -B webgl-prototype/tools/test_lookdev.py
node webgl-prototype/tools/test_lookdev_render.mjs
python3 webgl-prototype/tools/scene_capture_server.py --port 8768 --lookdev
```

1. 在可使用 WebGL 的瀏覽器開啟 `http://127.0.0.1:8768/webgl-prototype/taiwan-study.html?quality=high`。現有 import map 使用 Three.js 0.160.0 CDN，需網路。
2. 等地標與模型載入，確認左上「擷取 lookdev 四個鏡位」按鈕出現。無按鈕時先看主控台模組載入錯誤；可在主控台執行 `hopeStudy.audit().ready` 確認地標。
3. 按按鈕，等待「完成：lookdev 四張 PNG 已儲存」。輸出位置：`art-source/captures/web-lookdev/S01-day-overview.png`、`S02-hospital-entrance.png`、`S03-night-wish.png`、`S04-meteor-to-lighthouse.png`，皆為 canvas-only 1920×1080。
4. 若使用既有 Playwright 腳本，將按鈕文字改為「擷取 lookdev 四個鏡位」，完成條件改為上述完成訊息。不要沿用 GLB 匯出完成條件。
5. medium：開啟 `http://127.0.0.1:8768/webgl-prototype/taiwan-study.html?quality=medium`，重新擷取。**兩種品質使用相同輸出檔名，請先將 high 圖複製到 `art-source/lookdev/high/` 再跑 medium**，以保留比較。
6. 未按擷取時動畫持續，可觀察 30 fps 目標。按鈕擷取時暫停動畫，完成或失敗後恢復。
7. 停止伺服器後，原模式仍可用 `python3 webgl-prototype/tools/scene_capture_server.py --port 8767`，沿用原 GLB／JSON／PNG 匯出行為。一般網頁伺服器不載入 lookdev。

lookdev POST 白名單僅含四張指定 PNG，不接受 GLB、JSON、原 `captures/web/` 或任意路徑。實際執行時 PNG 由協調者啟動的伺服器寫入；本輪未覆寫協調者提供的截圖。

## 算圖接線

伺服器先附加 lookdev，再附加 capture hook。lookdev 使用區塊作用域與動態 imports，避免一般模式下載後製模組。未包裝 `setNight`：每次外層算圖前讀取 `night`、套用絕對數值，避免動畫覆蓋或乘數累積；原日夜海面、雲朵、花園和許願邏輯繼續運作。

順序為 RenderPass → GTAOPass → UnrealBloomPass → BokehPass（medium 跳過）→ OutputPass → ShaderPass（顯示空間調色）。半浮點 HDR composer 保留高亮值，Bloom 在 AgX 前計算，OutputPass 做 AgX 色調映射與 sRGB 輸出，之後調色 pass 依序調整飽和度、以 0.5 為中心的對比、色溫 RGB 增益，最後限制至 0–1；保留 alpha，不再次套用色調映射或 sRGB 編碼。正色溫偏暖、負值偏冷，單位為增益偏移而非 Kelvin；R × (1+t)、B × (1−t)。這是 Punchy 方向的簡易近似，不是 Blender Punchy 的完整轉換。這是亮度門檻 Bloom，並非用物件圖層挑選；所有超過門檻的高亮處都可能溢光。

包裝 `renderer.render`：只有主 scene／camera 且 render target 為螢幕的外層呼叫進 composer；composer 內部以旗標繞回原 render，包含 RenderPass、AO 法線、景深深度與全螢幕四邊形，避免遞迴。旗標以 finally 復原，其他離屏算圖直接繞過。每次外層呼叫檢查 renderer 大小與 pixel ratio，故正常 resize 與擷取尺寸都同步。

AO 與景深深度算圖暫時隱藏透明材質、ShaderMaterial、Sprite、Points、Line，完成後復原；beauty 色彩仍保留這些物件。此取捨避免遮罩平面變成實心 AO，但透明玻璃等不會提供正確遮蔽／景深深度，須看圖確認。

焦距每幀取 `controls.target` 的相機空間正深度，隨四個鏡位更新。未新增假移軸焦帶，使用輕微真正深度模糊。擷取保留當下島民與主角，與原匯出分支會移除群眾／主角不同；人物位置會依按下時間改變。S04 沿用既有靜態全景，不觸發流星事件。

## 第 2 輪參數與理由

參數來源是 hook 頂端 `LOOKDEV_PARAMS`；JSON 為快照，不會被瀏覽器讀取。修改 hook 後同步 JSON，再執行一致性檢查。主控台可查看 `window.__lookdev`；修改日夜 AO／Bloom／景深／grading／seaColor 值後呼叫 `__lookdev.refresh()`。品質與陰影初始化設定請修改後重新載入。

| 共用參數 | 初始值 | 理由 |
|---|---|---|
| quality | high | 先供視覺審查；展示設備可用 medium |
| toneMapping | AgX | 與 Blender 目標統一；不是色彩完全一致的保證 |
| shadow.type | PCFShadowMap | radius 可用；避免 VSM 光滲漏風險，PCFSoft 的 radius 不生效 |
| shadow.mapSize | 2048 | 保留原陰影解析度，避免額外大幅增加成本 |
| shadow.radius | 3 | 加寬濾波，讓硬陰影邊緣稍軟；非物理面光源半影 |
| shadow.normalBias／bias | 0.02／-0.0001 | 保守壓低接地分離；須檢查斜面痤瘡與陰影偏移 |
| high：aoResolutionScale／aoSamples／dof | 1／16／true | AO 全解析度、保留輕景深 |
| medium：aoResolutionScale／aoSamples／dof | 0.5／8／false | AO 像素數降為四分之一，另減少取樣；關掉景深 |

| 日夜參數 | 日間 | 夜間 | 理由 |
|---|---|---|---|
| exposure | 1.4 | 1.1 | 日間提高亮部；夜間保留 |
| grading.saturation | 1.3 | 1 | 還原日間綠色與粉色；夜間中性 |
| grading.contrast | 1.1 | 1 | 日間補回對比；夜間中性 |
| grading.temperature | 0.015 | 0 | 日間輕微暖色增益；夜間中性 |
| seaColor | #42b8d0 | 還原原始 #60a8b3 | 僅日間補償受光海面的青藍色 |
| background | #c5e4e8 | #172e49 | 清爽天空與深藍夜色；霧色同步 |
| fogNear／fogFar | 130／280 | 130／280 | 將霧推遠，降低島內灰霧感 |
| hemisphere.sky | #dceeff | #9fbeeb | 日間冷暖平衡，夜間偏冷填補 |
| hemisphere.ground | #8f9971 | #535f68 | 土地反光避免偏粉，夜間降低暖綠污染 |
| hemisphere.intensity | 1.3 | 0.5 | 提亮日間陰影面，保留主光方向 |
| sun.color | #ffe0ad | #b9d3ff | 暖金日光、冷色月光 |
| sun.intensity | 3.6 | 0.3 | 日間主光／半球光約 2.77，建立明暗；夜間仍辨識輪廓 |
| fill.color | #d4e7ff | #91b6ed | 冷色柔補光 |
| fill.intensity | 0.45 | 0.24 | 避免補光抹平造型 |
| emissive.lampIntensity | 1.8 | 4 | 保留白天微亮，夜間跨過 Bloom 門檻 |
| emissive.hospitalWindowScale | 0.18 | 1.2 | 乘原醫院窗材質 strength；白天微亮、夜間強調窗光 |
| emissive.lanternIntensity | 0 | 10 | 燈塔點光源夜間加強；沿用原許願 pulse × 5，不改燈塔材質 |
| ao.radius | 0.3 | 0.65 | 縮小日間接觸遮蔽範圍；夜間保留 |
| ao.thickness | 0.4 | 0.8 | 降低日間厚度容忍，減少不相鄰表面遮蔽 |
| ao.distanceExponent | 2 | 2 | 遮蔽偏向近接範圍 |
| ao.distanceFallOff | 1 | 1 | 距離衰減初值 |
| ao.scale | 1 | 1 | 保守遮蔽尺度 |
| ao.screenSpaceRadius | false | false | 不固定成像素半徑，維持場景尺度 |
| ao.blendIntensity | 0.4 | 0.5 | 降低日間大平面髒灰；夜間保留 |
| bloom.threshold | 1.6 | 0.85 | 白天限制於 HDR 高亮，夜間讓燈光較容易溢出 |
| bloom.strength | 0.22 | 0.336 | 夜間由 0.42 降低 20%，其他夜間效果參數不變 |
| bloom.radius | 0.35 | 0.45 | 小範圍柔暈，避免整片醫院白化 |
| dof.aperture | 0.00008 | 0.00006 | 深度差帶來極輕模糊，夜間更保守 |
| dof.maxblur | 0.0015 | 0.0012 | UV 模糊半徑上限；1920 寬約 2.9／2.3 px，需確認地標清晰度 |

主光／補光位置、陰影相機範圍與粗糙度沿用現況。唯一修改色彩的材質為 `mats['sea']`（即 `sea.material`／環境模組的 `waterMat`）：日間從 #60a8b3 調為 #42b8d0，夜間複製 hook 初始化保存的原色。它是受光的 MeshStandardMaterial，暖色主光、較弱環境光與 AgX 壓縮共同造成偏灰綠；波紋 shader 也會微量混入灰綠白，但未更動波紋、近岸透明材質或海岸線。原因為程式與截圖判讀，尚未做 GPU 分項隔離量測。日間以較高藍／綠、較低紅的基色補償，再由全畫面調色恢復彩度。GTAO 去雜訊沿用 r160 預設（16 samples、radius 8），Bloom 使用內建五層模糊，OutputPass 輸出 sRGB，再進入調色 pass。

API 依據：[r160 GTAOPass 原始碼](https://github.com/mrdoob/three.js/blob/r160/examples/jsm/postprocessing/GTAOPass.js)、[r160 BokehPass 原始碼](https://github.com/mrdoob/three.js/blob/r160/examples/jsm/postprocessing/BokehPass.js)。另核對 [r160 OutputPass](https://github.com/mrdoob/three.js/blob/r160/examples/jsm/postprocessing/OutputPass.js) 與 [ShaderPass](https://github.com/mrdoob/three.js/blob/r160/examples/jsm/postprocessing/ShaderPass.js)，確保調色在顯示空間執行；新 shader 的 WebGL 執行仍待驗證。

## 效能預算（估計，非量測）

以下為 1920×1080、DPR 1、一般獨立 GPU 的粗略規劃區間。展示設備 GPU 未知，不能據此宣稱 30 fps；整合顯示晶片可能顯著較慢。

| 項目 | high 額外成本／幀 | medium 額外成本／幀 | 主要工作 |
|---|---|---|---|
| RenderPass | 約原場景成本，另 0.2–1 ms 離屏開銷 | 同左 | 主場景與陰影，不含在以下後製總和 |
| GTAO | 約 2–6 ms | 約 0.8–3 ms | 再畫法線／深度、AO、去雜訊、合成；減解析度不減物件提交次數 |
| UnrealBloom | 約 1–3 ms | 約 1–3 ms | 門檻與多層模糊；兩品質相同 |
| Bokeh | 約 2–5 ms | 0 ms | 再畫深度、多次色彩取樣；medium 不執行 |
| OutputPass | 約 0.2–0.6 ms | 約 0.2–0.6 ms | AgX 與 sRGB |
| 後製合計（不含 RenderPass） | 約 5.2–14.6 ms | 約 2–6.6 ms | 僅規劃預估 |

本輪新增一個全螢幕調色 pass，額外耗時尚未量測，未計入上表。

30 fps 的整幀預算是 33.3 ms。測試需固定瀏覽器尺寸、DPR、島民數與鏡位，暖機後各品質觀察至少 30 秒，記錄中位與低百分位 fps；可用瀏覽器 Performance／GPU 計時工具量測，不能把 CPU `performance.now()` 包 pass 的時間當作 GPU 耗時。原 `hopeStudy.audit().drawCalls` 在多 pass 下只反映最後一次 renderer 計數，不代表整幀 draw calls。

一般互動沿用原網頁最高 DPR 1.5，像素數可達此預算的 2.25 倍；擷取固定 DPR 1。若 medium 仍未達標，下一步才評估降低整體 DPR／Bloom 解析度或場景 draw calls。

## 已檢查與待確認

已通過四項 Python 契約測試、兩模式組合 JavaScript 語法檢查，以及 high／medium 的 render 替身測試（不遞迴、尺寸更新、日夜調色／海色還原、refresh、例外復原、離屏繞過）。沒有啟動本機伺服器、瀏覽器或 Blender。

仍需協調者實測：CDN 模組載入、GPU framebuffer／shader 相容性、四張 PNG 寫入、日夜切換、擷取後動畫恢復、AO 邊緣與透明物件瑕疵、陰影痤瘡、燈光是否過曝、地標辨識、實機 fps。GTAO 為螢幕空間效果，畫面外物件不能提供遮蔽；低解析度 AO 可能有輪廓暈邊。

請回傳四張 high 圖、四張 medium 圖或其差異、瀏覽器主控台錯誤與展示設備／解析度／DPR／fps。這一版不宣稱已達概念圖外觀，也不宣稱已達 30 fps。
