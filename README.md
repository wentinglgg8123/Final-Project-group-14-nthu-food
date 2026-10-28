# 清食指南｜清大學餐及周邊餐廳選擇器

以 Python／Streamlit 實作的多人選餐網站，包含附件「清大食物 (1).xlsx」的 14 間餐廳。不需要 Node.js、JavaScript 建置、API 金鑰或額外資料庫服務。

## 執行與部署

建議 Python 3.12。於專案根目錄執行：

```sh
python -m venv .venv
source .venv/bin/activate
pip install -r requirements.txt
streamlit run streamlit_app.py
```

Windows 的虛擬環境啟用指令為 `.venv\Scripts\activate`。

Streamlit Community Cloud 設定：

- Repository：`wentinglgg8123/Final-Project-group-14-nthu-food`
- Branch：`main`
- Main file path：**`streamlit_app.py`**

依 `requirements.txt` 自動安裝依賴後即可啟動，不需要上傳 Excel。`scripts/import-restaurants.py` 是資料匯入工具，不是網站入口。原 Vite／JavaScript 版與嵌入的建置檔已移除，請勿再使用 npm 或將此網站發布為靜態 dist 目錄。

## 功能

- 最多 8 位用餐者，分別輸入姓名、預算上限、料理偏好與偏好區域。
- 調整預算、口味、區域偏好權重，依全員平均符合程度計算推薦分數。
- 預設符合全員預算；關閉此條件後可查看折衷選項。
- 搜尋、區域、情境、台灣時間營業篩選及推薦理由。
- 完整餐廳資料庫、店家詳情、收藏、隨機選餐。
- 每間餐廳皆提供 Google Maps 連結，卡片與詳情連到相同店家查詢。
- 桌面側欄輸入條件；手機可由左上角展開側欄。

收藏編號保留在網址的 `favorites` 查詢參數，重新整理或加入書籤後可保留，不需登入。分享網址也會分享其收藏編號。姓名、用餐條件僅在目前 Streamlit 工作階段內使用，不存入網址或持久資料庫。

## 金幣價格

價格保留 Excel 的 1、1.5、2、2.5 級距，不推定台幣金額。餐廳卡片及詳情以金幣圖案呈現：1.5 是一枚完整金幣加半枚金幣，2.5 是兩枚完整金幣加半枚；不會向上取整。預算選單以金幣與 `½` 標示，提供文字替代以便鍵盤與螢幕閱讀器操作。

## Google Maps 與位置

已移除先前的區域步行估算、可接受步行分鐘數與距離分數。推薦只使用附件有提供的價格、料理類型及區域資訊；區域偏好不等於實際距離。

各店連結使用 Google Maps 官方搜尋網址，帶入原始完整店名、所在區域與「新竹市」。例如漢城異國美食會查詢「新竹市 國立清華大學 小吃部 漢城異國美食」，而非僅開啟 Google Maps 首頁。連鎖店與同名店可能需要在地圖確認分店；附件沒有提供 Place ID、地址或分享網址，不能保證每一筆名稱查詢都只顯示單一店家。

若有已確認的 Google Maps 店家分享網址，可在 `data/restaurants.json` 對應餐廳新增 `mapsUrl`（HTTPS Google Maps 網址），程式會優先直接開啟該店家頁面。未填時採上述店名查詢。網站不自動取得 GPS，不計算或宣稱實測路線；實際距離、路線及即時狀態請至 Google Maps 查看。

## 營業時間與資料

`data/restaurants.json` 保留附件中的餐廳名稱、區域、料理類型、價格、一般／特殊營業時間與適用情境。餐廳資料庫頁面顯示所有 14 間店，不受目前推薦篩選限制。

- 指定日期及時間以台灣時區判斷；起點包含、結束時間不包含。
- 每週日／一公休及分段營業時間按原表格判斷；午夜 00:00 是當段結束時間。
- 「假日」按週六、日處理，未另外判斷國定假日。
- 未提供營業時間時顯示「待確認」，只看營業中的篩選會將其排除。
- 實際營業資訊可能變動，請以店家公告為準。

重新匯入相同欄位格式的 Excel：

```sh
python scripts/import-restaurants.py '/path/to/清大食物 (1).xlsx'
```

只讀取表格資料，不執行附件內指令。重新匯入會更新餐廳 JSON；手動新增的 `mapsUrl` 請保留並重新補入。匯入後不需要建置前端。

## 推薦演算法

所有計算由 `foodguide/recommend.py` 執行：

1. 依搜尋、區域、情境、營業條件與全員預算限制篩選。
2. 對每位用餐者計算預算、料理、區域符合度。
3. 對所有用餐者各項取平均，再依權重加權，換算為 0–100 分。
4. 分數相同時，依價格級距、原始餐廳編號排序。

預算內得分 1；超出時為 `max(0, 1 − 超出級距 / 1.5)`。料理不限或符合得 1，其他為 0.15。區域不限或符合得 1，其他為 0.25。三項權重皆為 0 時採等權平均。推薦分數表示條件符合程度，不是顧客評價。

## Python 程式碼與驗證

介面與狀態管理在 `streamlit_app.py`，資料處理在 `foodguide/data.py`，推薦與時間判斷在 `foodguide/recommend.py`，卡片、金幣與詳情在 `foodguide/views.py`。`assets/style.css` 僅負責外觀。專案不含自行撰寫的 JavaScript；以執行程式原始碼位元組計算（Python + CSS，不含測試、JSON 資料、文件及第三方依賴），Python 超過 50%。

測試：

```sh
python -m unittest discover -s tests -p 'test_*.py'
```

涵蓋多人預算、推薦排序、權重、區域、時區、公休、分段時間、金幣數量、店家地圖網址、收藏、搜尋、資料庫、條件重設與詳情互動。瀏覽器另驗證半枚金幣裁切、手機排版及地圖連結。
