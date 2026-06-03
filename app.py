#app.py

import streamlit as st
import pandas as pd
import sqlite3
import matplotlib.pyplot as plt
from matplotlib.font_manager import FontProperties

st.title(" goat🐐 Victor Wembanyama’s  Performance Tracker")
st.write("This is an automatically updated NBA player performance tracking system.")



def load_data():                                               #從 SQLite 資料庫讀取資料ppp.py的資料，並返回
    conn = sqlite3.connect('wemby_data.db')
    df = pd.read_sql("SELECT * FROM wembanyama_stats ORDER BY GAME_DATE DESC", conn)
    conn.close()
    return df

def visualize(df):                                         #設一個參數df，這個參數在之後要接收 load_data() 函數讀取到的 DataFrame 資料，然後在這個函數裡面進行資料視覺化的處理
    fig, ax = plt.subplots(figsize=(10, 5))
    ax.plot(df['GAME_DATE'], df['PTS'], marker='o', color='purple', label='Score (PTS)')
    ax.plot(df['GAME_DATE'], df['BLK'], marker='s', color='orange', label='Blocking (BLK)')
    ax.set_title("Wembanyama Performance Trend (2024-25 Season)")
    ax.set_xlabel("Game Date")
    ax.set_ylabel("Stats")
    ax.legend()
    plt.xticks(rotation=45)
    plt.tight_layout()

    return fig

try:
    data = load_data()
    
    st.subheader("Latest match data review")
    st.dataframe(data.tail(5)) # 顯示最後五場
    
    # 展示視覺化圖表
    st.subheader("Scoring and Blocking Trend Chart")
    fig = visualize(data)
    st.pyplot(fig) # 在 Streamlit 網頁顯示 Matplotlib 圖表

except Exception as e:
    st.error(f"cooked , you got an error")



