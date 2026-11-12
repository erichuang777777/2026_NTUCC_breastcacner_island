# 環境道具套件 v01

本版以 V12 確認板的圓潤木條、奶油石材、葉團、五瓣花與分層岩岸為造型依據。未製作橋樑。尚未在 Blender 執行，GLB、manifest、palette 與展示板會由以下指令產生。

## 執行

以下以 macOS 預設 Blender 安裝位置為例；兩支腳本皆不依賴目前工作目錄。

```sh
/Applications/Blender.app/Contents/MacOS/Blender --background --python-exit-code 1 --python /Users/eric777/Desktop/Breastcancer_island_of_hope/art-source/props/scripts/build_prop_kit_v01.py
/Applications/Blender.app/Contents/MacOS/Blender --background --python-exit-code 1 --python /Users/eric777/Desktop/Breastcancer_island_of_hope/art-source/props/scripts/render_prop_sheet_v01.py
```

第一支腳本成功後才執行第二支。建模程式只呼叫 glTF 匯出 operator；建模、倒角烘焙與合併均使用資料 API、bmesh 與 evaluated mesh。展示板僅使用 glTF 匯入與背景渲染 operator，不依賴 3D 視窗；EEVEE 實際渲染仍需要可用的圖形環境。

可先執行不需要 Blender 的靜態檢查：

```sh
python3 /Users/eric777/Desktop/Breastcancer_island_of_hope/art-source/props/scripts/check_prop_sources_v01.py
```

## 檔案

- `scripts/build_prop_kit_v01.py`：集中調色盤、13 件道具、共用材質、兩段倒角、匯出與驗收。
- `scripts/render_prop_sheet_v01.py`：重新匯入 13 件 GLB，使用 AgX、暖色太陽、柔光與米色背景，產生 2560×1440 展示板。為便於審查，小件採展示倍率，各件標籤明示倍率；GLB 本身保持原尺寸。
- `scripts/check_prop_sources_v01.py`：Python 語法、原始網格拓樸、有限座標、硬邊倒角設定、材質鍵與步道接點檢查，不會匯入或執行 Blender。
- `export/v01/<id>.glb`：執行後產生，每件一個網格，依材質分為 glTF primitives。
- `export/v01/manifest.json`：執行後產生，含實際三角形數、X/Y/Z 尺寸、材質名稱、位元組大小、SHA-256、尺寸來源及步道接點。
- `export/v01/palette.json`：執行後產生，調色盤 sRGB 色碼；材質內轉為線性數值。
- `renders/prop-sheet-v01.png`：執行展示板腳本後產生。

## 預估面數與尺寸

尺寸依序為網頁 X 寬、Y 高、Z 深；單位沿用網頁場景單位。下表尺寸為純 Python 直接計算的**倒角前包圍盒**；倒角後最終尺寸與面數以 manifest 為準。面數估計包含兩段倒角，不是 Blender 實測。

| ID | 預估三角形數 | 倒角前尺寸 X × Y × Z | 尺寸來源／設計選擇 |
|---|---:|---|---|
| bench | 約 1,404 | 0.700 × 0.630 × 0.270 | `webgl-prototype/hope-landscapes.js:22`，座板 .70/.07/.27、背板最高 .63；把腳底 .005 的原有偏移歸零。 |
| lamp | 約 1,260 | 0.164 × 0.750 × 0.164 | `webgl-prototype/taiwan-study.js:69`，柱底 .70、燈罩頂 1.45，局部高度 .75；柱徑與罩寬沿用 .035/.025 與 .13，新燈帽略寬。 |
| flowerbed-round | 約 3,880 | 0.740 × 0.521 × 0.740 | `webgl-prototype/hope-landmark-gardens.js:11–17`，牆半徑 .37、高 .11，原花朵最高約 .525；花型改為五瓣。 |
| flowerbed-long | 約 3,576 | 1.480 × 0.521 × 0.740 | 新增長條變體，長度取圓花圃直徑兩倍，其餘同圓花圃；原程式沒有同型道具。 |
| shrub-cluster | 1,032 | 0.790 × 0.400 × 0.568 | `webgl-prototype/hope-environment.js:63` 原地被分布半徑 .20；新設計三種主要葉團半徑 .19/.25/.16，另有底部葉團。非既有灌木的精確替換尺寸。 |
| tree-round | 約 1,788 | 1.033 × 1.275 × 0.756 | `webgl-prototype/hope-environment.js:70–75`，沿用樹幹與三顆主要葉團尺寸，採既有 .82 倍；新增三顆葉團與根草，深度稍增加。 |
| path-straight | 約 972 | 1.200 × 0.060 × 1.200 | 新模組。`webgl-prototype/taiwan-study.js:58` 明載沒有步道網格；`:63` 樹避開路線中心 .72，故採寬 1.20，並非從既有磚塊讀出的尺寸。 |
| path-curve | 約 1,200–1,450 | 2.400 × 0.060 × 2.400 | 新模組，90° 彎道內徑半徑 1.20、外徑半徑 2.40，寬同直段，占 2×2 格。 |
| path-plaza | 約 972 | 1.200 × 0.060 × 1.200 | 新模組，四邊均可連接；奶油色外圈、粉色中心，磚距 .40。 |
| rock-shore-a | 約 1,800–2,300 | 1.082 × 0.533 × 0.935 | `webgl-prototype/hope-environment.js:60`，沿用 .22/.29/.36 岩塊半徑；重作分層高度與群組配置，非原散石完整包圍盒。 |
| rock-shore-b | 約 1,800–2,300 | 1.123 × 0.493 × 0.851 | 同上，替代配置。 |
| foam-ring | 320 | 1.455 × 0 × 1.170 | 新增局部雙圈，配合本版岩石群；`webgl-prototype/hope-environment.js:12` 是全島浪花線，無可沿用的單件尺寸。 |
| signpost | 約 844 | 0.515 × 0.733 × 0.200 | `webgl-prototype/hope-landmark-gardens.js:30–33` 原橫式入口牌寬 1.50，頂部離地 .7325；新直立牌僅沿用高度，牌面寬 .47，藍柱與立體箭頭為新增設計。 |

模型在匯出前檢查實際面數：小件 300–1,500，花圃／樹 1,500–4,000，岩石 800–2,500。若超出範圍會停止並列出道具 ID 與面數，不會自動降低幾何品質或輸出成功 manifest。舊輸出不會預先刪除；失敗重跑時請以終端 `PROP_KIT_COMPLETE` 確認全套成功，避免把先前 manifest 當成本次結果。

## 座標、拼接與材質

採網頁座標設計，`(x,y,z)` 轉 Blender `(x,-z,y)`；標準 glTF 匯出轉回 `(x,z,-y)`。這與現有角色腳本相同；流程文件的反向轉換文字有正負號不一致，本版未修改該文件。所有匯出物件位移、旋轉均為零，縮放為一，實際包圍盒底面中心為原點；長椅與牌面朝網頁 +Z。

步道頂面 Y=.06。直段／廣場一格 1.20，彎段兩格 2.40，所有接縫寬 1.20；倒角在接縫留下細磚縫；彎段倒角後會校正外框為 2.40，以維持格線尺寸，接點是名義中心線，磚緣存在倒角等級的微小差異。彎段接點為 `(.6,0,-1.2)` 與 `(-1.2,0,.6)`，向外分別為 -Z、-X。將直段放在 `(.6,0,-1.8)` 即可接第一端；第二端接直段時轉 Y 軸 90°，位置 `(-1.8,0,.6)`。其他轉向沿用 90° 旋轉，接點詳見 manifest。

所有材質以 `hope-prop-` 開頭，同名同參數，不含程序式貼圖。Roughness=.72（浪花 .65）、Metallic=0。路燈單獨使用 `hope-prop-lamp-glow`，Emission Strength=.7，網頁載入後可依名稱調整 `emissiveIntensity`。未加入需由網頁控制的真實點光源。

浪花為雙面、Alpha=.68 的平面環帶，原點 Y=0。網頁擺放時應置於海面之上約 .005，避免深度衝突；與既有動態海面的互動需由整合端驗證。展示板讀取匯出 GLB，因此能檢視匯出後的材質與軸向。

## 已驗證與待驗證

已通過純 Python 靜態檢查，確認 13 件都有幾何、材質鍵存在、實心零件原始拓樸封閉、硬邊零件配置倒角，並檢查步道接點。

尚未執行 Blender，未驗證 Blender 5.2.3 的 modifier 求值、glTF 匯出／匯入、透明材質轉換、實際面數、最終包圍盒、展示板構圖與陰影。GLB 與 PNG 尚未產生。網頁材質合併、實例化、大量擺放效能與碰撞亦未測試；本任務未修改網頁或其他工作區。
