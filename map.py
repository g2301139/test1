import streamlit as st
import folium
from folium.plugins import Geocoder

# 画面を横いっぱいに広げる設定
st.set_page_config(layout="wide")

st.title("🗺️ 秋田 案内・検索マップ")
st.write("Safariのセキュリティブロックを受けずに、安全に場所を特定・検索できるマップです。")

# ========================================================
# 🛠️ 画面上部の入力コントロール（Safariの制限を受けません）
# ========================================================
col1, col2 = st.columns(2)
with col1:
    st.info("💡 左上の『場所を検索...（虫眼鏡マーク）』から、駅名や施設名を入力すると一瞬でその場所にジャンプできます！")

with col2:
    # 万が一、自分のいまの座標（Googleマップ等からコピーしたもの）を入れたい場合のワープ機能
    user_coords = st.text_input("📍 特定の座標へ移動したい場合は入力（例: 39.7169, 140.1292）", "")

# 初期位置（デフォルトは秋田駅）
start_lat, start_lng = 39.7169, 140.1292

if user_coords:
    try:
        lat_str, lng_str = user_coords.split(",")
        start_lat = float(lat_str.strip())
        start_lng = float(lng_str.strip())
        st.success(f"入力された座標（{start_lat}, {start_lng}）にマップを移動しました！")
    except:
        st.error("座標の形式が正しくありません。『39.7169, 140.1292』のようにカンマで区切って入力してください。")

# ========================================================
# 1. マップの作成
# ========================================================
akita_map = folium.Map(
    location=[start_lat, start_lng], 
    zoom_start=17,                
    min_zoom=8,
    max_zoom=18,                  
    height='100%', 
    tiles=None,                   
    max_bounds=True,
    min_lat=38.8, max_lat=40.5,
    min_lon=139.3, max_lon=141.0
)

# 各種レイヤー追加
folium.TileLayer('OpenStreetMap', name='通常の地図（道路・建物）', control=True).add_to(akita_map)
folium.TileLayer('https://cyberjapandata.gsi.go.jp/xyz/ort/{z}/{x}/{y}.jpg', attr='国土地理院 航空写真', name='航空写真（上空からの景色）', control=True).add_to(akita_map)
folium.TileLayer('https://cyberjapandata.gsi.go.jp/xyz/pale/{z}/{x}/{y}.png', attr='国土地理院 淡色地図', name='淡色地図（シンプル表示）', control=True).add_to(akita_map)
folium.LayerControl(position='topright', collapsed=True).add_to(akita_map)

# 指定位置にピンを立てる
folium.Marker(
    [start_lat, start_lng], 
    popup='選択中の位置',
    icon=folium.Icon(color='red' if user_coords else 'blue', icon='info-sign')
).add_to(akita_map)

# 🗺️ 検索機能（Geocoder）を追加
Geocoder(
    collapsed=False, # 最初から検索窓を開いておき、使いやすくします
    position='topleft', 
    zoom=17, 
    placeholder='場所を検索...'
).add_to(akita_map)

# ========================================================
# 🗺️ 地図を表示（絶対にエラーが起きない標準埋め込み）
# ========================================================
map_html = akita_map.get_root().render()
st.components.v1.html(map_html, height=650, scrolling=True)
