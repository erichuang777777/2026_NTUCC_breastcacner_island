# 希望之島真3D角色產線（DGX Spark）

目標：把 V10／V11 的四個正交角色視圖轉成真正的 PBR GLB，經拓樸整理與骨架動畫後，替換網站中的暫時2.5D角色。

## 1. 輸入素材

可直接使用網站目前的八方向透明圖集：

```text
assets/character-atlas.png
```

產線會自動抽取正面、左側、背面與右側。也可以自行準備四張相同角色、相同姿勢、透明背景且等比例的 PNG：

- `input/front.png`
- `input/left.png`
- `input/back.png`
- `input/right.png`

不可混入走路姿勢、投影、文字、地板或不同服裝。角色應採 A-pose 或自然站姿，手臂與軀幹保持少量間距，方便後續自動綁骨。

## 2. DGX Spark 環境

以官方 Hunyuan3D-2 多視角模型建立乾淨環境：

```bash
git clone https://github.com/Tencent-Hunyuan/Hunyuan3D-2.git
cd Hunyuan3D-2
conda create -n hope-island-3d python=3.10 -y
conda activate hope-island-3d
pip install -r requirements.txt
```

依官方 README 完成 `custom_rasterizer`、`DifferentiableRenderer` 等編譯步驟後，將本資料夾的 `generate_character_mv.py` 複製到官方專案根目錄。

## 3. 產生網格與材質

```bash
python generate_character_mv.py \
  --atlas assets/character-atlas.png \
  --output output/patient_headscarf_raw.glb
```

DGX Spark 60GB記憶體足以執行多視角形狀與材質流程。第一次執行會下載模型權重。

## 4. 必要的模型整理

AI輸出的原始GLB不能直接當遊戲角色，必須完成：

1. 移除浮游網格與封閉內部碎片。
2. 修正頭巾尾端、手指、背包帶及鞋底幾何。
3. 保留角色輪廓，重拓樸至約 20k–45k triangles。
4. 將材質整理為一組 2048×2048 PBR貼圖。
5. 原點設在雙腳中間地面，角色面向 +Z，單位使用公尺。
6. 建立 humanoid skeleton，至少包含 hips、spine、head、upper/lower arms、hands、upper/lower legs、feet。
7. 加入 `Idle`、`Walk`、`Wave` 三段動畫。
8. 匯出 `patient_headscarf.glb`，啟用 mesh compression 後目標小於 8MB。

## 5. 網站驗收條件

- Three.js讀取後身高約 3.6–4.2場景單位。
- 動畫名稱固定為 `Idle`、`Walk`、`Wave`。
- 不含燈光、攝影機或地板。
- 所有貼圖包在GLB內，不依賴外部絕對路徑。
- 角色以膠囊碰撞體移動，不使用模型網格直接碰撞。
- 建築使用獨立靜態碰撞體，角色可沿牆滑動但不能穿牆。

完成後將檔案放到：

```text
dist/assets/models/patient_headscarf.glb
```

