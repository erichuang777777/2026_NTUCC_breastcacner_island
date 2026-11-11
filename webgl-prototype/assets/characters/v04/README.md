# 希望島共用角色 v04

2026-11-11。狀態：第一輪網頁改善候選，尚非最終美術定稿。

六款原生立體 GLB：病友、陪伴者、醫師、護理師、手術醫師、手術室護理師。各款共用 18 根骨骼、關節混合權重，以及 idle / walk / wave / read 四組動畫。臉部、衣著、頭巾、五官、配件均為立體網格；不使用人物平面圖代替模型。

參考既有玫瑰頭巾病友美術與 `hope-characters.js` 的六款服裝配色。未使用外部下載的角色模型。

可重建來源：`component-system/hope-island-component-kit/assets/CHR-VISITOR-001/source/build_refined_cast_v04.py`。
可編輯病友母檔：同目錄 `refined-cast-v04.blend`。

本機重建（專案根目錄）：

```sh
/Applications/Blender.app/Contents/MacOS/Blender --background --threads 4 --python component-system/hope-island-component-kit/assets/CHR-VISITOR-001/source/build_refined_cast_v04.py
```

執行後須將本資料夾同步至 `webgl-prototype/dist/assets/characters/v04/`。網頁使用 `hope-avatar.js` 載入，玩家、居民與設定預覽共用此模組。髮型配件依語意群組切換；上衣、褲裝、膚色、頭髮可獨立換色。網格保留共用、材質依角色實例複製，移除角色時不釋放其他角色仍在使用的網格。

數量與容量紀錄見 `manifest.json`。此版未製作遠近細節切換，不保證手機畫格率。近景表情、服裝輪廓及個別人物辨識度仍可依美術審閱調整。
