#ライブラリのインポート
import requests
from bs4 import BeautifulSoup
from retry import retry
import urllib
import time
import pandas as pd

#検索するURI (東京23区の検索結果外面を指定)　
# ページは&page=2のように末尾に追加していく構造
base_url = "https://suumo.jp/jj/chintai/ichiran/FR301FC001/?ar=030&bs=040&ta=13&sc=13101&sc=13102&sc=13103&sc=13104&sc=13105&sc=13113&sc=13106&sc=13107&sc=13108&sc=13118&sc=13121&sc=13122&sc=13123&sc=13109&sc=13110&sc=13111&sc=13112&sc=13114&sc=13115&sc=13120&sc=13116&sc=13117&sc=13119&cb=0.0&ct=9999999&et=9999999&cn=9999999&mb=0&mt=9999999&shkr1=03&shkr2=03&shkr3=03&shkr4=03&fw2="

#エラーしたときの処理

@retry(tries=3, delay=10, backoff=2)

#URLからHTMSデータを取得しBeautifulSoupで解析可能な形に変換する関数を定義する
def get_html(url):
    r = requests.get(url)
    soup = BeautifulSoup(r.content, "html.parser")
    return soup

#データ枠の準備
all_data = []

#スクレイピングするページ数を定義
max_page = 3


#各ページのデータを取得する繰り返し処理を行う
for page in range(1, max_page+1):

    #ページのurlを取得する
    url = base_url.format(page)

    #htmlを取得しBeautifulSoupで解析可能な形に関数で変換する
    soup = get_html(url)

    # サイトのHTMLを見ると物件情報はcassetteitemと書かれたdivに入っているためこれを全て抜き出す
    items = soup.findAll("div", {"class": "cassetteitem"})
    print("page", page, "items", len(items))


#抜き出した情報から各物件ごとの情報を抜き出す
    for item in items:
        buildings = item.findAll("div", {"class": "cassetteitem_detail-text"})
        #物件ごとの格納先を準備する
        base_data = {}

    #建物の基本情報を取得する
        for building in buildings:

            #建物の基本情報を抽出する
            base_data["物件名"] = item.find("div", {"class": "cassetteitem_content-title"}).getText().strip() if item.find("div", {"class": "cassetteitem_content-title"}) else "情報なし"
            base_data["カテゴリ"] = item.find("div", {"class": "cassetteitem_content-label"}).getText().strip() if item.find("div", {"class": "cassetteitem_content-label"}) else "情報なし"
            base_data["住所"] = item.find("div", {"class": "cassetteitem_detail-col1"}).getText().strip() if item.find("div", {"class": "cassetteitem_detail-col1"}) else "情報なし"
            base_data["築年数"] = item.find("li", {"class": "cassetteitem_detail-col3"}).findAll("div")[0].getText().strip() if item.find("li", {"class": "cassetteitem_detail-col3"}).findAll("div") else "情報なし"
            base_data["ビル高さ"] = item.find("li", {"class": "cassetteitem_detail-col3"}).findAll("div")[1].getText().strip() if item.find("li", {"class": "cassetteitem_detail-col3"}).findAll("div") and len(item.find("li", {"class": "cassetteitem_detail-col3"}).findAll("div")) > 1 else "情報なし"


            # 部屋情報を取得する
            tbodys = item.find("table", {"class": "cassetteitem_other"}).findAll("tbody")

            for tbody in tbodys:

                # base_dataを上書きしないようにコピーして開始
                data = base_data.copy()

                data["階数"] = tbody.findAll("td")[2].getText().strip()
                data["家賃"] = tbody.findAll("td")[3].findAll("li")[0].getText().strip()
                data["間取り"] = tbody.findAll("td")[5].findAll("li")[0].getText().strip()
                data["面積"] = tbody.findAll("td")[5].findAll("li")[1].getText().strip()

                #all_dataの枠に全てのデータを加える
                all_data.append(data)    

# データフレームに変換する
df = pd.DataFrame(all_data)

#google スプレッドシートの作成

import gspread
import os

# 現在の作業ディレクトリを取得
dir_path = os.getcwd()

# json ファイルへの相対パス
json_file_path = "物件検索アプリ/client_secret_1090803508352-b00frcmjp826a9voat7gvr55kt6d1c73.apps.googleusercontent.com.json"

# gspread の認証
gc = gspread.oauth(
    credentials_filename=os.path.join(dir_path, json_file_path),
    authorized_user_filename=os.path.join(dir_path, "authorized_user.json"),
)

wb = gc.create("test05") # スプレッドシート作成

print(wb.id) # キーを参照用に出力

wb = gc.open_by_key(wb.id) # test04のファイルを開く(キーから)
ws = wb.get_worksheet(0) # 最初のシートを開く(idは0始まりの整数)

# スプレッドシートに書き込むためのデータ
#dfから値を習得
values = [df.columns.values.tolist()] + df.values.tolist()

# スプレッドシートの1行目（A1セル）からデータを追加
ws.update("A1", values)