# 階段 1 管線交付狀態

日期：2026-11-11。**工具已撰寫，尚未端到端執行，不代表階段 1 驗收完成。**

## 已新增檔案

- `webgl-prototype/tools/scene_capture_server.py`：僅綁定 127.0.0.1 的專用伺服器。在 HTTP 回應中附加擷取程式，原始網頁檔案保持不動。接收白名單內的產物，記錄來源 SHA-256。
- `webgl-prototype/tools/scene_capture_hook.js`：只供專用伺服器附加到 taiwan-study 模組。GLTFExporter 版本沿用網頁 import map（0.160.0）。固定動畫、移除主角與人群、展開 InstancedMesh，保存日夜可見性、發光材質與點光源狀態。切換實際 setView 後讀取相機，擷取純 WebGL 畫布。
- `art-source/scripts/assemble_scene.py`：GLB 匯入、軸向探針、四台相機、日夜光源、AgX／EEVEE 渲染、地標投影誤差檢查、儲存組裝 blend。
- `art-source/scripts/compare_shots.py`：以 Pillow 製作 3840×1120 並排圖；左側網頁，右側 Blender，上方標籤。
- 本文件：操作方式、限制、實際驗證狀態。

## 執行方式

在專案根目錄執行：

```sh
python3 webgl-prototype/tools/scene_capture_server.py --port 8767
```

用支援 WebGL 的瀏覽器開啟 `http://127.0.0.1:8767/webgl-prototype/taiwan-study.html`，待模型載入後按左上角「匯出 GLB 與四個鏡位」。需可連至原有 jsDelivr CDN。這個頁面固定動畫，僅供擷取；正常網站不受影響。請使用獨立瀏覽器設定檔，以避免既有願望資料影響星空。工具不提交活動或願望，也不觸發流星事件。

成功訊息出現後，應產生：

- `art-source/exports/taiwan-study-scene-v01.glb`
- `art-source/captures/shots-capture.json`
- `art-source/captures/export-manifest.json`（匯出數量、略過物件、日夜狀態）
- `art-source/captures/source-hashes.json`
- `art-source/captures/web/S01-day-overview.png`
- `art-source/captures/web/S02-hospital-entrance.png`
- `art-source/captures/web/S03-night-wish.png`
- `art-source/captures/web/S04-meteor-to-lighthouse.png`

接著執行：

```sh
/Applications/Blender.app/Contents/MacOS/Blender --background --python art-source/scripts/assemble_scene.py
python3 art-source/scripts/compare_shots.py
```

第二支腳本需要 Pillow。Blender 會輸出四張 `art-source/renders/<shotId>.png`、`art-source/blend/taiwan-study-assembly-v01.blend` 與 `art-source/captures/blender-validation.json`。最後一支腳本輸出四張 `art-source/compare/<shotId>.png`。blend 保留四台相機及 S04 夜間光線；其他鏡位需重跑腳本，以還原對應日夜材質與光源。

## 鏡位與驗證

| 鏡位 | 擷取方式 | 本次比對結論 |
| --- | --- | --- |
| S01 | 實際呼叫 setView('campus') | 未產生畫面，無法判定一致性 |
| S02 | 實際呼叫 setView('hospital')，讀取載入後 hospitalHeight | 未產生畫面，無法判定一致性 |
| S03 | setNight(true) + setView('tower') | 未產生畫面，無法判定一致性 |
| S04 | 夜間 setView('island')，overviewOffset 放大 1.08 倍、隱藏島名標籤 | 尚未確認臺灣輪廓與燈塔是否完整入鏡；沒有觸發流星 |

相機數值只有成功擷取後才寫入，不以規格中的 offset 冒充實測位置。視角使用 getEffectiveFOV()；畫布與 Blender 均固定 1920×1080。Blender 使用垂直 sensor fit。

匯出器加入無幾何的探針 `(1,2,3)`，Blender 匯入後必須為 `(1,-3,2)`，誤差小於 1e-5。模型不再旋轉；只有外部 JSON 相機與光源轉換座標。另比較醫院與燈塔基準點的網頁／Blender 螢幕投影，要求誤差小於 0.1 像素。這些檢查尚未實際執行，且即使通過，也不能取代島形與實際地標幾何的人工視覺審查。

## 已知視覺限制

- 白天 GLB 包含日夜任一狀態可見的標準網格，另存可見性及發光強度，Blender 依鏡位還原。GLB 本身不包含整套日夜切換邏輯。
- Sprite 星空、Points 星塵、Line 海岸泡沫與流星尾跡、自訂 Shader 燈塔光束／流星帶，不屬於本次標準網格匯出。它們仍可能出現在網頁截圖，GLB 中缺少；實際清單在 export-manifest。故這是幾何管線初版，尚非無損的整個視覺場景匯出。
- 程序式產生的標準網格可以匯出；CanvasTexture 是否完整匯出仍需實測。角色省略，SkinnedMesh 不烘焙。
- 網頁保留 ACESFilmic，Blender 使用 AgX；高光、飽和度與背景色觀感可能不同，未改動網頁色彩管理。
- HemisphereLight 以 World 漸層近似。EEVEE 對 World 的間接照明不等同 Three.js 的直接半球漫射，未建立光探針烘焙；環境亮度可能明顯不同。
- DirectionalLight 使用 SUN；點光源採 intensity × 4π 的幾何近似，未做光度校正，也未重現 Three.js 距離截斷。陰影、透明排序、加法混色與發光外溢不會完全一致。
- Three.js 線性距離霧尚未重建。近遠裁切沿用實際相機；霧、天空與海面外觀仍待比較。
- 動畫停止時刻不保證跨次完全相同。另有工作階段若在載入期間改寫來源，需協調固定版本再擷取；來源雜湊是啟動時記錄，並非整份專案快照。

## 本次執行紀錄與阻礙

通過：三支 Python 腳本以 `compile()` 檢查語法；JS 以 `node --input-type=module --check` 檢查語法。未新增相機實測 JSON 或假造圖片。

失敗：

1. `ego-browser nodejs` 無法啟動：`Connection Invalid error for service com.apple.hiservices-xpcservice`、`Failed to start ego lite`。電腦工具的瀏覽器連線清單也是空的。
2. 本機 socket 綁定測試：`PermissionError: [Errno 1] Operation not permitted`。此工作階段不能提升權限。
3. Blender 最小啟動測試（`--background --factory-startup --python-expr 'import bpy; print(bpy.app.version_string)'`）在執行 Python 前崩潰，exit 139。輸出含 `ArchWarn: ARCH_CACHE_LINE_SIZE != Arch_ObtainCacheLineSize()`，並寫入系統暫存區 `blender.crash.txt`。尚未確認警告是否為崩潰根因。

因此 GLB、實際鏡位 JSON、網頁 PNG、Blender PNG、blend、並排圖與投影驗證報告均未產生。需在可啟動瀏覽器、本機伺服器及 Blender 的執行環境跑完後才能驗收；若仍崩潰，應先診斷 Blender 安裝或執行環境。

## 寫入範圍

本任務只新增 `art-source/` 與 `webgl-prototype/tools/` 內檔案。沒有修改任何既有檔案，沒有寫入 scene、specifications、reviews 或微電影資料夾，也沒有 git commit。工作開始時既有的修改屬於其他工作階段。
