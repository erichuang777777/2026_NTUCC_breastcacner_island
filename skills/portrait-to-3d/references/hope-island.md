# 希望之島既有工作

從工作目錄辨認專案根目錄，不硬編碼使用者家目錄。以下是建立技能時的定位提示，使用時先確認現況。

- 比對頁：`webgl-prototype/character-study.html`、`.js`、`.css`；服務使用 `webgl-prototype/dist`，編輯後同步並驗證。
- 當時獨立角色為 `director-v15`，不代表主島版本。讀頁面與 manifest 確認，不強制退回 v15。
- 建置：`component-system/hope-island-component-kit/assets/CHR-VISITOR-001/source/build_director_wu_v15.py`，仍讀 v12 基準重建髮型、材質與曲面。專屬座標不能直接套到其他照片。
- 模型：`webgl-prototype/assets/characters/director-v15/`；原照：`webgl-prototype/assets/character-study/reference.jpg`。已授權本次角色製作，不代表要求公開原照。
- 授權：`art-source/director-wu/anatomy-base/sources.json` 與同目錄授權檔。
- 檢查：`webgl-prototype/reviews/v34`（髮型）、`v35`（接合與側膚）、`v36`（下顎）。
- 規劃：`specifications/taiwan-study-院區與內容管理-v20-開發規劃.md`。
- MCP 包裝：`webgl-prototype/tools/hope_blender_mcp.py`，需檢查結果 `success`，不能只看 exit 0。也可直接用 Blender CLI。

使用者要求每版 Ego Lite 截圖，禁止 computer use；姓名不顯示、原照不改、GB10 避免高熱。技能封裝不包含個人原照、模型、專屬標點或材質。
