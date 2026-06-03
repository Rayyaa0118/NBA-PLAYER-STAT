import time
import sqlalchemy
import pandas as pd
import streamlit as st
import matplotlib.pyplot as plt

from nba_api.stats.static import players
from nba_api.stats.endpoints import playergamelog

# -------------------------------
# 資料庫連線
# -------------------------------
DATABASE_URL = st.secrets["DATABASE_URL"]
engine = sqlalchemy.create_engine(DATABASE_URL)

st.title("Victor Wembanyama — Performance Tracker")
st.write("自動更新的 NBA 球員數據追蹤系統，顯示 PPM 與 BLK 趨勢（2025-26 賽季）")

N = 10

# -------------------------------
# Extract
# -------------------------------
def get_wemby_data():

    nba_players = players.get_players()

    wemby = next(
        p for p in nba_players
        if p["full_name"] == "Victor Wembanyama"
    )

    gamelog = playergamelog.PlayerGameLog(
        player_id=wemby["id"],
        season="2025-26"
    )

    return gamelog.get_data_frames()[0]


# -------------------------------
# Transform
# -------------------------------
def clean_data(df):

    df = df[
        [
            "GAME_DATE",
            "MATCHUP",
            "WL",
            "MIN",
            "PTS",
            "REB",
            "AST",
            "BLK"
        ]
    ].copy()

    # 真正日期格式
    df["GAME_DATE"] = pd.to_datetime(df["GAME_DATE"]).dt.date

    df["MIN"] = df["MIN"].astype(float)

    df["PPM"] = (
        df["PTS"] / df["MIN"]
    ).round(2)

    return df


# -------------------------------
# Load
# -------------------------------
def update_db():

    df_raw = get_wemby_data()

    with engine.begin() as conn:

        try:

            df_existing = pd.read_sql(
                "SELECT GAME_DATE FROM wembanyama_stats",
                conn
            )

            existing_dates = set(
                pd.to_datetime(
                    df_existing["GAME_DATE"]
                ).dt.date
            )

            is_new = ~pd.to_datetime(
                df_raw["GAME_DATE"]
            ).dt.date.isin(existing_dates)

            new_records = df_raw[is_new]

        except Exception as e:

            st.write("第一次建立資料表或讀取失敗：")
            st.code(str(e))

            new_records = df_raw

        if not new_records.empty:

            df_clean = clean_data(new_records)

            st.write("準備寫入資料：")
            st.dataframe(df_clean.head())

            try:

                df_clean.to_sql(
                    "wembanyama_stats",
                    conn,
                    if_exists="append",
                    index=False
                )

                st.success(
                    f"成功新增 {len(df_clean)} 筆資料"
                )

            except Exception as e:

                st.error("寫入資料庫失敗！")
                st.code(str(e))

                st.write("欄位型別：")
                st.write(df_clean.dtypes)

                raise


# -------------------------------
# 讀資料
# -------------------------------
@st.cache_data(ttl=30)
def load_data():

    with engine.connect() as conn:

        return pd.read_sql(
            """
            SELECT *
            FROM wembanyama_stats
            ORDER BY GAME_DATE ASC
            """,
            conn
        )


# -------------------------------
# 畫圖
# -------------------------------
def visualize(df):

    fig, ax = plt.subplots(figsize=(10, 5))

    ax.plot(
        df["GAME_DATE"],
        df["PPM"],
        marker="o",
        color="purple",
        label="PPM"
    )

    ax.plot(
        df["GAME_DATE"],
        df["BLK"],
        marker="s",
        color="orange",
        label="BLK"
    )

    ax.set_title(
        "Wembanyama Performance Trend"
    )

    ax.set_xlabel("Game Date")
    ax.set_ylabel("Stats")

    ax.legend()

    plt.xticks(rotation=45)
    plt.tight_layout()

    return fig


# -------------------------------
# Main
# -------------------------------
try:

    update_db()

    data = load_data()

    if data.empty:

        st.warning("資料庫目前沒有資料")

    else:

        recent = data.tail(N)

        st.subheader(f"最近 {N} 場比賽")

        st.dataframe(recent)

        st.subheader("PPM 與 BLK 趨勢")

        if len(recent) < 3:
            st.info("資料較少，圖表僅供參考")

        st.pyplot(
            visualize(recent)
        )

except Exception as e:

    st.error("頁面發生錯誤")
    st.code(str(e))


# -------------------------------
# 每30秒更新
# -------------------------------
time.sleep(30)
st.rerun()