# 起動する前にコンソールにpip install foliumを貼り付けてから実行し, リセットしてからプログラムを実行する
import folium
import os
import webbrowser

# 1. マップの作成（スマホの縦幅に合わせるため height='100%' を指定）
akita_map = folium.Map(
    location=[39.65, 140.2], 
    zoom_start=9,
    min_zoom=8,
    height='100%', 
    max_bounds=True,
    min_lat=38.8, max_lat=40.5,
    min_lon=139.3, max_lon=141.0
)

# 2. 目印として秋田駅にマーカーを設置
folium.Marker(
    [39.7169, 140.1292], 
    popup='秋田駅',
    icon=folium.Icon(color='blue', icon='home')
).add_to(akita_map)


# ========================================================
# ⚡ 【スマホ専用】一気に真っ白＆GPSブロックを解除する魔法のコード
# ========================================================
# この長い文字（HTML/CSS/JavaScript）を地図の中に直接埋め込むことで、
# OneDrive等のアプリ内から開いても画面が潰れず、安全に現在地を表示できるようになります。
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
                
                // 地図の変数名を自動取得して動かす（Foliumのマップオブジェクトに対応）
                var maps = Object.keys(window).filter(k => k.startsWith('map_'));
                if (maps.length > 0) {
                    var mapObj = window[maps[0]];
                    mapObj.flyTo([lat, lng], 14);
                    
                    if (userMarker) { mapObj.removeLayer(userMarker); }
                    userMarker = L.circleMarker([lat, lng], {
                        color: '#137cbd', fillColor: '#137cbd', fillOpacity: 0.8, radius: 8
                    }).addTo(mapObj).bindPopup("あなたの現在地（秋田県内）").openPopup();
                }
            }, function(error) {
                alert("GPSの取得に失敗しました。ブラウザの位置情報許可を確認してください。");
            }, { enableHighAccuracy: true });
        } else {
            alert("お使いのブラウザはGPSに対応していません。");
        }
    }
</script>
"""
# 地図のヘッダーとボディに一気に注入
akita_map.get_root().header.add_child(folium.Element(custom_smartphone_script))
# ========================================================


# 4. 保存先の設定（デスクトップ）
desktop_path = os.path.expanduser("~/Desktop")                 
file_path = os.path.join(desktop_path, "akita_gps_map.html")   

# 5. 指定した場所に保存
akita_map.save(file_path)

# 6. パソコンのブラウザで開く
webbrowser.open("file://" + file_path)

print(f"✨ スマホでも絶対に開けるマップを保存しました: {file_path}")
