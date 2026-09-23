from flask import Flask, render_template_string, request, jsonify
import sys
import os
import traceback

# Add parent directory to path to import db_manager and fetch_data
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

import db_manager
import fetch_data
import pandas as pd

app = Flask(__name__)

HTML_TEMPLATE = """
<!DOCTYPE html>
<html lang="zh-TW">
<head>
    <meta charset="UTF-8">
    <meta name="viewport" content="width=device-width, initial-scale=1.0">
    <title>Taiwan Weather & Alert Dashboard</title>
    <link href="https://cdn.jsdelivr.net/npm/bootstrap@5.3.0/dist/css/bootstrap.min.css" rel="stylesheet">
    <link rel="stylesheet" href="https://unpkg.com/leaflet@1.9.4/dist/leaflet.css" />
    <script src="https://cdn.plot.ly/plotly-2.27.0.min.js"></script>
    <style>
        body { font-family: 'Segoe UI', system-ui, -apple-system, sans-serif; background-color: #0e1117; color: #faafa8; }
        .bg-custom { background-color: #0e1117; color: #ffffff; }
        .main-header {
            background: linear-gradient(135deg, #0052D4 0%, #4364F7 50%, #6FB1FC 100%);
            padding: 24px 30px;
            border-radius: 16px;
            color: white;
            margin-bottom: 20px;
            box-shadow: 0 8px 24px rgba(67, 100, 247, 0.2);
        }
        .main-header h1 { color: #ffffff; font-weight: 700; font-size: 2.1rem; margin: 0 0 6px 0; }
        .main-header p { color: #f0f4f8; font-size: 1.05rem; margin: 0; }
        .alert-banner {
            background-color: #fff3cd; border-left: 6px solid #ffc107; padding: 12px 18px;
            border-radius: 8px; margin-bottom: 20px; color: #856404;
        }
        .stat-card {
            background: #1e293b; border-radius: 12px; padding: 16px; border: 1px solid #334155; color: #ffffff;
        }
        .stat-label { font-size: 0.85rem; color: #94a3b8; }
        .stat-value { font-size: 1.5rem; font-weight: 700; }
        .ai-card {
            background: #1e293b; border-radius: 12px; padding: 16px 20px;
            border: 1px solid #334155; margin-bottom: 12px; color: #ffffff;
        }
        .ai-title { font-size: 1.05rem; font-weight: 700; color: #38bdf8; margin-bottom: 6px; }
        .legend-chip { display: inline-block; padding: 4px 12px; border-radius: 20px; font-size: 0.85rem; font-weight: 600; margin-right: 6px; }
        #map { height: 480px; border-radius: 12px; border: 1px solid #334155; }
        .sidebar-card { background: #1e293b; border-radius: 12px; padding: 20px; border: 1px solid #334155; color: #ffffff; }
    </style>
</head>
<body class="bg-custom">
    <div class="container py-4">
        <!-- Header -->
        <div class="main-header">
            <h1>☀️ Taiwan Weather & Alert Dashboard</h1>
            <p>中央氣象署 CWA API x 颱風監測 x 降雨偵測 x AI 智慧生活建議 (全台 22 縣市)</p>
        </div>

        <!-- Severe Weather Alerts -->
        {% if alerts %}
        {% for alert in alerts[:2] %}
        <div class="alert-banner">
            <strong>⚠️ 【天氣特報提醒】{{ alert.headline }}</strong> ({{ alert.areaName }})<br>
            <span style="font-size:0.95rem;">{{ alert.description }} (更新時間: {{ alert.updatedTime }})</span>
        </div>
        {% endfor %}
        {% endif %}

        <!-- 4 Top Stat Cards -->
        <div class="row g-3 mb-4">
            <div class="col-6 col-md-3">
                <div class="stat-card">
                    <div class="stat-label">🌡️ 最高/最低氣溫</div>
                    <div class="stat-value text-danger">{{ curr_maxt }}°C / <span class="text-primary">{{ curr_mint }}°C</span></div>
                </div>
            </div>
            <div class="col-6 col-md-3">
                <div class="stat-card">
                    <div class="stat-label">🌧️ 降雨機率 (PoP)</div>
                    <div class="stat-value text-info">{{ curr_pop }}%</div>
                </div>
            </div>
            <div class="col-6 col-md-3">
                <div class="stat-card">
                    <div class="stat-label">🌤️ 天氣現象</div>
                    <div class="stat-value text-warning" style="font-size:1.2rem; margin-top:4px;">{{ curr_wx }}</div>
                    <div class="stat-label">體感: {{ curr_ci }}</div>
                </div>
            </div>
            <div class="col-6 col-md-3">
                <div class="stat-card">
                    <div class="stat-label">🌀 颱風警戒狀態</div>
                    <div class="stat-value text-success" style="font-size:1.2rem; margin-top:4px;">{{ typhoon_info.status_color }}</div>
                    <div class="stat-label">{{ typhoon_info.active_typhoons }} 個颱風警戒</div>
                </div>
            </div>
        </div>

        <!-- Controls Bar -->
        <div class="row mb-4">
            <div class="col-md-6 mb-2 mb-md-0">
                <div class="sidebar-card">
                    <label class="form-label fw-bold">📍 選擇縣市 (Select County / City):</label>
                    <form method="GET" action="/">
                        <input type="hidden" name="date" value="{{ selected_date }}">
                        <select name="county" class="form-select bg-dark text-light border-secondary" onchange="this.form.submit()">
                            {% for c in counties %}
                                <option value="{{ c }}" {% if c == selected_county %}selected{% endif %}>{{ c }}</option>
                            {% endfor %}
                        </select>
                    </form>
                </div>
            </div>
            <div class="col-md-6">
                <div class="sidebar-card">
                    <label class="form-label fw-bold">📅 選擇檢視日期 (Select Date):</label>
                    <form method="GET" action="/">
                        <input type="hidden" name="county" value="{{ selected_county }}">
                        <select name="date" class="form-select bg-dark text-light border-secondary" onchange="this.form.submit()">
                            {% for d in dates %}
                                <option value="{{ d }}" {% if d == selected_date %}selected{% endif %}>{{ d }}</option>
                            {% endfor %}
                        </select>
                    </form>
                </div>
            </div>
        </div>

        <!-- Main Grid: Left Charts & AI, Right Map -->
        <div class="row g-4">
            <div class="col-lg-6">
                <div class="sidebar-card mb-4">
                    <h5 class="fw-bold mb-3">📈 {{ selected_county }} 氣溫趨勢與降雨機率</h5>
                    <div id="plotly-chart" style="height: 320px;"></div>
                </div>

                <h5 class="fw-bold mb-3 text-light">🤖 AI 智慧生活與出遊指數</h5>
                <div class="ai-card">
                    <div class="ai-title">👕 AI 穿搭建議</div>
                    <div>{{ outfit_advice }} (體感預估: {{ curr_ci }})</div>
                </div>
                <div class="ai-card">
                    <div class="ai-title">☔ 雨水攜帶提醒</div>
                    <div>{{ rain_advice }} (預測降雨率: <b>{{ curr_pop }}%</b>)</div>
                </div>
                <div class="ai-card">
                    <div class="ai-title">🏃 戶外活動與洗車指數</div>
                    <div>{{ outdoor_advice }}</div>
                </div>
            </div>

            <div class="col-lg-6">
                <div class="sidebar-card">
                    <h5 class="fw-bold mb-3">🗺️ 全台 22 縣市地圖與氣象標記 ({{ selected_date }})</h5>
                    <div id="map"></div>
                    <div class="text-center mt-3">
                        <span class="legend-chip" style="background:#d6eaf8; color:#1b4f72;">🔵 &lt; 20°C</span>
                        <span class="legend-chip" style="background:#d4efdf; color:#117a65;">🟢 20-25°C</span>
                        <span class="legend-chip" style="background:#fdebd0; color:#b9770e;">🟠 25-30°C</span>
                        <span class="legend-chip" style="background:#fadbd8; color:#78281f;">🔴 &gt; 30°C</span>
                    </div>
                </div>
            </div>
        </div>

        <footer class="text-center text-muted mt-5 pt-3 border-top border-secondary">
            <small>Code Smarter, Build a Better Tomorrow! | ⚡ Vercel Serverless x Streamlit Dual Deployment</small>
        </footer>
    </div>

    <script src="https://unpkg.com/leaflet@1.9.4/dist/leaflet.js"></script>
    <script>
        // Plotly Dual Line/Bar Chart
        var chartData = {{ chart_payload | tojson }};
        var traceMaxT = {
            x: chartData.dates, y: chartData.maxt,
            name: '最高溫 MaxT (°C)', mode: 'lines+markers',
            line: {color: '#eb4d4b', width: 3}, marker: {size: 8}
        };
        var traceMinT = {
            x: chartData.dates, y: chartData.mint,
            name: '最低溫 MinT (°C)', mode: 'lines+markers',
            line: {color: '#0984e3', width: 3}, marker: {size: 8}
        };
        var tracePoP = {
            x: chartData.dates, y: chartData.pop,
            name: '降雨機率 PoP (%)', type: 'bar', yaxis: 'y2',
            marker: {color: 'rgba(52, 152, 219, 0.35)'}
        };
        var layout = {
            margin: {l: 30, r: 30, t: 10, b: 30},
            paper_bgcolor: 'rgba(0,0,0,0)',
            plot_bgcolor: 'rgba(0,0,0,0)',
            font: {color: '#ffffff'},
            xaxis: {title: '預報日期'},
            yaxis: {title: '氣溫 (°C)', side: 'left'},
            yaxis2: {title: '降雨機率 (%)', side: 'right', overlaying: 'y', range: [0, 100]},
            legend: {orientation: 'h', y: 1.15, x: 1, xanchor: 'right'}
        };
        Plotly.newPlot('plotly-chart', [traceMaxT, traceMinT, tracePoP], layout, {responsive: true});

        // Leaflet Map
        var map = L.map('map').setView([23.8, 121.0], 7);
        L.tileLayer('https://{s}.tile.openstreetmap.org/{z}/{x}/{y}.png', {
            attribution: '&copy; OpenStreetMap'
        }).addTo(map);

        var locations = {{ map_payload | tojson }};
        locations.forEach(loc => {
            var color = loc.avg_temp < 20 ? '#3498db' : (loc.avg_temp < 25 ? '#2ecc71' : (loc.avg_temp < 30 ? '#f39c12' : '#e74c3c'));
            L.circleMarker([loc.lat, loc.lng], {
                radius: 12, fillColor: color, color: color,
                weight: 2, opacity: 1, fillOpacity: 0.85
            }).addTo(map)
              .bindPopup(`<b>${loc.name}</b><br>現象: ${loc.wx}<br>氣溫: ${loc.mint}°C ~ ${loc.maxt}°C<br>降雨率: ${loc.pop}%<br>體感: ${loc.ci}`);
        });
    </script>
</body>
</html>
"""

REGION_COORDS = {
    "臺北市": (25.0330, 121.5654), "新北市": (24.9157, 121.6739), "基隆市": (25.1283, 121.7419),
    "桃園市": (24.9936, 121.3010), "新竹市": (24.8138, 120.9675), "新竹縣": (24.7033, 121.1444),
    "苗栗縣": (24.5601, 120.8217), "臺中市": (24.1477, 120.6736), "彰化縣": (24.0518, 120.5161),
    "南投縣": (23.9610, 120.9719), "雲林縣": (23.7092, 120.4313), "嘉義市": (23.4801, 120.4491),
    "嘉義縣": (23.4588, 120.5740), "臺南市": (22.9997, 120.2270), "高雄市": (22.6273, 120.3014),
    "屏東縣": (22.5520, 120.5487), "宜蘭縣": (24.7570, 121.7530), "花蓮縣": (23.9872, 121.6015),
    "臺東縣": (22.7583, 121.1444), "澎湖縣": (23.5711, 119.5793), "金門縣": (24.4493, 118.3766),
    "連江縣": (26.1505, 119.9499)
}

@app.route("/", methods=["GET"])
def index():
    try:
        db_manager.init_db()
        rows = db_manager.query_all()
        if not rows:
            fetch_data.run_pipeline()
            rows = db_manager.query_all()
            
        alerts = db_manager.query_alerts()
        typhoon_info = fetch_data.get_typhoon_status()
        
        df = pd.DataFrame(rows)
        if not df.empty:
            df["dataDate"] = pd.to_datetime(df["dataDate"]).dt.strftime("%Y-%m-%d")
            
        counties = sorted(df["regionName"].unique().tolist()) if not df.empty else list(REGION_COORDS.keys())
        dates = sorted(df["dataDate"].unique().tolist()) if not df.empty else ["2026-09-23"]
        
        selected_county = request.args.get("county", counties[0] if counties else "臺北市")
        selected_date = request.args.get("date", dates[0] if dates else "2026-09-23")
        
        df_loc = df[df["regionName"] == selected_county].sort_values("dataDate") if not df.empty else pd.DataFrame()
        
        latest_match = df_loc[df_loc["dataDate"] == selected_date]
        curr_row = latest_match.iloc[0] if not latest_match.empty else (df_loc.iloc[0] if not df_loc.empty else None)
        
        curr_maxt = curr_row["maxt"] if curr_row is not None else 28.0
        curr_mint = curr_row["mint"] if curr_row is not None else 22.0
        curr_pop = int(curr_row["pop"]) if curr_row is not None else 20
        curr_wx = curr_row.get("wx", "多雲") if curr_row is not None else "多雲"
        curr_ci = curr_row.get("ci", "舒適") if curr_row is not None else "舒適"

        # Chart payload
        chart_payload = {
            "dates": df_loc["dataDate"].tolist() if not df_loc.empty else [],
            "maxt": df_loc["maxt"].tolist() if not df_loc.empty else [],
            "mint": df_loc["mint"].tolist() if not df_loc.empty else [],
            "pop": df_loc["pop"].tolist() if not df_loc.empty else []
        }
        
        # Map payload filtered by selected date
        df_date = df[df["dataDate"] == selected_date] if not df.empty else pd.DataFrame()
        map_payload = []
        if not df_date.empty:
            for _, r in df_date.iterrows():
                cname = r["regionName"]
                lat, lng = REGION_COORDS.get(cname, (23.8, 121.0))
                mint, maxt = float(r["mint"]), float(r["maxt"])
                map_payload.append({
                    "name": cname, "lat": lat, "lng": lng,
                    "mint": mint, "maxt": maxt,
                    "avg_temp": (mint + maxt)/2.0,
                    "wx": r.get("wx", "多雲"),
                    "pop": int(r.get("pop", 20)),
                    "ci": r.get("ci", "舒適")
                })
                
        # AI Recommendation logic
        avg_t = (curr_mint + curr_maxt) / 2.0
        if avg_t < 18.0:
            outfit_advice = "🧥 保暖大衣/羽絨外套、搭配長褲，注意防風。"
        elif 18.0 <= avg_t < 24.0:
            outfit_advice = "👔 薄外套/長袖襯衫，早晚溫差大建議多層次穿搭。"
        else:
            outfit_advice = "👕 舒適短袖/透氣涼衫，搭配防曬配件。"

        if curr_pop >= 60:
            rain_advice = "☔ 降雨機率高 (≥60%)，出門必備折傘或雨具！"
        elif 30 <= curr_pop < 60:
            rain_advice = "🌂 局部地區可能降雨，建議隨身攜帶輕便備用傘。"
        else:
            rain_advice = "☀️ 降雨機率低 (＜30%)，出門免帶雨具，好天氣適合出遊。"

        if curr_pop < 30 and "雨" not in curr_wx:
            outdoor_advice = "🟢 適合戶外運動與洗車 (天氣晴朗乾爽)"
        elif curr_pop < 60:
            outdoor_advice = "🟡 戶外活動尚宜 (需留意短暫陣雨)"
        else:
            outdoor_advice = "🔴 不宜戶外長跑與洗車 (防大雨)"

        return render_template_string(
            HTML_TEMPLATE,
            counties=counties,
            dates=dates,
            selected_county=selected_county,
            selected_date=selected_date,
            curr_maxt=curr_maxt,
            curr_mint=curr_mint,
            curr_pop=curr_pop,
            curr_wx=curr_wx,
            curr_ci=curr_ci,
            alerts=alerts,
            typhoon_info=typhoon_info,
            chart_payload=chart_payload,
            map_payload=map_payload,
            outfit_advice=outfit_advice,
            rain_advice=rain_advice,
            outdoor_advice=outdoor_advice
        )
    except Exception as e:
        err_msg = traceback.format_exc()
        return f"<div style='padding:20px; font-family:sans-serif; color:white;'><h2>⚠️ Vercel Application Error</h2><pre>{err_msg}</pre></div>", 500

if __name__ == "__main__":
    app.run(debug=True)
