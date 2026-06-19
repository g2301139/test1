import streamlit as st
import streamlit.components.v1 as components

# 画面を横いっぱいに広げる設定
st.set_page_config(layout="wide")

st.title("🗺️ 秋田 現在地GPSマップ")
st.write("地図の右上にある『📱 現在地を取得』ボタンを押すと、Safariでも位置情報が起動します。")

# ========================================================
# 🔥 Safariのセキュリティをすり抜ける「生HTML・JS」の塊
# ========================================================
raw_html_code = """
<!DOCTYPE html>
<html>
<head>
    <meta charset="UTF-8">
    <meta name="viewport" content="width=device-width, initial-scale=1.0">
    <link rel="stylesheet" href="https://unpkg.com/leaflet@1.9.4/dist/leaflet.css" />
    <script src="https://unpkg.com/leaflet@1.9.4/dist/leaflet.js"></script>
    <style>
        html, body, #map { width: 100%; height: 100vh; margin: 0; padding: 0; }
        #gps-btn {
            position: absolute; top: 15px; right: 15px; z-index: 1000;
            background: #137cbd; color: white; border: 2px solid white; 
            padding: 10px 16px; border-radius: 8px; font-size: 14px; 
            font-weight: bold; cursor: pointer; box-shadow: 0 2px 5px rgba(0,0,0,0.3);
        }
    </style>
</head>
<body>

    <button id="gps-btn" onclick="askGPS()">📱 現在地を取得</button>
    <div id="map"></div>

    <script>
        // 1. マップ初期化（秋田駅周辺、ズーム17）
        var map = L.map('map', {
            zoomControl: true,
            maxZoom: 18,
            minZoom: 8
        }).setView([39.7169, 140.1292], 17);

        // 通常の地図レイヤー（OpenStreetMap）
        L.tileLayer('https://{s}.tile.openstreetmap.org/{z}/{x}/{y}.png', {
            attribution: '&copy; OpenStreetMap'
        }).addTo(map);

        var userMarker = null;

        // 2. GPS発動関数
        function askGPS() {
            if (!navigator.geolocation) {
                alert("お使いのブラウザはGPSに対応していません。");
                return;
            }

            navigator.geolocation.getCurrentPosition(function(position) {
                var lat = position.coords.latitude;
                var lng = position.coords.longitude;

                // 現在地へスムーズにジャンプ
                map.flyTo([lat, lng], 17);

                // 古いマーカーがあれば消す
                if (userMarker) { map.removeLayer(userMarker); }

                // 新しい現在地ピンを打つ
                userMarker = L.circleMarker([lat, lng], {
                    color: '#137cbd', fillColor: '#137cbd', fillOpacity: 0.8, radius: 8
                }).addTo(map).bindPopup("あなたの現在地").openPopup();

            }, function(error) {
                alert("❌ GPS取得失敗。iPhoneの『設定 ＞ プライバシーとセキュリティ ＞ 位置情報サービス』でSafariが許可されているか確認してください。");
            }, { enableHighAccuracy: true, timeout: 10000, maximumAge: 0 });
        }

        // ページが開いて1秒後に自動で位置情報を1回要求してみる
        window.onload = function() {
            setTimeout(askGPS, 1000);
        };
    </script>
</body>
</html>
"""

# ========================================================
# 🗺️ 埋め込み表示（お檻のロックを解除）
# ========================================================
# HTML文字列を直接コンポーネントに流し込みます。
# これにより、Pythonの文法エラーを完全に防ぎつつ、マップを描画します。
components.html(raw_html_code, height=700, scrolling=False)
