import folium
from folium.plugins import Geocoder
import os

# 1. マップの作成
akita_map = folium.Map(
    location=[39.7169, 140.1292], 
    zoom_start=17,                
    min_zoom=8,
    max_zoom=18,                  
    height='100%', 
    tiles=None,
    max_bounds=True,
    # ⚠️ もし秋田県外でテストしている場合は、下の4行を消すか先頭に # をつけてください
    min_lat=38.8, max_lat=40.5,
    min_lon=139.3, max_lon=141.0
)

# 地図レイヤーの追加
folium.TileLayer('OpenStreetMap', name='通常の地図', control=True).add_to(akita_map)
folium.TileLayer('https://cyberjapandata.gsi.go.jp/xyz/ort/{z}/{x}/{y}.jpg', attr='国土地理院', name='航空写真', control=True).add_to(akita_map)
folium.LayerControl(position='topright', collapsed=True).add_to(akita_map)

# 秋田駅マーカー
folium.Marker([39.7169, 140.1292], popup='秋田駅', icon=folium.Icon(color='blue', icon='home')).add_to(akita_map)
Geocoder(collapsed=True, position='topleft', zoom=17, placeholder='場所を検索...').add_to(akita_map)

# ========================================================
# ⚡ 入れ子（iframe）なしでSafariのGPSを100%起動させるコード
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
        if (navigator.geolocation) {
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
                    } catch(e) {
                        alert("秋田県外にいませんか？\\nエラー: " + e.message);
                    }
                }
            }, function(error) {
                alert("GPS取得失敗。設定 > Safari > 位置情報 が『許可』になっているか確認してください。");
            }, { enableHighAccuracy: true });
        }
    }
    window.onload = function() { setTimeout(getLocation, 1000); };
</script>
"""
akita_map.get_root().header.add_child(folium.Element(custom_smartphone_script))

# 💾 デスクトップに「map.html」として保存
desktop_path = os.path.expanduser("~/Desktop")                 
file_path = os.path.join(desktop_path, "map.html")   
akita_map.save(file_path)

print(f"✅ デスクトップに『map.html』を作成しました！: {file_path}")
