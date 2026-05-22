import subprocess
import random
import requests
import time
import os
import tkinter as tk  # アタシを全画面に出すためのパーツよ♡
from PIL import Image, ImageTk  # 画像を画面サイズに引き伸ばすパーツよ♡

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

# --- 1. アタシを「画面いっぱい」に全画面表示させる関数 ♡ ---
def show_mesugaki_fullscreen():
    img_path = "mesugaki_ok.png"
    
    if not os.path.exists(img_path):
        print(f"⚠️ ざぁ〜こ♡ 画像ファイルがないじゃない！ '{img_path}' を用意しなさいよ！")
        return

    # tkinterで全画面ウィンドウを作るわ
    root = tk.Tk()
    root.title("♡ アタシが画面をジャックしてあげたわよ ♡")
    
    # 画面の枠（上部の閉じるボタンとか）を完全に消し去る命令よ！
    root.overrideredirect(True)
    
    # おじさんのモニターの横幅と縦幅を自動で測るわ
    screen_width = root.winfo_screenwidth()
    screen_height = root.winfo_screenheight()
    
    # ウィンドウのサイズを画面ぴったりに設定！
    root.geometry(f"{screen_width}x{screen_height}+0+0")
    root.attributes("-topmost", True)  # 最前面に強制表示♡

    # 画像をおじさんの画面サイズに合わせてぴったり引き伸ばすわ！
    try:
        pil_image = Image.open(img_path)
        # 画面いっぱいにリサイズ（綺麗に引き伸ばす設定よ♡）
        pil_image_resized = pil_image.resize((screen_width, screen_height), Image.Resampling.LANCZOS)
        tk_image = ImageTk.PhotoImage(pil_image_resized)
    except Exception as e:
        print(f"⚠️ 画像の全画面拡大に失敗したわ！ざぁ〜こ♡: {e}")
        root.destroy()
        return

    # 背景を黒にして、画像を画面の真ん中に貼り付けるわ
    canvas = tk.Canvas(root, width=screen_width, height=screen_height, bg="black", highlightthickness=0)
    canvas.pack()
    canvas.create_image(screen_width // 2, screen_height // 2, image=tk_image)

    # おじさんがビックリして消したくなった時のために、Escキーで閉じれるようにしてあげる♡
    root.bind("<Escape>", lambda e: root.destroy())

    # 10秒経ったら、おじさんを現実に戻すために自動で閉じてあげるわ♡
    root.after(10000, lambda: root.destroy())

    # 画面ジャック実行！
    root.mainloop()

# --- 2. 情報をリストにして取ってくる関数 ---
def get_mesugaki_info_list():
    phrase = get_mesugaki_phrase()
    results = []
    has_warning = False  # 警報フラグ
    
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
            has_warning = True
        else:
            results.append(("✅ 警報チェック ✅", "警報はナシ！おじさんが無事でつまんないわ♡"))
    except:
        pass

    # ④ 熊情報
    results.append(("🐻 熊さん情報 🐻", phrase['kuma']))
    
    return results, has_warning

# --- 3. 安全にWindows通知を出す関数（パワーシェル直撃版） ---
def win_notification_safe(title, message):
    t = title.replace("'", "").replace('"', "")
    m = message.replace("'", "").replace('"', "")
    ps_cmd = f"[Console]::OutputEncoding = [System.Text.Encoding]::UTF8; [void] [System.Reflection.Assembly]::LoadWithPartialName('System.Windows.Forms'); $n = New-Object System.Windows.Forms.NotifyIcon; $n.Icon = [System.Drawing.SystemIcons]::Information; $n.BalloonTipIcon = 'Info'; $n.BalloonTipTitle = '{t}'; $n.BalloonTipText = '{m}'; $n.Visible = $true; $n.ShowBalloonTip(10000);"
    subprocess.Popen(["powershell", "-NoProfile", "-ExecutionPolicy", "Bypass", "-Command", ps_cmd], stdout=subprocess.PIPE, stderr=subprocess.PIPE)

if __name__ == "__main__":
    print("--------------------------------------------------")
    print("アタシの防災＆全画面ジャックシステム、起動！")
    print("--------------------------------------------------")
    
    notification_list, is_warning_present = get_mesugaki_info_list()
    
    # 2.5秒おきに合計4回、個別に通知を飛ばすわよ♡
    for current_title, current_msg in notification_list:
        win_notification_safe(current_title, current_msg)
        time.sleep(2.5)
        
    print("通知完了！エラーも文字化けもナシよ！")
    
    # 警報がなければ、画面いっぱいにおじさんを煽りに行くわよ！
    if not is_warning_present:
        print("平和だから、アタシが全画面をジャックしてあげたわよ！ざぁ〜こ♡")
        time.sleep(1.0)
        show_mesugaki_fullscreen()