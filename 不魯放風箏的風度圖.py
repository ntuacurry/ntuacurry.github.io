import streamlit as st
import yfinance as yf
import pandas as pd
from plotly.subplots import make_subplots
import plotly.graph_objects as go
from datetime import date
from pandas.tseries.offsets import DateOffset
import re

# ---------------------------------------------------------
# 1. 顏色與風度定義
# ---------------------------------------------------------
WIND_COLORS = {
    "強風": "rgba(255, 0, 0, 0.5)",      # 紅色 (50% 透明度)
    "亂流": "rgba(0, 128, 0, 0.5)",    # 綠色 (50% 透明度)
    "陣風": "rgba(255, 192, 203, 0.5)",  # 粉紅色 (50% 透明度)
    "無風": "rgba(105, 105, 105, 0.5)"   # 深灰色 (50% 透明度)
}

# ---------------------------------------------------------
# 2. 數據獲取與處理
# ---------------------------------------------------------
st.set_page_config(page_title="不魯放風箏的風度圖", layout="wide")
st.title("🪁 不魯放風箏的風度圖")

@st.cache_data
def load_data(symbol):
    """下載股票資料並計算技術指標和風度狀態。"""
    stock = yf.Ticker(symbol)
    df = stock.history(interval="1d", start="2020-01-01", end=None, actions=False, auto_adjust=False, back_adjust=False)
    
    if df.empty:
        return df

    # 資料處理與指標計算
    df["Close"] = round(df["Close"], 2)
    df["Price"] = round((df["High"] + df["Low"] + 2 * df["Close"]) / 4, 2)
    df["EMA12"] = df["Price"].ewm(span=12).mean()
    df["EMA26"] = df["Price"].ewm(span=26).mean()
    df["DIF"] = df["EMA12"] - df["EMA26"]
    df["MACD"] = df["DIF"].ewm(span=9).mean()
    df["MACD Histogram"] = df["DIF"] - df["MACD"]
    df["20ma"] = df["Close"].rolling(window=20).mean()
    
    # 風度判斷邏輯
    df["Prev_MACD_H"] = df["MACD Histogram"].shift(1) 
    df["Wind"] = "未知"
    
    MACD_UP = (df["MACD Histogram"] > df["Prev_MACD_H"]) 
    MACD_DOWN = (df["MACD Histogram"] < df["Prev_MACD_H"]) 
    
    CLOSE_ABOVE_20MA = (df["Close"] >= df["20ma"])
    CLOSE_BELOW_20MA = (df["Close"] < df["20ma"])

    df.loc[CLOSE_ABOVE_20MA & MACD_UP, "Wind"] = "強風"
    df.loc[CLOSE_ABOVE_20MA & MACD_DOWN, "Wind"] = "亂流"
    df.loc[CLOSE_BELOW_20MA & MACD_UP, "Wind"] = "陣風"
    df.loc[CLOSE_BELOW_20MA & MACD_DOWN, "Wind"] = "無風"
    
    df["Wind_Color"] = df["Wind"].map(WIND_COLORS)

    return df.drop(columns=["Prev_MACD_H"]) 

# ---------------------------------------------------------
# 3. 側邊欄：使用者輸入參數
# ---------------------------------------------------------
st.sidebar.header("參數設定")

ticker_symbol = st.sidebar.text_input("股票代碼 (Yahoo Finance)", "^TWOII")

# **預設顯示近三個月的資料**
current_date = date.today()
three_months_ago = current_date - DateOffset(months=1) 

default_end_date = current_date
default_start_date = three_months_ago.date()

start_input = st.sidebar.date_input("開始日期", default_start_date)
end_input = st.sidebar.date_input("結束日期", default_end_date)

start_date_str = start_input.strftime("%Y-%m-%d")
end_date_str = end_input.strftime("%Y-%m-%d")

# **控制風度圖層開關**
show_wind_layer = st.sidebar.checkbox("顯示 K 線風度圖層", value=True)

# 載入資料
data_load_state = st.text('資料下載運算中...')
data = load_data(ticker_symbol)
data_load_state.text('') 

# ---------------------------------------------------------
# 4. 繪製 Plotly 圖表 (日期格式化與風度開關)
# ---------------------------------------------------------
if data.empty:
    st.error(f"找不到代碼 **{ticker_symbol}** 的資料，請確認輸入正確。")
else:
    # 篩選特定時間區間
    filtered_data = data.loc[start_date_str:end_date_str].copy()

    if filtered_data.empty:
        st.warning("選取的日期區間沒有資料，請調整日期。")
    else:
        # **將日期索引格式化為 yyyy.mm.dd 字串 (用於 X 軸顯示)**
        formatted_index = filtered_data.index.strftime('%Y.%m.%d')
        
        # --- 建立雙軸子圖 ---
        fig = make_subplots(
            rows=2, 
            cols=1, 
            shared_xaxes=True, 
            vertical_spacing=0.08, 
            row_heights=[0.7, 0.3]
        )

        # ------------------ 風度矩形 (Layer Shapes) ------------------
        wind_shapes = []
        if show_wind_layer:
            for idx, date_str in enumerate(formatted_index):
                row = filtered_data.iloc[idx]
                if row["Wind_Color"] and row["Wind"] != "未知":
                    fill_color = row["Wind_Color"]
                    wind_shapes.append(
                        dict(
                            type="rect",
                            # X 座標使用類別軸索引 (0, 1, 2, ...) 
                            xref="x", x0=idx - 0.5, x1=idx + 0.5, 
                            yref="y", y0=filtered_data['Low'].min() * 0.99, y1=filtered_data['High'].max() * 1.01,
                            fillcolor=fill_color,
                            line_width=0,
                            layer="below" # 讓矩形位於 K 線圖層下方
                        )
                    )

        # 1. 主圖：K線圖與 20MA
        fig.add_trace(go.Candlestick(
            # X 軸使用格式化的日期字串
            x=formatted_index,
            open=filtered_data['Open'], high=filtered_data['High'], 
            low=filtered_data['Low'], close=filtered_data['Close'], 
            name='K線', increasing_line_color='red', decreasing_line_color='green'
        ), row=1, col=1)

        fig.add_trace(go.Scatter(
            x=formatted_index, y=filtered_data['20ma'],
            line=dict(color='orange', width=1.5), name='20MA'
        ), row=1, col=1)

        # 2. 副圖：MACD Histogram
        colors = ['red' if val >= 0 else 'green' for val in filtered_data['MACD Histogram']]
        fig.add_trace(go.Bar(
            x=formatted_index, y=filtered_data['MACD Histogram'],
            marker_color=colors, name='MACD 柱狀圖'
        ), row=2, col=1)

        # 3. 副圖：DIF 線 (快線)
        fig.add_trace(go.Scatter(
            x=formatted_index, y=filtered_data['DIF'],
            line=dict(color='blue', width=1.5), name='DIF', connectgaps=False
        ), row=2, col=1)
        
        # 4. 副圖：MACD 線 (慢線)
        fig.add_trace(go.Scatter(
            x=formatted_index, y=filtered_data['MACD'],
            line=dict(color='orange', width=1.5), name='MACD', connectgaps=False
        ), row=2, col=1)

        # --- 版面設定 (Layout Configuration) ---
        fig.update_layout(
            title=f"{ticker_symbol}的風度圖",
            xaxis_rangeslider_visible=False,
            height=800,
            hovermode="x unified",
            template="plotly_white",
            shapes=wind_shapes # 根據開關決定是否顯示
        )
        
        # **X 軸格式化為 yyyy.mm.dd** (使用 category 類型)
        fig.update_xaxes(type='category', showgrid=True, showticklabels=False, row=1, col=1)
        fig.update_xaxes(type='category', showticklabels=True, row=2, col=1)
        fig.update_yaxes(title='股價 (Price)', row=1, col=1)
        fig.update_yaxes(title='MACD 指標', row=2, col=1)
        fig.update_traces(showlegend=True)

        # --- 在 Streamlit 顯示圖表 (修正: use_container_width -> width='stretch') ---
        st.plotly_chart(fig, width='stretch')
        
        # ------------------ 風度圖例顯示 (與開關同步) ------------------
        # **最終修正：使用 st.columns 避免 HTML 解析錯誤**
        if show_wind_layer:
            st.markdown("---")
            st.subheader("風度與顏色對應")
            
            # 使用列表確保順序，並定義用於圖例的不透明顏色
            WIND_LEGEND_HEX = {
                "強風": "#FF0000",      
                "亂流": "#008000",    
                "陣風": "#FFC0CB",  
                "無風": "#696969"   
            }
            
            # 使用 Streamlit columns 來並排顯示圖例
            cols = st.columns(len(WIND_LEGEND_HEX))
            
            i = 0
            for wind, color_hex in WIND_LEGEND_HEX.items():
                
                # 每個色塊的 HTML 標籤
                color_block = f"<span style='background-color: {color_hex}; width: 20px; height: 20px; border: 1px solid #333; display: inline-block;'></span>"
                
                # 在每個欄位中，使用 Markdown 語法和 HTML 標籤渲染色塊和名稱
                cols[i].markdown(
                    f"{color_block} **{wind}**", 
                    unsafe_allow_html=True
                )
                i += 1
            
            st.markdown("---")

        # ------------------ 詳細數據表格 (格式化、上色、置中、倒序) ------------------
        with st.expander("查看詳細數據與風度狀態"):
            
            # 1. 複製、日期格式化及欄位名稱調整
            # **預設由新至舊排列 (Descending by Date)**
            display_df = filtered_data.sort_index(ascending=False).copy()
            
            display_df.reset_index(inplace=True)
            
            # **將日期格式化為 yyyy.mm.dd**
            display_df['Date'] = display_df['Date'].dt.strftime('%Y.%m.%d')
            
            new_names = {
                'Date': '日期', 'Wind': '風度', 'Open': '開', 'High': '高', 
                'Low': '低', 'Close': '收', 'MACD Histogram': 'MACD柱'
            }
            display_df.rename(columns=new_names, inplace=True)
            
            # 2. 調整欄位順序
            cols = ['日期', '風度', '開', '高', '低', '收', '20ma', 'DIF', 'MACD', 'MACD柱']
            display_df = display_df[cols]

            # 3. 定義風度樣式函數
            def color_wind_table(val):
                """根據風度值返回背景顏色 CSS 樣式"""
                color = WIND_COLORS.get(val, 'transparent')
                return f'background-color: {color}; color: black;'

            # 4. 應用格式化和樣式
            styled_df = display_df.style.format({
                # 數值格式化到小數點下第二位
                '開': "{:.2f}",
                '高': "{:.2f}",
                '低': "{:.2f}",
                '收': "{:.2f}",
                '20ma': "{:.2f}",
                'DIF': "{:.2f}",
                'MACD': "{:.2f}",
                'MACD柱': "{:.2f}",
            })
            
            # 應用風度欄位的背景顏色樣式 (修正: applymap -> map)
            styled_df = styled_df.map(color_wind_table, subset=['風度'])
            
            # 5. 垂直置中和水平置中 CSS 樣式
            cell_center_style = [
                # 設置表頭 (th) 和單元格 (td) 內容置中
                {'selector': 'th', 'props': [('text-align', 'center'), ('vertical-align', 'middle')]},
                {'selector': 'td', 'props': [('text-align', 'center'), ('vertical-align', 'middle')]},
            ]
            styled_df = styled_df.set_table_styles(cell_center_style, overwrite=False)

            # 在 Streamlit 中顯示格式化後的表格 (修正: use_container_width -> width='stretch')
            st.dataframe(styled_df, hide_index=True, width='stretch')
