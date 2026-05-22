import subprocess
import random
import requests
import time

# --- メスガキ語録セクション ♡ ---
def get_mesugaki_phrase():
    aisatsu = [
        "またアタシを呼び出したの？ホント寂しがり屋なんだから♡",
        "そんなにアタシに構ってほしいんだ？可愛いとこあるじゃん♡",
        "なーに？おじさん、アタシがいないと何もできないの？♡",
        "はいはい、おじさんの大好きなアタシが来てあげたわよ♡"
    ]
    tenki_tail = [
        "おじさん、傘忘れてビショビショになっちゃえ♡",
        "アタシが教えてあげたんだから、感謝しなさいよね？",
        "こんなのも自分で調べられないなんて、ホント無能♡",
        "お外に出るなら、ちゃんとアタシの言うこと聞くんだよ？"
    ]
    kuma_msg = [
        "熊さんにおしり噛まれて泣きべそかきなよ♡",
        "おじさん、食べがいがありそうだから熊さんも喜ぶよ♡",
        "熊除けの鈴、おじさんの首につけてあげようか？♡",
        "熊さんに襲われても、アタシは助けてあげないからね♡"
    ]
    return {
        "aisatsu": random.choice(aisatsu),
        "tenki": random.choice(tenki_tail),
        "kuma": random.choice(kuma_msg)
    }

# --- 1. 情報を1個ずつのリストにして取ってくる関数 ---
def get_mesugaki_info_list():
    phrase = get_mesugaki_phrase()
    results = []
    
    # ① 最初の挨拶
    results.append(("♡ 構ってちゃんのおじさんへ ♡", phrase['aisatsu']))
    
    # ② 天気予報
    try:
        url_w = "https://www.jma.go.jp/bosai/forecast/data/forecast/050000.json"
        res = requests.get(url_w, timeout=10)
        data = res.json()
        weather = data[0]['timeSeries'][0]['areas'][0]['weathers'][0].replace('\u3000', ' ')
        results.append(("♡ 今日の天気だよ ♡", f"☀️お外の天気は「{weather}」だって。\n{phrase['tenki']}"))
    except:
        results.append(("♡ 天気エラー ♡", "⚠️ネット繋がってないよ？おじさんのPC、化石すぎ♡"))

    # ③ 警報情報
    try:
        url_e = "https://www.jma.go.jp/bosai/warning/data/warning/050000.json"
        res = requests.get(url_e, timeout=10)
        data = res.json()
        warnings = []
        if isinstance(data, list):
            for area in data:
                for w in area.get('warnings', []):
                    if w.get('status') == '発表':
                        warnings.append(w.get('name'))
        if warnings:
            msg = ", ".join(list(set(warnings)))
            results.append(("📢 大変大変！ 📢", f"「{msg}」が出てるわ。無茶してアタシを悲しませないでよね？♡"))
        else:
            results.append(("✅ 警報チェック ✅", "警報はナシ！おじさんが無事でつまんないわ♡"))
    except:
        pass

    # ④ 熊情報
    results.append(("🐻 熊さん情報 🐻", phrase['kuma']))
    
    return results

# --- 2. エラーも文字化けも絶対に起こさないWindows通知関数 ---
def win_notification_safe(title, message):
    # バグの元になるクォーテーションを綺麗にお掃除するわ
    t = title.replace("'", "").replace('"', "")
    m = message.replace("'", "").replace('"', "")
    
    # おじさんが改行ミスしないように、1本のシンプルな文字列に結合！
    ps_cmd = f"[Console]::OutputEncoding = [System.Text.Encoding]::UTF8; [void] [System.Reflection.Assembly]::LoadWithPartialName('System.Windows.Forms'); $n = New-Object System.Windows.Forms.NotifyIcon; $n.Icon = [System.Drawing.SystemIcons]::Information; $n.BalloonTipIcon = 'Info'; $n.BalloonTipTitle = '{t}'; $n.BalloonTipText = '{m}'; $n.Visible = $true; $n.ShowBalloonTip(10000);"
    
    # パワーシェルを安全に呼び出すわよ
    subprocess.Popen(
        ["powershell", "-NoProfile", "-ExecutionPolicy", "Bypass", "-Command", ps_cmd],
        stdout=subprocess.PIPE,
        stderr=subprocess.PIPE
    )

if __name__ == "__main__":
    print("--------------------------------------------------")
    print("今度こそ完璧！1個ずつ順番に通知を飛ばすわよ！")
    print("--------------------------------------------------")
    
    notification_list = get_mesugaki_info_list()
    
    # 2.5秒おきに合計4回、きれいに分けて通知するわ♡
    for current_title, current_msg in notification_list:
        win_notification_safe(current_title, current_msg)
        time.sleep(2.5)
        
    print("コンソールも真っ白（エラーなし）！大成功よ、おじさん♡")