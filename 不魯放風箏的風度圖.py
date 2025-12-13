import streamlit as st
import yfinance as yf
import pandas as pd
from plotly.subplots import make_subplots
import plotly.graph_objects as go
from datetime import date, datetime
from pandas.tseries.offsets import DateOffset
import re

# ---------------------------------------------------------
# 1. 顏色與風度定義
# ---------------------------------------------------------
WIND_COLORS = {
    "強風": "rgba(255, 0, 0, 0.5)",      # 紅色
    "亂流": "rgba(0, 128, 0, 0.5)",    # 綠色
    "陣風": "rgba(255, 192, 203, 0.5)",  # 粉紅色
    "無風": "rgba(105, 105, 105, 0.5)"   # 深灰色
}

# ---------------------------------------------------------
# 股票資料讀取與轉換
# ---------------------------------------------------------
@st.cache_data
def load_stock_map(file_path="股票資料.csv"):
    try:
        df = pd.read_csv(file_path, encoding='utf-8', engine='python')
        df.columns = df.columns.str.replace(r'\s+', '', regex=True)
        
        stock_map = {} 
        stock_names = {} 

        for index, row in df.iterrows():
            code = str(row['公司代號']) 
            name = row['公司名稱'].strip()
            market = str(row['市場別']).strip() if not pd.isna(row['市場別']) else ""
            
            stock_map[code] = (name, market)
            if name not in stock_names:
                stock_names[name] = code
                
        return stock_map, stock_names
    except FileNotFoundError:
        return {}, {}
    except Exception as e:
        st.error(f"讀取或處理股票資料時發生錯誤: {e}")
        return {}, {}

STOCK_MAP, STOCK_NAMES = load_stock_map()
if not STOCK_MAP:
    ALL_SEARCH_OPTIONS = ["^TWOII", "2330", "0050"]
else:
    ALL_SEARCH_OPTIONS = list(STOCK_MAP.keys()) + list(STOCK_NAMES.keys())


def process_ticker_input(input_value, stock_map, stock_names):
    input_value = input_value.strip()
    code = input_value
    name = input_value
    yfinance_ticker = input_value
    
    if input_value in stock_names:
        code = stock_names[input_value] 
        if code in stock_map:
            name, market = stock_map[code]
            if not market: yfinance_ticker = code
            elif market == '上市': yfinance_ticker = f"{code}.TW"
            elif market == '上櫃': yfinance_ticker = f"{code}.TWO"
            else: yfinance_ticker = code
            return yfinance_ticker, name
            
    elif input_value in stock_map:
        code = input_value
        name, market = stock_map[code]
        if not market: yfinance_ticker = code
        elif market == '上市': yfinance_ticker = f"{code}.TW"
        elif market == '上櫃': yfinance_ticker = f"{code}.TWO"
        else: yfinance_ticker = code
        return yfinance_ticker, name
        
    if re.match(r'^\d+$', input_value):
        return f"{input_value}.TW", input_value
        
    return input_value, input_value 

# ---------------------------------------------------------
# 2. 數據獲取與處理
# ---------------------------------------------------------
st.set_page_config(page_title="不魯放風箏的風度圖", layout="wide")
st.title("🪁 不魯放風箏的風度圖")

@st.cache_data
def calculate_indicators(df):
    """計算技術指標、風度狀態、多空循環及交界。嚴格執行 20MA 分界邏輯。"""
    if df.empty:
        return df

    # 資料處理與指標計算
    df["Close"] = round(df["Close"], 2)
    df['Pct_Change'] = (df['Close'] - df['Close'].shift(1)) / df['Close'].shift(1)
    
    def get_pct_color(pct):
        if pd.isna(pct): return 'black'
        elif pct > 0: return 'red'
        elif pct < 0: return 'green'
        else: return 'black'
            
    def format_pct_display(pct):
        if pd.isna(pct): return '-' 
        return f'{pct:+.2%}'

    df['Pct_Color'] = df['Pct_Change'].apply(get_pct_color)
    df['Pct_Change_Display'] = df['Pct_Change'].apply(format_pct_display)
    
    # 技術指標計算
    df["Price"] = round((df["High"] + df["Low"] + 2 * df["Close"]) / 4, 2)
    df["EMA12"] = df["Price"].ewm(span=12).mean()
    df["EMA26"] = df["Price"].ewm(span=26).mean()
    df["DIF"] = df["EMA12"] - df["EMA26"]
    df["MACD"] = df["DIF"].ewm(span=9).mean()
    df["MACD Histogram"] = df["DIF"] - df["MACD"]
    df["20ma"] = df["Close"].rolling(window=20).mean()
    
    df["Prev_MACD_H"] = df["MACD Histogram"].shift(1) 
    
    # --- 風度判斷邏輯 ---
    df["Wind"] = "未知"
    
    MACD_UP = (df["MACD Histogram"] > df["Prev_MACD_H"]) 
    MACD_DOWN = (df["MACD Histogram"] < df["Prev_MACD_H"]) 
    
    # 這裡的邏輯嚴格定義了每個交易日的狀態
    CLOSE_ABOVE_20MA = (df["Close"] >= df["20ma"])
    CLOSE_BELOW_20MA = (df["Close"] < df["20ma"])

    df.loc[CLOSE_ABOVE_20MA & MACD_UP, "Wind"] = "強風"
    df.loc[CLOSE_ABOVE_20MA & MACD_DOWN, "Wind"] = "亂流"
    df.loc[CLOSE_BELOW_20MA & MACD_UP, "Wind"] = "陣風"
    df.loc[CLOSE_BELOW_20MA & MACD_DOWN, "Wind"] = "無風"
    
    df["Wind_Color"] = df["Wind"].map(WIND_COLORS)

    # ==========================================
    # 邏輯一：強風-亂流循環 (多頭回檔轉強) - 紅色
    # 重要觀念：區間僅限於 Close > 20MA，一旦跌破必須重新判斷
    # ==========================================
    df['Cycle_Active'] = False
    
    df['is_above_20ma'] = CLOSE_ABOVE_20MA
    # 使用 cumsum 建立群組 ID，這確保了每次股價跌破 20MA 後，群組 ID 會改變，
    # 使得下一次站上 20MA 時會被視為一個全新的區間 (重新判斷)。
    df['block_id'] = (df['is_above_20ma'] != df['is_above_20ma'].shift()).cumsum()

    # 只針對「股價 > 20MA」的群組進行運算
    above_blocks = df[df['is_above_20ma']].groupby('block_id')

    for block_id, group in above_blocks:
        if len(group) < 2: continue 

        # 1. 在此區間內尋找「亂流」(MACD < Prev)
        macd_down_mask = group['MACD Histogram'] < group['Prev_MACD_H']
        
        if macd_down_mask.any():
            first_turb_idx = macd_down_mask.idxmax()
            subsequent_data = group.loc[first_turb_idx:]
            
            if len(subsequent_data) > 1:
                # 2. 在亂流之後尋找「轉強」(MACD > Prev)
                search_data = subsequent_data.iloc[1:]
                macd_up_mask = search_data['MACD Histogram'] > search_data['Prev_MACD_H']
                
                if macd_up_mask.any():
                    cycle_start_idx = macd_up_mask.idxmax()
                    # 循環終點強制設為該區間的最後一天
                    # 只要隔天跌破 20MA，這個 group 就結束了，紅條也會自然停止
                    cycle_end_idx = group.index[-1]
                    df.loc[cycle_start_idx:cycle_end_idx, 'Cycle_Active'] = True

    # ==========================================
    # 邏輯二：無風-陣風循環 (空頭反彈轉弱) - 綠色
    # 重要觀念：區間僅限於 Close < 20MA，一旦突破必須重新判斷
    # ==========================================
    df['Bear_Cycle_Active'] = False
    
    df['is_below_20ma'] = CLOSE_BELOW_20MA
    # 同樣使用 cumsum 確保連續性被截斷
    df['bear_block_id'] = (df['is_below_20ma'] != df['is_below_20ma'].shift()).cumsum()

    # 只針對「股價 < 20MA」的群組進行運算
    below_blocks = df[df['is_below_20ma']].groupby('bear_block_id')

    for block_id, group in below_blocks:
        if len(group) < 2: continue

        # 1. 在此區間內尋找「陣風」(MACD > Prev)
        macd_up_mask = group['MACD Histogram'] > group['Prev_MACD_H']

        if macd_up_mask.any():
            first_gust_idx = macd_up_mask.idxmax()
            subsequent_data = group.loc[first_gust_idx:]

            if len(subsequent_data) > 1:
                # 2. 在陣風之後尋找「轉弱」(MACD < Prev)
                search_data = subsequent_data.iloc[1:]
                macd_down_mask = search_data['MACD Histogram'] < search_data['Prev_MACD_H']
                
                if macd_down_mask.any():
                    cycle_start_idx = macd_down_mask.idxmax()
                    # 循環終點強制設為該區間的最後一天
                    cycle_end_idx = group.index[-1]
                    df.loc[cycle_start_idx:cycle_end_idx, 'Bear_Cycle_Active'] = True

    # ==========================================
    # 邏輯三：循環的交界 - 灰色
    # ==========================================
    df['Boundary_Active'] = ~(df['Cycle_Active'] | df['Bear_Cycle_Active'])

    # 移除運算用的暫存欄位
    df = df.drop(columns=["Prev_MACD_H", "is_above_20ma", "block_id", "is_below_20ma", "bear_block_id"])

    return df 

@st.cache_data
def load_data(symbol):
    try:
        stock = yf.Ticker(symbol)
        df = stock.history(interval="1d", start="2007-01-01", end=None, actions=False, auto_adjust=False, back_adjust=False)
        return df
    except Exception as e:
        st.error(f"下載股票資料失敗: {e}")
        return pd.DataFrame()

# ---------------------------------------------------------
# 週/月 K線重採樣函數
# ---------------------------------------------------------
def resample_weekly_data(df_daily):
    if df_daily.empty: return df_daily
    weekly_data = df_daily.resample('W').agg({'Open':'first', 'High':'max', 'Low':'min', 'Close':'last'})
    return weekly_data[weekly_data['Open'].notna()] 

def resample_monthly_data(df_daily):
    if df_daily.empty: return df_daily
    monthly_data = df_daily.resample('ME').agg({'Open':'first', 'High':'max', 'Low':'min', 'Close':'last'})
    return monthly_data[monthly_data['Open'].notna()] 


# ---------------------------------------------------------
# 3. 側邊欄：使用者輸入參數
# ---------------------------------------------------------
st.sidebar.success("請選擇上方頁面進行導覽")
st.sidebar.header("參數設定")

DEFAULT_TICKER = '^TWOII' 

default_index = 0
if DEFAULT_TICKER in ALL_SEARCH_OPTIONS:
    default_index = ALL_SEARCH_OPTIONS.index(DEFAULT_TICKER)

selected_option = st.sidebar.selectbox(
    "請輸入公司代碼或名稱:",
    options=ALL_SEARCH_OPTIONS,
    index=default_index,
    key='stock_input'
)

TICKER_SYMBOL, COMPANY_NAME = process_ticker_input(selected_option, STOCK_MAP, STOCK_NAMES)

# ---------------------------------------------------------
# 4. 主頁面：K線週期選擇
# ---------------------------------------------------------

if 'K_PERIOD' not in st.session_state:
    st.session_state['K_PERIOD'] = '日 K'
    
st.markdown("##### 選擇 K 線圖週期:", unsafe_allow_html=True) 

col_left_spacer, col_day, col_week, col_month, col_right_spacer = st.columns([1, 0.15, 0.15, 0.15, 1])

def set_period(period):
    st.session_state['K_PERIOD'] = period

with col_day:
    st.button("日 K", on_click=set_period, args=('日 K',), disabled=(st.session_state.K_PERIOD == '日 K'), key='btn_day', use_container_width=True)
with col_week:
    st.button("週 K", on_click=set_period, args=('週 K',), disabled=(st.session_state.K_PERIOD == '週 K'), key='btn_week', use_container_width=True)
with col_month:
    st.button("月 K", on_click=set_period, args=('月 K',), disabled=(st.session_state.K_PERIOD == '月 K'), key='btn_month', use_container_width=True)

K_PERIOD = st.session_state.K_PERIOD 

current_date = date.today()
if K_PERIOD == '日 K':
    default_start_offset = DateOffset(months=3)
elif K_PERIOD == '週 K':
    default_start_offset = DateOffset(years=2)
else: 
    default_start_offset = DateOffset(years=5)

start_input = st.sidebar.date_input("開始日期", (current_date - default_start_offset).date())
end_input = st.sidebar.date_input("結束日期", current_date)

start_date_str = start_input.strftime("%Y-%m-%d")
end_date_str = end_input.strftime("%Y-%m-%d")

# --- 圖層顯示設定 (Radio Button 互斥) ---
st.sidebar.subheader("圖層顯示設定")
layer_mode = st.sidebar.radio(
    "選擇顯示圖層",
    ("基本風度圖", "多空循環圖"),
    index=0, 
    help="一次僅能顯示一種圖層模式"
)

# 載入資料
data_load_state = st.text(f'資料下載運算中... ({COMPANY_NAME} / {TICKER_SYMBOL})')
daily_data = load_data(TICKER_SYMBOL)

# =========================================================
# 新增功能：櫃買指數 (^TWOII) 資料延遲警示
# =========================================================
if TICKER_SYMBOL == '^TWOII' and not daily_data.empty:
    last_data_date = daily_data.index[-1].date()
    today_date = date.today()
    
    if last_data_date < today_date:
        st.warning(f"⚠️ 注意：櫃買指數 ({TICKER_SYMBOL}) 尚無最新交易日之資料。\n\n目前資料更新至：**{last_data_date}**，請留意報價可能會有延遲。")

if K_PERIOD == '日 K':
    data = daily_data.copy()
elif K_PERIOD == '週 K':
    data = resample_weekly_data(daily_data)
else: 
    data = resample_monthly_data(daily_data)
    
data = calculate_indicators(data)
data_load_state.text('') 

# ---------------------------------------------------------
# 5. 繪製 Plotly 圖表
# ---------------------------------------------------------
if data.empty:
    st.error(f"找不到代碼 **{TICKER_SYMBOL}** 的資料，請確認輸入正確。")
else:
    end_date_dt = pd.to_datetime(end_input)
    final_end_date_str = end_date_str 
    
    if K_PERIOD == '月 K':
        next_month = end_date_dt + DateOffset(months=1)
        final_end_date_str = next_month.strftime("%Y-%m-%d")
    elif K_PERIOD == '週 K':
        next_week = end_date_dt + DateOffset(weeks=1)
        final_end_date_str = next_week.strftime("%Y-%m-%d")

    filtered_data = data.loc[start_date_str:final_end_date_str].copy()

    if filtered_data.empty:
        st.warning("選取的日期區間沒有資料，請調整日期。")
    else:
        formatted_index = filtered_data.index.strftime('%Y.%m.%d')
        
        fig = make_subplots(
            rows=2, cols=1, 
            shared_xaxes=True, 
            vertical_spacing=0.08, 
            row_heights=[0.7, 0.3]
        )
        
        candlestick_hovertemplate = (
            '<b>日期:</b> %{x}<br>' +
            '<b>開:</b> %{open:.2f}<br><b>高:</b> %{high:.2f}<br><b>低:</b> %{low:.2f}<br><b>收:</b> %{close:.2f}<br>' +
            '<b>漲跌幅:</b> <span style="color:%{customdata[0]}; font-weight:bold;">%{customdata[1]}</span><br>' +
            '<extra></extra>' 
        )

        shapes_list = []
        
        # =======================================================
        # 繪製圖層邏輯與圖例整合 (將圖例加入 Plotly 原生系統)
        # =======================================================
        
        # 模式 1: 基本風度圖層
        if layer_mode == "基本風度圖":
            # 1. 繪製背景色塊
            for idx, date_str in enumerate(formatted_index):
                row = filtered_data.iloc[idx]
                if pd.notna(row["Wind_Color"]) and row["Wind"] != "未知": 
                    shapes_list.append(
                        dict(
                            type="rect",
                            xref="x", x0=idx - 0.5, x1=idx + 0.5, 
                            yref="y", y0=filtered_data['Low'].min() * 0.99, y1=filtered_data['High'].max() * 1.01,
                            fillcolor=row["Wind_Color"],
                            line_width=0,
                            layer="below" 
                        )
                    )
            
            # 2. 右側圖例 (Dummy Traces)
            legend_items = [
                ("強風", "rgba(255, 0, 0, 0.5)"),
                ("亂流", "rgba(0, 128, 0, 0.5)"),
                ("陣風", "rgba(255, 192, 203, 0.5)"),
                ("無風", "rgba(105, 105, 105, 0.5)")
            ]
            for name, color in legend_items:
                fig.add_trace(go.Scatter(
                    x=[None], y=[None],
                    mode='markers',
                    marker=dict(size=10, color=color, symbol='square'),
                    name=name,
                    showlegend=True,
                    legendgroup='wind_layer'
                ), row=1, col=1)

        # 模式 2: 多空循環圖層
        elif layer_mode == "多空循環圖":
            # 1. 繪製背景色塊
            for idx, date_str in enumerate(formatted_index):
                row = filtered_data.iloc[idx]
                fill_color = None
                
                if row['Cycle_Active']:
                    fill_color = "rgba(255, 0, 0, 0.5)" # 紅
                elif row['Bear_Cycle_Active']:
                    fill_color = "rgba(0, 128, 0, 0.5)" # 綠
                else:
                    fill_color = "rgba(128, 128, 128, 0.5)" # 灰
                
                if fill_color:
                    shapes_list.append(
                        dict(
                            type="rect",
                            xref="x", x0=idx - 0.5, x1=idx + 0.5,
                            yref="y", y0=filtered_data['Low'].min() * 0.99, 
                            y1=filtered_data['High'].max() * 1.01,
                            fillcolor=fill_color,
                            line_width=0,
                            layer="below"
                        )
                    )
            
            # 2. 右側圖例 (Dummy Traces)
            legend_items = [
                ("強風-亂流循環", "rgba(255, 0, 0, 0.5)"),
                ("無風-陣風循環", "rgba(0, 128, 0, 0.5)"),
                ("循環的交界", "rgba(128, 128, 128, 0.5)")
            ]
            for name, color in legend_items:
                fig.add_trace(go.Scatter(
                    x=[None], y=[None],
                    mode='markers',
                    marker=dict(size=10, color=color, symbol='square'),
                    name=name,
                    showlegend=True,
                    legendgroup='cycle_layer'
                ), row=1, col=1)

        # K線圖 (主圖)
        fig.add_trace(go.Candlestick(
            x=formatted_index,
            open=filtered_data['Open'], high=filtered_data['High'], 
            low=filtered_data['Low'], close=filtered_data['Close'], 
            name='K線', increasing_line_color='red', decreasing_line_color='green',
            customdata=filtered_data[['Pct_Color', 'Pct_Change_Display']].values,
            hovertemplate=candlestick_hovertemplate
        ), row=1, col=1)

        # 20MA
        fig.add_trace(go.Scatter(
            x=formatted_index, y=filtered_data['20ma'],
            line=dict(color='orange', width=1.5), name='20MA'
        ), row=1, col=1)

        # MACD (副圖)
        colors = ['red' if val >= 0 else 'green' for val in filtered_data['MACD Histogram']]
        fig.add_trace(go.Bar(
            x=formatted_index, y=filtered_data['MACD Histogram'],
            marker_color=colors, name='MACD 柱狀圖'
        ), row=2, col=1)

        fig.add_trace(go.Scatter(
            x=formatted_index, y=filtered_data['DIF'],
            line=dict(color='blue', width=1.5), name='DIF', connectgaps=False
        ), row=2, col=1)
        fig.add_trace(go.Scatter(
            x=formatted_index, y=filtered_data['MACD'],
            line=dict(color='orange', width=1.5), name='MACD', connectgaps=False
        ), row=2, col=1)

        clean_ticker = str(TICKER_SYMBOL).replace('.TW', '').replace('.TWO', '')
        title_text = f"{K_PERIOD} - {COMPANY_NAME} ({clean_ticker}) 的風度圖 - {layer_mode}"
            
        fig.update_layout(
            title=title_text,
            xaxis_rangeslider_visible=False,
            height=800,
            hovermode="x", 
            template="plotly_white",
            shapes=shapes_list,
            # 強制顯示圖例於右側
            showlegend=True,
            legend=dict(
                orientation="v", 
                yanchor="top",
                y=1,
                xanchor="left",
                x=1.02 
            )
        )
        
        fig.update_xaxes(type='category', showgrid=True, showticklabels=False, row=1, col=1)
        fig.update_xaxes(type='category', showticklabels=True, row=2, col=1)
        fig.update_yaxes(title='股價 (Price)', row=1, col=1)
        fig.update_yaxes(title='MACD 指標', row=2, col=1)

        st.plotly_chart(fig, width='stretch')
        
        # ------------------ 詳細數據表格 ------------------
        with st.expander(f"查看 {K_PERIOD} 詳細數據"):
            display_df = filtered_data.sort_index(ascending=False).copy()
            display_df.reset_index(inplace=True)
            
            if K_PERIOD == '月 K':
                display_df['Date'] = display_df['Date'].dt.strftime('%Y-%m')
                display_df.rename(columns={'Date': '月份'}, inplace=True)
            elif K_PERIOD == '週 K':
                display_df['Date'] = display_df['Date'].dt.strftime('%Y.%m.%d')
                display_df.rename(columns={'Date': '週結日'}, inplace=True)
            else:
                display_df['Date'] = display_df['Date'].dt.strftime('%Y.%m.%d')
                display_df.rename(columns={'Date': '日期'}, inplace=True)
            
            def get_cycle_status(row):
                if row['Cycle_Active']: return '強風-亂流循環'
                elif row['Bear_Cycle_Active']: return '無風-陣風循環'
                else: return '循環的交界'
            
            display_df['目前行情方向（延續性）'] = display_df.apply(get_cycle_status, axis=1)

            new_names = {
                'Wind': '風度', 'Open': '開', 'High': '高', 'Low': '低', 'Close': '收', 
                'MACD Histogram': 'MACD柱', 'Pct_Change': '漲跌幅'
            }
            display_df.rename(columns=new_names, inplace=True)
            
            date_col = display_df.columns[0]
            target_cols = [date_col, '目前行情方向（延續性）', '風度', '開', '高', '低', '收', '漲跌幅', '20ma', 'MACD柱']
            target_cols = [c for c in target_cols if c in display_df.columns]
            display_df = display_df[target_cols]

            def color_wind_table(val):
                colors = {"強風": "rgba(255,0,0,0.2)", "亂流": "rgba(0,128,0,0.2)", 
                          "陣風": "rgba(255,192,203,0.2)", "無風": "rgba(105,105,105,0.2)"}
                return f'background-color: {colors.get(val, "transparent")}; color: black;'
            
            def color_percent(val):
                if pd.isna(val): return ''
                return 'color: red' if val > 0 else ('color: green' if val < 0 else 'color: black')
            
            def highlight_cycle_status(val):
                if val == '強風-亂流循環': return 'background-color: rgba(255, 0, 0, 0.3); font-weight: bold;'
                elif val == '無風-陣風循環': return 'background-color: rgba(0, 128, 0, 0.3); font-weight: bold;'
                elif val == '循環的交界': return 'background-color: rgba(128, 128, 128, 0.3); color: #555;'
                return ''

            styled_df = display_df.style.format({
                '開': "{:.2f}", '高': "{:.2f}", '低': "{:.2f}", '收': "{:.2f}",
                '漲跌幅': "{:.2%}", '20ma': "{:.2f}", 'MACD柱': "{:.2f}"
            })
            
            styled_df = styled_df.map(color_wind_table, subset=['風度'])
            styled_df = styled_df.map(color_percent, subset=['漲跌幅'])
            styled_df = styled_df.map(highlight_cycle_status, subset=['目前行情方向（延續性）'])
            
            st.dataframe(styled_df, hide_index=True, width='stretch')
