import streamlit as st
from streamlit_folium import st_folium
import folium
from folium.plugins import Geocoder  

# 画面にタイトルを表示
st.title("🗺️ 秋田 現在地GPSマップ")

# 1. マップの作成（初期表示は秋田駅周辺）
akita_map = folium.Map(
    location=[39.7169, 140.1292], 
    zoom_start=17,                
    min_zoom=8,
    max_zoom=18,                  
    height='100%', 
    tiles=None,                   # レイヤーコントロールを使うため、ここではいったんNoneにします
    max_bounds=True,
    min_lat=38.8, max_lat=40.5,
    min_lon=139.3, max_lon=141.0
)

# ========================================================
# 🗺️ レイヤー（地図の種類）を3種類追加
# ========================================================
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

# ③ 国土地理院 淡色地図（シンプルで見やすい地図）
folium.TileLayer(
    tiles='https://cyberjapandata.gsi.go.jp/xyz/pale/{z}/{x}/{y}.png',
    attr='国土地理院 淡色地図',
    name='淡色地図（シンプル表示）',
    control=True
).add_to(akita_map)

# 右上：切り替えボタンを表示
folium.LayerControl(position='topright', collapsed=True).add_to(akita_map)
# ========================================================


# 2. 目印として秋田駅にマーカーを設置
folium.Marker(
    [39.7169, 140.1292], 
    popup='秋田駅',
    icon=folium.Icon(color='blue', icon='home')
).add_to(akita_map)

# 3. 🗺️ 検索機能（Geocoder）を追加
Geocoder(
    collapsed=True, 
    position='topleft', 
    zoom=17, 
    placeholder='場所を検索...'
).add_to(akita_map)


# ========================================================
# ⚡ 【修正版】高精度で現在地を取得してマップを移動するコード
# ========================================================
custom_smartphone_script = """
<style>
    html, body { width: 100%; height: 100vh; margin: 0; padding: 0; }
    #current-location-btn {
        position: absolute; top: 10px; right: 10px; z-index: 1000;
        background: white; border: 2px solid #ccc; padding: 8px 12px;
        border-radius: 5px; cursor: pointer; font-weight: bold; font-size: 14px;
        box-shadow: 0 2px 5px rgba(0,0,0,0.2);
    }
    .leaflet-control-layers {
        margin-top: 60px !important; /* ボタンと被らないように下にずらす */
        border: 2px solid #ccc !important;
        border-radius: 5px !important;
    }
</style>
<button id="current-location-btn" onclick="getLocation()">📱 現在地を取得</button>
<script>
    var userMarker = null;

    function getLocation() {
        if (navigator.geolocation) {
            // 🛠️ 高精度モード（GPS強制）を有効にして位置情報をリクエスト
            var gpsOptions = {
                enableHighAccuracy: true,  // 👈 これが最重要！基地局や駅ではなくGPSチップから取得します
                timeout: 10000,            // 10秒探して見つからなければタイムアウト
                maximumAge: 0              // キャッシュ（過去の古い位置）を使わず、今現在の場所を探す
            };

            navigator.geolocation.getCurrentPosition(function(position) {
                var lat = position.coords.latitude;
                var lng = position.coords.longitude;
                
                var maps = Object.keys(window).filter(k => k.startsWith('map_'));
                if (maps.length > 0) {
                    var mapObj = window[maps[0]];
                    
                    // 取得した現在地にカメラをスムーズに移動（ズーム17でドアップ）
                    mapObj.flyTo([lat, lng], 17);
                    
                    // すでに古い青ピンがあれば消して、新しい正確な場所にピンを打つ
                    if (userMarker) { mapObj.removeLayer(userMarker); }
                    userMarker = L.circleMarker([lat, lng], {
                        color: '#137cbd', fillColor: '#137cbd', fillOpacity: 0.8, radius: 8
                    }).addTo(mapObj).bindPopup("あなたの現在地").openPopup();
                }
            }, function(error) {
                // エラー内容を画面に分かりやすく出すように改善
                var errorMsg = "位置情報の取得に失敗しました。";
                if(error.code == 1) errorMsg = "位置情報の利用がブロックされています。ブラウザの設定で許可してください。";
                if(error.code == 2) errorMsg = "GPS信号が受信できません。電波の良い場所でお試しください。";
                if(error.code == 3) errorMsg = "位置情報の取得がタイムアウトしました。";
                alert(errorMsg);
            }, gpsOptions);
        } else {
            alert("お使いのブラウザはGPSに対応していません。");
        }
    }

    // 画面が開いてから0.5秒後に、自動で現在地へのワープを試みる
    setTimeout(getLocation, 500); 
</script>
"""
akita_map.get_root().header.add_child(folium.Element(custom_smartphone_script))
# ========================================================

# Streamlitの画面に地図を描画
st_folium(akita_map, width="100%", height=600)
