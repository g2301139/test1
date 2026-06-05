import streamlit as st
import folium
from folium.plugins import Geocoder

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
# ⚡ 【Safari完全突破】現在地ワープJavaScript
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

        // 高精度をあえてfalseにし、Safariに警戒させずに素早く位置を出させます
        var options = {
            enableHighAccuracy: false, 
            timeout: 10000,
            maximumAge: 60000
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
                    alert("⚠️ 秋田県外にいませんか？\\nエラー: " + e.message);
                }
            }
        }, function(error) {
            alert("❌ GPS取得失敗。Safariの履歴リセットが必要かもしれません。");
        }, options);
    }

    // 読み込み完了後、確実に実行
    window.onload = function() {
        setTimeout(getLocation, 1500); 
    };
</script>
"""
akita_map.get_root().header.add_child(folium.Element(custom_smartphone_script))
# ========================================================

# 💡 ここからがSafari対策の魔法の処理です
# 地図を一度HTML文字列にして、Streamlit自体の「最上位のHTML」として直接書き出します
map_html = akita_map.get_root().render()

# タイトルは地図の中に浮かび上がらせるか、不要なら消してもOKです
st.markdown("<h3 style='text-align: center;'>🗺️ 秋田 現在地GPSマップ</h3>", unsafe_allow_html=True)

# 🔥 二重の箱（iframe）を作らず、Streamlitのメイン画面にそのままHTMLをドカンと融合させる
st.html(map_html)
