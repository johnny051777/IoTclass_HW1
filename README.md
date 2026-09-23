# ☀️ Taiwan Weather & Alert Dashboard (全台 22 縣市即時天氣與警特報)

[![Python](https://img.shields.io/badge/Python-3.10%2B-blue.svg)](https://www.python.org/)
[![Streamlit](https://img.shields.io/badge/Streamlit-1.64.0-ff4b4b.svg)](https://streamlit.io/)
[![SQLite](https://img.shields.io/badge/SQLite-3.0-003b57.svg)](https://www.sqlite.org/)
[![CWA Open Data](https://img.shields.io/badge/API-CWA%20Open%20Data-00a8e8.svg)](https://opendata.cwa.gov.tw/)

本專案依據「**AI 創新微課程 Taiwan Weather Forecast**」24 步驟藍圖打造，整合中央氣象署 (CWA) Open Data API、SQLite 資料庫與 Streamlit 互動式 Web App，提供全台灣 22 縣市即時氣象預報、天氣特報提醒、颱風動態監測、降雨機率柱狀圖與 AI 智慧穿搭/出遊建議。

---

## 🚀 Live Demo 快速啟動

### 1. 本地即時運行 (Local Live Demo)
拉取專案並在本地啟動 Streamlit 儀表板：

```bash
# 1. 複製專案儲存庫
git clone https://github.com/johnny051777/IoTclass_HW1.git
cd IoTclass_HW1

# 2. 安裝必要依賴套件
pip install -r requirements.txt

# 3. 啟動 Streamlit Web App
python -m streamlit run app.py
```
啟動後瀏覽器會自動開啟 `http://localhost:8501` 展示 Live 儀表板。

---

## 🌟 核心功能特色 (Key Features)

- 📍 **全台 22 縣市完整涵蓋**：包含臺北市、新北市、桃園市、臺中市、臺南市、高雄市、基隆市、新竹市、新竹縣、苗栗縣、彰化縣、南投縣、雲林縣、嘉義市、嘉義縣、屏東縣、宜蘭縣、花蓮縣、臺東縣、澎湖縣、金門縣與連江縣。
- ⚠️ **中央氣象署天氣警特報 (CWA Alerts)**：自動串接 `W-C0033-001` API，於頂端即時顯示大雨、豪雨、高溫與陸上強風特報。
- 🌀 **颱風與熱帶低壓監測 (Typhoon Tracker)**：即時追蹤西北太平洋颱風警戒狀態、近中心氣壓 (hPa)、最大風速與侵臺警戒區域。
- 🌧️ **雨水偵測與降雨機率柱狀圖 (PoP%)**：呈現 7 天降雨機率 (PoP%) 雙軸圖表與雨水風險提示。
- 🤖 **AI 智慧生活與出遊指數**：
  - 👕 **AI 穿搭靈感**：根據溫差與體感舒適度 (`CI`) 建議保暖大衣/薄外套/短袖。
  - ☔ **AI 攜帶雨具提醒**：根據降雨機率提供免帶傘 / 備用短傘 / 必帶大雨傘建議。
  - 🏃 **AI 戶外活動與洗車指數**：評估戶外長跑與洗車適宜度。
- 🗺️ **Folium 互動式氣溫地圖**：使用免費無須 Key 的 **OpenStreetMap**，地圖標記依平均氣溫顏色區分 (`<20°C` 🔵, `20-25°C` 🟢, `25-30°C` 🟠, `>30°C` 🔴)。

---

## 🛠️ 技術架構 (Technology Stack)

| 模組 (Layer) | 使用技術 (Technologies) |
|---|---|
| **Web Frontend** | Streamlit, Plotly Express, Folium, streamlit-folium, Custom CSS |
| **Data Backend** | Python 3, Requests, Pandas, urllib3 |
| **Database** | SQLite 3 (`data.db`), SQL DDL/DML, Idempotent Operations |
| **API Integration** | CWA Open Data REST API (`F-C0032-001`, `W-C0033-001`) |
| **Security & Config**| `.env` Environment Variables, Git Ignore Protection |

---

## 📂 專案檔案結構 (Project Structure)

```text
IoTclass_HW1/
├── app.py                      # Streamlit 視覺化主程式 (含地圖、圖表、AI建議)
├── fetch_data.py               # CWA API 抓取、JSON 解析與 SQLite 資料寫入管道
├── db_manager.py               # SQLite 資料庫 CRUD 操作與 Schema 自動遷移模組
├── data.db                     # SQLite 氣象與警特報資料庫
├── .env                        # 環境變數設定檔 (存儲 CWA_API_KEY)
├── .env.example                # 環境變數範本檔
├── requirements.txt            # Python 依賴套件清單
├── .agent/workflows/
│   └── taiwan_weather_forecast.md  # 24 步驟完整開發工作流程文檔
└── README.md                   # 專案說明與 Live Demo 指南
```

---

## 🔑 環境變數設定 (`.env`)

本專案使用 `.env` 檔案管理敏感金鑰，已設定 `.gitignore` 防止金鑰外洩：

1. 參考 `.env.example` 建立 `.env`：
   ```env
   CWA_API_KEY=CWA-55FDA6D3-A43C-4AE0-BB30-E62D5F684FB2
   ```
2. API Key 可於 [中央氣象署開放資料平台](https://opendata.cwa.gov.tw/) 免費註冊取得。

---

## 📜 24 步驟學習藍圖 (Roadmap)

本專案完整落實以下 24 個步驟開發藍圖：
1. 課程介紹 2. 台灣的天氣與生活 3. 中央氣象署 CWA 平台 4. API 資料取得 5. JSON 資料解析 6. 提取溫差數值 7. Pandas 資料整理 8. 建立 SQLite 資料庫 9. 資料庫設計 10. 查詢驗證 11. Streamlit 入門 12. 從資料庫讀取 13. 下拉選單地區選擇 14. 繪製折線圖 15. 顯示資料表格 16. 整合 Web 介面 17. 台灣地圖視覺化 18. 選擇日期顯示地圖 19. 完整成果展示 20. 程式碼優化 21. 專案上傳至 GitHub 22. 延伸應用想法 23. 回顧與重點整理 24. 下一步探索。

文檔詳見 [.agent/workflows/taiwan_weather_forecast.md](.agent/workflows/taiwan_weather_forecast.md)。

---

## 📄 授權條款 (License)

This project is licensed under the MIT License - see the [LICENSE](LICENSE) file for details.
