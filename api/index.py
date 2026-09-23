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
    <title>Taiwan Weather & Alert Dashboard (Vercel Live)</title>
    <link href="https://cdn.jsdelivr.net/npm/bootstrap@5.3.0/dist/css/bootstrap.min.css" rel="stylesheet">
    <link rel="stylesheet" href="https://unpkg.com/leaflet@1.9.4/dist/leaflet.css" />
    <style>
        body { font-family: 'Segoe UI', Tahoma, sans-serif; background-color: #f8fafc; }
        .hero-header { background: linear-gradient(135deg, #0052D4 0%, #4364F7 50%, #6FB1FC 100%); color: white; padding: 24px; border-radius: 16px; margin-bottom: 20px; }
        .card-custom { border: none; border-radius: 12px; box-shadow: 0 4px 12px rgba(0,0,0,0.05); }
        #map { height: 460px; border-radius: 12px; }
    </style>
</head>
<body>
    <div class="container py-4">
        <div class="hero-header shadow-sm">
            <h1 class="h2 mb-1">☀️ Taiwan Weather & Alert Dashboard</h1>
            <p class="mb-0">中央氣象署 CWA API x Vercel Serverless x 全台 22 縣市即時預報</p>
        </div>

        {% if alerts %}
        <div class="alert alert-warning border-0 shadow-sm mb-4" role="alert">
            <h5 class="alert-heading">⚠️ 天氣特報警示</h5>
            {% for a in alerts[:2] %}
                <div><strong>【{{ a.headline }}】</strong> {{ a.description }} (更新時間: {{ a.updatedTime }})</div>
            {% endfor %}
        </div>
        {% endif %}

        <div class="row g-4">
            <!-- Left Side: Controls, Weather Stat & AI Card -->
            <div class="col-lg-6">
                <div class="card card-custom p-4 mb-4">
                    <h5 class="card-title fw-bold">📍 選擇縣市預報</h5>
                    <form method="GET" action="/">
                        <select name="county" class="form-select form-select-lg mb-3" onchange="this.form.submit()">
                            {% for c in counties %}
                                <option value="{{ c }}" {% if c == selected_county %}selected{% endif %}>{{ c }}</option>
                            {% endfor %}
                        </select>
                    </form>
                    
                    <div class="row text-center my-2">
                        <div class="col-4">
                            <div class="text-muted small">最高氣溫</div>
                            <div class="fs-4 fw-bold text-danger">{{ curr_data.maxt if curr_data else '28' }}°C</div>
                        </div>
                        <div class="col-4">
                            <div class="text-muted small">最低氣溫</div>
                            <div class="fs-4 fw-bold text-primary">{{ curr_data.mint if curr_data else '22' }}°C</div>
                        </div>
                        <div class="col-4">
                            <div class="text-muted small">降雨機率</div>
                            <div class="fs-4 fw-bold text-info">{{ curr_data.pop if curr_data else '20' }}%</div>
                        </div>
                    </div>
                </div>

                <!-- AI Recommendations -->
                <div class="card card-custom p-4">
                    <h5 class="card-title fw-bold mb-3">🤖 AI 智慧生活指數 ({{ selected_county }})</h5>
                    <div class="mb-3">
                        <strong>👕 穿搭建議:</strong>
                        <div class="text-secondary">{{ outfit_advice }}</div>
                    </div>
                    <div class="mb-3">
                        <strong>☔ 雨水防範:</strong>
                        <div class="text-secondary">{{ rain_advice }}</div>
                    </div>
                    <div>
                        <strong>🏃 戶外活動指數:</strong>
                        <div class="text-secondary">{{ outdoor_advice }}</div>
                    </div>
                </div>
            </div>

            <!-- Right Side: Interactive Leaflet Map -->
            <div class="col-lg-6">
                <div class="card card-custom p-3">
                    <h5 class="card-title fw-bold mb-3">🗺️ 全台 22 縣市地圖</h5>
                    <div id="map"></div>
                </div>
            </div>
        </div>

        <footer class="text-center text-muted mt-5 pt-3 border-top">
            <small>Deployed on ⚡ Vercel Serverless | CWA API Open Data | Author: johnny051777</small>
        </footer>
    </div>

    <script src="https://unpkg.com/leaflet@1.9.4/dist/leaflet.js"></script>
    <script>
        var map = L.map('map').setView([23.8, 121.0], 7);
        L.tileLayer('https://{s}.tile.openstreetmap.org/{z}/{x}/{y}.png', {
            attribution: '&copy; OpenStreetMap'
        }).addTo(map);

        var locations = {{ map_data | tojson }};
        locations.forEach(loc => {
            var color = loc.avg_temp < 20 ? '#3498db' : (loc.avg_temp < 25 ? '#2ecc71' : (loc.avg_temp < 30 ? '#f39c12' : '#e74c3c'));
            L.circleMarker([loc.lat, loc.lng], {
                radius: 12,
                fillColor: color,
                color: color,
                weight: 2,
                opacity: 1,
                fillOpacity: 0.8
            }).addTo(map)
              .bindPopup(`<b>${loc.name}</b><br>現象: ${loc.wx}<br>氣溫: ${loc.mint}°C ~ ${loc.maxt}°C<br>降雨率: ${loc.pop}%`);
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
        
        df = pd.DataFrame(rows)
        counties = sorted(df["regionName"].unique().tolist()) if not df.empty else list(REGION_COORDS.keys())
        
        selected_county = request.args.get("county", counties[0] if counties else "臺北市")
        
        df_loc = df[df["regionName"] == selected_county] if not df.empty else pd.DataFrame()
        curr_data = df_loc.iloc[0].to_dict() if not df_loc.empty else None
        
        # Map markers payload
        map_data = []
        if not df.empty:
            latest_df = df.groupby("regionName").first().reset_index()
            for _, r in latest_df.iterrows():
                cname = r["regionName"]
                lat, lng = REGION_COORDS.get(cname, (23.8, 121.0))
                mint, maxt = float(r["mint"]), float(r["maxt"])
                map_data.append({
                    "name": cname,
                    "lat": lat, "lng": lng,
                    "mint": mint, "maxt": maxt,
                    "avg_temp": (mint + maxt) / 2.0,
                    "wx": r.get("wx", "多雲"),
                    "pop": r.get("pop", 20)
                })
                
        # AI Recommendations
        avg_t = (curr_data["mint"] + curr_data["maxt"])/2.0 if curr_data else 25.0
        pop_v = curr_data["pop"] if curr_data else 20.0
        
        outfit_advice = "🧥 保暖外套" if avg_t < 18 else ("👔 薄長袖外套" if avg_t < 24 else "👕 舒適短袖與防曬")
        rain_advice = "☔ 降雨機率高，務必攜帶雨具！" if pop_v >= 50 else ("🌂 建議準備備用小傘" if pop_v >= 30 else "☀️ 天氣良好出門免帶傘")
        outdoor_advice = "🟢 適合戶外活動與洗車" if pop_v < 30 else "🔴 降雨風險高，建議室內活動"

        return render_template_string(
            HTML_TEMPLATE,
            counties=counties,
            selected_county=selected_county,
            curr_data=curr_data,
            alerts=alerts,
            map_data=map_data,
            outfit_advice=outfit_advice,
            rain_advice=rain_advice,
            outdoor_advice=outdoor_advice
        )
    except Exception as e:
        err_msg = traceback.format_exc()
        return f"<div style='padding:20px; font-family:sans-serif;'><h2>⚠️ Vercel Application Error</h2><pre>{err_msg}</pre></div>", 500

if __name__ == "__main__":
    app.run(debug=True)
