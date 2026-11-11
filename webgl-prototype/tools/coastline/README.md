# 臺灣海岸來源

Natural Earth 1:10m Admin 0 Countries，臺灣本島外環（原始 406 點），公有領域資料。

- https://www.naturalearthdata.com/downloads/10m-cultural-vectors/10m-admin-0-countries/
- https://github.com/nvkelso/natural-earth-vector/blob/master/geojson/ne_10m_admin_0_countries.geojson

僅擷取本島，用當地緯度修正經度比例，正北朝上，保留海岸形狀並以 0.012 場景單位簡化。十島的分隔線與水道是藝術設計，並非行政區界。此模型不是測繪用途；離島不包含在十島外輪廓內。

`build.py` 使用 Shapely 離線裁切真實海岸與內部曲線，輸出 `taiwan-coastline.js`，瀏覽器不需 GIS 套件。
