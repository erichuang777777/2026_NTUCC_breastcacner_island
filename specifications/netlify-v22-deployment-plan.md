> 2026-11-15 更新：下列為原始部署規劃；完整雲端 API 已實作，最新進度與驗證界線請見 [deployment/STATUS.md](../deployment/STATUS.md)。

# 希望島 Netlify 部署規劃 — 2026-11-12

## 已完成與尚未部署的界線

本次完成四欄位編輯、Bearer 金鑰 Agent API、多人手機控制的本機共用服務，以及院長模型。正式本機資料仍在 SQLite。尚未建立 Netlify 網站、雲端資料庫或公開網址；不可直接將 dist 拖入 Netlify 後就認為所有 API 已可使用。

## 預定結構

- Netlify：部署前端靜態頁面與模型。
- Netlify Functions：以 TypeScript/JavaScript 移植現有 Python API，維持 /api/admin/*、/api/agent/*、/api/events/*、/api/participant/* 及既有角色 API 的契約。
- Netlify Database（Postgres）：保存文章、修訂、API 金鑰雜湊、活動、參加者、角色與共享位置。此為目前建議；建立正式站點時確認帳號方案及資料放置需求。
- 附件使用持久物件儲存，保留已發布／草稿附件的讀取權限；不能寫入 Functions 的臨時檔案系統。
- 門口專屬人物與背景居民屬場景資產。手機操控者的位置由伺服器驗證與保存，手機不能指定其他角色 ID 或直接傳入任意座標。

Netlify 官方文件確認 Functions 可搭配持久 Postgres；Netlify Database 提供資料庫分支與遷移。參考：
- https://docs.netlify.com/build/functions/overview/
- https://docs.netlify.com/build/data-and-storage/netlify-database/
- https://docs.netlify.com/build/data-and-storage/netlify-database/api/

## 部署階段要完成的工作

1. 以此次 OpenAPI 規格與整合測試作為移植依據，實作全部動態 API，不只 Agent 入口。
2. SQLite 資料轉入 Postgres，保持文章 ID、版本、活動 ID、角色 ID 及金鑰雜湊；附件另行移轉。正式資料匯出檔不得放入 dist 或版本庫。
3. 更新管理登入為 HTTPS Cookie，設定正式網域；首次管理設定限制在部署流程，避免公開網站被搶先設定。
4. 先在 Deploy Preview 驗證新增／更新／發布／附件、QR 加入、手機移動、兩個投影畫面同步及權限，再正式切換。
5. 正式網址放入活動入口設定，重新下載 QR Code。Agent 只需更新 base URL，Bearer 金鑰與 POST 欄位契約沿用。
6. 現階段本機採手機約每 150 ms 提交方向、投影每 250 ms 讀取位置；上雲前須驗證延遲與請求量，若活動規模擴大，改為持久即時訊息服務推送位置，避免把高頻操控全部堆在 Functions 上。
7. 現有願望星空仍沿用舊儲存機制；正式部署時應另行移轉成共用資料，不把這次位置同步誤認為願望已跨裝置同步。

## 同步規則

每個參加者的 Bearer 憑證只能控制自己的角色；位移速度與可走區域由伺服器驗證。每筆控制有遞增序號，重送不會加倍移動；離線無新輸入就停在原處，90 秒未連線後釋出操控名額。目前同時提供七個手機操控名額，搭配五位電影人物維持十二位移動島民；院長為入口定點人物，不占操控名額。背景居民仍在各顯示端模擬，手機操控角色的位置共用。
