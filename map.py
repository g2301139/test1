import streamlit as st
import folium
from folium.plugins import Geocoder, LocateControl
import base64

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

# 各種レイヤー追加
folium.TileLayer('OpenStreetMap', name='通常の地図（道路・建物）', control=True).add_to(akita_map)
folium.TileLayer('https://cyberjapandata.gsi.go.jp/xyz/ort/{z}/{x}/{y}.jpg', attr='国土地理院 航空写真', name='航空写真（上空からの景色）', control=True).add_to(akita_map)
folium.TileLayer('https://cyberjapandata.gsi.go.jp/xyz/pale/{z}/{x}/{y}.png', attr='国土地理院 淡色地図', name='淡色地図（シンプル表示）', control=True).add_to(akita_map)
folium.LayerControl(position='topright', collapsed=True).add_to(akita_map)

# 秋田駅マーカーと検索機能
folium.Marker([39.7169, 140.1292], popup='秋田駅', icon=folium.Icon(color='blue', icon='home')).add_to(akita_map)
Geocoder(collapsed=True, position='topleft', zoom=17, placeholder='場所を検索...').add_to(akita_map)

# ⚡ Safariの防壁を突破する公式GPSボタン（別タブ表示時にも機能します）
LocateControl(
    position='topleft',
    zoom=17,
    fly_to=True,
    strings={"title": "📱 現在地を表示する", "popup": "あなたの現在地"},
    locate_options={"enableHighAccuracy": True, "timeout": 10000}
).add_to(akita_map)

# タイトルを表示
st.title("🗺️ 秋田 現在地GPSマップ")

# ========================================================
# 🔥【究極の解決策】Streamlitの檻から地図を脱出させる
# ========================================================
# 1. 地図をHTML文字列としてレンダリング
map_html = akita_map.get_root().render()

# 2. HTMLをBase64に変換
b64_html = base64.b64encode(map_html.encode('utf-8')).decode('utf-8')
data_url = f"data:text/html;base64,{b64_html}"

st.warning("⚠️ Streamlit内の地図ではSafariのセキュリティ制限によりGPSが動きません。下のボタンを押して『全画面地図』を開いてください。")

# 3. Safariで直接開くための特別なボタンを設置（st.markdownで装飾）
# ボタンを押すと、Streamlitを巻き込まずにSafariが直接地図を新規タブで開くため、GPSが100%機能します。
st.markdown(
    f'''
    <a href="{data_url}" target="_blank" style="text-decoration: none;">
        <button style="
            width: 100%;
            background-color: #008CBA;
            color: white;
            padding: 14px 20px;
            margin: 8px 0;
            border: none;
            border-radius: 8px;
            cursor: pointer;
            font-size: 20px;
            font-weight: bold;
            box-shadow: 0 4px 6px rgba(0,0,0,0.1);
        ">
            🚀 制限を解除して全画面で地図を開く（GPS有効化）
        </button>
    </a>
    ''',
    unsafe_allow_html=True
)

# プレビュー用（元々の埋め込み地図も一応残しておきます）
st.write("---")
st.subheader("プレビュー（※ここではGPSは動きません）")
st.components.v1.html(map_html, height=500, scrolling=True)
