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
# 股票資料讀取與轉換
# ---------------------------------------------------------
@st.cache_data
def load_stock_map(file_path="股票資料.csv"):
    """
    載入股票資料CSV，並建立代碼、名稱的對應關係。
    """
    try:
        df = pd.read_csv(file_path, encoding='utf-8', engine='python')
        df.columns = df.columns.str.replace(r'\s+', '', regex=True)
        
        stock_map = {} # key: 代碼 (str), value: (名稱, 市場別)
        stock_names = {} # key: 名稱 (str), value: 代碼 (str)

        for index, row in df.iterrows():
            code = str(row['公司代號']) 
            name = row['公司名稱'].strip()
            market = str(row['市場別']).strip() if not pd.isna(row['市場別']) else ""
            
            stock_map[code] = (name, market)
            
            if name not in stock_names:
                stock_names[name] = code
                
        return stock_map, stock_names
        
    except FileNotFoundError:
        st.error(f"錯誤：找不到檔案 {file_path}。請確保檔案已上傳。")
        return {}, {}
    except Exception as e:
        st.error(f"讀取或處理股票資料時發生錯誤: {e}")
        return {}, {}

# 載入股票代碼對應表
STOCK_MAP, STOCK_NAMES = load_stock_map()
ALL_SEARCH_OPTIONS = list(STOCK_MAP.keys()) + list(STOCK_NAMES.keys())


def process_ticker_input(input_value, stock_map, stock_names):
    """
    處理使用者輸入，將公司代碼/名稱轉換為 yfinance 格式的代碼和公司名稱。
    
    回傳: (yfinance_ticker_symbol, company_name)
    """
    input_value = input_value.strip()
    
    code = input_value
    name = input_value
    yfinance_ticker = input_value
    
    # 1. 輸入為公司名稱
    if input_value in stock_names:
        code = stock_names[input_value] 
        
        if code in stock_map:
            name, market = stock_map[code]
            
            if not market: 
                yfinance_ticker = code
            elif market == '上市':
                yfinance_ticker = f"{code}.TW"
            elif market == '上櫃':
                yfinance_ticker = f"{code}.TWO"
            else:
                yfinance_ticker = code
            
            return yfinance_ticker, name
            
    # 2. 輸入為公司代碼
    elif input_value in stock_map:
        code = input_value
        name, market = stock_map[code]

        if not market: 
            yfinance_ticker = code
        elif market == '上市':
            yfinance_ticker = f"{code}.TW"
        elif market == '上櫃':
            yfinance_ticker = f"{code}.TWO"
        else:
            yfinance_ticker = code
            
        return yfinance_ticker, name
        
    # 3. 輸入為指數或其他代號
    return input_value, input_value 

# ---------------------------------------------------------
# 2. 數據獲取與處理
# ---------------------------------------------------------
st.set_page_config(page_title="不魯放風箏的風度圖", layout="wide")
st.title("🪁 不魯放風箏的風度圖")

@st.cache_data
def calculate_indicators(df):
    """計算技術指標、風度狀態，並新增漲跌幅及其顏色。"""
    if df.empty:
        return df

    # 資料處理與指標計算
    df["Close"] = round(df["Close"], 2)
    
    # 計算漲跌幅：(最新收盤價 - 前一期收盤價) / 前一期收盤價
    df['Pct_Change'] = (df['Close'] - df['Close'].shift(1)) / df['Close'].shift(1)
    
    # ====== 懸浮視窗顯示所需的欄位計算 (確保字串類型一致，避免 Plotly 錯誤) ======
    
    def get_pct_color(pct):
        """返回顏色字串，NaN 返回 'black'。"""
        if pd.isna(pct):
            return 'black'
        elif pct > 0:
            return 'red'
        elif pct < 0:
            return 'green'
        else:
            return 'black'
            
    def format_pct_display(pct):
        """返回格式化後的百分比字串，NaN 返回 '-'。"""
        if pd.isna(pct):
            return '-' # 使用 '-' 確保是字串，避免 Plotly 陣列轉換問題
        # 使用 f-string 格式化，確保正數有 '+' 符號
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

@st.cache_data
def load_data(symbol):
    """下載股票資料。"""
    stock = yf.Ticker(symbol)
    df = stock.history(interval="1d", start="2007-01-01", end=None, actions=False, auto_adjust=False, back_adjust=False)
    return df

# ---------------------------------------------------------
# 週/月 K線重採樣函數 (保留當前不完整週期)
# ---------------------------------------------------------
def resample_weekly_data(df_daily):
    """將日 K 資料轉換為週 K 資料，保留不完整的當前週期。"""
    if df_daily.empty:
        return df_daily
        
    weekly_data = df_daily.resample('W').agg({
        'Open': 'first',      
        'High': 'max',        
        'Low': 'min',         
        'Close': 'last',      
    })
    
    return weekly_data[weekly_data['Open'].notna()] 

def resample_monthly_data(df_daily):
    """將日 K 資料轉換為月 K 資料，保留不完整的當前週期。"""
    if df_daily.empty:
        return df_daily
        
    monthly_data = df_daily.resample('ME').agg({
        'Open': 'first',      
        'High': 'max',        
        'Low': 'min',         
        'Close': 'last',      
    })

    return monthly_data[monthly_data['Open'].notna()] 


# ---------------------------------------------------------
# 3. 側邊欄：使用者輸入參數
# ---------------------------------------------------------
st.sidebar.header("參數設定")

DEFAULT_TICKER = '^TWOII' 

selected_option = st.sidebar.selectbox(
    "請輸入公司代碼或名稱:",
    options=ALL_SEARCH_OPTIONS,
    index=ALL_SEARCH_OPTIONS.index(DEFAULT_TICKER) if DEFAULT_TICKER in ALL_SEARCH_OPTIONS else 0,
    key='stock_input'
)

# 處理使用者輸入
TICKER_SYMBOL, COMPANY_NAME = process_ticker_input(selected_option, STOCK_MAP, STOCK_NAMES)

# ---------------------------------------------------------
# 4. 主頁面：K線週期選擇 (水平置中按鈕)
# ---------------------------------------------------------

# 確保狀態已初始化
if 'K_PERIOD' not in st.session_state:
    st.session_state['K_PERIOD'] = '日 K'
    
st.markdown("##### 選擇 K 線圖週期:", unsafe_allow_html=True) 

# 設定欄位比例：[左空白, 日K, 週K, 月K, 右空白]
col_left_spacer, col_day, col_week, col_month, col_right_spacer = st.columns([1, 0.15, 0.15, 0.15, 1])

# Helper function to set state
def set_period(period):
    st.session_state['K_PERIOD'] = period

with col_day:
    st.button(
        "日 K", 
        on_click=set_period, 
        args=('日 K',), 
        disabled=(st.session_state.K_PERIOD == '日 K'), 
        key='btn_day',
        use_container_width=True
    )
with col_week:
    st.button(
        "週 K", 
        on_click=set_period, 
        args=('週 K',), 
        disabled=(st.session_state.K_PERIOD == '週 K'),
        key='btn_week',
        use_container_width=True
    )
with col_month:
    st.button(
        "月 K", 
        on_click=set_period, 
        args=('月 K',), 
        disabled=(st.session_state.K_PERIOD == '月 K'),
        key='btn_month',
        use_container_width=True
    )

# 從 Session State 讀取當前選擇的週期
K_PERIOD = st.session_state.K_PERIOD 

# 預設顯示日期區間調整 (必須在 K_PERIOD 定義之後)
current_date = date.today()
if K_PERIOD == '日 K':
    default_start_offset = DateOffset(months=1)
elif K_PERIOD == '週 K':
    default_start_offset = DateOffset(years=1)
else: # 月 K
    default_start_offset = DateOffset(years=3)

default_end_date = current_date
start_input = st.sidebar.date_input("開始日期", (current_date - default_start_offset).date())
end_input = st.sidebar.date_input("結束日期", default_end_date)

start_date_str = start_input.strftime("%Y-%m-%d")
end_date_str = end_input.strftime("%Y-%m-%d")

# 控制風度圖層開關
show_wind_layer = st.sidebar.checkbox("顯示 K 線風度圖層", value=True)

# 載入資料
data_load_state = st.text(f'資料下載運算中... ({COMPANY_NAME} / {TICKER_SYMBOL})')
daily_data = load_data(TICKER_SYMBOL)

# 根據選擇的週期進行重採樣
if K_PERIOD == '日 K':
    data = daily_data.copy()
elif K_PERIOD == '週 K':
    data = resample_weekly_data(daily_data)
else: # 月 K
    data = resample_monthly_data(daily_data)
    
# 計算指標（包含漲跌幅及顏色）
data = calculate_indicators(data)

data_load_state.text('') 

# ---------------------------------------------------------
# 5. 繪製 Plotly 圖表
# ---------------------------------------------------------
if data.empty:
    st.error(f"找不到代碼 **{TICKER_SYMBOL}** ({COMPANY_NAME}) 的資料，請確認輸入正確。")
else:
    # 篩選特定時間區間
    
    # 🎯 修正月K和週K篩選問題：由於 resample 的索引 (Index) 晚於實際資料日 (例如月 K 索引是 12/31)，
    # 如果使用者篩選截止於 12/5，最後一個週期會被遺漏。
    
    end_date_dt = pd.to_datetime(end_input)

    # 預設使用使用者輸入的結束日期字串
    final_end_date_str = end_date_str 
    
    if K_PERIOD == '月 K':
        # 將篩選結束日期推到下個月初，確保包含當前月K的索引 (ME: 月底)
        # 例如 12/5 -> 設為 1/1 (下一月的第一天)
        next_month = end_date_dt + DateOffset(months=1)
        final_end_date_str = next_month.strftime("%Y-%m-%d")
        
    elif K_PERIOD == '週 K':
        # 將篩選結束日期推到下一週，確保包含當前週K的索引 (W: 週末)
        next_week = end_date_dt + DateOffset(weeks=1)
        final_end_date_str = next_week.strftime("%Y-%m-%d")

    filtered_data = data.loc[start_date_str:final_end_date_str].copy()

    if filtered_data.empty:
        st.warning("選取的日期區間沒有資料，請調整日期。")
    else:
        # 將日期索引格式化為 yyyy.mm.dd 字串 (用於 X 軸顯示)
        formatted_index = filtered_data.index.strftime('%Y.%m.%d')
        
        # --- 建立雙軸子圖 ---
        fig = make_subplots(
            rows=2, 
            cols=1, 
            shared_xaxes=True, 
            vertical_spacing=0.08, 
            row_heights=[0.7, 0.3]
        )
        
        # K 線圖懸浮視窗模板 (Hoover Template)
        candlestick_hovertemplate = (
            '<b>日期:</b> %{x}<br>' +
            '<b>開:</b> %{open:.2f}<br>' +
            '<b>高:</b> %{high:.2f}<br>' +
            '<b>低:</b> %{low:.2f}<br>' +
            '<b>收:</b> %{close:.2f}<br>' +
            # 使用 customdata[0] (顏色字串) 和 customdata[1] (漲跌幅顯示字串)
            '<b>漲跌幅:</b> <span style="color:%{customdata[0]}; font-weight:bold;">%{customdata[1]}</span><br>' +
            '<extra></extra>' 
        )

        # ------------------ 風度矩形 (Layer Shapes) ------------------
        wind_shapes = []
        if show_wind_layer:
            for idx, date_str in enumerate(formatted_index):
                row = filtered_data.iloc[idx]
                if pd.notna(row["Wind_Color"]) and row["Wind"] != "未知": 
                    fill_color = row["Wind_Color"]
                    wind_shapes.append(
                        dict(
                            type="rect",
                            xref="x", x0=idx - 0.5, x1=idx + 0.5, 
                            yref="y", y0=filtered_data['Low'].min() * 0.99, y1=filtered_data['High'].max() * 1.01,
                            fillcolor=fill_color,
                            line_width=0,
                            layer="below" 
                        )
                    )

        # 1. 主圖：K線圖與 20MA
        fig.add_trace(go.Candlestick(
            x=formatted_index,
            open=filtered_data['Open'], high=filtered_data['High'], 
            low=filtered_data['Low'], close=filtered_data['Close'], 
            name='K線', increasing_line_color='red', decreasing_line_color='green',
            
            # 傳遞 customdata：[漲跌幅顏色字串, 漲跌幅顯示字串]
            customdata=filtered_data[['Pct_Color', 'Pct_Change_Display']].values,
            hovertemplate=candlestick_hovertemplate
            
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
        clean_ticker = TICKER_SYMBOL.replace('.TW', '').replace('.TWO', '')
        
        if COMPANY_NAME == TICKER_SYMBOL:
            title_text = f"{K_PERIOD} - {clean_ticker} 的風度圖"
        else:
            title_text = f"{K_PERIOD} - {COMPANY_NAME} ({clean_ticker}) 的風度圖"
            
        fig.update_layout(
            title=title_text,
            xaxis_rangeslider_visible=False,
            height=800,
            hovermode="x", 
            template="plotly_white",
            shapes=wind_shapes 
        )
        
        # **X 軸格式化為 yyyy.mm.dd** (使用 category 類型)
        fig.update_xaxes(type='category', showgrid=True, showticklabels=False, row=1, col=1)
        fig.update_xaxes(type='category', showticklabels=True, row=2, col=1)
        fig.update_yaxes(title='股價 (Price)', row=1, col=1)
        fig.update_yaxes(title='MACD 指標', row=2, col=1)
        fig.update_traces(showlegend=True)

        # --- 在 Streamlit 顯示圖表 ---
        st.plotly_chart(fig, width='stretch')
        
        # ------------------ 風度圖例顯示 ------------------
        if show_wind_layer:
            st.markdown("---")
            st.subheader("風度與顏色對應")
            
            WIND_LEGEND_HEX = {
                "強風": "#FF0000",      
                "亂流": "#008000",    
                "陣風": "#FFC0CB",  
                "無風": "#696969"   
            }
            
            cols = st.columns(len(WIND_LEGEND_HEX))
            
            i = 0
            for wind, color_hex in WIND_LEGEND_HEX.items():
                
                color_block = f"<span style='background-color: {color_hex}; width: 20px; height: 20px; border: 1px solid #333; display: inline-block;'></span>"
                
                cols[i].markdown(
                    f"{color_block} **{wind}**", 
                    unsafe_allow_html=True
                )
                i += 1
            
            st.markdown("---")

        # ------------------ 詳細數據表格 ------------------
        with st.expander(f"查看 {K_PERIOD} 詳細數據與風度狀態"):
            
            # 1. 複製、日期格式化及欄位名稱調整
            display_df = filtered_data.sort_index(ascending=False).copy()
            
            display_df.reset_index(inplace=True)
            
            # 根據週期格式化日期
            if K_PERIOD == '月 K':
                # 月 K 的索引是月末，因此顯示為月份
                display_df['Date'] = display_df['Date'].dt.strftime('%Y-%m')
                display_df.rename(columns={'Date': '月份'}, inplace=True)
            elif K_PERIOD == '週 K':
                # 週 K 的索引是週末 (通常是週日)，顯示為該週的日期
                display_df['Date'] = display_df['Date'].dt.strftime('%Y.%m.%d')
                display_df.rename(columns={'Date': '週結日'}, inplace=True)
            else:
                display_df['Date'] = display_df['Date'].dt.strftime('%Y.%m.%d')
                display_df.rename(columns={'Date': '日期'}, inplace=True)
            
            # 欄位名稱映射
            new_names = {
                'Wind': '風度', 'Open': '開', 'High': '高', 
                'Low': '低', 'Close': '收', 'MACD Histogram': 'MACD柱',
                'Pct_Change': '漲跌幅' 
            }
            display_df.rename(columns=new_names, inplace=True)
            
            # 2. 調整欄位順序 (將漲跌幅放在收盤價後面)
            date_col_name = display_df.columns[0]
            cols = [date_col_name, '風度', '開', '高', '低', '收', '漲跌幅', '20ma', 'DIF', 'MACD', 'MACD柱']
            display_df = display_df[cols]

            # 3. 定義風度/漲跌幅樣式函數
            def color_wind_table(val):
                """根據風度值返回背景顏色 CSS 樣式"""
                table_colors = {
                    "強風": "rgba(255, 0, 0, 0.2)",      
                    "亂流": "rgba(0, 128, 0, 0.2)",    
                    "陣風": "rgba(255, 192, 203, 0.2)", 
                    "無風": "rgba(105, 105, 105, 0.2)"
                }
                color = table_colors.get(val, 'transparent')
                return f'background-color: {color}; color: black;'
            
            # 4. 應用格式化和樣式
            styled_df = display_df.style.format({
                '開': "{:.2f}",
                '高': "{:.2f}",
                '低': "{:.2f}",
                '收': "{:.2f}",
                '漲跌幅': "{:.2%}", # 以百分比顯示到小數點下第二位
                '20ma': "{:.2f}",
                'DIF': "{:.2f}",
                'MACD': "{:.2f}",
                'MACD柱': "{:.2f}",
            })
            
            # 應用風度欄位的背景顏色樣式 
            styled_df = styled_df.map(color_wind_table, subset=['風度'])
            
            # 應用漲跌幅的顏色樣式 (正紅/負綠)
            def color_percent(val):
                """根據漲跌幅數值返回文字顏色 CSS 樣式"""
                if pd.isna(val):
                    return ''
                elif val > 0:
                    return 'color: red'
                elif val < 0:
                    return 'color: green'
                else:
                    return 'color: black'

            styled_df = styled_df.map(color_percent, subset=['漲跌幅'])
            
            # 5. 垂直置中和水平置中 CSS 樣式
            cell_center_style = [
                {'selector': 'th', 'props': [('text-align', 'center'), ('vertical-align', 'middle')]},
                {'selector': 'td', 'props': [('text-align', 'center'), ('vertical-align', 'middle')]},
            ]
            styled_df = styled_df.set_table_styles(cell_center_style, overwrite=False)

            st.dataframe(styled_df, hide_index=True, width='stretch')
