#ライブラリのインポート
import requests
from bs4 import BeautifulSoup
from retry import retry
import urllib
import time
import pandas as pd
import re
import geocoder

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
max_page = 10


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
            base_data["住所"] = item.find("li", {"class": "cassetteitem_detail-col1"}).getText().strip() if item.find("li", {"class": "cassetteitem_detail-col1"}) else "情報なし"
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

                
                data["URL"] = "https://suumo.jp" + tbody.findAll("td")[8].find("a").get("href")

                #all_dataの枠に全てのデータを加える
                all_data.append(data)    

# データフレームに変換する
df = pd.DataFrame(all_data)

print(df)

len(df)

#データから数字だけを抽出する関数を定義する

def get_number(value):
    n = re.findall(r'\d+', value)
    
    if len(n) != 0:
        return float(n[0])
    else:
        return 0

df["築年数"] = df["築年数"].apply(get_number)
df["ビル高さ"] = df["ビル高さ"].apply(get_number)
df["階数"] = df["階数"].apply(get_number)
df["家賃"] = df["家賃"].apply(get_number)
df["面積"] = df["面積"].apply(get_number)
print(df)

# 住所をA都、B区、Cに分割する関数を定義する

def split_address(address):

    #正規表現にマッチする部分を抽出する

    result = re.search('(...??[都道府県])(.+?[市区町村])(.+)', address)
    if result:
        a_pref, b_ward, c_others = result.groups()
        return a_pref, b_ward, c_others
    else:
        return '情報なし', '情報なし', '情報なし'

# 住所を都道府県都、市区町村、その他住所に分割して新しい列に代入
    
split_result = df['住所'].apply(split_address).apply(pd.Series)

# 分割結果の列名を調整

split_result.columns = ["都道府県", "市区町村", "その他住所"]

# 元のDataFrameに新しい列を追加

df = pd.concat([df, split_result], axis=1)

print(df)


# "物件名", "カテゴリ", "住所", "築年数", "ビル高さ","階数", "家賃","間取り","面積"をキーに全てが一致したデータを削除

df.drop_duplicates(subset=["物件名", "カテゴリ", "住所", "築年数", "ビル高さ","階数", "家賃","間取り","面積"], inplace=True)


# 住所に「丁目」を追加して新しい列を作成
df['座標検索用住所'] = df['住所'] + '丁目'

# 座標検索用住所から緯度と経度を特定

for i, r in df.iterrows():
    location = r['座標検索用住所']
    ret = geocoder.osm(location, timeout=5.0)
    
    if ret.ok:  # geocoderが成功した場合
        df.loc[i, '緯度'] = ret.latlng[0]
        df.loc[i, '経度'] = ret.latlng[1]
        #print(i)
        #print(ret.latlng)
        #print(ret.address)
    else:
        print(f"Geocoding failed for address: {location}")

len(df)
print(df.columns)

# "URL"をキーに重複データを削除

df.drop_duplicates(subset=["URL"], inplace=True)

len(df)
print(df)


#MySQLにデータを格納する準備

import mysql.connector
from mysql.connector import Error
import pandas as pd

#サーバーへの接続を行う関数

def create_server_connection(host_name, user_name, user_password, database_name=None):
    connection = None
    try:
        connection = mysql.connector.connect(
            host=host_name,
            user=user_name,
            passwd=user_password,
            database=database_name
        )
        if connection.is_connected():
            print("MySQL Database connection successful")

    except Error as err:
        print(f"Error: '{err}'")

    return connection

#サーバーへの接続

connection = create_server_connection("localhost", "root", "-mypassword")

#データベースを作成する関数

def create_database(connection, query):
    cursor = connection.cursor()
    try:
        cursor.execute(query)
        print("Database created successfully")
    except Error as err:
        print(f"Error: '{err}'")

#データベースの作成

create_database_query = "CREATE DATABASE RealEstateSearchResult_01;"
create_database(connection, create_database_query)

# データベースの選択
connection.database = "RealEstateSearchResult_01"

# テーブルの作成を行う関数

def create_table(connection, table_name, columns):
    cursor = connection.cursor()
    try:
        create_table_query = f"CREATE TABLE {table_name} ({columns});"
        cursor.execute(create_table_query)
        print(f"Table {table_name} created successfully")
    except Error as err:
        print(f"Error: '{err}'")

# テーブルの作成
table_name = "RealEstateTable7"
columns = "id INT AUTO_INCREMENT PRIMARY KEY, 物件名 VARCHAR(255), カテゴリ VARCHAR(255), 住所 VARCHAR(255), 築年数 FLOAT, ビル高さ FLOAT, 階数 FLOAT, 家賃 FLOAT, 間取り VARCHAR(255), 面積 FLOAT, URL VARCHAR(255), 都道府県 VARCHAR(255), 市区町村 VARCHAR(255), その他住所 VARCHAR(255), 座標検索用住所 VARCHAR(255), 緯度 FLOAT, 経度 FLOAT"
create_table(connection, table_name, columns)

# データの挿入

def insert_data(connection, table_name, data):
    cursor = connection.cursor()
    try:
        for index, row in data.iterrows():
            insert_query = f"INSERT INTO {table_name} (物件名, カテゴリ, 住所, 築年数, ビル高さ,階数, 家賃,間取り,面積,URL,都道府県,市区町村 ,その他住所,座標検索用住所, 緯度, 経度) " \
                           f"VALUES (%s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s,%s, %s, %s);"
            cursor.execute(insert_query, (row['物件名'], row['カテゴリ'], row['住所'], row['築年数'], row['ビル高さ'],
                                          row['階数'], row['家賃'], row['間取り'], row['面積'], row['URL'], row['都道府県'], row['市区町村'], row['その他住所'], row['座標検索用住所'], row['緯度'], row['経度']))
        connection.commit()
        print("Data inserted successfully")
    except Error as err:
        print(f"Error: '{err}'")

        # データセットの挿入
insert_data(connection, "RealEstateTable7", df)

# 接続を閉じる
connection.close()