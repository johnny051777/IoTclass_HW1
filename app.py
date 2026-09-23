import streamlit as st
import pandas as pd
import sqlite3
import folium
from streamlit_folium import st_folium
from datetime import datetime
import plotly.graph_objects as go
import db_manager
import fetch_data

# Page Configuration
st.set_page_config(
    page_title="Taiwan Weather Forecast Dashboard - 全台 22 縣市",
    page_icon="☀️",
    layout="wide",
    initial_sidebar_state="expanded"
)

# Custom Styling (CSS)
st.markdown("""
<style>
    .main-header {
        font-family: 'Outfit', 'Inter', sans-serif;
        background: linear-gradient(135deg, #0052D4 0%, #4364F7 50%, #6FB1FC 100%);
        padding: 24px 30px;
        border-radius: 16px;
        color: white;
        margin-bottom: 25px;
        box-shadow: 0 8px 24px rgba(67, 100, 247, 0.2);
    }
    .main-header h1 {
        color: #ffffff;
        font-weight: 700;
        font-size: 2.2rem;
        margin: 0 0 8px 0;
    }
    .main-header p {
        color: #f0f4f8;
        font-size: 1.05rem;
        margin: 0;
    }
    .legend-chip {
        display: inline-block;
        padding: 4px 12px;
        border-radius: 20px;
        font-size: 0.85rem;
        font-weight: 600;
        margin-right: 8px;
    }
</style>
""", unsafe_allow_html=True)

# Step 12: Ensure DB is initialized and populates data via backend
@st.cache_data(show_spinner="讀取全台 22 縣市即時氣象資料庫...")
def load_data():
    db_manager.init_db()
    data = db_manager.query_all()
    if not data:
        fetch_data.run_pipeline()
        data = db_manager.query_all()
    df = pd.DataFrame(data)
    if not df.empty:
        df["dataDate"] = pd.to_datetime(df["dataDate"]).dt.strftime("%Y-%m-%d")
    return df

try:
    df_all = load_data()
except Exception as e:
    st.error(f"資料讀取失敗: {e}")
    df_all = pd.DataFrame()

# Header Area (Step 16 & 19)
st.markdown("""
<div class="main-header">
    <h1>☀️ Taiwan Weather Forecast Dashboard</h1>
    <p>中央氣象署 CWA API x Python x SQLite x Streamlit 全台 22 縣市天氣預報</p>
</div>
""", unsafe_allow_html=True)

# Sidebar Controls (Step 13 & 18)
st.sidebar.header("🔍 縣市選擇與過濾")

# Backend API Status (API Key is hidden from UI)
st.sidebar.success("🟢 API 狀態：已連線中央氣象署 (CWA)")

if st.sidebar.button("🔄 同步即時氣象資料"):
    with st.spinner("連線中央氣象署同步最新預報..."):
        df_new = fetch_data.run_pipeline()
        st.cache_data.clear()
        st.sidebar.success("✅ 已成功同步全台 22 縣市最新氣象！")
        st.rerun()

st.sidebar.markdown("---")

if not df_all.empty:
    distinct_locations = sorted(df_all["regionName"].unique().tolist())
    distinct_dates = sorted(df_all["dataDate"].unique().tolist())
else:
    distinct_locations = ["臺北市", "新北市", "桃園市", "臺中市", "臺南市", "高雄市"]
    distinct_dates = [datetime.now().strftime("%Y-%m-%d")]

# Step 13: Region Selectbox Dropdown for ALL 22 Counties
selected_location = st.sidebar.selectbox(
    "📍 選擇縣市 (Select County / City):",
    options=distinct_locations,
    index=0
)

# Step 18: Date Picker for Map & Dashboard (Default to latest live date)
selected_date_str = st.sidebar.selectbox(
    "📅 選擇檢視日期 (Select Date):",
    options=distinct_dates,
    index=0
)

st.sidebar.markdown("---")
st.sidebar.info(f"📊 目前展現全台 {len(distinct_locations)} 個縣市氣象預報。")

# Main Content Layout - 2 Columns (Left: Trends & Table, Right: Folium Map)
col_left, col_right = st.columns([1.1, 0.9])

with col_left:
    st.subheader(f"📈 {selected_location} 氣溫預報趨勢 (MaxT & MinT)")
    
    # Filter data by selected location
    df_loc = df_all[df_all["regionName"] == selected_location].sort_values("dataDate") if not df_all.empty else pd.DataFrame()
    
    if not df_loc.empty:
        # Step 14: Interactive Line Chart with Plotly
        fig = go.Figure()
        
        # MaxT Line
        fig.add_trace(go.Scatter(
            x=df_loc["dataDate"],
            y=df_loc["maxt"],
            mode='lines+markers',
            name='最高溫 MaxT (°C)',
            line=dict(color='#eb4d4b', width=3),
            marker=dict(size=8)
        ))
        
        # MinT Line
        fig.add_trace(go.Scatter(
            x=df_loc["dataDate"],
            y=df_loc["mint"],
            mode='lines+markers',
            name='最低溫 MinT (°C)',
            line=dict(color='#0984e3', width=3),
            marker=dict(size=8)
        ))
        
        fig.update_layout(
            xaxis_title="預報時間 (Date / Time)",
            yaxis_title="氣溫 (°C)",
            hovermode="x unified",
            legend=dict(orientation="h", yanchor="bottom", y=1.02, xanchor="right", x=1),
            margin=dict(l=20, r=20, t=30, b=20),
            height=320,
            template="plotly_white"
        )
        
        st.plotly_chart(fig, use_container_width=True)
        
        # Step 15: Display Data Table
        st.subheader("📋 數據表格 (Data Table)")
        df_display = df_loc[["dataDate", "mint", "maxt"]].rename(
            columns={"dataDate": "日期 Date", "mint": "最低溫 MinT (°C)", "maxt": "最高溫 MaxT (°C)"}
        )
        st.dataframe(df_display, use_container_width=True, hide_index=True)
    else:
        st.warning(f"查無 {selected_location} 的氣溫資料。")

with col_right:
    st.subheader(f"🗺️ 全台 22 縣市地圖 ({selected_date_str})")
    
    # Step 17 & 18: Folium Map Visualization using OpenStreetMap (Free, No Key Required)
    region_coords = {
        "臺北市": (25.0330, 121.5654),
        "新北市": (24.9157, 121.6739),
        "基隆市": (25.1283, 121.7419),
        "桃園市": (24.9936, 121.3010),
        "新竹市": (24.8138, 120.9675),
        "新竹縣": (24.7033, 121.1444),
        "苗栗縣": (24.5601, 120.8217),
        "臺中市": (24.1477, 120.6736),
        "彰化縣": (24.0518, 120.5161),
        "南投縣": (23.9610, 120.9719),
        "雲林縣": (23.7092, 120.4313),
        "嘉義市": (23.4801, 120.4491),
        "嘉義縣": (23.4588, 120.5740),
        "臺南市": (22.9997, 120.2270),
        "高雄市": (22.6273, 120.3014),
        "屏東縣": (22.5520, 120.5487),
        "宜蘭縣": (24.7570, 121.7530),
        "花蓮縣": (23.9872, 121.6015),
        "臺東縣": (22.7583, 121.1444),
        "澎湖縣": (23.5711, 119.5793),
        "金門縣": (24.4493, 118.3766),
        "連江縣": (26.1505, 119.9499)
    }
    
    # Use standard OpenStreetMap tiles (100% free, no API key needed!)
    m = folium.Map(location=[23.8, 121.0], zoom_start=7, tiles="OpenStreetMap")
    
    # Filter data for selected date
    df_date = df_all[df_all["dataDate"] == selected_date_str] if not df_all.empty else pd.DataFrame()
    
    def get_color(avg_temp):
        if avg_temp < 20.0:
            return "#3498db"  # Blue
        elif 20.0 <= avg_temp < 25.0:
            return "#2ecc71"  # Green
        elif 25.0 <= avg_temp < 30.0:
            return "#f39c12"  # Orange
        else:
            return "#e74c3c"  # Red

    if not df_date.empty:
        for idx, row in df_date.iterrows():
            rname = row["regionName"]
            mint = row["mint"]
            maxt = row["maxt"]
            avg_temp = (mint + maxt) / 2.0
            color = get_color(avg_temp)
            
            coords = region_coords.get(rname, (23.8, 121.0))
            
            popup_html = f"""
            <div style="font-family: sans-serif; width: 160px;">
                <h4 style="margin:0 0 6px 0; color:#2c3e50;">{rname}</h4>
                <p style="margin:2px 0;"><b>最低溫 Min:</b> {mint}°C</p>
                <p style="margin:2px 0;"><b>最高溫 Max:</b> {maxt}°C</p>
                <p style="margin:2px 0;"><b>平均氣溫:</b> {avg_temp:.1f}°C</p>
            </div>
            """
            
            folium.CircleMarker(
                location=coords,
                radius=14,
                popup=folium.Popup(popup_html, max_width=200),
                tooltip=f"{rname}: {mint}°C ~ {maxt}°C",
                color=color,
                fill=True,
                fill_color=color,
                fill_opacity=0.85,
            ).add_to(m)
    
    # Display Streamlit-Folium Component
    st_folium(m, width=500, height=450)
    
    # Temperature Legend Chips
    st.markdown("""
    <div style="margin-top: 10px; text-align: center;">
        <span class="legend-chip" style="background:#d6eaf8; color:#1b4f72;">🔵 &lt; 20°C</span>
        <span class="legend-chip" style="background:#d4efdf; color:#117a65;">🟢 20-25°C</span>
        <span class="legend-chip" style="background:#fdebd0; color:#b9770e;">🟠 25-30°C</span>
        <span class="legend-chip" style="background:#fadbd8; color:#78281f;">🔴 &gt; 30°C</span>
    </div>
    """, unsafe_allow_html=True)

# Footer
st.markdown("---")
st.markdown("<p style='text-align: center; color: #7f8c8d;'>Code Smarter, Build a Better Tomorrow! | 全台 22 縣市 CWA 氣象預報儀表板</p>", unsafe_allow_html=True)
