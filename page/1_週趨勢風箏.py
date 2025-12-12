import streamlit as st
import yfinance as yf
import pandas as pd
from datetime import date
import time 

# ---------------------------------------------------------
# 從原程式碼複製必要的輔助函數和常量 (路徑已修正)
# ---------------------------------------------------------

# 顏色定義 (從原程式碼複製)
WIND_COLORS = {
    "強風": "rgba(255, 0, 0, 0.5)",
    "亂流": "rgba(0, 128, 0, 0.5)",
    "陣風": "rgba(255, 192, 203, 0.5)",
    "無風": "rgba(105, 105, 105, 0.5)"
}

@st.cache_data
def load_stock_map(file_path="股票資料.csv"): 
    """
    載入股票資料CSV，並建立代碼、名稱、yfinance_ticker 的對應關係。
    篩選出 CFICode = 'ESVUFR' 的股票。
    """
    try:
        # 使用 root_path 來讀取位於應用程式根目錄的 '股票資料.csv'
        # 注意: 在 Streamlit 多頁面結構中，程式執行的當前目錄可能不同，
        # 但 Streamlit 通常能找到與應用程式文件在同一層的資源文件。
        df = pd.read_csv(file_path, encoding='utf-8', engine='python')
        df.columns = df.columns.str.replace(r'\s+', '', regex=True)
        
        # 🎯 關鍵步驟：篩選 CFICode
        df_filtered = df[df['CFICode'] == 'ESVUFR'].copy()
            
        stock_map = {} # key: 代碼 (str), value: (名稱, 市場別, yfinance_ticker)
        
        for index, row in df_filtered.iterrows():
            code = str(row['公司代號']).strip()
            name = row['公司名稱'].strip()
            market = str(row['市場別']).strip() if not pd.isna(row['市場別']) else ""
            
            # 轉換為 yfinance 格式 (假設台灣上市/上櫃)
            if not market: 
                yfinance_ticker = code
            elif market == '上市':
                yfinance_ticker = f"{code}.TW"
            elif market == '上櫃':
                yfinance_ticker = f"{code}.TWO"
            else:
                yfinance_ticker = code
            
            # 確保代碼是純數字，且不為空
            if code.isdigit() and code:
                stock_map[code] = (name, market, yfinance_ticker)
                
        return stock_map
        
    except FileNotFoundError:
        st.error(f"錯誤：找不到檔案 {file_path}。請確保檔案已存在於應用程式的根目錄。")
        return {}
    except KeyError as e:
        st.error(f"錯誤：CSV 檔案中找不到必要的欄位: {e}。請確認 Header 是否包含 '公司代號', '公司名稱', '市場別', 'CFICode'。")
        return {}
    except Exception as e:
        st.error(f"讀取或處理股票資料時發生錯誤: {e}")
        return {}

# 載入股票代碼對應表 (僅限 ESVUFR 類別)
STOCK_MAP = load_stock_map("../股票資料.csv") # 假定 CSV 在根目錄
# 篩選出 yfinance ticker 列表
TICKER_LIST = [item[2] for item in STOCK_MAP.values()]
# 建立 code -> (name, ticker) 的反向查表
CODE_TO_INFO = {code: (name, ticker) for code, (name, market, ticker) in STOCK_MAP.items()}


@st.cache_data
def load_data(symbol):
    """下載股票資料 (包含 Volume)，使用一年週期確保足夠的 MACD 數據。"""
    stock = yf.Ticker(symbol)
    df = stock.history(interval="1d", period="1y", actions=False, auto_adjust=False, back_adjust=False)
    # 確保只返回包含 Open/High/Low/Close/Volume 的有效數據
    return df[['Open', 'High', 'Low', 'Close', 'Volume']].dropna()

def resample_weekly_data(df_daily):
    """將日 K 資料轉換為週 K 資料，保留不完整的當前週期。"""
    if df_daily.empty:
        return df_daily
        
    # 計算 MACD 需要 Price，Price 依賴 High/Low/Close，所以週 K 需要彙整這些數據
    weekly_data = df_daily.resample('W').agg({
        'Open': 'first',      
        'High': 'max',        
        'Low': 'min',         
        'Close': 'last', 
        'Volume': 'sum' # 成交量總和
    })
    
    return weekly_data[weekly_data['Open'].notna()] 


# ---------------------------------------------------------
# 週趨勢風箏篩選邏輯
# ---------------------------------------------------------
def calculate_weekly_kite(df_daily, yf_ticker):
    """計算並篩選符合「週趨勢風箏」條件的股票。"""
    
    # 1. 轉換為週 K 數據
    df_weekly = resample_weekly_data(df_daily)
    
    if df_weekly.empty or len(df_weekly) < 2:
        return None

    # 2. 計算指標
    # MACD 需要 Price
    df_weekly["Price"] = round((df_weekly["High"] + df_weekly["Low"] + 2 * df_weekly["Close"]) / 4, 2)
    df_weekly["EMA12"] = df_weekly["Price"].ewm(span=12, adjust=False).mean()
    df_weekly["EMA26"] = df_weekly["Price"].ewm(span=26, adjust=False).mean()
    df_weekly["DIF"] = df_weekly["EMA12"] - df_weekly["EMA26"]
    df_weekly["MACD"] = df_weekly["DIF"].ewm(span=9, adjust=False).mean()
    df_weekly["MACD_H"] = df_weekly["DIF"] - df_weekly["MACD"] # MACD 柱狀圖

    # 3. 準備最新兩週數據 (確保 MACD 數據不為 NaN)
    df_valid = df_weekly.dropna(subset=['MACD_H'])
    if len(df_valid) < 2:
        return None
        
    latest = df_valid.iloc[-1]
    prev = df_valid.iloc[-2]
    
    # 4. 計算最新交易日成交金額 (以億為單位)
    # 成交額 = (價格*1000)*成交量/100000000
    
    # 取得最新一筆日 K 數據
    latest_trade_day = df_daily.iloc[-1]
    
    # 價格計算 (Price)
    latest_price = round((latest_trade_day["High"] + latest_trade_day["Low"] + 2 * latest_trade_day["Close"]) / 4, 2)
    
    # 計算基礎金額 (價格 * 成交量)
    base_amount = latest_price * latest_trade_day["Volume"]
    
    # 條件 1a: 基礎金額 > 100000 (交易活躍度初篩)
    if base_amount <= 100000:
        return None 

    # 計算成交額 (億) = (基礎金額 * 1000) / 100,000,000 = 基礎金額 / 100,000
    turnover_billion = base_amount / 100000.0

    # 條件 1b: 最新交易日的成交金額大於1億
    cond_turnover = turnover_billion >= 1.0 

    # 條件 2, 3, 4: MACD 篩選
    cond_macd_up = latest["MACD_H"] > prev["MACD_H"]     # 目前最新這週的MACD柱 > 前一週的MACD柱
    cond_macd_positive = latest["MACD_H"] > 0                 # 目前最新這週的MACD柱 > 0
    cond_macd_prev_negative = prev["MACD_H"] < 0              # 前一週的MACD柱 < 0
    
    if cond_macd_up and cond_macd_positive and cond_macd_prev_negative and cond_turnover:
        return {
            "週MACD柱 (最新)": latest["MACD_H"],
            "週MACD柱 (前一週)": prev["MACD_H"],
            "最新日成交額 (億)": turnover_billion,
        }
    else:
        return None

# ---------------------------------------------------------
# Streamlit 頁面主體
# ---------------------------------------------------------

st.set_page_config(page_title="週趨勢風箏", layout="wide")
st.title("🚀 週趨勢風箏篩選")

st.markdown(r"""
#### 篩選條件 (必須同時符合)：
1. **MACD 柱轉紅:** 本週 MACD 柱 $\text{(最新)} >$ 上週 MACD 柱 $\text{(前一週)}$
2. **MACD 柱翻多:** 本週 MACD 柱 $\text{(最新)} > 0$
3. **MACD 柱底背離:** 上週 MACD 柱 $\text{(前一週)} < 0$
4. **活躍度門檻:** 最新交易日成交金額 $\ge 1$ 億
   (成交額計算依據：$\text{成交額 (億)} = \frac{(Price \times Volume \times 1000)}{100,000,000}$，其中 $Price = (High + Low + 2 \times Close) / 4$)
""")

if st.button("開始執行篩選", type="primary"):
    
    if not STOCK_MAP:
        st.error("股票列表為空，請檢查 '股票資料.csv' 檔案是否位於應用程式根目錄，並確認其中包含 CFICode = 'ESVUFR' 的股票資料。")
        st.stop()

    results = []
    total_tickers = len(TICKER_LIST)
    progress_bar = st.progress(0, text="初始化...")
    status_text = st.empty()
    
    start_time = time.time()
    
    for i, yf_ticker in enumerate(TICKER_LIST):
        
        # 更新進度條
        percent_complete = (i + 1) / total_tickers
        progress_bar.progress(percent_complete, text=f"處理中: {i+1}/{total_tickers} 個代碼 ({yf_ticker})")
        
        code = yf_ticker.split('.')[0]
        company_name, _ = CODE_TO_INFO.get(code, ('未知名稱', yf_ticker))

        # 1. 下載數據
        daily_data = load_data(yf_ticker)

        if daily_data.empty:
            status_text.markdown(f"處理 **{code} ({company_name})**: ❌ 資料下載失敗或為空。")
            continue

        # 2. 執行篩選邏輯
        try:
            kite_info = calculate_weekly_kite(daily_data, yf_ticker)
        except Exception as e:
             # 僅輸出錯誤提示，不中斷整體進程
             status_text.markdown(f"處理 **{code} ({company_name})**: ❌ 計算錯誤：{e}")
             continue
        
        # 3. 記錄符合條件的股票
        if kite_info:
            results.append({
                "公司代碼": code,
                "公司名稱": company_name,
                "YF_TICKER": yf_ticker,
                **kite_info 
            })
            status_text.markdown(f"處理 **{code} ({company_name})**: ✅ **符合條件!** (成交額: {kite_info['最新日成交額 (億)']:.2f} 億)")
        else:
            status_text.markdown(f"處理 **{code} ({company_name})**: ⬜ 不符合條件。")
        
    # 結束處理
    progress_bar.empty()
    status_text.empty()
    end_time = time.time()
    st.success(f"✅ 篩選完成！共處理 {total_tickers} 個代碼，耗時 {end_time - start_time:.2f} 秒。")

    if results:
        # 4. 轉換為 DataFrame 並按成交額排序
        results_df = pd.DataFrame(results)
        results_df = results_df.sort_values(by="最新日成交額 (億)", ascending=False)
        
        # 5. 顯示結果
        st.subheader(f"✨ 符合「週趨勢風箏」條件的股票 ({len(results)} 檔)")
        
        # 格式化顯示 (不顯示 YF_TICKER)
        display_df = results_df.drop(columns=["YF_TICKER"])
        
        st.dataframe(
            display_df.style.format({
                "週MACD柱 (最新)": "{:.2f}",
                "週MACD柱 (前一週)": "{:.2f}",
                "最新日成交額 (億)": "{:.2f} 億"
            }),
            hide_index=True,
            width='stretch'
        )

    else:
        st.warning("🥲 沒有找到符合「週趨勢風箏」條件的股票。")
