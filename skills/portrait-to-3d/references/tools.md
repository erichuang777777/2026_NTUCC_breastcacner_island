# 指令與設定格式

`SKILL_DIR` 是技能資料夾，`blender` 是已安裝 Blender 執行檔；macOS 範例為 `/Applications/Blender.app/Contents/MacOS/Blender`。先確認實際位置。所有輸出工具預設拒絕覆寫，讓每一版本與證據可追蹤。

一般 Python 工具只用標準函式庫；`blender_portrait.py` 在 Blender Python 內執行，`landmarks.py` 額外需要已安裝的 MediaPipe 與 FaceLandmarker task 檔案。不要為了跑一個工具覆寫全域 Python 套件。GLB 稽核只支援未壓縮且影像內嵌的檔案。

## 建立研究與標點

```sh
python3 "$SKILL_DIR/scripts/init_study.py" --out /work/portrait-study --reference /input/portrait.jpg --subject-id visitor-001 --source-note '使用者提供，供本次建模'
python3 "$SKILL_DIR/scripts/landmarks.py" --image /work/portrait-study/reference/portrait.jpg --model /tools/face_landmarker.task --out /work/portrait-study/source/landmarks.json
```

沒有 MediaPipe 時可人工標點，不能把依賴缺少說成模型製作完全不可進行。task model 需由合法來源取得並記錄版本；腳本不會自行下載或上傳照片。

## Blender 檢查與局部編輯

```sh
blender -b -t 2 --python-exit-code 1 --python "$SKILL_DIR/scripts/blender_portrait.py" -- inspect --blend /work/base.blend --report /work/inspect.json
blender -b -t 2 --python-exit-code 1 --python "$SKILL_DIR/scripts/blender_portrait.py" -- edit --blend /work/base.blend --config /work/chin.json --out /work/v02.blend --report /work/v02-edit.json
```

局部平滑設定範例（物件與頂點群組需先實際建立；數字必須依模型大小調整）：

```json
{
  "object": "Head",
  "mode": "relax",
  "vertex_group": "chin_transition",
  "iterations": 8,
  "strength": 0.3,
  "max_displacement": 0.002
}
```

`relax` 的群組權重應有平順邊界，避免把硬切範圍變成另一條折線。

量測後的位移設定範例：

```json
{
  "object": "Head",
  "mode": "handles",
  "vertex_group": "face_only",
  "max_displacement": 0.004,
  "handles": [
    {"center": [0, -0.15, 1.05], "delta": [0, 0.002, 0], "radius": 0.035}
  ]
}
```

center、delta、radius 為**物件局部座標**；沒有自動照片到模型對應。頂點群組可在 handles 模式省略，影響仍限於 radius。兩模式皆以原始頂點位置限制總位移；不是逐次允許累積超出上限。含 modifier、shape key 或共用 mesh 的模型會拒絕直接編輯，避免默默改壞既有綁定；請用專案原本流程或另存確認後的基準副本。

## 匯出與稽核

```sh
blender -b -t 2 --python-exit-code 1 --python "$SKILL_DIR/scripts/blender_portrait.py" -- export --blend /work/v02.blend --objects Head Eyes Hair --out /work/v02.glb --report /work/v02-export.json
python3 "$SKILL_DIR/scripts/audit_glb.py" /work/v02.glb --report /work/v02-glb-audit.json
```

匯出工具限定指定 mesh，保留切線、停用動畫及自訂 extras，不會替你建材質、烘焙或建立骨架。需動畫時沿用完整專案匯出設定。檢查 Blender 程序狀態與輸出報告；MCP 還需讀內部 success。

## 獨立比對頁

先使用專案現有 Three.js 套件根目錄（包含 build、examples/jsm、LICENSE），保持同一版本。若沒有，可在隔離工具目錄取得固定版本套件；不要把套件或人物素材寫進此 skill。

```sh
python3 "$SKILL_DIR/scripts/create_preview.py" --model /work/v02.glb --reference /input/portrait.jpg --three-dir /project/node_modules/three --out /work/preview-v02 --label '角色 v02'
python3 -m http.server 8002 --bind 127.0.0.1 --directory /work/preview-v02
```

腳本複製模型、原照與本機 Three.js，預覽不依賴 CDN。不要使用已被占用的連接埠或停止其他服務。只有同一電腦可連到 127.0.0.1；要手機或外網存取時，依使用者部署範圍另行設定，不能把 localhost 當公開網址。

`viewer.json` 可調：

- `rotation`：GLB 載入後的 xyz 歐拉角，弧度。若 Blender 匯出後人物朝後，先校準朝向。
- `initialAngle`：起始 y 旋轉角，相對 rotation。
- `camera.target`：世界座標 xyz；`halfHeight`：正交半高。null 時以模型框景估算，不能作精密比例驗收。
- `photo.scale`：等比顯示倍率；`xPercent`／`yPercent`：顯示位置，來源檔案不變。比對時不要裁掉需要檢查的輪廓。
- `hideInClay`：切素模時隱藏的精確 mesh 名稱，可填頭髮／眉毛細節，以免遮住頭型。

Ego Lite 先 snapshot 取得實際控制項，再操作。此範本提供 `window.portraitStudy.audit()`、`setAngle(radians)`、`setClay(boolean)`；現有希望之島使用不同 API，不能混用。audit.ready 只證明模型已載入，還需檢查原照顯示與 screenshot。下載按鈕只輸出模型 canvas，原照並排須另存整頁截圖。

這是建模檢查工具，不是已做好的使用者即時捏臉滑桿產品；若使用者要介面，須另外定義可編輯參數、保存方式及模型 morph targets。
