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
# 新增: 股票資料讀取與轉換 (Step 1: 初始讀取)
# ---------------------------------------------------------
@st.cache_data
def load_stock_map(file_path="股票資料.csv"):
    """
    載入股票資料CSV，並建立代碼、名稱的對應關係。
    """
    try:
        # 使用 engine='python' 避免 C engine 的警告，並確保編碼正確讀取中文
        # 假設 '股票資料.csv' 檔案位於應用程式的根目錄
        df = pd.read_csv(file_path, encoding='utf-8', engine='python')
        # 移除欄位名稱中的空格
        df.columns = df.columns.str.replace(r'\s+', '', regex=True)
        
        # 建立主要對應字典
        stock_map = {} # key: 代碼 (str), value: (名稱, 市場別)
        stock_names = {} # key: 名稱 (str), value: 代碼 (str)

        for index, row in df.iterrows():
            # --- 修改點 1: 移除 .zfill(4) ---
            code = str(row['公司代號']) # 不再強制為四位數字
            name = row['公司名稱'].strip()
            # 確保市場別是字串，並移除前後空白
            market = str(row['市場別']).strip() if not pd.isna(row['市場別']) else ""
            
            # 代碼 -> (名稱, 市場別)
            stock_map[code] = (name, market)
            
            # 名稱 -> 代碼
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
# 使用代碼列表作為預設選項，確保指數代碼如 ^TWOII 也能被搜尋
ALL_SEARCH_OPTIONS = list(STOCK_MAP.keys()) + list(STOCK_NAMES.keys())


def process_ticker_input(input_value, stock_map, stock_names):
    """
    處理使用者輸入，將公司代碼/名稱轉換為 yfinance 格式的代碼和公司名稱。
    
    回傳: (yfinance_ticker_symbol, company_name)
    """
    # 清理輸入值，並去除前後空白
    input_value = input_value.strip()
    
    # 預設代碼和名稱都使用輸入值
    code = input_value
    name = input_value
    yfinance_ticker = input_value
    
    # 1. 如果輸入的是公司名稱 (優先判斷名稱，因為代碼長度不再固定)
    if input_value in stock_names:
        code = stock_names[input_value] # 從名稱取得代碼
        
        if code in stock_map:
            name, market = stock_map[code]
            
            # 3. 檢查市場別是否有值
            if not market: 
                yfinance_ticker = code
            # 4. 根據市場別加上後綴
            elif market == '上市':
                yfinance_ticker = f"{code}.TW"
            elif market == '上櫃':
                yfinance_ticker = f"{code}.TWO"
            else:
                yfinance_ticker = code
            
            return yfinance_ticker, name
            
    # 2. 如果輸入的是公司代碼 (無論長度，只要在 stock_map 中找到)
    elif input_value in stock_map:
        code = input_value
        name, market = stock_map[code]

        # 3. 檢查市場別是否有值
        if not market: 
            yfinance_ticker = code
        # 4. 根據市場別加上後綴
        elif market == '上市':
            yfinance_ticker = f"{code}.TW"
        elif market == '上櫃':
            yfinance_ticker = f"{code}.TWO"
        else:
            yfinance_ticker = code
            
        return yfinance_ticker, name
        
    # 5. 如果輸入的是其他代碼或指數代碼 (如 ^TWOII)，則名稱和代碼都使用原始輸入
    # --- 修改點 2: 指數代號的顯示方式 ---
    # 這裡的邏輯確保如果輸入的值既不是 CSV 中的代碼也不是名稱，
    # 則 yfinance_ticker = input_value, name = input_value (即代號本身)
    # 例如: 輸入 ^TWOII，回傳 (^TWOII, ^TWOII)
    return input_value, input_value 

# ---------------------------------------------------------
# 2. 數據獲取與處理
# ---------------------------------------------------------
st.set_page_config(page_title="不魯放風箏的風度圖", layout="wide")
st.title("🪁 不魯放風箏的風度圖")

@st.cache_data
def load_data(symbol):
    """下載股票資料並計算技術指標和風度狀態。"""
    stock = yf.Ticker(symbol)
    # 這裡的日期參數是 yfinance 固定的，不變
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
# 3. 側邊欄：使用者輸入參數 (Step 2: 搜尋介面)
# ---------------------------------------------------------
st.sidebar.header("參數設定")

# 預設顯示櫃買指數 (^TWOII)
DEFAULT_TICKER = '^TWOII' 

# 搜尋框使用 st.selectbox 實現預測/搜尋功能
# 使用者的輸入或選擇都會儲存在 selected_option
selected_option = st.sidebar.selectbox(
    "請輸入公司代碼或名稱:",
    options=ALL_SEARCH_OPTIONS,
    index=ALL_SEARCH_OPTIONS.index(DEFAULT_TICKER) if DEFAULT_TICKER in ALL_SEARCH_OPTIONS else 0,
    key='stock_input'
)

# 處理使用者輸入 (Step 3: 輸入處理)
TICKER_SYMBOL, COMPANY_NAME = process_ticker_input(selected_option, STOCK_MAP, STOCK_NAMES)

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
data_load_state = st.text(f'資料下載運算中... ({COMPANY_NAME} / {TICKER_SYMBOL})')
# 將處理好的 yfinance 格式代碼傳入 load_data
data = load_data(TICKER_SYMBOL)
data_load_state.text('') 

# ---------------------------------------------------------
# 4. 繪製 Plotly 圖表 (日期格式化與風度開關)
# ---------------------------------------------------------
if data.empty:
    # 找不到資料時，使用公司名稱/代碼組合顯示錯誤訊息
    st.error(f"找不到代碼 **{TICKER_SYMBOL}** ({COMPANY_NAME}) 的資料，請確認輸入正確。")
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
        # 標題顯示邏輯：
        # 如果 COMPANY_NAME 與 TICKER_SYMBOL 相同 (例如輸入 ^TWOII)，則只顯示 TICKER_SYMBOL (即 ^TWOII)
        # 如果 COMPANY_NAME 不相同 (例如輸入 2330, 則顯示 台積電 (2330))
        # 移除 .TW/.TWO 確保代碼顯示乾淨
        clean_ticker = TICKER_SYMBOL.replace('.TW', '').replace('.TWO', '')
        
        if COMPANY_NAME == TICKER_SYMBOL:
            title_text = f"{clean_ticker} 的風度圖"
        else:
            title_text = f"{COMPANY_NAME} ({clean_ticker}) 的風度圖"
            
        fig.update_layout(
            title=title_text,
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
        with st.expander("查看詳細數據與風度狀態"):
            
            # 1. 複製、日期格式化及欄位名稱調整
            display_df = filtered_data.sort_index(ascending=False).copy()
            
            display_df.reset_index(inplace=True)
            
            # 將日期格式化為 yyyy.mm.dd
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
                # 使用不透明顏色進行表格上色，避免過度干擾閱讀
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
                '20ma': "{:.2f}",
                'DIF': "{:.2f}",
                'MACD': "{:.2f}",
                'MACD柱': "{:.2f}",
            })
            
            # 應用風度欄位的背景顏色樣式
            styled_df = styled_df.map(color_wind_table, subset=['風度'])
            
            # 5. 垂直置中和水平置中 CSS 樣式
            cell_center_style = [
                {'selector': 'th', 'props': [('text-align', 'center'), ('vertical-align', 'middle')]},
                {'selector': 'td', 'props': [('text-align', 'center'), ('vertical-align', 'middle')]},
            ]
            styled_df = styled_df.set_table_styles(cell_center_style, overwrite=False)

            # 在 Streamlit 中顯示格式化後的表格
            st.dataframe(styled_df, hide_index=True, width='stretch')
