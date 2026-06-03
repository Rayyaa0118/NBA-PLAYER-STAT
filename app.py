

import streamlit as st
import pandas as pd
import sqlite3
import matplotlib.pyplot as plt
from matplotlib.font_manager import FontProperties

st.title("  Victor Wembanyama’s  Performance  In the Last Five Games")
st.write("This is an automatically updated NBA player(Victor Wembanyama’s) performance tracking system , which shows the data of PPM and BLK" )



def load_data():                                               #從 SQLite 資料庫讀取資料ppp.py的資料，並返回
    conn = sqlite3.connect('wemby_data.db')
    df = pd.read_sql("SELECT * FROM wembanyama_stats ORDER BY GAME_DATE DESC", conn)
    conn.close()
    return df

def visualize(df):                                         #設一個參數df，這個參數在之後要接收 load_data() 函數讀取到的 DataFrame 資料，然後在這個函數裡面進行資料視覺化的處理
    fig, ax = plt.subplots(figsize=(10, 5))
    ax.plot(df['GAME_DATE'], df['PPM'], marker='o', color='purple', label='Points Per Minute (PPM)')
    ax.plot(df['GAME_DATE'], df['BLK'], marker='s', color='orange', label='Blocking (BLK)')
    ax.set_title("Wembanyama Performance Trend (2025-26 Season)")
    ax.set_xlabel("Game Date")
    ax.set_ylabel("Stats")
    ax.legend()
    plt.xticks(rotation=45)
    plt.tight_layout()

    return fig

try:
    data = load_data()
    
    if not data.empty:
        st.subheader("Latest match data review")
        st.dataframe(data.head(5)) 
        
        st.subheader("PPM and BLK Trend Chart")
        fig = visualize(data.head(10))  
        st.pyplot(fig) 
    else:

        st.warning("資料庫目前是空的，請確認 ppp.py 是否已成功執行並產生 wemby_data.db！")

except Exception as e:
    st.error(f"目前網頁發生錯誤: {e}")


