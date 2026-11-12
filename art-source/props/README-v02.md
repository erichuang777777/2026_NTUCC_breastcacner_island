# 環境道具套件 v02：待 Blender 執行驗收

已檢視 v01 展示板與 V12 環境道具參考板。v01 所有來源與輸出均保留；本輪只寫入 `art-source/props/`，未 commit。

## 修改

- 硬物件倒角後使用平滑著色與加權法線，合併網格時保留每個角點的法線；有機網格採平滑著色，樹冠提高至每團 16 邊、10 層。
- 路燈改為四面發光玻璃、四角奶油色細框、上下金黃色框、尖頂，配深灰圓柱與倒角奶油色圓台。
- 圓花圃 9 朵、長花圃 8 朵五瓣花，花徑參數由 .045 提高為 .078–.085；加入花莖、尖葉與密集底層葉團，矮牆拆成 12／14 塊奶油色石塊。
- 灌木改為 10 個不同大小葉團、6 片尖葉與 3 朵花。
- 樹冠改為 7 個不同大小的葉團，樹幹彎曲並向根部外擴，加入草地圓盤、尖葉、小花。
- 岩岸改為錯落柱狀岩與七層輪廓；苔蘚是沿崖頂覆蓋、邊緣不規則下垂的封閉網格。
- 兩組岩岸自帶白色立體浪緣與淺青水盤；獨立浪花有雙層起伏浪緣及水盤。白色泡沫不透明，水盤 Alpha=.62。岩岸總占地因加入水盤而擴大，詳見 preflight；步道模組尺寸及接點保持原設定。
- 展示板腳本使用暖米白背景、曝光 +.65、柔和陰影與 `AgX - Punchy`。名稱已直接核對本機 Blender 5.2 的 `datafiles/colormanagement/config.ocio`；尚未執行設定驗證與渲染。
- 保留協調者的修正：迭代 `bpy.data.objects`，檢查物件存在且位於目前 view layer，再呼叫 `select_set`。

## 驗證狀態與限制

已通過 `check_prop_sources_v02.py`：語法、有限座標、索引、封閉邊拓樸、材質鍵、基本結構與預估預算。實際匯出腳本仍強制檢查 Blender 求值後的三角形數、底部置零、中心原點、有限座標與 modifier 烘焙。

本次執行 Blender 5.2.3 時，在 Python 執行前的 Metal 裝置偵測崩潰（exit 139；`supports_barycentric_whitelist` → `MTLBackend::metal_is_supported`）。因此 **v02 GLB、manifest 與 prop-sheet-v02.png 尚未產生**，也尚未完成匯出後視覺驗收。`export/v02/preflight.json` 刻意使用不同名稱，不冒充實測 manifest。未使用 v01 圖片代替 v02。

以下是原始網格加兩段倒角的解析估計，**不是 Blender 實測值**。圓角限制、角點處理可能影響最終值，特別是接近上限的路燈與長花圃；實際超標時建置會停止，不會跳過預算檢查。目前無申請超出原預算。

| ID | 預估三角形數 | 上限 |
|---|---:|---:|
| bench | 1,404 | 1,500 |
| lamp | 1,494 | 1,500 |
| flowerbed-round | 3,832 | 4,000 |
| flowerbed-long | 3,964 | 4,000 |
| shrub-cluster | 1,432 | 1,500 |
| tree-round | 3,112 | 4,000 |
| path-straight | 972 | 1,500 |
| path-curve | 1,188 | 1,500 |
| path-plaza | 972 | 1,500 |
| rock-shore-a | 2,054 | 2,500 |
| rock-shore-b | 2,054 | 2,500 |
| foam-ring | 1,404 | 1,500 |
| signpost | 844 | 1,500 |

## Blender 可執行環境中的完成指令

```sh
/Applications/Blender.app/Contents/MacOS/Blender --background --python-exit-code 1 --python /Users/eric777/Desktop/Breastcancer_island_of_hope/art-source/props/scripts/build_prop_kit_v02.py
```

確認印出 `PROP_KIT_COMPLETE` 後執行：

```sh
/Applications/Blender.app/Contents/MacOS/Blender --background --python-exit-code 1 --python /Users/eric777/Desktop/Breastcancer_island_of_hope/art-source/props/scripts/render_prop_sheet_v02.py
```

成功後以 `export/v02/manifest.json` 的實測數字為準。展示板會重新匯入 13 個 v02 GLB，輸出至 `renders/prop-sheet-v02.png`；仍須與 V12 並排檢視光線、密度、輪廓及透明水面。網頁端的透明排序、海面重疊與大量擺放效能尚未驗證。
