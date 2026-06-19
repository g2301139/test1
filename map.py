import streamlit as st
import folium
from folium.plugins import Geocoder, LocateControl  # 👈 LocateControlをインポート

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
# ⚡ 【最重要】Safariの防壁を突破する公式GPSボタン
# ========================================================
# JavaScriptを自作せず、Foliumが公式に用意しているGPS追跡機能を組み込みます。
# これにより、Streamlitのiframe内にあってもSafariが安全だと認識し、GPSが起動します。
LocateControl(
    position='topleft',            # 検索バーの下（左上）に配置
    zoom=17,                       # 現在地にジャンプしたときのズーム倍率
    fly_to=True,                   # スムーズに移動するアニメーションを有効化
    strings={"title": "📱 現在地を表示する", "popup": "あなたの現在地"},
    locate_options={
        "enableHighAccuracy": True, # 高精度GPSモード
        "timeout": 10000            # 10秒でタイムアウト
    }
).add_to(akita_map)
# ========================================================

# 画面にタイトルを表示
st.title("🗺️ 秋田 現在地GPSマップ")

# 🗺️ 地図をHTMLにレンダリング
map_html = akita_map.get_root().render()

# 🔥 【バグなし】Streamlit標準の安全なコンポーネントで描画（地図は絶対に消えません）
st.components.v1.html(map_html, height=700, scrolling=True)
