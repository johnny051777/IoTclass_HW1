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
    page_title="Taiwan Weather Forecast Dashboard",
    page_icon="☀️",
    layout="wide",
    initial_sidebar_state="expanded"
)

# Custom Styling (CSS)
st.markdown("""
<style>
    .main-header {
        font-family: 'Outfit', 'Inter', sans-serif;
        background: linear-gradient(135deg, #1e3c72 0%, #2a5298 100%);
        padding: 24px 30px;
        border-radius: 16px;
        color: white;
        margin-bottom: 25px;
        box-shadow: 0 8px 24px rgba(30, 60, 114, 0.15);
    }
    .main-header h1 {
        color: #ffffff;
        font-weight: 700;
        font-size: 2.2rem;
        margin: 0 0 8px 0;
    }
    .main-header p {
        color: #e0e6ed;
        font-size: 1.05rem;
        margin: 0;
    }
    .metric-card {
        background: #ffffff;
        border-radius: 12px;
        padding: 18px;
        box-shadow: 0 4px 12px rgba(0,0,0,0.05);
        border: 1px solid #eef2f6;
        text-align: center;
    }
    .metric-title {
        color: #64748b;
        font-size: 0.9rem;
        font-weight: 600;
        text-transform: uppercase;
        letter-spacing: 0.5px;
    }
    .metric-value {
        color: #0f172a;
        font-size: 1.8rem;
        font-weight: 700;
        margin-top: 4px;
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

# Step 12: Ensure DB is initialized and populates data if empty
@st.cache_data(show_spinner="讀取氣象資料庫中...")
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
    st.error(f"資料庫讀取失敗: {e}")
    df_all = pd.DataFrame()

# Header Area (Step 16 & 19)
st.markdown("""
<div class="main-header">
    <h1>☀️ Taiwan Weather Forecast Dashboard</h1>
    <p>中央氣象署 CWA API x Python x SQLite x Streamlit 互動式天氣預報應用</p>
</div>
""", unsafe_allow_html=True)

# Sidebar Controls (Step 13 & 18)
st.sidebar.header("🔍 預報操作與過濾")

if not df_all.empty:
    distinct_regions = sorted(df_all["regionName"].unique().tolist())
    distinct_dates = sorted(df_all["dataDate"].unique().tolist())
else:
    distinct_regions = ["北部地區", "中部地區", "南部地區", "東北部地區", "東部地區", "東南部地區"]
    distinct_dates = ["2026-04-14"]

# Step 13: Region Selectbox Dropdown
selected_region = st.sidebar.selectbox(
    "📍 選擇預報地區 (Select Region):",
    options=distinct_regions,
    index=0
)

# Step 18: Date Picker for Map & Dashboard
selected_date_str = st.sidebar.selectbox(
    "📅 選擇檢視日期 (Select Date):",
    options=distinct_dates,
    index=0
)

st.sidebar.markdown("---")
st.sidebar.info("""
**專案特色:**
- CWA API / Open Data JSON 提取
- SQLite 氣溫資料庫存儲
- 雙折線圖 (MaxT vs MinT)
- Folium 台灣氣溫分區地圖
""")

# Main Content Layout - 2 Columns (Left: Trends & Table, Right: Folium Map)
col_left, col_right = st.columns([1.1, 0.9])

with col_left:
    st.subheader(f"📈 {selected_region} 一週氣溫預報 (MaxT & MinT)")
    
    # Filter data by selected region (Step 13)
    df_region = df_all[df_all["regionName"] == selected_region].sort_values("dataDate") if not df_all.empty else pd.DataFrame()
    
    if not df_region.empty:
        # Step 14: Interactive Line Chart with Plotly (MaxT & MinT)
        fig = go.Figure()
        
        # MaxT Line
        fig.add_trace(go.Scatter(
            x=df_region["dataDate"],
            y=df_region["maxt"],
            mode='lines+markers',
            name='最高溫 MaxT (°C)',
            line=dict(color='#eb4d4b', width=3),
            marker=dict(size=8)
        ))
        
        # MinT Line
        fig.add_trace(go.Scatter(
            x=df_region["dataDate"],
            y=df_region["mint"],
            mode='lines+markers',
            name='最低溫 MinT (°C)',
            line=dict(color='#0984e3', width=3),
            marker=dict(size=8)
        ))
        
        fig.update_layout(
            xaxis_title="預報日期 (Date)",
            yaxis_title="氣溫 (°C)",
            hovermode="x unified",
            legend=dict(orientation="h", yanchor="bottom", y=1.02, xanchor="right", x=1),
            margin=dict(l=20, r=20, t=30, b=20),
            height=320,
            template="plotly_white"
        )
        
        st.plotly_chart(fig, use_container_width=True)
        
        # Step 15: Display Data Table
        st.subheader("📋 氣溫數據表格 (Data Table)")
        df_display = df_region[["dataDate", "mint", "maxt"]].rename(
            columns={"dataDate": "預報日期 Date", "mint": "最低溫 MinT (°C)", "maxt": "最高溫 MaxT (°C)"}
        )
        st.dataframe(df_display, use_container_width=True, hide_index=True)
    else:
        st.warning("查無該地區的氣溫資料。")

with col_right:
    st.subheader(f"🗺️ 台灣氣溫分區地圖 ({selected_date_str})")
    
    # Step 17 & 18: Folium Map Visualization
    # Region Coordinates mapping (Latitude, Longitude)
    region_coords = {
        "北部地區": (25.0330, 121.5654),
        "中部地區": (24.1477, 120.6736),
        "南部地區": (22.6273, 120.3014),
        "東北部地區": (24.7570, 121.7530),
        "東部地區": (23.9872, 121.6015),
        "東南部地區": (22.7583, 121.1444)
    }
    
    # Create Folium Map centered on Taiwan
    m = folium.Map(location=[23.8, 121.0], zoom_start=7, tiles="CartoDB positron")
    
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
                radius=18,
                popup=folium.Popup(popup_html, max_width=200),
                tooltip=f"{rname}: Min {mint}°C / Max {maxt}°C",
                color=color,
                fill=True,
                fill_color=color,
                fill_opacity=0.75,
            ).add_to(m)
    
    # Display Streamlit-Folium Component
    st_folium(m, width=500, height=450)
    
    # Temperature Legend Chips (Step 17)
    st.markdown("""
    <div style="margin-top: 10px; text-align: center;">
        <span class="legend-chip" style="background:#d6eaf8; color:#1b4f72;">🔵 &lt; 20°C</span>
        <span class="legend-chip" style="background:#d4efdf; color:#117a65;">🟢 20-25°C</span>
        <span class="legend-chip" style="background:#fdebd0; color:#b9770e;">🟠 25-30°C</span>
        <span class="legend-chip" style="background:#fadbd8; color:#78281f;">🔴 &gt; 30°C</span>
    </div>
    """, unsafe_allow_html=True)

# Footer (Step 23 & 24)
st.markdown("---")
st.markdown("<p style='text-align: center; color: #7f8c8d;'>Code Smarter, Build a Better Tomorrow! | AI x Data x Streamlit 專案作品</p>", unsafe_allow_html=True)
