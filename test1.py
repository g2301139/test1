import streamlit as st
from streamlit_folium import st_folium
import requests
import folium
from folium.plugins import Geocoder
from folium.features import DivIcon
from folium import Popup
import json
import time
from datetime import datetime, timedelta

# 【最優先】Streamlitの画面設定（横幅を広く使い、タイトルを設定）
st.set_page_config(layout="wide", page_title="秋田お天気GPSマップ")

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

# 画面にメインタイトルを表示
st.title("🗺️ 秋田 現在地GPS ＆ お天気レーダーマップ")

# ========================================================
# 📡 データのバックエンド取得処理
# ========================================================
headers = {
    "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36",
    "Referer": "https://www.jma.go.jp/bosai/nowc/",
    "Cache-Control": "no-cache"
}
session = requests.Session()
session.headers.update(headers)

# 1. 気象庁の防災情報
jma_text = "防災情報の取得に失敗しました。"
try:
    jma_url = "https://www.jma.go.jp/bosai/forecast/data/overview_forecast/050000.json"
    jma_response = session.get(jma_url, timeout=5)
    if jma_response.status_code == 200:
        jma_text = jma_response.json().get("text", "").replace('\n', '<br>')
except Exception: 
    pass

# 2. Open-Meteo 天気データ
lats = ",".join([str(city["lat"]) for city in AKITA_CITIES.values()])
lons = ",".join([str(city["lon"]) for city in AKITA_CITIES.values()])
om_url = f"https://api.open-meteo.com/v1/forecast?latitude={lats}&longitude={lons}&current_weather=true&daily=weathercode,temperature_2m_max,temperature_2m_min&timezone=Asia/Tokyo"

weather_data = None
try:
    om_resp = session.get(om_url, timeout=10)
    if om_resp.status_code == 200:
        weather_data = om_resp.json()
except Exception:
    pass

if weather_data is None or type(weather_data) is not list:
    weather_data = [{"current_weather": {"weathercode": -1, "temperature": "--"}, 
                     "daily": {"time": ["----/--/--"]*7, "weathercode": [-1]*7, 
                               "temperature_2m_max": ["--"]*7, "temperature_2m_min": ["--"]*7}} 
                    for _ in AKITA_CITIES]

# 3. 雨雲レーダーの時間データ取得
js_urls = []
js_labels = []
all_times = {}
prods_to_try = ["nowc", "prca", "rasrf"]
fnames_to_try = ["targetTimes_N1.json", "targetTimes_N2.json", "targetTimes_N3.json", "targetTimes.json"]
current_ts = int(time.time() * 1000)

for prod in prods_to_try:
    for fname in fnames_to_try:
        url = f"https://www.jma.go.jp/bosai/jmatile/data/{prod}/{fname}?_={current_ts}"
        try:
            resp = session.get(url, timeout=5)
            if resp.status_code == 200:
                for t in resp.json():
                    if "basetime" in t and "validtime" in t:
                        key = t["validtime"]
                        t["prod"] = prod
                        if key not in all_times or t["basetime"] > all_times[key]["basetime"]:
                            all_times[key] = t
        except Exception:
            pass 

current_time_str = None
for t in all_times.values():
    if t["basetime"] == t["validtime"]:
        if current_time_str is None or t["validtime"] > current_time_str:
            current_time_str = t["validtime"]

forecast_list = list(all_times.values())
forecast_list.sort(key=lambda x: x["validtime"])

if current_time_str:
    forecast_list = [t for t in forecast_list if t["validtime"] >= current_time_str]

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
        if diff_mins == 0: lbl = f"現在 ({time_str})"
        elif diff_mins >= 60: lbl = f"{diff_mins // 60}時間後 ({time_str})" if diff_mins % 60 == 0 else f"{diff_mins // 60}時間{diff_mins % 60}分後 ({time_str})"
        else: lbl = f"{diff_mins}分後 ({time_str})"
        js_labels.append(lbl)

if len(js_urls) == 0:
    js_urls = [""] * 2
    js_labels = ["エラー(現在)", "エラー(未来)"]
    success_msg = "⚠️ レーダーデータが見つかりませんでした"
    msg_color = "#f44336"
else:
    success_msg = f"✅ 最大 {js_labels[-1]} まで取得成功"
    msg_color = "#4CAF50"

urls_json = json.dumps(js_urls)
labels_json = json.dumps(js_labels)


# ========================================================
# 🗺️ ベースマップの作成（秋田全体表示、初期タイルをNoneにして追加）
# ========================================================
akita_map = folium.Map(
    location=[39.6, 140.1], 
    zoom_start=8,                
    min_zoom=5,
    max_zoom=18,                  
    height='100%', 
    tiles=None,
    max_bounds=True,
    min_lat=38.0, max_lat=41.0,
    min_lon=138.5, max_lon=142.0
)

# ① 通常の道路地図（OpenStreetMap）
folium.TileLayer(
    tiles='OpenStreetMap',
    name='通常の地図（道路・建物）',
    control=True
).add_to(akita_map)

# ② 国土地理院 航空写真（サテライト）
folium.TileLayer(
    tiles='https://cyberjapandata.gsi.go.jp/xyz/ort/{z}/{x}/{y}.jpg',
    attr='国土地理院 航空写真',
    name='航空写真（上空からの景色）',
    control=True
).add_to(akita_map)

# ③ 国土地理院 淡色地図（シンプル表示）
folium.TileLayer(
    tiles='https://cyberjapandata.gsi.go.jp/xyz/pale/{z}/{x}/{y}.png',
    attr='国土地理院 淡色地図',
    name='淡色地図（シンプル表示）',
    control=True
).add_to(akita_map)

# レイヤー切り替えを右上に配置
folium.LayerControl(position='topright', collapsed=True).add_to(akita_map)

# 🗺️ 検索機能（Geocoder）を左上に追加
Geocoder(
    collapsed=True, 
    position='topleft', 
    zoom=17, 
    placeholder='場所を検索...'
).add_to(akita_map)


# ========================================================
# 🎨 UI表示アイテムと【自動高精度GPS起動】JavaScript
# ========================================================
# 左側のコントロールUI（雨雲ボタン、現在地ボタン、スライダー）
external_ui_html = f"""
<div id="independent-ui" style="position: fixed; top: 15px; left: 50px; z-index: 999999; background: rgba(255,255,255,0.95); padding: 15px; border-radius: 12px; border: 3px solid #0D47A1; box-shadow: 0 4px 10px rgba(0,0,0,0.4); width: 280px; font-family: sans-serif;">
    <button id="radar-btn" style="width: 100%; background: #2196F3; color: white; border: none; padding: 12px; border-radius: 8px; font-size: 16px; font-weight: bold; cursor: pointer; box-shadow: 0 2px 4px rgba(0,0,0,0.2);">
        🌧️ 雨雲レーダーをつける
    </button>
    <button id="gps-btn" style="width: 100%; background: #4CAF50; color: white; border: none; padding: 12px; border-radius: 8px; font-size: 16px; font-weight: bold; cursor: pointer; box-shadow: 0 2px 4px rgba(0,0,0,0.2); margin-top: 8px;">
        📱 現在地を取得
    </button>
    <div id="slider-box" style="display: none; margin-top: 15px;">
        <div style="font-weight: bold; margin-bottom: 8px; color: #333; text-align: center;">
            時間: <span id="time-label" style="color: #d32f2f; font-size: 18px; border-bottom: 2px solid #d32f2f;">{js_labels[0]}</span>
        </div>
        <input type="range" id="time-slider" min="0" max="{len(js_urls)-1}" value="0" style="width: 100%; cursor: pointer; pointer-events: auto;">
        <div style="display: flex; justify-content: space-between; font-size: 12px; color: #666; font-weight: bold; margin-top: 5px;">
            <span>{js_labels[0].split(' ')[0]}</span>
            <span>{js_labels[-1].split(' ')[0]}</span>
        </div>
        <div style="font-size: 13px; color: {msg_color}; font-weight: bold; margin-top: 10px; text-align: center; background: #f9f9f9; padding: 5px; border-radius: 5px;">
            {success_msg}
        </div>
    </div>
</div>
"""

external_ui_script = f"""
<script>
document.addEventListener("DOMContentLoaded", function() {{
    var urls = {urls_json};
    var labels = {labels_json};
    
    var mapObj = null;
    var userMarker = null;
    var checkMapInterval = setInterval(function() {{
        for (var key in window) {{
            if (window[key] instanceof L.Map) {{
                mapObj = window[key];
                clearInterval(checkMapInterval);
                initLogic();
                break;
            }
        }
    }}, 500);

    function initLogic() {{
        var radarLayer = L.tileLayer(urls[0], {{opacity: 0.6, zIndex: 1000}});
        var isRadarOn = false;
        
        var btn = document.getElementById('radar-btn');
        var gpsBtn = document.getElementById('gps-btn');
        var sliderBox = document.getElementById('slider-box');
        var slider = document.getElementById('time-slider');
        var timeLabel = document.getElementById('time-label');
        
        var ui = document.getElementById('independent-ui');
        ['mousedown', 'touchstart', 'dblclick', 'wheel', 'pointerdown'].forEach(function(evt) {{
            ui.addEventListener(evt, function(e) {{ e.stopPropagation(); }});
        }});

        btn.addEventListener('click', function() {{
            isRadarOn = !isRadarOn;
            if (isRadarOn) {{
                btn.style.background = '#f44336';
                btn.innerHTML = '☀️ 雨雲をけす';
                sliderBox.style.display = 'block';
                if (urls[slider.value] !== "") {{
                    radarLayer.addTo(mapObj);
                    radarLayer.setUrl(urls[slider.value]);
                }}
            } else {{
                btn.style.background = '#2196F3';
                btn.innerHTML = '🌧️ 雨雲レーダーをつける';
                sliderBox.style.display = 'none';
                mapObj.removeLayer(radarLayer);
            }
        }});

        slider.addEventListener('input', function(e) {{
            e.stopPropagation();
            var idx = this.value;
            timeLabel.innerText = labels[idx];
            if (isRadarOn && urls[idx] !== "") {{
                radarLayer.setUrl(urls[idx]);
            }
        }});

        // 【修正版】高精度で現在地を強制取得する自動追跡ワープ関数
        function findMe() {{
            if (navigator.geolocation) {{
                var gpsOptions = {{
                    enableHighAccuracy: true,
                    timeout: 10000,
                    maximumAge: 0
                }};
                navigator.geolocation.getCurrentPosition(function(position) {{
                    var lat = position.coords.latitude;
                    var lng = position.coords.longitude;
                    mapObj.flyTo([lat, lng], 17);  // ズーム17の超ドアップ
                    if (userMarker) {{ mapObj.removeLayer(userMarker); }}
                    userMarker = L.circleMarker([lat, lng], {{
                        color: '#137cbd', fillColor: '#137cbd', fillOpacity: 0.8, radius: 8
                    }}).addTo(mapObj).bindPopup("あなたの現在地").openPopup();
                }}, function(error) {{
                    console.log("GPS自動起動失敗。ブラウザの設定または電波状況を確認してください。");
                }}, gpsOptions);
            }
        }}

        // ① ボタン押下時
        gpsBtn.addEventListener('click', findMe);

        // ② 読み込み完了0.5秒後の自動実行
        setTimeout(findMe, 500);
    }}
}});
</script>
"""

akita_map.get_root().html.add_child(folium.Element(external_ui_html))
akita_map.get_root().html.add_child(folium.Element(external_ui_script))

# 右上：いまの天気一覧パネルの組み込み
summary_html = """
<div style="position: fixed; top: 15px; right: 15px; z-index: 999999; background-color: white; border: 3px solid #333; padding: 10px; border-radius: 10px; box-shadow: 4px 4px 10px rgba(0,0,0,0.4); width: 220px; max-height: 45vh; overflow-y: auto; font-family: sans-serif;">
    <div style="font-weight: bold; font-size: 16px; margin-bottom: 8px; text-align: center; border-bottom: 2px solid #333;">🌡️ いまの天気</div>
    <table style="width: 100%; font-size: 14px; border-collapse: collapse;">
"""
for i, city_name in enumerate(AKITA_CITIES.keys()):
    current = weather_data[i]["current_weather"]
    summary_html += f"""
    <tr style="border-bottom: 1px solid #ddd; height: 35px;">
        <td style="font-weight: bold;">{city_name}</td>
        <td style="font-size: 20px;">{get_weather_icon(current.get("weathercode", -1))}</td>
        <td style="color: #d32f2f; font-weight: bold;">{current.get("temperature", "--")}℃</td>
    </tr>"""
summary_html += "</table></div>"
akita_map.get_root().html.add_child(folium.Element(summary_html))

# 左下：防災お天気アラートパネルの組み込み
warning_html = f"""
<div style="position: fixed; bottom: 15px; left: 15px; z-index: 999999; background-color: #FFF0F0; border: 3px solid #d32f2f; padding: 15px; border-radius: 12px; font-family: sans-serif; box-shadow: 3px 3px 6px rgba(0,0,0,0.4); width: 380px; max-height: 180px; overflow-y: auto;">
    <div style="color: #d32f2f; font-size: 18px; font-weight: bold; margin-bottom: 8px;">⚠️ 防災・天気のお知らせ</div>
    <div style="font-size: 16px; color: #000; line-height: 1.6; font-weight: bold;">{jma_text}</div>
</div>
"""
akita_map.get_root().html.add_child(folium.Element(warning_html))


# ========================================================
# 🏙️ 各都市のお天気マーカー ＆ タップで週間天気表示ポップアップ
# ========================================================
for i, (city_name, coords) in enumerate(AKITA_CITIES.items()):
    current = weather_data[i]["current_weather"]
    daily = weather_data[i]["daily"]
    
    # 吹き出し（ポップアップ）の中身を作成
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

    # マップ上に表示されるかわいいお天気アイコンを作成
    marker_html = f"""
    <div style="background-color: white; border: 3px solid #333; border-radius: 10px; padding: 5px; text-align: center; width: 100px; cursor: pointer; box-shadow: 3px 3px 6px rgba(0,0,0,0.3);">
        <div style="font-size: 14px; font-weight: bold;">{city_name}</div>
        <div style="font-size: 24px;">{get_weather_icon(current.get('weathercode', -1))}</div>
        <div style="font-size: 16px; color: #d32f2f; font-weight: bold;">{current.get('temperature', '--')}℃</div>
    </div>"""
    
    folium.Marker(
        location=[coords["lat"], coords["lon"]], 
        icon=DivIcon(html=marker_html, icon_anchor=(50, 50)), 
        popup=Popup(popup_html, max_width=400)
    ).add_to(akita_map)


# ========================================================
# 🚀 描画：Streamlit画面にマップをドカンと表示！
# ========================================================
st_folium(akita_map, width="100%", height=700)
