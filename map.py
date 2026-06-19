import streamlit as st
import folium
from folium.plugins import Geocoder  
import os

# 画面を横いっぱいに広げる設定
st.set_page_config(layout="wide")

# 1. マップの作成（初期ズーム17の超ドアップ設定）
akita_map = folium.Map(
    location=[39.7169, 140.1292], 
    zoom_start=17,                
    min_zoom=8,
    max_zoom=18,                  
    height='100%', 
    tiles=None,                   
    max_bounds=True,
    min_lat=38.8, max_lat=40.5,
    min_lon=139.3, max_lon=141.0
)

# 各種レイヤー追加
folium.TileLayer('OpenStreetMap', name='通常の地図（道路・建物）', control=True).add_to(akita_map)
folium.TileLayer('https://cyberjapandata.gsi.go.jp/xyz/ort/{z}/{x}/{y}.jpg', attr='国土地理院 航空写真', name='航空写真（上空からの景色）', control=True).add_to(akita_map)
folium.TileLayer('https://cyberjapandata.gsi.go.jp/xyz/pale/{z}/{x}/{y}.png', attr='国土地理院 淡色地図', name='淡色地図（シンプル表示）', control=True).add_to(akita_map)
folium.LayerControl(position='topright', collapsed=True).add_to(akita_map)

# 秋田駅マーカーと検索機能
folium.Marker([39.7169, 140.1292], popup='秋田駅', icon=folium.Icon(color='blue', icon='home')).add_to(akita_map)
Geocoder(collapsed=True, position='topleft', zoom=17, placeholder='場所を検索...').add_to(akita_map)

# ========================================================
# ⚡ 現在地ワープJavaScript
# ========================================================
custom_smartphone_script = """
<style>
    html, body { width: 100%; height: 100vh; margin: 0; padding: 0; }
    #current-location-btn {
        position: absolute; top: 10px; right: 10px; z-index: 1000;
        background: white; border: 2px solid #ccc; padding: 8px 12px;
        border-radius: 5px; cursor: pointer; font-weight: bold; font-size: 14px;
    }
</style>
<button id="current-location-btn" onclick="getLocation()">📱 現在地を取得</button>
<script>
    var userMarker = null;
    function getLocation() {
        if (!navigator.geolocation) {
            alert("お使いのブラウザはGPSに対応していません。");
            return;
        }
        navigator.geolocation.getCurrentPosition(function(position) {
            var lat = position.coords.latitude;
            var lng = position.coords.longitude;
            var maps = Object.keys(window).filter(k => k.startsWith('map_'));
            if (maps.length > 0) {
                var mapObj = window[maps[0]];
                try {
                    mapObj.flyTo([lat, lng], 17);
                    if (userMarker) { mapObj.removeLayer(userMarker); }
                    userMarker = L.circleMarker([lat, lng], {
                        color: '#137cbd', fillColor: '#137cbd', fillOpacity: 0.8, radius: 8
                    }).addTo(mapObj).bindPopup("あなたの現在地").openPopup();
                } catch(e) { alert("エラー: " + e.message); }
            }
        }, function(error) {
            var errMsg = "GPS取得失敗: ";
            if (error.code === 1) errMsg += "位置情報の利用が許可されていません。";
            else if (error.code === 2) errMsg += "位置情報が特定できません。";
            else if (error.code === 3) errMsg += "タイムアウトしました。";
            alert("❌ " + errMsg + " (" + error.message + ")");
        }, { enableHighAccuracy: true, timeout: 10000, maximumAge: 0 });
    }
    window.onload = function() { setTimeout(getLocation, 1500); };
</script>
"""
akita_map.get_root().header.add_child(folium.Element(custom_smartphone_script))

# タイトルを表示
st.title("🗺️ 秋田 現在地GPSマップ")

# ========================================================
# 🔥【公式推奨アプローチ】書き込み可能なカスタムstatic機能を利用
# ========================================================
# 1. 自身のプロジェクト内に「static」というフォルダを自動作成する（書き込み権限あり）
static_dir = os.path.join(os.path.dirname(os.path.abspath(__file__)), "static")
if not os.path.exists(static_dir):
    os.makedirs(static_dir)

map_filename = "akita_gps_map.html"
map_full_path = os.path.join(static_dir, map_filename)

# 2. 地図HTMLを安全に保存
akita_map.save(map_full_path)

# 3. Streamlitに「static」フォルダ内のファイルを同一ドメインの静的ファイルとして公開させる設定
# StreamlitではアプリURLの末尾に「/app/static/ファイル名」で直接アクセスできます。
# これによりSafariは安全な同一オリジンとみなし、かつ地図が消える不具合も起きません。
st.markdown(
    f'<iframe src="./app/static/{map_filename}" width="100%" height="700" style="border:none;" allow="geolocation"></iframe>',
    unsafe_allow_html=True
)
