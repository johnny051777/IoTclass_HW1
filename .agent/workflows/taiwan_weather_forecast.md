---
description: Taiwan Weather Forecast - 從氣象資料到互動式天氣預報應用 (CWA API x JSON x Python x SQLite x Streamlit)
---

# Taiwan Weather Forecast - 互動式天氣預報應用開發工作流程

本工作流程依據「AI 創新微課程 Taiwan Weather Forecast」藍圖，涵蓋從中央氣象署 (CWA) Open Data API 抓取資料、解析 JSON、建立 SQLite 資料庫、使用 Streamlit 建立 Web App 介面，到整合 Folium 視覺化地圖與 GitHub 版本管理的 24 個完整開發步驟。

## 步驟列表

### Step 1: 課程介紹 (AI x 資料 x 天氣 x 實作)
- [ ] 確定專案目標與學習地圖
- [ ] 展示最終 Taiwan Weather Dashboard 成果目標

### Step 2: 台灣的天氣與生活 (氣象的重要性)
- [ ] 了解天氣資料對日常生活與決策的重要性
- [ ] 探討智慧氣象應用案例

### Step 3: 中央氣象署 CWA Open Data 平台
- [ ] 註冊中央氣象署開放資料平台帳號 (https://opendata.cwa.gov.tw/)
- [ ] 取得個人 API 授權碼 (API Key)
- [ ] 選擇所需預報資料集 (如 F-C0032-001 一般天氣預報)

### Step 4: API 資料取得 (使用 Requests 取得 JSON)
- [ ] 使用 Python `requests` 套件呼叫 CWA API
- [ ] 傳入 Header 或 URL 參數 (Authorization Token)
- [ ] 取得 JSON 格式的回應資料 (`resp.json()`)

```python
import requests

url = "https://opendata.cwa.gov.tw/api/v1/rest/datastore/F-C0032-001"
headers = {"Authorization": "YOUR_CWA_API_KEY"}
response = requests.get(url, headers=headers)
data = response.json()
```

### Step 5: JSON 資料結構解析 (找到氣溫資料的位置)
- [ ] 分析返回的 JSON 物件結構
- [ ] 定位 `locations` / `location` / `weatherElement` 中的最低溫 (`MinT`) 與最高溫 (`MaxT`) 節點

### Step 6: 提取最高與最低氣溫 (資料分析與處理)
- [ ] 撰寫解析邏輯，抽取各區域 (地區/縣市) 的預報時間段與對應氣溫
- [ ] 將 Raw JSON 轉換為結構化列表資料 (Dictionaries / Lists)

### Step 7: 資料整理與預覽 (使用 Pandas 觀察資料)
- [ ] 將資料載入 `pandas.DataFrame`
- [ ] 檢視與整理欄位：`regionName`, `dataDate`, `mint`, `maxt`

```python
import pandas as pd

# 範例結構: regionName, dataDate, mint, maxt
df = pd.DataFrame(data_list)
print(df.head())
```

### Step 8: 建立 SQLite 資料庫 (儲存氣溫資料)
- [ ] 使用 Python 內建 `sqlite3` 模組連接或建立 `data.db` 資料庫
- [ ] 建立 `TemperatureForecasts` 資料表
- [ ] 將整理好的氣溫資料寫入資料庫

### Step 9: 資料庫設計 (TemperatureForecasts)
- [ ] 設定資料庫 Schema 如下：
  - `id`: INTEGER PRIMARY KEY AUTOINCREMENT
  - `regionName`: TEXT (例如：北部地區、中部地區、南部地區)
  - `dataDate`: TEXT (例如：2026-04-14)
  - `mint`: REAL (最低溫)
  - `maxt`: REAL (最高溫)

```sql
CREATE TABLE IF NOT EXISTS TemperatureForecasts (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    regionName TEXT,
    dataDate TEXT,
    mint REAL,
    maxt REAL
);
```

### Step 10: 查詢資料驗證 (使用 SQL 檢查資料)
- [ ] 執行 SQL 查詢確認資料正確寫入與過濾：

```sql
SELECT DISTINCT regionName FROM TemperatureForecasts;
SELECT * FROM TemperatureForecasts WHERE regionName = '中部地區';
```

### Step 11: Streamlit 入門 (快速建立 Web App)
- [ ] 安裝 Streamlit 環境 (`pip install streamlit`)
- [ ] 建立基礎 Web App 主程式檔案 (`app.py`)
- [ ] 執行 `streamlit run app.py` 測試 Hello World

### Step 12: 從資料庫讀取資料 (使用 SQL 查詢)
- [ ] 於 Streamlit App 中連結 `data.db`
- [ ] 使用 `pandas.read_sql_query` 讀取 `TemperatureForecasts` 資料表內容

```python
import sqlite3
import pandas as pd

conn = sqlite3.connect('data.db')
df = pd.read_sql_query("SELECT * FROM TemperatureForecasts", conn)
```

### Step 13: 下拉選單選擇地區 (互動式操作)
- [ ] 使用 `st.selectbox` 提供地區選單 (北部地區、中部地區、南部地區、東北部地區、東部地區、東南部地區)
- [ ] 根據使用者選擇過濾 DataFrame 顯示內容

### Step 14: 繪製折線圖 (一週最高與最低氣溫)
- [ ] 使用 `st.line_chart` 或 `plotly` / `altair` 繪製一週最高氣溫 (`MaxT`) 與最低氣溫 (`MinT`) 雙折線圖

### Step 15: 顯示資料表格 (清楚呈現一週資料)
- [ ] 使用 `st.dataframe` 或 `st.table` 清楚展示該地區特定日期區間的氣溫數據表格

### Step 16: 整合 Web App 介面 (選地區看氣溫預報)
- [ ] 統整 Selectbox、圖表與數據表格於統一儀表板 Layout 中
- [ ] 提供流暢互動體驗

### Step 17: 進階：台灣地圖視覺化 (使用 Folium + Streamlit)
- [ ] 安裝 `folium` 與 `streamlit-folium`
- [ ] 結合台灣縣市/區域 GeoJSON 繪製顏色區分的地圖 (溫度區間標示: <20°C, 20-25°C, 25-30°C, >30°C)

### Step 18: 選擇日期顯示地圖 (互動式天氣地圖)
- [ ] 加入 `st.date_input` 日期選擇器
- [ ] 地圖根據所選日期顯示全台各地區平均或高低溫資訊 Popup / Tooltip

### Step 19: 完整成果展示 (Taiwan Weather Dashboard)
- [ ] 驗證並展示全功能「Taiwan Weather Dashboard」儀表板

### Step 20: 程式碼品質與優化 (更好的程式設計)
- [ ] 模組化與結構化程式碼 (重構 API, DB, UI 邏輯)
- [ ] 加入 `try-except` 錯誤處理與 Exception Logging
- [ ] 設計 Idempotent 機制 (重複執行不重複插入 SQL 資料)
- [ ] 補充完整 Docstring 與註解

### Step 21: 專案上傳至 GitHub (版本管理與備份)
- [ ] 初始化 Git 儲存庫並關聯 Remote (`https://github.com/johnny051777/IoTclass_HW1.git`)
- [ ] 設定 `.gitignore` (排除 `__pycache__`, `.env`, 免傳重複資料檔)
- [ ] 執行 `git add`, `git commit`, 與 `git push` 上傳

### Step 22: 延伸應用與想法 (從天氣氣象到更多可能)
- [ ] 延伸 Line Bot 天氣預報提醒服務
- [ ] 結合旅遊行程與穿著建議功能
- [ ] 農業 / 防災極端天氣警報應用
- [ ] 結合 LLM / AI 做智慧分析預報

### Step 23: 回顧與重點整理 (你學到了什麼？)
- [ ] 複習 API 介面串接、JSON 解析與 Pandas 資料清理
- [ ] 複習 SQLite 資料庫關聯操作與 SQL 語法
- [ ] 複習 Streamlit 互動式 Web App 與 Folium 地圖整合

### Step 24: 下一步：繼續探索 (AI x Data x Real World)
- [ ] 探索更多政府 Open Data API
- [ ] 強化 Data Visualization 技能
- [ ] 運用 AI 輔助開發高效實作更多作品
