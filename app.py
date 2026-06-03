import time
import sqlalchemy
import pandas as pd
import streamlit as st
import matplotlib.pyplot as plt
from nba_api.stats.static import players
from nba_api.stats.endpoints import playergamelog

# ── 1. 初始化 Supabase (PostgreSQL) 連線 ───────────────────────────
# 從 Streamlit Secrets 讀取連線字串
DATABASE_URL = st.secrets["DATABASE_URL"]
engine = sqlalchemy.create_engine(DATABASE_URL)

st.title(" Victor Wembanyama — Performance Tracker")
st.write("自動更新的 NBA 球員數據追蹤系統，顯示 PPM 與 BLK 趨勢（2025-26 賽季）")
N = 10  # 顯示最近幾場比賽

# ── 2. 抓取原始資料 (Extract) ──────────────────────────────────────
def get_wemby_data() -> pd.DataFrame:
    nba_players = players.get_players()
    wemby = next(p for p in nba_players if p['full_name'] == 'Victor Wembanyama')
    gamelog = playergamelog.PlayerGameLog(player_id=wemby['id'], season='2025-26')
    return gamelog.get_data_frames()[0]

# ── 3. 清洗資料 (Transform) ──────────────────────────────────────────
def clean_data(df: pd.DataFrame) -> pd.DataFrame:
    df = df[['GAME_DATE', 'MATCHUP', 'WL', 'MIN', 'PTS', 'REB', 'AST', 'BLK']].copy()
    df['GAME_DATE'] = pd.to_datetime(df['GAME_DATE']).dt.strftime('%Y-%m-%d')
    df['MIN'] = df['MIN'].astype(float)
    df['PPM'] = (df['PTS'] / df['MIN']).round(2)
    return df

# ── 4. 寫入資料庫 (Load - 只寫入新資料) ───────────────────────────
def update_db():
    df_raw = get_wemby_data()
    with engine.connect() as conn:
        try:
            # 檢查資料庫現有的日期，避免重複寫入
            df_existing = pd.read_sql("SELECT GAME_DATE FROM wembanyama_stats", conn)
            existing_dates = set(pd.to_datetime(df_existing['GAME_DATE']).dt.strftime('%Y-%m-%d'))
            is_new = ~pd.to_datetime(df_raw['GAME_DATE']).dt.strftime('%Y-%m-%d').isin(existing_dates)
            new_records = df_raw[is_new]
        except Exception:
            # 如果資料表剛建立還沒有資料，會走這裏（視為首次寫入）
            new_records = df_raw

        if not new_records.empty:
            df_clean = clean_data(new_records)
            # 使用 SQLAlchemy 將資料寫入 Supabase
            df_clean.to_sql('wembanyama_stats', conn, if_exists='append', index=False)

# ── 5. 從資料庫讀取資料 ──────────────────────────────────
@st.cache_data(ttl=30)  # 每 30 秒自動重新整理快取
def load_data() -> pd.DataFrame:
    with engine.connect() as conn:
        return pd.read_sql("SELECT * FROM wembanyama_stats ORDER BY GAME_DATE ASC", conn)

# ── 6. 畫圖 (使用半形括號防止字體報錯) ──────────────────────────────────────
def visualize(df: pd.DataFrame):
    fig, ax = plt.subplots(figsize=(10, 5))
    ax.plot(df['GAME_DATE'], df['PPM'], marker='o', color='purple', label='PPM (Points Per Minute)')
    ax.plot(df['GAME_DATE'], df['BLK'], marker='s', color='orange', label='BLK (Blocks)')
    ax.set_title("Wembanyama Performance Trend (2025-26 Season)")
    ax.set_xlabel("Game Date")
    ax.set_ylabel("Stats")
    ax.legend()
    plt.xticks(rotation=45)
    plt.tight_layout()
    return fig

# ── 主程式邏輯 ───────────────────────────────────────────────
try:
    update_db()  # 每次頁面整理時，自動去 NBA API 抓資料更新到雲端資料庫
    data = load_data()
    
    if data.empty:
        st.warning("雲端資料庫目前是空的，請稍後再試！")
    else:
        recent = data.tail(N)  # 取最新 N 筆顯示
        
        st.subheader(f"最近 {N} 場比賽數據")
        st.dataframe(recent)
        
        st.subheader("PPM 與 BLK 趨勢圖")
        if len(recent) < 3:
            st.info("資料筆數不足，圖表僅供參考")
        st.pyplot(visualize(recent))

except Exception as e:
    st.error(f"頁面發生錯誤：{e}")

# 每 30 秒自動觸發頁面重新整理
time.sleep(30)
st.rerun()