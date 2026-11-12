# v08 第 2 輪執行狀態

2026-11-12：已檢視既有正面、四分之三、姿勢檢查、六張原始 RGBA 與 V10 規格板，完成腳本修改；尚未重建 GLB 或渲染，既有輸出仍為第 1 輪。

## 修改

- 正面投影法線夾角嚴格小於 50°，以每位角色的雙眼搜尋種子計算深色虹膜中心，對齊可調整的 `mesh_eye_z` 與 `mesh_eye_half_width`。
- 五官貼圖只保留眼睛、眉毛、嘴巴與腮紅區域，其他像素混回同一個 skin 純色；刷手護理師不投影口罩內的嘴巴與腮紅。
- 色塊平滑 6 輪，小島門檻 60 面；平滑後重套允許區域，禁止區域改選下一個合法的近色。cream 限定軀幹前方，護理師胸牌與醫師聽診器使用較寬範圍。皮膚在頭部限於臉與耳朵區域。
- 減面、頭部調整、放下手臂後清除舊自訂法線，40° 銳邊搭配 Weighted Normal；GLB 必須帶有 NORMAL 屬性。
- 外展 15°，肩部 spine／upper_arm 依距離平滑混合；放下手臂時使用 preserve volume，將結果烘焙進休息姿勢。
- `HEAD_SCALE = 1.12`，頸部至下巴 smoothstep 過渡，只縮短身體補償頭部增加的高度，總高維持 1.57。
- 新增六人正面特寫輸出 `renders/v08-face-check.png`。
- 保留三處協調者修正；減面迴圈也不再存取失效的 group 參照。

## 已完成測試

三份 Python 語法解析與純 NumPy 測試通過，涵蓋 Lab、色塊平滑、小島合併、雙眼對位、膚色排除、五官遮罩及口罩排除。

## 執行限制與待驗證

本機 Blender 5.2.3 在 Python 啟動前於 `MTLBackend::metal_is_supported`／`supports_barycentric_whitelist` 崩潰（exit 139）。本版本僅提供 Metal，無 OpenGL 後端可切換。需協調者在可使用 Metal 的沙箱外執行以下指令，才能取得新的面數、位元組與圖像。未將舊數字當成本輪結果。

```sh
/Applications/Blender.app/Contents/MacOS/Blender --background --python art-source/characters/scripts/build_cast_v08_hunyuan.py
/Applications/Blender.app/Contents/MacOS/Blender --background --python art-source/characters/scripts/render_cast_v08.py
```

必須檢查：六位雙眼是否落在眼窩、50° 邊界是否切到五官、髮際及頭巾交界、胸牌／聽診器是否完整、wave 腋下體積、匯入後法線與 8 個動作。雙眼網格位置目前採 bbox 比例估計，尚未經本輪渲染校準；幾何原有五官雕刻與參考圖仍可能不完全吻合。
