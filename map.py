<!DOCTYPE html>
<html lang="ja">
<head>
    <meta charset="UTF-8">
    <meta name="viewport" content="width=device-width, initial-scale=1.0">
    <title>秋田 完全GPSマップ</title>
    <link rel="stylesheet" href="https://unpkg.com/leaflet@1.9.4/dist/leaflet.css" />
    <script src="https://unpkg.com/leaflet@1.9.4/dist/leaflet.js"></script>
    <style>
        html, body, #map { width: 100%; height: 100%; margin: 0; padding: 0; }
        #gps-btn {
            position: absolute; top: 20px; right: 20px; z-index: 1000;
            background: #008CBA; color: white; border: none; padding: 15px 20px;
            border-radius: 8px; font-size: 16px; font-weight: bold; cursor: pointer;
            box-shadow: 0 4px 6px rgba(0,0,0,0.2);
        }
    </style>
</head>
<body>

    <button id="gps-btn" onclick="getMyLocation()">📱 現在地を取得</button>
    <div id="map"></div>

    <script>
        // 初期位置は秋田駅
        var map = L.map('map').setView([39.7169, 140.1292], 16);

        // 背景地図（OpenStreetMap）
        L.tileLayer('https://{s}.tile.openstreetmap.org/{z}/{x}/{y}.png', {
            attribution: '&copy; OpenStreetMap contributors'
        }).addTo(map);

        var userMarker = null;

        // 【本物のGPS起動関数】
        function getMyLocation() {
            if (!navigator.geolocation) {
                alert("お使いのスマホはGPSに対応していません。");
                return;
            }

            navigator.geolocation.getCurrentPosition(function(position) {
                var lat = position.coords.latitude;
                var lng = position.coords.longitude;

                // 現在地にワープしてピンを立てる
                map.flyTo([lat, lng], 17);

                if (userMarker) { map.removeLayer(userMarker); }
                userMarker = L.circleMarker([lat, lng], {
                    color: '#137cbd', fillColor: '#137cbd', fillOpacity: 0.8, radius: 10
                }).addTo(map).bindPopup("あなたの現在地").openPopup();

            }, function(error) {
                alert("GPSの取得に失敗しました。スマホの設定でSafariの位置情報を許可してください。");
            }, { enableHighAccuracy: true, timeout: 10000, maximumAge: 0 });
        }

        // 起動時に自動でGPSを呼び出す
        window.onload = function() {
            setTimeout(getMyLocation, 1000);
        };
    </script>
</body>
</html>
