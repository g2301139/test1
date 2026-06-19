import streamlit as st
import streamlit.components.v1 as components

# 画面を横いっぱいに広げる設定
st.set_page_config(layout="wide")

st.title("🗺️ 秋田 現在地GPS＆観光・行政マップ")
st.write("右上のメニューで『航空写真』に切り替えられます。また、主要な場所にピンを設置しました。")

# ========================================================
# 🔥 機能を大幅に強化した「生HTML・JS」の塊
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
            position: absolute; top: 15px; right: 70px; z-index: 1000;
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
        // ----------------------------------------------------
        // 【機能1】各種背景地図レイヤーの定義（国土地理院など）
        // ----------------------------------------------------
        // ① 通常の道路地図（OpenStreetMap）
        var osm = L.tileLayer('https://{s}.tile.openstreetmap.org/{z}/{x}/{y}.png', {
            attribution: '&copy; OpenStreetMap contributors'
        });

        // ② 国土地理院 航空写真
        var gsiSatellite = L.tileLayer('https://cyberjapandata.gsi.go.jp/xyz/ort/{z}/{x}/{y}.jpg', {
            attribution: '国土地理院 航空写真'
        });

        // ③ 国土地理院 淡色地図（シンプルで見やすい）
        var gsiPale = L.tileLayer('https://cyberjapandata.gsi.go.jp/xyz/pale/{z}/{x}/{y}.png', {
            attribution: '国土地理院 淡色地図'
        });

        // 1. マップ初期化（初期背景は通常の地図、秋田駅周辺、ズーム15）
        var map = L.map('map', {
            zoomControl: true,
            maxZoom: 18,
            minZoom: 8,
            layers: [osm] // 最初に表示する地図を指定
        }).setView([39.7169, 140.1292], 15);

        // ----------------------------------------------------
        // 【機能1の続き】地図切り替えボタンを画面右上に追加
        // ----------------------------------------------------
        var baseMaps = {
            "通常の地図": osm,
            "航空写真 (上空)": gsiSatellite,
            "シンプルな地図": gsiPale
        };
        L.control.layers(baseMaps, null, { position: 'topright' }).addTo(map);

        // ----------------------------------------------------
        // 【機能3】最初から特定の場所にピンを立てておく
        // ----------------------------------------------------
        // ① 秋田駅
        L.marker([39.7169, 140.1292])
            .addTo(map)
            .bindPopup("<b>🏢 秋田駅</b><br>秋田の玄関口です。");

        // ② 千秋公園
        L.marker([39.7222, 140.1236])
            .addTo(map)
            .bindPopup("<b>🌸 千秋公園</b><br>秋田城跡にある美しい公園です。");

        // ③ 秋田県庁
        L.marker([39.7182, 140.1030])
            .addTo(map)
            .bindPopup("<b>🔰 秋田県庁</b><br>行政の中心地です。");


        // 2. GPS発動関数（変わりません）
        var userMarker = null;
        function askGPS() {
            if (!navigator.geolocation) {
                alert("お使いのブラウザはGPSに対応していません。");
                return;
            }

            navigator.geolocation.getCurrentPosition(function(position) {
                var lat = position.coords.latitude;
                var lng = position.coords.longitude;

                // 現在地へスムーズにジャンプ（ドアップにズーム17）
                map.flyTo([lat, lng], 17);

                if (userMarker) { map.removeLayer(userMarker); }

                userMarker = L.circleMarker([lat, lng], {
                    color: '#137cbd', fillColor: '#137cbd', fillOpacity: 0.8, radius: 8
                }).addTo(map).bindPopup("あなたの現在地").openPopup();

            }, function(error) {
                alert("❌ GPS取得失敗。iPhoneの『設定 ＞ プライバシーとセキュリティ ＞ 位置情報サービス』でSafariが許可されているか確認してください。");
            }, { enableHighAccuracy: true, timeout: 10000, maximumAge: 0 });
        }

        // ページが開いて1.5秒後に自動で位置情報を1回要求してみる
        window.onload = function() {
            setTimeout(askGPS, 1500);
        };
    </script>
</body>
</html>
"""

# ========================================================
# 🗺️ 埋め込み表示
# ========================================================
components.html(raw_html_code, height=700, scrolling=False)
