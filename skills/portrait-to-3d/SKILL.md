---
name: portrait-to-3d
description: 從肖像照片建立或修整可旋轉的 3D 人物頭部，進行捏臉、五官比例校準、頭髮與皮膚接合、Blender／GLB 匯出及網頁截圖比對。適用於真人相似度與角色細修；單純生成 2D 肖像或製作捏臉介面時不使用。
---

# Portrait to 3D｜肖像捏臉

交付可編輯的立體模型、可檢查的網頁預覽，以及與未修改原照的比對證據。相似度與網格／匯出正確性分開判斷；單張照片不能證明側後方的真實輪廓。

## 起點與範圍

- **既有角色細修**：先檢視使用者指出的角度、目前模型、前版截圖與建置腳本。沿用已認可部位，只修問題區域。
- **新角色**：先保存授權與來源紀錄，建立頭骨／眼眶／口腔／耳頸連續的解剖底模，再校準比例。點雲或正面三角面片只可作量測參考，不能當完整頭部交付。
- **場景整合**：只有任務包含整合時，才處理服裝、身體、骨架、動畫、LOD 與主場景效能。獨立頭部完成不等於全身角色完成。

讀取專案指示與現有工具。Blender 可直接使用 headless CLI，已設定的 MCP 亦可；不擅改全域 MCP。預設本機 CPU 2 執行緒、一次一個建置，依設備與使用者限制調整。沒有溫度監測時，不宣稱已驗證熱安全。

已有授權與素材時直接繼續；缺少側面照片可製作標註為推估的側面，不把它當成必須停工的理由。不要把照片上姓名或識別文字自動帶入衣服及介面。

## 工作順序

1. **建檔**：新工作可執行 `scripts/init_study.py`，保存原照副本及 SHA256、來源／用途、未知側面、輸出路徑與檢查狀態。使用穩定角色代號，不把個人照片寫進技能套件。
2. **量測與素模**：讀 [references/modeling.md](references/modeling.md)。先固定視角、投影與頭部尺度，再比較眉眼、鼻翼、嘴角、下巴、頭寬與髮際。可用 `scripts/landmarks.py` 本機擷取參考點，但偵測點不是深度真值。先修大輪廓，再修五官。
3. **頭髮與皮膚**：讀 [references/materials.md](references/materials.md)。把照片投影至完整曲面，側面使用連續材質；處理髮根到頭皮的接合、耳後與下巴過渡。禁止以正面圖片板或改原照掩蓋模型問題。
4. **可重現版本**：保留前版，輸出新 `.blend`、GLB、建置參數與修改紀錄。`scripts/blender_portrait.py` 提供檢查、局部頂點調整、平滑與限定物件匯出；它不是自動重建或相似度評分器。指令與設定格式見 [references/tools.md](references/tools.md)。
5. **技術檢查**：執行 GLB 檢查及必要幾何比較。不要把面數增加、頂點距離合格或載入成功視為外觀合格。
6. **視覺修訂**：讀 [references/review.md](references/review.md)。在實際網頁截圖，比較照片角度、左右側面、斜側面、後腦及素模。明顯瑕疵先修再交付。兩輪修改都沒有改善同一缺陷時，改查成因或必要參考，不以無限重生取代診斷。
7. **交付**：附預覽連結、原照並排、多角度截圖、資產雜湊、已修正項目與剩餘限制。`technical-pass`、`visual-candidate`、`user-approved` 是不同狀態，最後一項須有使用者認可。

## 隨附工具

所有路徑由參數提供。`SKILL_DIR` 指本檔案所在資料夾，不是目前工作目錄。

```sh
python3 "$SKILL_DIR/scripts/init_study.py" --out /absolute/new-study --reference /absolute/photo.jpg --subject-id visitor-001 --source-note '使用者提供，用於本次角色製作'
blender -b -t 2 --python-exit-code 1 --python "$SKILL_DIR/scripts/blender_portrait.py" -- inspect --blend /absolute/head.blend --report /absolute/inspection.json
python3 "$SKILL_DIR/scripts/audit_glb.py" /absolute/head.glb --report /absolute/glb-audit.json
```

新專案缺少比對頁時，用 `scripts/create_preview.py` 建立使用本機 Three.js 的獨立檢查頁；既有專案沿用其頁面。瀏覽器依使用者選擇；已安裝 Ego Lite 時，讀 `ego-browser` skill 與 CLI 最新指令再操作。沒有該技能時不要捏造 API，可交付預覽並如實說明尚未完成瀏覽器驗證。

不綁定生成式 3D 服務。Hunyuan 等可作初稿，仍須解剖、接合、材質與網頁檢查；新增外部服務或上傳人像須符合既有任務授權。

只有在希望之島延續角色時，讀 [references/hope-island.md](references/hope-island.md)；其中版本、座標、相機數字與人物特徵不可套用到其他肖像。
