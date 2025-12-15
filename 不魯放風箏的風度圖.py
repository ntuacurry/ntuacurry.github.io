import streamlit as st
import yfinance as yf
import pandas as pd
from plotly.subplots import make_subplots
import plotly.graph_objects as go
from datetime import date, datetime
from pandas.tseries.offsets import DateOffset
import re

# ---------------------------------------------------------
# 櫃買指數備援設定 (現為主要資料源)
# ---------------------------------------------------------
OTC_INDEX_URL = "https://docs.google.com/spreadsheets/d/e/2PACX-1vRxAhYyyPNAgvSGDDfFUM36dqwIC4KCxysWibJRyn7zvqiz-d351uaNNV7DekJiO58q4YrueFU_Sg4v/pub?gid=0&single=true&output=csv"
OTC_TICKER = "^TWOII"

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
    ALL_SEARCH_OPTIONS = ["^TWII", "2330", "0050", OTC_TICKER] # 將櫃買指數加入預設清單
else:
    ALL_SEARCH_OPTIONS = list(STOCK_MAP.keys()) + list(STOCK_NAMES.keys()) + [OTC_TICKER]


def process_ticker_input(input_value, stock_map, stock_names):
    input_value = input_value.strip()
    code = input_value
    name = input_value
    yfinance_ticker = input_value
    
    if input_value == OTC_TICKER:
        return OTC_TICKER, "櫃買指數"

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
    """計算技術指標、風度狀態、多空循環、連續天數及交界。嚴格執行 20MA 分界邏輯。"""
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
    
    CLOSE_ABOVE_20MA = (df["Close"] >= df["20ma"])
    CLOSE_BELOW_20MA = (df["Close"] < df["20ma"])

    df.loc[CLOSE_ABOVE_20MA & MACD_UP, "Wind"] = "強風"
    df.loc[CLOSE_ABOVE_20MA & MACD_DOWN, "Wind"] = "亂流"
    df.loc[CLOSE_BELOW_20MA & MACD_UP, "Wind"] = "陣風"
    df.loc[CLOSE_BELOW_20MA & MACD_DOWN, "Wind"] = "無風"
    
    df["Wind_Color"] = df["Wind"].map(WIND_COLORS)

    # --- 計算連續天數 (Wind Count) ---
    wind_groups = (df['Wind'] != df['Wind'].shift()).cumsum()
    counts = df.groupby(wind_groups).cumcount() + 1
    df['Wind_Count_Label'] = df['Wind'] + counts.astype(str)


    # ==========================================
    # 邏輯一：強風-亂流循環 (多頭回檔轉強) - 紅色
    # ==========================================
    df['Cycle_Active'] = False
    
    df['is_above_20ma'] = CLOSE_ABOVE_20MA
    df['block_id'] = (df['is_above_20ma'] != df['is_above_20ma'].shift()).cumsum()

    above_blocks = df[df['is_above_20ma']].groupby('block_id')

    for block_id, group in above_blocks:
        if len(group) < 2: continue 

        macd_down_mask = group['MACD Histogram'] < group['Prev_MACD_H']
        
        if macd_down_mask.any():
            first_turb_idx = macd_down_mask.idxmax()
            subsequent_data = group.loc[first_turb_idx:]
            
            if len(subsequent_data) > 1:
                search_data = subsequent_data.iloc[1:]
                macd_up_mask = search_data['MACD Histogram'] > search_data['Prev_MACD_H']
                
                if macd_up_mask.any():
                    cycle_start_idx = macd_up_mask.idxmax()
                    cycle_end_idx = group.index[-1]
                    df.loc[cycle_start_idx:cycle_end_idx, 'Cycle_Active'] = True

    # ==========================================
    # 邏輯二：無風-陣風循環 (空頭反彈轉弱) - 綠色
    # ==========================================
    df['Bear_Cycle_Active'] = False
    
    df['is_below_20ma'] = CLOSE_BELOW_20MA
    df['bear_block_id'] = (df['is_below_20ma'] != df['is_below_20ma'].shift()).cumsum()

    below_blocks = df[df['is_below_20ma']].groupby('bear_block_id')

    for block_id, group in below_blocks:
        if len(group) < 2: continue

        macd_up_mask = group['MACD Histogram'] > group['Prev_MACD_H']

        if macd_up_mask.any():
            first_gust_idx = macd_up_mask.idxmax()
            subsequent_data = group.loc[first_gust_idx:]

            if len(subsequent_data) > 1:
                search_data = subsequent_data.iloc[1:]
                macd_down_mask = search_data['MACD Histogram'] < search_data['Prev_MACD_H']
                
                if macd_down_mask.any():
                    cycle_start_idx = macd_down_mask.idxmax()
                    cycle_end_idx = group.index[-1]
                    df.loc[cycle_start_idx:cycle_end_idx, 'Bear_Cycle_Active'] = True

    # ==========================================
    # 邏輯三：循環的交界 - 灰色
    # ==========================================
    df['Boundary_Active'] = ~(df['Cycle_Active'] | df['Bear_Cycle_Active'])

    df = df.drop(columns=["Prev_MACD_H", "is_above_20ma", "block_id", "is_below_20ma", "bear_block_id"])

    return df 

@st.cache_data
def load_otc_from_google_sheet(symbol):
    """專門從 Google Sheet 載入櫃買指數資料"""
    st.info(f"偵測到 **{symbol}**，直接從 Google Sheet 載入資料...")
    try:
        # 1. 讀取 CSV
        # 設置 skiprows=1 以應對 Google Sheet CSV 在表頭前可能存在的空行
        df_otc_raw = pd.read_csv(OTC_INDEX_URL, skiprows=1) 
        
        # 2. 清理列名並進行映射
        df_otc = df_otc_raw.rename(columns={
            '日期': 'Date',
            '開盤指數': 'Open',
            '最高指數': 'High',
            '最低指數': 'Low',
            '收盤指數': 'Close'
        })
        
        # 3. 處理日期與索引 (日期格式 YYYYMMDD)
        df_otc['Date'] = pd.to_datetime(df_otc['Date'], format='%Y%m%d', errors='coerce')
        df_otc = df_otc.dropna(subset=['Date']) 
        df_otc.set_index('Date', inplace=True)
        
        # 4. 處理數值欄位並建立 yfinance 必需的欄位
        df_otc = df_otc[['Open', 'High', 'Low', 'Close']].apply(pd.to_numeric, errors='coerce')
        df_otc = df_otc.dropna(subset=['Open', 'High', 'Low', 'Close'])
        
        # 補上其他 yfinance 期望的欄位 (指數資料通常沒有這些)
        df_otc['Volume'] = 0.0
        df_otc['Dividends'] = 0.0
        df_otc['Stock Splits'] = 0.0
        df_otc['Adj Close'] = df_otc['Close'] 
        
        df = df_otc.sort_index()
        st.success(f"成功從 Google Sheet 載入 **{symbol}** 資料。")
        return df
        
    except Exception as google_sheet_e:
        st.error(f"從 Google Sheet 載入備援資料失敗: {google_sheet_e}")
        return pd.DataFrame() 


@st.cache_data
def load_data(symbol):
    
    # --- 1. 如果是櫃買指數，直接使用 Google Sheet 資料源 (新邏輯) ---
    if symbol == OTC_TICKER:
        return load_otc_from_google_sheet(symbol)
        
    # --- 2. 其他代碼，使用 yfinance ---
    try:
        stock = yf.Ticker(symbol)
        # auto_adjust=False: 抓取未調整的原始價格
        # actions=True: 抓取除權息與分割資訊
        df = stock.history(interval="1d", start="2007-01-01", end=None, actions=True, auto_adjust=False, back_adjust=False)
        
        if df.empty:
            st.error(f"yfinance 找不到 **{symbol}** 的資料。")
            return pd.DataFrame()
            
        return df
            
    except Exception as e:
        st.error(f"下載股票資料失敗 ({symbol} / yfinance): {e}")
        return pd.DataFrame()

def adjust_for_total_return(df):
    """計算「還原權值」股價 (Adjusted for Splits AND Dividends)"""
    if df.empty: return df
    df_adj = df.copy()
    
    if 'Adj Close' in df_adj.columns:
        df_adj['Adj_Factor'] = df_adj['Adj Close'] / df_adj['Close']
        df_adj['Adj_Factor'] = df_adj['Adj_Factor'].fillna(1.0)
        
        df_adj['Open'] = df_adj['Open'] * df_adj['Adj_Factor']
        df_adj['High'] = df_adj['High'] * df_adj['Adj_Factor']
        df_adj['Low'] = df_adj['Low'] * df_adj['Adj_Factor']
        df_adj['Close'] = df_adj['Adj Close']
        
        df_adj = df_adj.drop(columns=['Adj_Factor', 'Adj Close'])
    return df_adj

def restore_nominal_prices(df):
    """計算「原始」股價 (Nominal Price)，還原分割影響。"""
    if df.empty or 'Stock Splits' not in df.columns: 
        return df
    
    df_nominal = df.copy()
    splits = df_nominal['Stock Splits'].replace(0, 1)
    cum_split_factor = splits.iloc[::-1].cumprod().iloc[::-1]
    
    df_nominal['Open'] = df_nominal['Open'] * cum_split_factor
    df_nominal['High'] = df_nominal['High'] * cum_split_factor
    df_nominal['Low'] = df_nominal['Low'] * cum_split_factor
    df_nominal['Close'] = df_nominal['Close'] * cum_split_factor
    
    return df_nominal

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
st.sidebar.header("參數設定")

DEFAULT_TICKER = '^TWII' 

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
# 4. 主頁面：觀念與連結區塊
# ---------------------------------------------------------

IG_ICON_SVG = """
<svg width="20" height="20" viewBox="0 0 24 24" fill="none" xmlns="http://www.w3.org/2000/svg">
<path fill-rule="evenodd" clip-rule="evenodd" d="M12 7C9.23858 7 7 9.23858 7 12C7 14.7614 9.23858 17 12 17C14.7614 17 17 14.7614 17 12C17 9.23858 14.7614 7 12 7ZM9 12C9 10.3431 10.3431 9 12 9C13.6569 9 15 10.3431 15 12C15 13.6569 13.6569 15 12 15C10.3431 15 9 13.6569 9 12Z" fill="currentColor"/>
<path fill-rule="evenodd" clip-rule="evenodd" d="M18 5C17.4477 5 17 5.44772 17 6C17 6.55228 17.4477 7 18 7C18.5523 7 19 6.55228 19 6C19 5.44772 18.5523 5 18 5Z" fill="currentColor"/>
<path fill-rule="evenodd" clip-rule="evenodd" d="M5 1C2.79086 1 1 2.79086 1 5V19C1 21.2091 2.79086 23 5 23H19C21.2091 23 23 21.2091 23 19V5C23 2.79086 21.2091 1 19 1H5ZM19 3H5C3.89543 3 3 3.89543 3 5V19C3 20.1046 3.89543 21 5 21H19C20.1046 21 21 20.1046 21 19V5C21 3.89543 20.1046 3 19 3Z" fill="currentColor"/>
</svg>
"""

credit_html = f"""
<style>
    .credit-card {{
        background-color: #f8f9fa; /* 淺灰背景 */
        border: 1px solid #e0e0e0;
        border-radius: 12px;
        padding: 20px;
        margin: 20px 0;
        text-align: center;
        box-shadow: 0 4px 6px rgba(0,0,0,0.05);
    }}
</style>

<div class="credit-card">
    💡 本網頁內容依照 <b>不魯放風箏選股APP</b> 的觀念製作
</div>
"""
st.markdown(credit_html, unsafe_allow_html=True)

# ---------------------------------------------------------
# 5. 主頁面：K線週期與還原權值設定
# ---------------------------------------------------------
st.markdown("##### 圖表設定:", unsafe_allow_html=True) 

col_settings_1, col_settings_2 = st.columns([1, 1])

with col_settings_1:
    K_PERIOD = st.radio(
        "選擇 K 線週期",
        ('日 K', '週 K', '月 K'),
        index=0,
        horizontal=True
    )

with col_settings_2:
    # 櫃買指數 (OTC) 資料本身沒有 Dividends/Splits，還原權值選項在此處不會改變指數價格
    if TICKER_SYMBOL == OTC_TICKER:
        use_adjusted_price = st.checkbox(
            "還原權值",
            value=False,
            disabled=True,
            help="櫃買指數無須還原權值，此選項已禁用。"
        )
    else:
        use_adjusted_price = st.checkbox(
            "還原權值",
            value=False,
            help="勾選後將顯示包含除權息與分割調整的股價；未勾選則顯示當時的原始股價"
        )


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

# 載入資料 (Raw Data, 未過濾停牌日)
data_load_state = st.text(f'資料下載運算中... ({COMPANY_NAME} / {TICKER_SYMBOL})')
daily_data_raw = load_data(TICKER_SYMBOL) 

# --- 關鍵分支：決定使用哪種股價 ---
if use_adjusted_price and TICKER_SYMBOL != OTC_TICKER:
    # 模式 A: 還原權值 (含股利、分割)
    daily_data = adjust_for_total_return(daily_data_raw)
    chart_mode_label = "還原權值"
else:
    # 模式 B: 原始股價 (指數資料或不還原權值的股票)
    daily_data = restore_nominal_prices(daily_data_raw)
    chart_mode_label = "原始股價"


# --- 關鍵修改：價格處理完畢後，才過濾停牌 (成交量為0) 的日子 ---
if not daily_data.empty and 'Volume' in daily_data.columns:
    # 判斷是否為 OTC 資料 (Volume 皆為 0)
    is_otc_data = (TICKER_SYMBOL == OTC_TICKER)
    
    if not is_otc_data:
        # 僅對股票資料過濾停牌日
        daily_data = daily_data[daily_data['Volume'] > 0]
    
    # 確保沒有 NaN 值干擾 (以防計算過程中產生)
    daily_data = daily_data.dropna(subset=['Open', 'High', 'Low', 'Close'])


# =========================================================
# 櫃買指數 (^TWOII) 資料延遲警示 (僅顯示來源為 Google Sheet)
# =========================================================
if TICKER_SYMBOL == OTC_TICKER and not daily_data.empty:
    last_data_date = daily_data.index[-1].date()
    today_date = date.today()
    if last_data_date < today_date:
        st.warning(f"⚠️ 注意：櫃買指數 ({TICKER_SYMBOL}) 尚無最新交易日之資料。\n\n目前資料更新至：**{last_data_date}**，請留意資料延遲狀況。")

# 重採樣 (基於已經調整好 並 過濾掉停牌日的 daily_data)
if K_PERIOD == '日 K':
    data = daily_data.copy()
elif K_PERIOD == '週 K':
    data = resample_weekly_data(daily_data)
else: 
    data = resample_monthly_data(daily_data)
    
data = calculate_indicators(data)
data_load_state.text('') 

# ---------------------------------------------------------
# 6. 繪製 Plotly 圖表
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
        # 繪製圖層邏輯與圖例整合
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
            
            # 2. 右側圖例
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
            
            # 2. 右側圖例
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
        title_text = f"{K_PERIOD} ({chart_mode_label}) - {COMPANY_NAME} ({clean_ticker}) 的風度圖 - {layer_mode}"
            
        fig.update_layout(
            title=title_text,
            xaxis_rangeslider_visible=False,
            height=800,
            hovermode="x", 
            template="plotly_white",
            shapes=shapes_list,
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
        with st.expander(f"查看 {K_PERIOD} 詳細數據 ({chart_mode_label})"):
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
                'Wind': '風度', 
                'Wind_Count_Label': '連續天數', 
                'Open': '開', 'High': '高', 'Low': '低', 'Close': '收', 
                'MACD Histogram': 'MACD柱', 'Pct_Change': '漲跌幅'
            }
            display_df.rename(columns=new_names, inplace=True)
            
            date_col = display_df.columns[0]
            target_cols = [date_col, '目前行情方向（延續性）', '風度', '連續天數', '開', '高', '低', '收', '漲跌幅', '20ma', 'MACD柱']
            target_cols = [c for c in target_cols if c in display_df.columns]
            display_df = display_df[target_cols]

            def color_wind_table(val):
                colors = {"強風": "rgba(255,0,0,0.2)", "亂流": "rgba(0,128,0,0.2)", 
                          "陣風": "rgba(255,192,203,0.2)", "無風": "rgba(105,105,105,0.2)"}
                return f'background-color: {colors.get(val, "transparent")}; color: black;'
            
            def color_wind_count(val):
                colors = {"強風": "rgba(255,0,0,0.2)", "亂流": "rgba(0,128,0,0.2)", 
                          "陣風": "rgba(255,192,203,0.2)", "無風": "rgba(105,105,105,0.2)"}
                for wind_type in colors.keys():
                    if wind_type in str(val):
                        return f'background-color: {colors[wind_type]}; color: black;'
                return ''

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
            styled_df = styled_df.map(color_wind_count, subset=['連續天數']) 
            styled_df = styled_df.map(color_percent, subset=['漲跌幅'])
            styled_df = styled_df.map(highlight_cycle_status, subset=['目前行情方向（延續性）'])
            
            st.dataframe(styled_df, hide_index=True, width='stretch')
