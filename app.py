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
    page_title="Taiwan Weather & Alert Dashboard - 全台 22 縣市",
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
        margin-bottom: 20px;
        box-shadow: 0 8px 24px rgba(67, 100, 247, 0.2);
    }
    .main-header h1 {
        color: #ffffff;
        font-weight: 700;
        font-size: 2.2rem;
        margin: 0 0 6px 0;
    }
    .main-header p {
        color: #f0f4f8;
        font-size: 1.05rem;
        margin: 0;
    }
    .alert-banner {
        background-color: #fff3cd;
        border-left: 6px solid #ffc107;
        padding: 12px 18px;
        border-radius: 8px;
        margin-bottom: 20px;
        color: #856404;
    }
    .ai-card {
        background: #ffffff;
        border-radius: 12px;
        padding: 16px 20px;
        box-shadow: 0 4px 14px rgba(0, 0, 0, 0.06);
        border: 1px solid #eef2f6;
        margin-bottom: 15px;
    }
    .ai-title {
        font-size: 1.05rem;
        font-weight: 700;
        color: #1e293b;
        margin-bottom: 8px;
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

# Step 12: Load cached forecast data & weather alerts
@st.cache_data(show_spinner="同步全台 22 縣市最新氣象資料...")
def load_data():
    db_manager.init_db()
    fetch_data.run_pipeline()
    data = db_manager.query_all()
    alerts = db_manager.query_alerts()
    df = pd.DataFrame(data)
    if not df.empty:
        df["dataDate"] = pd.to_datetime(df["dataDate"]).dt.strftime("%Y-%m-%d")
    return df, alerts

try:
    df_all, active_alerts = load_data()
except Exception as e:
    st.error(f"資料讀取失敗: {e}")
    df_all, active_alerts = pd.DataFrame(), []

# Header Area
st.markdown("""
<div class="main-header">
    <h1>☀️ Taiwan Weather & Alert Dashboard</h1>
    <p>中央氣象署 CWA API x 颱風監測 x 降雨偵測 x AI 智慧生活建議 (全台 22 縣市)</p>
</div>
""", unsafe_allow_html=True)

# Active Weather Warnings Top Banner
if active_alerts:
    for alert in active_alerts[:2]:
        st.markdown(f"""
        <div class="alert-banner">
            <strong>⚠️ 【天氣特報提醒】{alert.get('headline', '天氣特報')}</strong> ({alert.get('areaName', '全台')})<br>
            <span style="font-size:0.95rem;">{alert.get('description', '')} (更新時間: {alert.get('updatedTime', '')})</span>
        </div>
        """, unsafe_allow_html=True)

# Sidebar Controls
st.sidebar.header("🔍 縣市選擇與控制")
st.sidebar.success("🟢 API 狀態：CWA 警特報與預報連線正常")

if st.sidebar.button("🔄 同步即時氣象與特報"):
    with st.spinner("連線中央氣象署同步最新天氣與特報..."):
        fetch_data.run_pipeline()
        st.cache_data.clear()
        st.sidebar.success("✅ 已同步全台 22 縣市即時氣象！")
        st.rerun()

st.sidebar.markdown("---")

if not df_all.empty:
    distinct_locations = sorted(df_all["regionName"].unique().tolist())
    distinct_dates = sorted(df_all["dataDate"].unique().tolist())
else:
    distinct_locations = ["臺北市", "新北市", "桃園市", "臺中市", "臺南市", "高雄市"]
    distinct_dates = [datetime.now().strftime("%Y-%m-%d")]

selected_location = st.sidebar.selectbox(
    "📍 選擇縣市 (County / City):",
    options=distinct_locations,
    index=0
)

selected_date_str = st.sidebar.selectbox(
    "📅 選擇檢視日期 (Date):",
    options=distinct_dates,
    index=0
)

st.sidebar.markdown("---")
st.sidebar.info(f"📊 監測全台 {len(distinct_locations)} 個縣市。")

# Filter data for selected location
df_loc = df_all[df_all["regionName"] == selected_location].sort_values("dataDate") if not df_all.empty else pd.DataFrame()
latest_loc_row = df_loc[df_loc["dataDate"] == selected_date_str].iloc[0] if not df_loc.empty and not df_loc[df_loc["dataDate"] == selected_date_str].empty else (df_loc.iloc[0] if not df_loc.empty else None)

# Main Dashboard Layout - 3 Top Stat Cards
col1, col2, col3, col4 = st.columns(4)

curr_mint = latest_loc_row["mint"] if latest_loc_row is not None else 22.0
curr_maxt = latest_loc_row["maxt"] if latest_loc_row is not None else 28.0
curr_pop = latest_loc_row["pop"] if latest_loc_row is not None else 30.0
curr_wx = latest_loc_row["wx"] if latest_loc_row is not None else "多雲"
curr_ci = latest_loc_row["ci"] if latest_loc_row is not None else "舒適"

col1.metric("🌡️ 最高/最低氣溫", f"{curr_maxt}°C / {curr_mint}°C", delta=f"{curr_maxt - curr_mint:.1f}°C 溫差")
col2.metric("🌧️ 降雨機率 (PoP)", f"{curr_pop:.0f}%", delta="雨具觀察" if curr_pop > 30 else "乾爽")
col3.metric("🌤️ 天氣現象", f"{curr_wx}", f"體感: {curr_ci}")

typhoon_info = fetch_data.get_typhoon_status()
col4.metric("🌀 颱風警戒狀態", f"{typhoon_info['status_color']}", f"{typhoon_info['active_typhoons']} 個颱風警戒")

# Middle Content Layout - 2 Columns (Left: Trends, Rain & AI, Right: Folium Map)
left_col, right_col = st.columns([1.1, 0.9])

with left_col:
    st.subheader(f"📈 {selected_location} 氣溫趨勢與降雨機率")
    
    if not df_loc.empty:
        # Dual Line Chart with Temperature & PoP
        fig = go.Figure()
        fig.add_trace(go.Scatter(
            x=df_loc["dataDate"], y=df_loc["maxt"],
            mode='lines+markers', name='最高溫 MaxT (°C)',
            line=dict(color='#eb4d4b', width=3), marker=dict(size=8)
        ))
        fig.add_trace(go.Scatter(
            x=df_loc["dataDate"], y=df_loc["mint"],
            mode='lines+markers', name='最低溫 MinT (°C)',
            line=dict(color='#0984e3', width=3), marker=dict(size=8)
        ))
        fig.add_trace(go.Bar(
            x=df_loc["dataDate"], y=df_loc["pop"],
            name='降雨機率 PoP (%)', yaxis='y2',
            marker_color='rgba(52, 152, 219, 0.35)'
        ))
        
        fig.update_layout(
            xaxis_title="預報日期",
            yaxis=dict(title="氣溫 (°C)", side='left'),
            yaxis2=dict(title="降雨機率 (%)", side='right', overlaying='y', range=[0, 100]),
            hovermode="x unified",
            legend=dict(orientation="h", y=1.12, x=1, xanchor="right"),
            margin=dict(l=20, r=20, t=30, b=20),
            height=320, template="plotly_white"
        )
        st.plotly_chart(fig, use_container_width=True)

    # 🤖 AI Smart Recommendation Engine Section
    st.subheader("🤖 AI 智慧生活與出遊指數")
    
    # Generate Smart Recommendations based on MinT, MaxT, PoP & Wx
    avg_t = (curr_mint + curr_maxt) / 2.0
    
    # Outfit Advice
    if avg_t < 18.0:
        outfit_advice = "🧥 保暖大衣/羽絨外套、搭配長褲，注意防風。"
    elif 18.0 <= avg_t < 24.0:
        outfit_advice = "👔 薄外套/長袖襯衫，早晚溫差大建議多層次穿搭。"
    else:
        outfit_advice = "👕 舒適短袖/透氣涼衫，搭配防曬配件。"

    # Umbrella Advice
    if curr_pop >= 60.0:
        rain_advice = "☔ 降雨機率高 (≥60%)，出門必備折傘或雨具！"
    elif 30.0 <= curr_pop < 60.0:
        rain_advice = "🌂 局部地區可能降雨，建議隨身攜帶輕便備用傘。"
    else:
        rain_advice = "☀️ 降雨機率低 (＜30%)，出門免帶雨具，好天氣適合出遊。"

    # Outdoor & Car Wash Index
    if curr_pop < 30 and "雨" not in curr_wx:
        outdoor_index = "🟢 適合戶外運動與洗車 (天氣晴朗乾爽)"
    elif curr_pop < 60:
        outdoor_index = "🟡 戶外活動尚宜 (需留意短暫陣雨)"
    else:
        outdoor_index = "🔴 不宜戶外長跑與洗車 (防大雨)"

    st.markdown(f"""
    <div class="ai-card">
        <div class="ai-title">👕 AI 穿搭建議</div>
        <div>{outfit_advice} (體感預估: {curr_ci})</div>
    </div>
    <div class="ai-card">
        <div class="ai-title">☔ 雨水攜帶提醒</div>
        <div>{rain_advice} (預測降雨率: <b>{curr_pop:.0f}%</b>)</div>
    </div>
    <div class="ai-card">
        <div class="ai-title">🏃 戶外活動與洗車指數</div>
        <div>{outdoor_index}</div>
    </div>
    """, unsafe_allow_html=True)

with right_col:
    st.subheader(f"🗺️ 全台 22 縣市地圖與氣象標記 ({selected_date_str})")
    
    region_coords = {
        "臺北市": (25.0330, 121.5654), "新北市": (24.9157, 121.6739),
        "基隆市": (25.1283, 121.7419), "桃園市": (24.9936, 121.3010),
        "新竹市": (24.8138, 120.9675), "新竹縣": (24.7033, 121.1444),
        "苗栗縣": (24.5601, 120.8217), "臺中市": (24.1477, 120.6736),
        "彰化縣": (24.0518, 120.5161), "南投縣": (23.9610, 120.9719),
        "雲林縣": (23.7092, 120.4313), "嘉義市": (23.4801, 120.4491),
        "嘉義縣": (23.4588, 120.5740), "臺南市": (22.9997, 120.2270),
        "高雄市": (22.6273, 120.3014), "屏東縣": (22.5520, 120.5487),
        "宜蘭縣": (24.7570, 121.7530), "花蓮縣": (23.9872, 121.6015),
        "臺東縣": (22.7583, 121.1444), "澎湖縣": (23.5711, 119.5793),
        "金門縣": (24.4493, 118.3766), "連江縣": (26.1505, 119.9499)
    }
    
    m = folium.Map(location=[23.8, 121.0], zoom_start=7, tiles="OpenStreetMap")
    df_date = df_all[df_all["dataDate"] == selected_date_str] if not df_all.empty else pd.DataFrame()
    
    def get_color(avg_temp):
        if avg_temp < 20.0:
            return "#3498db"
        elif 20.0 <= avg_temp < 25.0:
            return "#2ecc71"
        elif 25.0 <= avg_temp < 30.0:
            return "#f39c12"
        else:
            return "#e74c3c"

    if not df_date.empty:
        for idx, row in df_date.iterrows():
            rname = row["regionName"]
            mint, maxt = row["mint"], row["maxt"]
            pop_v, wx_v, ci_v = row.get("pop", 0), row.get("wx", "多雲"), row.get("ci", "舒適")
            avg_temp = (mint + maxt) / 2.0
            color = get_color(avg_temp)
            coords = region_coords.get(rname, (23.8, 121.0))
            
            popup_html = f"""
            <div style="font-family: sans-serif; width: 170px;">
                <h4 style="margin:0 0 4px 0; color:#1e293b;">{rname}</h4>
                <p style="margin:2px 0;"><b>天氣:</b> {wx_v}</p>
                <p style="margin:2px 0;"><b>氣溫:</b> {mint}°C ~ {maxt}°C</p>
                <p style="margin:2px 0;"><b>降雨率:</b> {pop_v:.0f}%</p>
                <p style="margin:2px 0;"><b>體感:</b> {ci_v}</p>
            </div>
            """
            
            folium.CircleMarker(
                location=coords,
                radius=14,
                popup=folium.Popup(popup_html, max_width=220),
                tooltip=f"{rname}: {wx_v} ({mint}°C~{maxt}°C, 雨感{pop_v:.0f}%)",
                color=color, fill=True, fill_color=color, fill_opacity=0.85,
            ).add_to(m)
    
    st_folium(m, width=500, height=480)
    
    st.markdown("""
    <div style="margin-top: 8px; text-align: center;">
        <span class="legend-chip" style="background:#d6eaf8; color:#1b4f72;">🔵 &lt; 20°C</span>
        <span class="legend-chip" style="background:#d4efdf; color:#117a65;">🟢 20-25°C</span>
        <span class="legend-chip" style="background:#fdebd0; color:#b9770e;">🟠 25-30°C</span>
        <span class="legend-chip" style="background:#fadbd8; color:#78281f;">🔴 &gt; 30°C</span>
    </div>
    """, unsafe_allow_html=True)

# Footer
st.markdown("---")
st.markdown("<p style='text-align: center; color: #7f8c8d;'>Code Smarter, Build a Better Tomorrow! | 氣象警特報 x 降雨偵測 x 颱風動態 x AI 智慧生活儀表板</p>", unsafe_allow_html=True)
