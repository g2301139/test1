#たつし--------------------------------------------------------------------------------------------------------------
import requests
import folium
from folium.features import DivIcon
from folium import Popup
import webbrowser
import os
import json
import time
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
    if code == 0: return "☀️"
    elif 1 <= code <= 3: return "☁️"
    elif 45 <= code <= 48: return "🌫️"
    elif 51 <= code <= 55: return "🌧️"
    elif 61 <= code <= 65: return "☔"
    elif 71 <= code <= 75: return "⛄"
    elif 80 <= code <= 82: return "🌦️"
    elif 95 <= code <= 99: return "⛈️"
    else: return "❓"

def create_future_weather_map():
    print("最新の時間を計算し、15時間先までのデータを準備しています...")
    
    # 1. 気象庁の防災情報
    jma_text = "情報の取得に失敗しました。"
    try:
        jma_url = "https://www.jma.go.jp/bosai/forecast/data/overview_forecast/050000.json"
        jma_response = requests.get(jma_url)
        jma_text = jma_response.json().get("text", "").replace('\n', '<br>')
    except: pass

    # 2. Open-Meteo 天気データ
    lats = ",".join([str(city["lat"]) for city in AKITA_CITIES.values()])
    lons = ",".join([str(city["lon"]) for city in AKITA_CITIES.values()])
    om_url = f"https://api.open-meteo.com/v1/forecast?latitude={lats}&longitude={lons}&current_weather=true&daily=weathercode,temperature_2m_max,temperature_2m_min&timezone=Asia/Tokyo"
    try:
        data = requests.get(om_url).json()
    except Exception as e:
        print(f"天気データの取得エラー: {e}")
        return

    # 3. 雨雲レーダーの時間データ取得
    js_urls = []
    js_labels = []
    try:
        # 気象庁のサーバーキャッシュを回避するためタイムスタンプを付与
        cb = int(time.time() * 1000)
        urls_to_fetch = [
            f"https://www.jma.go.jp/bosai/jmatile/data/nowc/targetTimes_N1.json?_={cb}",
            f"https://www.jma.go.jp/bosai/jmatile/data/nowc/targetTimes_N2.json?_={cb}",
            f"https://www.jma.go.jp/bosai/jmatile/data/nowc/targetTimes_N3.json?_={cb}",
            f"https://www.jma.go.jp/bosai/jmatile/data/nowc/targetTimes_N4.json?_={cb}"
        ]
        
        all_times = {}
        for url in urls_to_fetch:
            try:
                resp = requests.get(url)
                if resp.status_code == 200:
                    for t in resp.json():
                        key = t["validtime"]
                        if key not in all_times or t["basetime"] > all_times[key]["basetime"]:
                            all_times[key] = t
            except:
                pass
                
        # ★最重要: 観測データ(basetime == validtime)の中で最新のものを「本当の現在」とする
        current_time_str = None
        for t in all_times.values():
            if t["basetime"] == t["validtime"]:
                if current_time_str is None or t["validtime"] > current_time_str:
                    current_time_str = t["validtime"]

        # 時間順に並び替え
        forecast_list = list(all_times.values())
        
        # 過去データを確実に切り捨て、「現在時刻」以降のデータだけを残す
        if current_time_str:
            forecast_list = [t for t in forecast_list if t["validtime"] >= current_time_str]
            
        forecast_list.sort(key=lambda x: x["validtime"])

        if len(forecast_list) > 0:
            # 基準となる「現在」のUTC時間
            dt_base_now_utc = datetime.strptime(forecast_list[0]["validtime"], "%Y%m%d%H%M%S")

            for t in forecast_list:
                elements = t.get("elements", [])
                if "prca" in elements:
                    element = "prca"
                elif "hrpns" in elements:
                    element = "hrpns"
                else:
                    element = "hrpns"

                url = f"https://www.jma.go.jp/bosai/jmatile/data/nowc/{t['basetime']}/none/{t['validtime']}/surf/{element}/{{z}}/{{x}}/{{y}}.png"
                js_urls.append(url)

                # 対象時間のUTC時間
                dt_vt_utc = datetime.strptime(t['validtime'], "%Y%m%d%H%M%S")
                
                # UTCから日本時間（+9時間）へ変換
                dt_vt_jst = dt_vt_utc + timedelta(hours=9)
                time_str = dt_vt_jst.strftime('%H:%M')

                # 現在からの経過分（計算はUTC同士）
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
            
    except Exception as e:
        print(f"時間データの取得エラー: {e}")

    # 万が一データが空になった時の保険
    if len(js_urls) == 0:
        js_urls = [""] * 10
        js_labels = [f"エラー({i})" for i in range(10)]

    urls_json = json.dumps(js_urls)
    labels_json = json.dumps(js_labels)

    # 地図の初期化
    akita_map = folium.Map(location=[39.6, 140.1], zoom_start=8, tiles="OpenStreetMap")

    # 4. UIの構築
    external_ui_html = f"""
    <div id="independent-ui" style="position: fixed; top: 15px; left: 50px; z-index: 999999; background: rgba(255,255,255,0.95); padding: 15px; border-radius: 12px; border: 3px solid #0D47A1; box-shadow: 0 4px 10px rgba(0,0,0,0.4); width: 280px; font-family: sans-serif;">
        <button id="radar-btn" style="width: 100%; background: #2196F3; color: white; border: none; padding: 12px; border-radius: 8px; font-size: 16px; font-weight: bold; cursor: pointer; box-shadow: 0 2px 4px rgba(0,0,0,0.2);">
            🌧️ 雨雲レーダーをつける
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
            <div style="font-size: 11px; color: #666; margin-top: 8px; text-align: center; line-height: 1.3;">
                ※レーダー観測の仕様上、5〜10分前の時刻が「現在(最新)」となります。
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
        var checkMapInterval = setInterval(function() {{
            for (var key in window) {{
                if (window[key] instanceof L.Map) {{
                    mapObj = window[key];
                    clearInterval(checkMapInterval);
                    initLogic();
                    break;
                }}
            }}
        }}, 500);

        function initLogic() {{
            var radarLayer = L.tileLayer(urls[0], {{opacity: 0.6, zIndex: 1000}});
            var isRadarOn = false;
            
            var btn = document.getElementById('radar-btn');
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
                }} else {{
                    btn.style.background = '#2196F3';
                    btn.innerHTML = '🌧️ 雨雲レーダーをつける';
                    sliderBox.style.display = 'none';
                    mapObj.removeLayer(radarLayer);
                }}
            }});

            slider.addEventListener('input', function(e) {{
                e.stopPropagation();
                var idx = this.value;
                timeLabel.innerText = labels[idx];
                if (isRadarOn && urls[idx] !== "") {{
                    radarLayer.setUrl(urls[idx]);
                }}
            }});
        }}
    }});
    </script>
    """

    akita_map.get_root().html.add_child(folium.Element(external_ui_html))
    akita_map.get_root().html.add_child(folium.Element(external_ui_script))

    summary_html = """
    <div style="position: fixed; top: 15px; right: 15px; z-index: 999999; background-color: white; border: 3px solid #333; padding: 10px; border-radius: 10px; box-shadow: 4px 4px 10px rgba(0,0,0,0.5); width: 220px; max-height: 80vh; overflow-y: auto; font-family: sans-serif;">
        <div style="font-weight: bold; font-size: 16px; margin-bottom: 8px; text-align: center; border-bottom: 2px solid #333;">🌡️ いまの天気</div>
        <table style="width: 100%; font-size: 14px; border-collapse: collapse;">
    """
    for i, city_name in enumerate(AKITA_CITIES.keys()):
        current = data[i]["current_weather"]
        summary_html += f"""
        <tr style="border-bottom: 1px solid #ddd; height: 35px;">
            <td style="font-weight: bold;">{city_name}</td>
            <td style="font-size: 20px;">{get_weather_icon(current["weathercode"])}</td>
            <td style="color: #d32f2f; font-weight: bold;">{current["temperature"]}℃</td>
        </tr>"""
    summary_html += "</table></div>"
    akita_map.get_root().html.add_child(folium.Element(summary_html))

    warning_html = f"""
    <div style="position: fixed; bottom: 15px; left: 15px; z-index: 999999; background-color: #FFF0F0; border: 3px solid #d32f2f; padding: 15px; border-radius: 12px; font-family: sans-serif; box-shadow: 3px 3px 6px rgba(0,0,0,0.4); width: 380px; max-height: 180px; overflow-y: auto;">
        <div style="color: #d32f2f; font-size: 18px; font-weight: bold; margin-bottom: 8px;">⚠️ 防災・天気のお知らせ</div>
        <div style="font-size: 16px; color: #000; line-height: 1.6; font-weight: bold;">{jma_text}</div>
    </div>
    """
    akita_map.get_root().html.add_child(folium.Element(warning_html))

    for i, (city_name, coords) in enumerate(AKITA_CITIES.items()):
        current = data[i]["current_weather"]
        daily = data[i]["daily"]
        
        popup_html = f"<h3 style='margin:0 0 10px 0;'>📅 {city_name}の1週間</h3>"
        popup_html += "<table style='width: 350px; text-align: center; font-size: 16px; border-collapse: collapse;'>"
        popup_html += "<tr style='background-color: #eee;'><th>日</th><th>空</th><th>最高</th><th>最低</th></tr>"
        for d in range(7):
            popup_html += f"<tr style='border-bottom: 1px solid #ccc; height: 35px;'><td>{daily['time'][d][5:]}</td><td style='font-size:20px;'>{get_weather_icon(daily['weathercode'][d])}</td><td style='color:red;'>{daily['temperature_2m_max'][d]}℃</td><td style='color:blue;'>{daily['temperature_2m_min'][d]}℃</td></tr>"
        popup_html += "</table>"

        marker_html = f"""
        <div style="background-color: white; border: 3px solid #333; border-radius: 10px; padding: 5px; text-align: center; width: 100px; cursor: pointer; box-shadow: 3px 3px 6px rgba(0,0,0,0.3);">
            <div style="font-size: 14px; font-weight: bold;">{city_name}</div>
            <div style="font-size: 24px;">{get_weather_icon(current['weathercode'])}</div>
            <div style="font-size: 16px; color: #d32f2f; font-weight: bold;">{current['temperature']}℃</div>
        </div>"""
        
        folium.Marker(location=[coords["lat"], coords["lon"]], icon=DivIcon(html=marker_html, icon_anchor=(50, 50)), popup=Popup(popup_html, max_width=400)).add_to(akita_map)

    map_filename = "akita_final_perfect_cache_fixed.html"
    akita_map.save(map_filename)
    webbrowser.open('file://' + os.path.realpath(map_filename))
    print(f"キャッシュ対策と時間計算を最適化したマップを開きました！")

if __name__ == "__main__":
    create_future_weather_map()
#-----------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------

  
