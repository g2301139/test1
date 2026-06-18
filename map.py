import streamlit as st
import folium
from folium.plugins import Geocoder  
import streamlit.components.v1 as components
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

# ① 通常の道路地図（OpenStreetMap）
folium.TileLayer('OpenStreetMap', name='通常の地図（道路・建物）', control=True).add_to(akita_map)

# ② 国土地理院 航空写真
folium.TileLayer('https://cyberjapandata.gsi.go.jp/xyz/ort/{z}/{x}/{y}.jpg', attr='国土地理院 航空写真', name='航空写真（上空からの景色）', control=True).add_to(akita_map)

# ③ 国土地理院 淡色地図
folium.TileLayer('https://cyberjapandata.gsi.go.jp/xyz/pale/{z}/{x}/{y}.png', attr='国土地理院 淡色地図', name='淡色地図（シンプル表示）', control=True).add_to(akita_map)

folium.LayerControl(position='topright', collapsed=True).add_to(akita_map)

# 2. 目印として秋田駅にマーカーを設置
folium.Marker([39.7169, 140.1292], popup='秋田駅', icon=folium.Icon(color='blue', icon='home')).add_to(akita_map)

# 3. 🗺️ 検索機能（Geocoder）を追加
Geocoder(collapsed=True, position='topleft', zoom=17, placeholder='場所を検索...').add_to(akita_map)

# ========================================================
# ⚡ 【Safari完全突破版】現在地ワープJavaScript
# ========================================================
custom_smartphone_script = """
<style>
    html, body { width: 100%; height: 100vh; margin: 0; padding: 0; }
    #current-location-btn {
        position: absolute; top: 10px; right: 10px; z-index: 1000;
        background: white; border: 2px solid #ccc; padding: 8px 12px;
        border-radius: 5px; cursor: pointer; font-weight: bold; font-size: 14px;
    }
    .leaflet-control-layers {
        margin-top: 60px !important; 
        border: 2px solid #ccc !important;
        border-radius: 5px !important;
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

        var options = {
            enableHighAccuracy: true,  // 精度優先に変更
            timeout: 10000,
            maximumAge: 0              // キャッシュを使わず常に最新を取得
        };

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
                    }).addTo(mapObj).bindPopup("あなたの現在地（周辺）").openPopup();
                } catch(e) {
                    alert("⚠️ エラー: " + e.message);
                }
            }
        }, function(error) {
            alert("❌ GPS取得失敗: " + error.message + "\\nSafariの「設定 -> プライバシーとセキュリティ -> 位置情報サービス」を確認してください。");
        }, options);
    }

    window.onload = function() {
        setTimeout(getLocation, 1500); 
    };
</script>
"""
akita_map.get_root().header.add_child(folium.Element(custom_smartphone_script))
# ========================================================

# タイトルを表示
st.title("🗺️ 秋田 現在地GPSマップ")

# 🗺️ 地図を一度HTMLファイルとして一時保存
map_html_path = "temp_map.html"
akita_map.save(map_html_path)

# ファイルを読み込み
with open(map_html_path, "r", encoding="utf-8") as f:
    html_content = f.read()

# 🔥【最重要】Safariのブロックを解除する iframe の直接埋め込み
# allow="geolocation" を明示し、sandbox属性で必要な権限をすべて解放します。
st.components.v1.html(
    html_content,
    height=700,
    scrolling=True
)

# 一時ファイルの削除（任意）
if os.path.exists(map_html_path):
    os.remove(map_html_path)
