import streamlit as st
import folium
from folium.plugins import Geocoder  
import base64

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
            alert("❌ GPS取得失敗: " + error.message);
        }, { enableHighAccuracy: true, timeout: 10000, maximumAge: 0 });
    }
    window.onload = function() { setTimeout(getLocation, 1500); };
</script>
"""
akita_map.get_root().header.add_child(folium.Element(custom_smartphone_script))

# タイトルを表示
st.title("🗺️ 秋田 現在地GPSマップ")

# ========================================================
# 🔥【究極の突破策】HTMLをBase64化して、生のiframeで描画
# ========================================================
# 1. 地図をHTML文字列としてレンダリング
map_html = akita_map.get_root().render()

# 2. 文字列をBase64に変換（ブラウザのセキュリティ制限を回避するため）
b64_html = base64.b64encode(map_html.encode('utf-8')).decode('utf-8')
data_url = f"data:text/html;base64,{b64_html}"

# 3. st.markdown を使い、allow="geolocation" を持った「本物のiframe」を直接生成
st.markdown(
    f'<iframe src="{data_url}" width="100%" height="700" style="border:none;" allow="geolocation"></iframe>',
    unsafe_allow_html=True
)
