import urllib.request
import json
import os
import webbrowser
from datetime import datetime, timedelta

# 秋田県全13市の緯度・経度データ
AKITA_CITIES = {
    "秋田市": {"lat": 39.7186, "lon": 140.1023},
    "能代市": {"lat": 40.2120, "lon": 140.0270},
    "横手市": {"lat": 39.3134, "lon": 140.5658},
    "大館市": {"lat": 40.2727, "lon": 140.5638},
    "男鹿市": {"lat": 39.8839, "lon": 139.8454},
    "湯沢市": {"lat": 39.1627, "lon": 140.4883},
    "鹿角市": {"lat": 40.1788, "lon": 140.7891},
    "由利本荘市": {"lat": 39.3855, "lon": 140.0461},
    "潟上市": {"lat": 39.8732, "lon": 140.0152},
    "大仙市": {"lat": 39.4533, "lon": 140.4754},
    "北秋田市": {"lat": 40.2223, "lon": 140.3662},
    "にかほ市": {"lat": 39.2995, "lon": 139.9079},
    "仙北市": {"lat": 39.5966, "lon": 140.5652}
}

def get_weather_icon(code):
    if code == -1: return "⚠️"
    elif code == 0: return "☀️"
    elif 1 <= code <= 3: return "☁️"
    elif 45 <= code <= 48: return "🌫️"
    elif 51 <= code <= 55: return "🌧️"
    elif 61 <= code <= 65: return "☔"
    elif 71 <= code <= 75: return "⛄"
    elif 80 <= code <= 82: return "🌦️"
    elif 95 <= code <= 99: return "⛈️"
    else: return "❓"

# 外部ライブラリ(requests)を使わずにデータを取得する関数
def fetch_json(url):
    req = urllib.request.Request(url, headers={
        "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64)",
        "Referer": "https://www.jma.go.jp/bosai/nowc/"
    })
    try:
        with urllib.request.urlopen(req, timeout=10) as response:
            return json.loads(response.read().decode('utf-8'))
    except Exception as e:
        return None

def create_future_weather_map():
    print("気象データを取得しています（拡張機能なしで通信中）...")

    # 1. 気象庁の防災情報
    jma_text = "防災情報の取得に失敗しました。"
    jma_data = fetch_json("https://www.jma.go.jp/bosai/forecast/data/overview_forecast/050000.json")
    if jma_data:
        jma_text = jma_data.get("text", "").replace('\n', '<br>')

    # 2. Open-Meteo 天気データ
    lats = ",".join([str(city["lat"]) for city in AKITA_CITIES.values()])
    lons = ",".join([str(city["lon"]) for city in AKITA_CITIES.values()])
    om_url = f"https://api.open-meteo.com/v1/forecast?latitude={lats}&longitude={lons}&current_weather=true&daily=weathercode,temperature_2m_max,temperature_2m_min&timezone=Asia/Tokyo"
    
    weather_data = fetch_json(om_url)
    if not weather_data or type(weather_data) is not list:
        weather_data = []
        for _ in AKITA_CITIES:
            weather_data.append({
                "current_weather": {"weathercode": -1, "temperature": "--"},
                "daily": {
                    "time": ["----/--/--"] * 7, "weathercode": [-1] * 7,
                    "temperature_2m_max": ["--"] * 7, "temperature_2m_min": ["--"] * 7
                }
            })

    # 3. 雨雲レーダーの時間データ取得（全12パターンの隠し場所を徹底探索）
    print("気象庁サーバーからレーダーデータを探索しています...")
    all_times = {}
    prods_to_try = ["nowc", "prca", "rasrf"]
    fnames_to_try = ["targetTimes_N1.json", "targetTimes_N2.json", "targetTimes_N3.json", "targetTimes.json"]
    
    for prod in prods_to_try:
        for fname in fnames_to_try:
            url = f"https://www.jma.go.jp/bosai/jmatile/data/{prod}/{fname}"
            data = fetch_json(url)
            if data:
                for t in data:
                    if "basetime" in t and "validtime" in t:
                        key = t["validtime"]
                        t["prod"] = prod
                        if key not in all_times or t["basetime"] > all_times[key]["basetime"]:
                            all_times[key] = t

    current_time_str = None
    for t in all_times.values():
        if t["basetime"] == t["validtime"]:
            if current_time_str is None or t["validtime"] > current_time_str:
                current_time_str = t["validtime"]

    forecast_list = list(all_times.values())
    forecast_list.sort(key=lambda x: x["validtime"])

    if current_time_str:
        forecast_list = [t for t in forecast_list if t["validtime"] >= current_time_str]

    js_urls = []
    js_labels = []

    if len(forecast_list) > 0:
        dt_base_now_utc = datetime.strptime(current_time_str, "%Y%m%d%H%M%S")
        for t in forecast_list:
            prod = t["prod"]
            elements = t.get("elements", [])
            element = elements[0] if elements else ("hrpns" if prod == "nowc" else ("prca" if prod == "prca" else "rasrf"))
            
            url = f"https://www.jma.go.jp/bosai/jmatile/data/{prod}/{t['basetime']}/none/{t['validtime']}/surf/{element}/{{z}}/{{x}}/{{y}}.png"
            js_urls.append(url)

            dt_vt_utc = datetime.strptime(t['validtime'], "%Y%m%d%H%M%S")
            dt_vt_jst = dt_vt_utc + timedelta(hours=9)
            time_str = dt_vt_jst.strftime('%H:%M')
            
            diff_mins = int((dt_vt_utc - dt_base_now_utc).total_seconds() / 60)
            if diff_mins == 0:
                lbl = f"現在 ({time_str})"
            elif diff_mins >= 60:
                hours = diff_mins // 60
                mins = diff_mins % 60
                lbl = f"{hours}時間後 ({time_str})" if mins == 0 else f"{hours}時間{mins}分後 ({time_str})"
            else:
                lbl = f"{diff_mins}分後 ({time_str})"
            js_labels.append(lbl)

    if not js_urls:
        js_urls = [""]
        js_labels = ["エラー(現在)"]

   

    # 修正後（『後』という文字を消すだけ！）
    success_msg = f"✅ 最大 {js_labels[-1]} まで取得成功" if "時間" in js_labels[-1] else "⚠️ 1時間以降のデータが見つかりませんでした"
    msg_color = "#4CAF50" if "時間" in js_labels[-1] else "#f44336"

    # マーカーデータの作成
    markers_data = []
    summary_html_rows = ""
    
    for i, (city_name, coords) in enumerate(AKITA_CITIES.items()):
        current = weather_data[i]["current_weather"]
        daily = weather_data[i]["daily"]
        w_code_current = current.get('weathercode', -1)
        t_current = current.get('temperature', '--')
        
        # 画面右のリスト用
        summary_html_rows += f"""
        <tr style="border-bottom: 1px solid #ddd; height: 35px;">
            <td style="font-weight: bold;">{city_name}</td>
            <td style="font-size: 20px;">{get_weather_icon(w_code_current)}</td>
            <td style="color: #d32f2f; font-weight: bold;">{t_current}℃</td>
        </tr>"""

        # ポップアップ用
        popup_html = f"<h3 style='margin:0 0 10px 0;'>📅 {city_name}の1週間</h3>"
        popup_html += "<table style='width: 350px; text-align: center; font-size: 16px; border-collapse: collapse;'>"
        popup_html += "<tr style='background-color: #eee;'><th>日</th><th>空</th><th>最高</th><th>最低</th></tr>"
        
        loop_count = min(7, len(daily.get('time', [])))
        for d in range(loop_count):
            date_str = daily['time'][d][5:] if len(daily['time'][d]) > 5 else "--/--"
            w_code = daily['weathercode'][d]
            t_max = daily['temperature_2m_max'][d]
            t_min = daily['temperature_2m_min'][d]
            popup_html += f"<tr style='border-bottom: 1px solid #ccc; height: 35px;'><td>{date_str}</td><td style='font-size:20px;'>{get_weather_icon(w_code)}</td><td style='color:red;'>{t_max}℃</td><td style='color:blue;'>{t_min}℃</td></tr>"
        popup_html += "</table>"

        # マーカーアイコン用
        marker_html = f"""
        <div style="background-color: white; border: 3px solid #333; border-radius: 10px; padding: 5px; text-align: center; width: 100px; box-shadow: 3px 3px 6px rgba(0,0,0,0.3);">
            <div style="font-size: 14px; font-weight: bold;">{city_name}</div>
            <div style="font-size: 24px;">{get_weather_icon(w_code_current)}</div>
            <div style="font-size: 16px; color: #d32f2f; font-weight: bold;">{t_current}℃</div>
        </div>"""

        markers_data.append({
            "lat": coords["lat"],
            "lon": coords["lon"],
            "html": marker_html,
            "popup": popup_html
        })

    # Pythonで直接HTMLファイルを組み立てる（foliumの代わり）
    html_content = f"""<!DOCTYPE html>
<html>
<head>
    <meta charset="utf-8">
    <title>秋田県 お天気＆雨雲マップ (インストール不要版)</title>
    <link rel="stylesheet" href="https://unpkg.com/leaflet@1.9.4/dist/leaflet.css" />
    <script src="https://unpkg.com/leaflet@1.9.4/dist/leaflet.js"></script>
    <style>
        body {{ margin: 0; padding: 0; font-family: sans-serif; }}
        #map {{ width: 100vw; height: 100vh; }}
        .leaflet-div-icon {{ background: transparent; border: none; }}
    </style>
</head>
<body>
    <div id="map"></div>

    <div style="position: fixed; top: 15px; left: 50px; z-index: 999; background: rgba(255,255,255,0.95); padding: 15px; border-radius: 12px; border: 3px solid #0D47A1; box-shadow: 0 4px 10px rgba(0,0,0,0.4); width: 280px;">
        <button id="radar-btn" style="width: 100%; background: #2196F3; color: white; border: none; padding: 12px; border-radius: 8px; font-size: 16px; font-weight: bold; cursor: pointer;">
            🌧️ 雨雲レーダーをつける
        </button>
        <div id="slider-box" style="display: none; margin-top: 15px;">
            <div style="font-weight: bold; margin-bottom: 8px; color: #333; text-align: center;">
                時間: <span id="time-label" style="color: #d32f2f; font-size: 18px; border-bottom: 2px solid #d32f2f;">{js_labels[0]}</span>
            </div>
            <input type="range" id="time-slider" min="0" max="{len(js_urls)-1}" value="0" style="width: 100%; cursor: pointer;">
            <div style="display: flex; justify-content: space-between; font-size: 12px; color: #666; font-weight: bold; margin-top: 5px;">
                <span>{js_labels[0].split(' ')[0]}</span>
                <span>{js_labels[-1].split(' ')[0]}</span>
            </div>
            <div style="font-size: 13px; color: {msg_color}; font-weight: bold; margin-top: 10px; text-align: center; background: #f9f9f9; padding: 5px; border-radius: 5px;">
                {success_msg}
            </div>
        </div>
    </div>

    <div style="position: fixed; top: 15px; right: 15px; z-index: 999; background-color: white; border: 3px solid #333; padding: 10px; border-radius: 10px; box-shadow: 4px 4px 10px rgba(0,0,0,0.5); width: 220px; max-height: 80vh; overflow-y: auto;">
        <div style="font-weight: bold; font-size: 16px; margin-bottom: 8px; text-align: center; border-bottom: 2px solid #333;">🌡️ いまの天気</div>
        <table style="width: 100%; font-size: 14px; border-collapse: collapse;">
            {summary_html_rows}
        </table>
    </div>

    <div style="position: fixed; bottom: 15px; left: 15px; z-index: 999; background-color: #FFF0F0; border: 3px solid #d32f2f; padding: 15px; border-radius: 12px; box-shadow: 3px 3px 6px rgba(0,0,0,0.4); width: 380px; max-height: 180px; overflow-y: auto;">
        <div style="color: #d32f2f; font-size: 18px; font-weight: bold; margin-bottom: 8px;">⚠️ 防災・天気のお知らせ</div>
        <div style="font-size: 16px; color: #000; line-height: 1.6; font-weight: bold;">{jma_text}</div>
    </div>

    <script>
        // 地図の初期化
        var map = L.map('map', {{ zoomControl: false }}).setView([39.6, 140.1], 8);
        L.control.zoom({{ position: 'topright' }}).addTo(map);

        // 背景地図（OpenStreetMap）
        L.tileLayer('https://{{s}}.tile.openstreetmap.org/{{z}}/{{x}}/{{y}}.png', {{
            attribution: '&copy; <a href="https://www.openstreetmap.org/copyright">OpenStreetMap</a>'
        }}).addTo(map);

        // マーカーの追加
        var markersData = {json.dumps(markers_data)};
        markersData.forEach(function(m) {{
            var icon = L.divIcon({{
                className: 'custom-icon',
                html: m.html,
                iconSize: [110, 80],
                iconAnchor: [55, 40]
            }});
            var marker = L.marker([m.lat, m.lon], {{icon: icon}}).addTo(map);
            marker.bindPopup(m.popup, {{maxWidth: 400}});
        }});

        // 雨雲レーダーのロジック
        var urls = {json.dumps(js_urls)};
        var labels = {json.dumps(js_labels)};
        
        var radarLayer = L.tileLayer(urls[0], {{opacity: 0.6, zIndex: 1000}});
        var isRadarOn = false;
        
        var btn = document.getElementById('radar-btn');
        var sliderBox = document.getElementById('slider-box');
        var slider = document.getElementById('time-slider');
        var timeLabel = document.getElementById('time-label');

        btn.addEventListener('click', function() {{
            isRadarOn = !isRadarOn;
            if (isRadarOn) {{
                btn.style.background = '#f44336';
                btn.innerHTML = '☀️ 雨雲をけす';
                sliderBox.style.display = 'block';
                if (urls[slider.value] !== "") {{
                    radarLayer.addTo(map);
                    radarLayer.setUrl(urls[slider.value]);
                }}
            }} else {{
                btn.style.background = '#2196F3';
                btn.innerHTML = '🌧️ 雨雲レーダーをつける';
                sliderBox.style.display = 'none';
                map.removeLayer(radarLayer);
            }}
        }});

        slider.addEventListener('input', function() {{
            var idx = this.value;
            timeLabel.innerText = labels[idx];
            if (isRadarOn && urls[idx] !== "") {{
                radarLayer.setUrl(urls[idx]);
            }}
        }});

        // マップ上のスクロールがUIに干渉しないようにする
        var uis = ['radar-btn', 'slider-box'];
        uis.forEach(function(id) {{
            var el = document.getElementById(id);
            if(el) {{
                ['mousedown', 'dblclick', 'wheel', 'touchstart'].forEach(function(evt) {{
                    el.addEventListener(evt, function(e) {{ e.stopPropagation(); }});
                }});
            }}
        }});
    </script>
</body>
</html>
"""

    map_filename = "akita_weather_no_install.html"
    with open(map_filename, "w", encoding="utf-8") as f:
        f.write(html_content)

    webbrowser.open('file://' + os.path.realpath(map_filename))
    print("マップを開きました！（インストール不要版）")

if __name__ == "__main__":
    create_future_weather_map()
