# 2026 臺大癌醫・乳癌希望之島

十座拼合成臺灣輪廓的互動島嶼，包含醫院、希望燈塔、角色、衛教站點、活動闖關與願望星空。

正式網站：[開啟希望之島](https://ntucc-hope-island-2026.netlify.app/) · [衛教與活動管理](https://ntucc-hope-island-2026.netlify.app/education-admin.html)。已連接 GitHub main 自動部署；新站獨立使用，舊資料留在本機。

## 完整雲端架構

- 前端：原生 JavaScript／Three.js；大螢幕投影、角色設定、手機搖桿／POV、衛教管理各有獨立頁面。
- Netlify Functions：維持 `/api/*` 路徑，處理文章與修訂、Agent POST、附件權限、活動／QR 加入、角色、闖關、操控與共用願望。
- Netlify Database（Postgres）：保存內容、活動、角色、控制序號與願望；以交易、鎖與版本條件避免跨裝置互相覆寫。
- Netlify Blobs：保存附件；分段上傳支援 12 MB，草稿附件只限管理者讀取。
- 闖關：三題四選一，答對／答錯動畫；管理頁可看各題正確率、首次作答正確率與選項分布。
- 角色移動：伺服器驗證方向、速度及碰撞，前端保留預測／修正；SSE 短連線輪替，失敗時以 polling 補送。

`skills/portrait-to-3d` 為製作人物模型的 Codex skill，不是病患端即時捏臉編輯器。網站上的角色設定仍使用已建立的角色與外觀選項。

## Netlify 部署

1. 將此 GitHub repository 匯入 Netlify；根目錄 `netlify.toml` 設定 `npm run build`，發布目錄為 `public`。
2. 在該站啟用 Netlify Database，確認 `netlify/database/migrations` 已套用。若使用自有 Postgres，設定 `DATABASE_URL` 並執行 `npm run db:migrate`。
3. 在 Netlify 環境變數（Functions scope）設定 `HOPE_ADMIN_PASSWORD_HASH`。以 `scripts/hash-password.mjs` 從 stdin 產生，不能提交密碼／雜湊。已匯入本機資料庫的管理密碼亦可使用。
4. 附件使用站點的 Netlify Blobs；正式環境自動取得權限，不在原始碼保存 token。
5. 先部署預覽，檢查 `/api/health`、管理登入／發布、附件、活動加入、兩裝置操控與願望同步，再上線並以正式網址重新產生 QR Code。

如需搬移現有 SQLite 資料，先在網站尚未被使用、目的資料庫為空時執行：

```sh
python3 scripts/export-local-data.py --database webgl-prototype/data/hope-island.sqlite3 --out .netlify/private-import.json
# 先連接 Netlify 站點、完成資料庫 schema，並提供其 Database／Blobs 環境
node scripts/import-local-data.mjs .netlify/private-import.json
```

匯出檔包含管理密碼雜湊與參加者憑證，只保留於本機忽略目錄。匯入不覆寫已有資料，不搬移舊登入工作階段、暫時操控位置或本機入口網址。瀏覽器舊願望不會擅自公開搬移；新雲端願望的文字僅原建立瀏覽器及管理者可讀，其他顯示端只接收星星狀態。

## 本機開發

```sh
npm ci
npm test
npm run build
npm run dev:api
```

`dev:api` 使用 `.netlify/hope-dev` 中的獨立 PGlite 與附件，不碰原本 SQLite。管理登入需預先設定 `HOPE_ADMIN_PASSWORD_HASH`。預設 `http://127.0.0.1:8002`，可用 `PORT` 調整。

原本 Python 服務仍可於本機使用：`python3 webgl-prototype/hope-server.py --port 8001`，來源頁面修改後需同步 `webgl-prototype/dist`。Netlify 只發布 build 產生的 `public`，不會部署 Python 服務。

## 主要入口

| 頁面 | 用途 |
| --- | --- |
| `taiwan-study.html` | 島嶼與願望星空 |
| `island-projection.html` | 大螢幕投影 |
| `education-admin.html` | 衛教文章、附件、活動與 Agent 金鑰 |
| `resident-setup.html` | 角色外觀；`?event=…` 加入活動 |
| `event-join.html?event=…` | 三題衛教闖關 |
| `mobile-controller.html?event=…` | 手機搖桿與 POV |
| `character-study.html` | 人物模型比對工作室 |
| `agent-api.html` | Agent POST 用法與 OpenAPI |

模型採 `deployment/assets.json` 明列網站所需資產，不上傳 Blender 原始檔、本機工具、資料庫與測試截圖。人物／醫院／美術參考的來源紀錄保留於對應資料夾，專案未授予所有人像或第三方素材無限制再散布權。

部署實況與待驗證項目見 [部署紀錄](deployment/STATUS.md)。Netlify 的設定及資料庫行為以[官方部署設定](https://docs.netlify.com/build/configure-builds/file-based-configuration/)、[Database API](https://docs.netlify.com/build/data-and-storage/netlify-database/api/)及[資料庫遷移](https://docs.netlify.com/build/data-and-storage/netlify-database/migrations/)為準。
