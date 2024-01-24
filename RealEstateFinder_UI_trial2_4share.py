#ライブラリのインポート
import streamlit as st

from PIL import Image
import datetime
import pandas as pd
import matplotlib.pyplot as plt

#緯度経度を特定するためのライブラリ
import geocoder

#MySQLにアクセスするためのライブラリ
import mysql.connector
from mysql.connector import Error
import sqlalchemy as sa

#地図表示のためのライブラリ

import folium

#メイン画面表示

st.title("東京23区物件検索")
st.write(f'このアプリでは重複物件をあらかじめ取り除いて表示します')
st.write(f'余計なお手間はとらせません')

#スライドバー選択画面

with st.sidebar:

    with st.form(key='profile_form'):

        #テキストボックスの作成
        name = st.text_input('名前')
        password = st.text_input('Password')
        #ボタン
        submit_btn = st.form_submit_button('決定')
        if submit_btn:
            st.text(f'ようこそ{name}さん！あなたにおすすめの物件をお探しします')

        st.title("検索条件を入力してください")
        #　複数選択
        district = st.multiselect(
                '23区から選択',
                ('足立区', '葛飾区', '荒川区', '江戸川区', '江東区', '台東区', '文京区', '台東区', '豊島区', '中央区', '中野区', '中野区', '杉並区', '渋谷区', '港区', '目黒区', '新宿区', '板橋区', '江戸川区', '江東区', '港区', '品川区', '世田谷区'))
        
        #　スライダー(上限から下限表示)
        lower_limit, upper_limit = st.slider('家賃（万円）',0.0,50.0,(10.0, 30.0))
        
        room_type = st.multiselect(
                '間取り',
                ('1R', '1LDK', '1DK', '1K', '2R', '2K', '2DK', '2LDK', '3R', '3K', '3DK', '3LDK', '4R', '4K', '4DK', '4LDK'))
    
        #ボタン
        submit_btn = st.form_submit_button('送信')
        cancel_btn = st.form_submit_button('cancel')
        if submit_btn:
            st.text(f'{name}さん！以下の条件で物件をご紹介します')

        #戻り値を表示させる
        st.write(f'【検索条件】')
        st.text(f'エリア：{",".join(district)}')
        st.text(f'部屋のタイプ：{",".join(room_type)}')
        st.text(f'家賃: {lower_limit} 万円から {upper_limit} 万円')

        #入力された値に従って処理を行う

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

#データを抽出する関数

def read_query(connection, query):
    cursor = connection.cursor()
    result = None
    try:
        cursor.execute(query)
        result = cursor.fetchall()
        return result
    except Error as err:
        print(f"Error: '{err}'")

# SQLクエリ
q1 = """
SELECT *
FROM realEstateTable7;
"""

# データベースへの接続
connection = create_server_connection("localhost", "root", "-password-", "RealEstateSearchResult_01")

# クエリを実行して結果を表示
results = read_query(connection, q1)

for result in results:
    print(result)

# 接続を閉じる
if connection:
    connection.close()

# カラム名を定義します
columns = [
    "id","物件名", "カテゴリ", "住所", "築年数", "ビル高さ", "階数", "家賃", "間取り", "面積",
    "URL", "都道府県", "市区町村", "その他住所", "座標検索用住所", "緯度", "経度"
]

# Pandasのデータフレームを作成します
df = pd.DataFrame(results, columns=columns)

# データフレームを表示します
print(df)

# Streamlitの入力に合わせてデータを抽出する
if submit_btn:
    # 初めて filtered_df を定義する場合
    filtered_df = df[df['家賃'].between(lower_limit, upper_limit) & (df['間取り'].isin(room_type))]

# 各区ごとにフィルタリング
    for district_name in district:
         filtered_df = filtered_df[filtered_df['住所'].str.contains(district_name)]

# 結果を表示
    print(filtered_df)

   # 抽出されたデータの緯度経度の取得
    if not filtered_df.empty:
        st.dataframe(filtered_df)

        # 抽出されたデータの緯度経度の取得
        if not filtered_df[['緯度', '経度']].isnull().any().any():

            # folium Mapを作成
            map = folium.Map(location=[filtered_df.iloc[0, filtered_df.columns.get_loc('緯度')],
                                        filtered_df.iloc[0, filtered_df.columns.get_loc('経度')]], zoom_start=10)

            # 全てのマーカーを地図に追加
            for i, r in filtered_df.iterrows():
                folium.Marker(location=[r['緯度'], r['経度']], popup=r['住所']).add_to(map)

           # folium MapをHTMLに変換
            html_map = map._repr_html_()

            # HTMLを表示
            st.components.v1.html(html_map, width=700, height=500)

        else:
            st.warning("物件の緯度経度情報が存在しません。")
    else:
        st.warning("条件に一致する物件はありません。条件を変更して再検索してください")