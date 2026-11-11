# 影像檢查島元件化建模

本資產不再把整座島與建築一次生成。電影參考圖拆成三層：

1. `terrain-circulation`：岩岸、平台、道路、廣場、階梯、碼頭與橋梁接頭。
2. `imaging-pavilion`：中央影像檢查館與室內檢查設備。
3. `garden-props`：展示棚、植栽、座椅與燈具。

每一層先獨立完成高模，再建立網頁 LOD，最後在 `ENV-TAIWAN-ARCHIPELAGO-001` 的同一個連續世界座標中組裝。不得另建「點入小島」的第二視角。

目前建模輸入：

- `reference/modeling/imaging-island-terrain-input-v01.png`
- `reference/modeling/imaging-pavilion-input-v01.png`

`generate_hunyuan_pavilion_shape.py` 僅建立中央檢查館的幾何；島體與庭園物件會使用各自的輸入與輸出，不共用一個黏合網格。
