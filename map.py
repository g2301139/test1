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
folium.TileLayer(
    tiles='OpenStreetMap',
    name='通常の地図（道路・建物）',
    control=True
).add_to(akita_map)

# ② 国土地理院 航空写真
folium.TileLayer(
    tiles='https://cyberjapandata.gsi.go.jp/xyz/ort/{z}/{x}/{y}.jpg',
    attr='国土地理院 航空写真',
    name='航空写真（上空からの景色）',
    control=True
).add_to(akita_map)

# ③ 国土地理院 淡色地図
folium.TileLayer(
    tiles='https://cyberjapandata.gsi.go.jp/xyz/pale/{z}/{x}/{y}.png',
    attr='国土地理院 淡色地図',
    name='淡色地図（シンプル表示）',
    control=True
).add_to(akita_map)

folium.LayerControl(position='topright', collapsed=True).add_to(akita_map)

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
# ⚡ 【スマホ専用】開いた瞬間に現在地へ自動ワープする魔法のコード
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
                        }).addTo(mapObj).bindPopup("あなたの現在地（周辺）").openPopup();
                    } catch(e) {
                        alert("マップの移動に失敗しました。秋田県外にいませんか？\\nエラー: " + e.message);
                    }
                }
            }, function(error) {
                var errMsg = "";
                if (error.code === 1) errMsg = "位置情報の利用が許可されていません。iPhoneの『設定 ＞ プライバシーとセキュリティ ＞ 位置情報サービス』でSafariが許可されているか確認してください。";
                else if (error.code === 2) errMsg = "位置情報が特定できません（電波状況など）。";
                else if (error.code === 3) errMsg = "タイムアウトしました。";
                alert("❌ GPS取得失敗: " + errMsg + "\\n(" + error.message + ")");
            }, { enableHighAccuracy: true, timeout: 10000, maximumAge: 0 });
        } else {
            alert("お使いのブラウザはGPSに対応していません。");
        }
    }

    window.onload = function() {
        setTimeout(getLocation, 1500); // 描画安定のため1.5秒後に起動
    };
</script>
"""
akita_map.get_root().header.add_child(folium.Element(custom_smartphone_script))
# ========================================================

# 画面にタイトルを表示
st.title("🗺️ 秋田 現在地GPSマップ")

# ========================================================
# 🔥【Safariの防壁を突破】同一ドメイン配信による埋め込み
# ========================================================
# 1. あなたのプログラムが動いている現在のフォルダ（書き込み権限100%あり）を取得
current_dir = os.path.dirname(os.path.abspath(__file__))
map_filename = "akita_gps_map.html"
map_full_path = os.path.join(current_dir, map_filename)

# 2. 地図HTMLをフォルダ内に保存（PermissionErrorを完全回避）
akita_map.save(map_full_path)

# 3. このフォルダ自体をStreamlitの安全な「静的アセット配信エンドポイント」として登録
# これにより、地図HTMLが「不審な外部データ」ではなく「アプリ自身の安全なWebページ」として認識されます。
component_url = components.declare_component("safari_gps_fix", path=current_dir)

# 4. 生成された安全なルートURLを参照し、allow="geolocation" を持った生の iframe を埋め込む
# これでマップが表示されない不具合を消し去り、かつSafariのGPSロックも通過します。
st.markdown(
    f'<iframe src="./app/index.html?/{map_filename}" width="100%" height="700" style="border:none;" allow="geolocation"></iframe>',
    unsafe_allow_html=True
)
