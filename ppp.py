from nba_api.stats.static import players
import sqlite3
import time
import pandas as pd
from nba_api.stats.endpoints import playergamelog



def get_wemby_data():
    nba_players = players.get_players()
    wemby =  [p for p in nba_players if p['full_name'] == 'Victor Wembanyama']
    wemby_id = wemby[0]['id']                                                          # 641705   this is the player id for wemby
    gamelog = playergamelog.PlayerGameLog(player_id=wemby_id, season='2025-26')         #抓取2025-26賽季的比賽數據
    return gamelog.get_data_frames()                                                   #藉由get_data_frames()方法將前面抓取到的api資料轉換成DataFrame格式，方便後續分析和處理  

def transfer_load():
    df_new_raw = get_wemby_data()[0]                                                   # get_wemby_data()回傳的是一個list，裡面有一個DataFrame，所以用[0]取出來
    conn = sqlite3.connect('wemby_data.db')                 #嘗試「開啟」一個叫 wemby_data.db 的 SQLite 資料庫檔案 如果不存在，自動幫建立一個新的檔案called wemby_data.db
    try:
        df_existing = pd.read_sql("SELECT GAME_DATE FROM wembanyama_stats", conn)             # 資料表存在 → 讀取舊日期來比對
        new_records = df_new_raw[~pd.to_datetime(df_new_raw['GAME_DATE']).dt.strftime('%Y-%m-%d').isin(pd.to_datetime(df_existing['GAME_DATE']).dt.strftime('%Y-%m-%d'))]     
    except:                                                                                   
        new_records = df_new_raw
    
    if not new_records.empty:    
                                                                            
        print(f"寫入新資料")
        df_clean = new_records[['GAME_DATE', 'MATCHUP', 'WL', 'MIN', 'PTS', 'REB', 'AST', 'BLK']].copy()
        df_clean['GAME_DATE'] = pd.to_datetime(df_clean['GAME_DATE']).dt.strftime('%Y-%m-%d')   
        df_clean['MIN'] = df_clean['MIN'].astype(float)                                                            #STR 無法做運算 換成float才能做運算
        df_clean['PPM'] = round(df_clean['PTS'] / df_clean['MIN'] , 2)                                             #PPM = Points Per Minute 每分鐘得分  創建新的一欄ppm，計算方式是PTS除以MIN                                       #把 GAME_DATE 這一欄的資料轉換成日期格式，方便後續的日期比對和排序
        df_clean.to_sql('wembanyama_stats', conn, if_exists='append', index=False)             #把清洗好的資料寫入資料庫，資料表名稱叫 wembanyama_stats，如果資料表已經存在，就用 append 模式（新增資料到現有表格），不寫入索引欄位  
         
        print("資料寫入完成")

        df_final = pd.read_sql("SELECT DISTINCT * FROM wembanyama_stats", conn)                #從資料庫讀取最新的完整資料表，並存成一個 DataFrame 叫 df_final
        df_final.to_csv('wemby_final_report.csv', index=False)                        #把 df_final 這個 DataFrame 寫成一個 CSV 檔案，檔名叫 wemby_final_report.csv
        print("匯出最新 CSV")  

    else:                                                                       #如果 new_records 是空的(即在這段自己設定的時間中沒有比賽數據)，代表沒有新資料需要寫入，
        print("沒有新資料需要寫入,斑馬強 ,下次更新資料五秒後 :>>>>")
    
    conn.close()

def timer():
    if 1 == 1:
        while True:
            transfer_load()
            time.sleep(5)  # 每60秒執行一次    

timer()



