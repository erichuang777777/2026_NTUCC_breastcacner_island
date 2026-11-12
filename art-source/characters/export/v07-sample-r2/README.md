# v07-sample-r2 執行與驗證狀態

第二輪腳本已完成，尚未產生 GLB、三角形統計與渲染圖。2026-11-12 在受限環境嘗試 Blender 5.2.3 兩次，均在執行 Python 腳本前以錯誤碼 139 崩潰；詳見 `../../build-r2.log`。Python 語法檢查通過。

於可執行 Blender 的環境，在專案根目錄依序執行：

```sh
blender --background --python art-source/characters/scripts/build_cast_v07_sample_r2.py
blender --background --python art-source/characters/scripts/render_cast_lineup_r2.py
```

建模成功後，本資料夾會有 `patient-scarf.glb`、`nurse.glb`、`manifest.json`；實際三角形數記錄在 manifest 的 roles[].triangles。保留每角色情境配件、18 根骨骼與八個動作。骨架位置逐項與第一輪 manifest 比對，總高 1.57、腳底 0、38,000 三角形上限與基準 130% 上限均有斷言。

渲染預設 idle 第 1 格，正面與側面順序皆為：病友 r1、病友 r2、護理師 r1、護理師 r2。輸出 `../../renders/v07-sample-r2-front.png`、`v07-sample-r2-three-quarter.png`、`v07-sample-r2-panorama.png`。全景只呈現兩位 r2，使用簡化沙岸／草地島嶼作為比例情境，並非正式遊戲場景；透視鏡頭距目標 12 單位、俯角 30 度、48 mm。

## 修正

- 鞋底改用圓潤橢圓環截面，與鞋面相同輪廓，移除薄方板。
- 頸部加粗、縮短；頭部幾何放大 9%，以頂部 1.57 為錨點向下延伸，骨架位置不變。
- 臉頰及額頭使用連續曲面起伏，柔化下巴、眼球向內移，保留兩人的臉型差異與睫毛。
- 護理師瀏海分線、重疊髮束、內收髮尾與深淺色分層。
- 角色幾何未含文字；第一輪場景的立體文字有投影到頭巾的可能，r2 移除所有場景標籤，待渲染確認痕跡消失。
- idle／walk 使用上臂外展 10 度、肘彎 15 度；原本幾何偏移移除，避免重複旋轉。手掌保持朝內，保留拇指造型。walk 第 1–25 格逐格檢查手掌是否越入軀幹最寬的橫向範圍，最小間距記錄於 manifest。
- 病友肩部收圓下垂，保留胸腰臀曲線、短袖制服、立體口袋、袖口／褲管反摺、卡其褲與識別證。
- 皮膚 Blender Subsurface Weight 0.15、roughness 0.43；glTF 使用偏暖 base color 與較低 roughness 代替次表面散射，布料 roughness 維持 0.8。

尚待實際執行、視覺檢查及正式 WebGL 的動作／眨眼／換色驗證。手掌間距檢查只涵蓋 walk 與橫向軀幹包絡，並非全身碰撞求解；其他動作仍需目視確認。未更動第一輪檔案，未 commit。
