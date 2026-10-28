# 清食指南｜清大學餐及周邊餐廳選擇器

以附件「清大食物 (1).xlsx」的 14 間餐廳製作的繁體中文網站，使用 Vite 與原生 JavaScript，無需 API 金鑰、資料庫服務或登入即可使用。

## 執行

需求：Node.js 20.19+ 或 22.12+（已在 Node.js 24 驗證）。

```sh
npm ci
npm run dev
```

開發伺服器預設為 5173 埠。正式建置：`npm run build`，靜態網站產物在 `dist/`；`npm run preview` 可檢查正式產物。測試：`npm test`。

## 功能

- 最多 8 位用餐者，各自設定姓名、預算級距、料理偏好及可接受步行時間。
- 預算、距離、口味權重可調；預設嚴格符合全員預算及距離，可取消以顯示折衷選項。
- 區域、料理／名稱搜尋、用餐情境、台灣指定時間營業篩選。
- 推薦排序、推薦理由、詳細資料、Google 地圖搜尋、隨機選餐。
- 收藏以 localStorage 儲存於目前瀏覽器；不跨裝置。無後端，不會上傳用餐者資料。

## 資料與限制

`src/restaurants.json` 是由原始 Excel 匯出的唯讀餐廳資料庫。價格 1、1.5、2、2.5 是附件原始級距，沒有定義台幣金額，因此網站不虛構金額。類型、時間、特殊營業資訊及情境旗標皆保留原始資料。

附件沒有經緯度或路線資料。`src/recommend.js` 的步行時間為區域估算：從清大校門到小吃部 8 分鐘、清夜 5 分鐘；從小吃部到當區 2 分鐘、清夜 12 分鐘；從清夜到當區 3 分鐘、小吃部 12 分鐘。不使用 GPS 或即時路線，請按實際需求調整這些估算。

- 未提供營業時間的餐廳標示待確認，啟用只看營業時會排除。
- 假日條件按週六、日推定，未包含國定假日；公休按表格指定星期計算。
- 時段採起點包含、終點不包含，00:00 表示跨至午夜的結束時間。查詢以台灣時區為準。
- 可離線使用核心功能；線上 Google 字型會退回系統字型；外部地圖搜尋需要網路。

重新匯入相同欄位格式的檔案：

```sh
python scripts/import-restaurants.py '/path/to/清大食物 (1).xlsx'
```

此腳本只讀取表格資料，不執行附件內任何指令。匯入後請重新執行測試與建置。

## 分數公式

對每位用餐者計算：預算內價格得分 1，超出每 1.5 級距線性遞減至 0；步行可接受時得分為 `1 − 0.25 × 步行分鐘 / 可接受分鐘`，超過時為 `max(0, 0.6 − 超出分鐘 / 15)`；料理不限或符合得分 1，不符合為 0.15。

先對全員各項取平均，再按三個權重加權，換算為 0–100 分、四捨五入。權重皆為 0 時採等權平均。平手依步行時間、價格級距、原始資料順序排序。推薦分數代表條件符合程度，並非餐廳評價。

## 部署至 Streamlit Community Cloud

此專案的主要介面是 JavaScript 網站。`scripts/import-restaurants.py` 僅供匯入 Excel，**不是網站入口**。若將它選為 Streamlit 的入口，原版本會因缺少命令列參數產生 `IndexError`。

已提供可沿用完整網站介面的 Streamlit 入口：

1. 在 Streamlit Cloud 建立或重新部署 App，選擇此 GitHub 儲存庫及 `main` 分支。
2. **Main file path 請選 `streamlit_app.py`**，不要選 `scripts/import-restaurants.py`。
3. 依 `requirements.txt` 自動安裝依賴，不需要提供 Excel 路徑、API 金鑰或執行 npm。
4. 若現有 App 仍指向匯入腳本，請更改部署入口；若介面無法修改入口，請以正確入口重新建立 App。

本機驗證：

```sh
pip install -r requirements.txt
python -m unittest discover -s tests -p 'test_*.py'
streamlit run streamlit_app.py
```

`npm run build` 會同時生成 `dist/` 與 `streamlit_assets/site.html`。後者為自包含網站，需一起提交到 GitHub，讓 Streamlit 不必在伺服器安裝 Node.js。修改前端或餐廳資料後，請重新建置並提交這個檔案。Streamlit 內透過自動調整高度的嵌入頁面顯示網站，收藏依瀏覽器的儲存政策保存。若瀏覽器限制嵌入頁面儲存，收藏僅限本次開啟。

如採 Vercel、Netlify 或其他靜態網站平台，建置命令仍為 `npm run build`，發布目錄為 `dist`，不需使用 Streamlit。
