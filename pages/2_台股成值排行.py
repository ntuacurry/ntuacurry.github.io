import streamlit as st
import pandas as pd
import requests
import datetime
import urllib3

# 忽略 SSL 憑證警告訊息
urllib3.disable_warnings(urllib3.exceptions.InsecureRequestWarning)

st.set_page_config(page_title="台股成交排行", layout="wide")

# 設定 Header 避免被網站阻擋
HEADERS = {
    'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/91.0.4472.124 Safari/537.36'
}

def clean_num(val):
    if isinstance(val, str):
        val = val.replace(',', '').replace('--', '0')
        return pd.to_numeric(val, errors='coerce')
    return val

@st.cache_data(ttl=3600)  # 快取一小時，避免重複抓取
def fetch_twse(date_str):
    """抓取上市資料 (對應截圖 2)"""
    url = f"https://www.twse.com.tw/rwd/zh/afterTrading/MI_INDEX?date={date_str}&type=ALLBUT0999&response=json"
    try:
        # 加入 verify=False 解決 SSLError
        res = requests.get(url, headers=HEADERS, verify=False, timeout=10)
        data = res.json()
        if data.get('stat') != 'OK': return None
        
        # 尋找收盤行情表格
        target_table = next((t for t in data['tables'] if "每日收盤行情" in t['title']), None)
        if not target_table: return None
        
        df = pd.DataFrame(target_table['data'])
        # 依截圖：0代號, 1名稱, 4成交金額, 8收盤價, 9符號, 10漲跌
        df = df[[0, 1, 4, 8, 9, 10]]
        df.columns = ['代碼', '名稱', '成交金額', '收盤價', '符號', '漲跌價差']
        
        # 解析漲跌正負號
        def parse_sign(x):
            if 'red' in x or '+' in x: return 1
            if 'green' in x or '-' in x: return -1
            return 0
            
        df['漲跌價差'] = df['漲跌價差'].apply(clean_num) * df['符號'].apply(parse_sign)
        df['成交金額'] = df['成交金額'].apply(clean_num)
        df['收盤價'] = df['收盤價'].apply(clean_num)
        df['市場'] = '市'
        return df
    except Exception as e:
        return None

@st.cache_data(ttl=3600)
def fetch_tpex(date_obj):
    """抓取上櫃資料 (對應截圖 1)"""
    minguo_date = f"{date_obj.year - 1911}/{date_obj.month:02d}/{date_obj.day:02d}"
    url = f"https://www.tpex.org.tw/web/stock/aftertrading/otc_quotes_no1430/stk_wn1430_result.php?l=zh-tw&d={minguo_date}&se=AL"
    tpex_headers = {**HEADERS, 'Referer': 'https://www.tpex.org.tw/'}
    try:
        res = requests.get(url, headers=tpex_headers, verify=False, timeout=10)
        data = res.json()
        # 截圖 1 顯示資料在 tables[0]['data']
        if 'tables' not in data or not data['tables'][0].get('data'): return None
        
        df = pd.DataFrame(data['tables'][0]['data'])
        # 依截圖：0代號, 1名稱, 2收盤, 3漲跌, 8成交金額
        df = df[[0, 1, 8, 2, 3]]
        df.columns = ['代碼', '名稱', '成交金額', '收盤價', '漲跌價差']
        df['成交金額'] = df['成交金額'].apply(clean_num)
        df['收盤價'] = df['收盤價'].apply(clean_num)
        df['漲跌價差'] = df['漲跌價差'].apply(clean_num)
        df['市場'] = '櫃'
        return df
    except Exception as e:
        return None

# --- 網頁配置 ---
st.title("📊 台股成交金額前 30 名排行榜")

# 取得最近交易日（週一至週五）
def get_default_date():
    d = datetime.date.today()
    if d.weekday() == 5: d -= datetime.timedelta(days=1)
    if d.weekday() == 6: d -= datetime.timedelta(days=2)
    return d

# 日期選擇（一旦改變，Streamlit 會自動觸發下方的抓取流程）
selected_date = st.date_input("選擇日期", value=get_default_date())
date_str = selected_date.strftime("%Y%m%d")

# 直接執行抓取邏輯 (不使用按鈕)
with st.spinner(f'正在讀取 {selected_date} 資料...'):
    df_twse = fetch_twse(date_str)
    df_tpex = fetch_tpex(selected_date)

    if df_twse is None and df_tpex is None:
        st.error(f"⚠️ 查無 {selected_date} 的成交資料，可能為休市日。")
    else:
        # 合併與計算
        full_df = pd.concat([df_twse, df_tpex], ignore_index=True)
        
        # 計算漲跌幅 (現價 / (現價 - 漲跌) - 1)
        full_df['漲跌幅'] = (full_df['漲跌價差'] / (full_df['收盤價'] - full_df['漲跌價差'])) * 100
        
        # 排序並取前 30
        top_30 = full_df.sort_values(by='成交金額', ascending=False).head(30).copy()
        top_30['成交金額'] = (top_30['成交金額'] / 100_000_000).round(1) # 轉億元
        
        # 整理欄位
        res_df = top_30[['代碼', '名稱', '市場', '成交金額', '收盤價', '漲跌幅']]
        res_df.index = range(1, 31)

        # 配色函式
        def style_price(val):
            color = '#FF3333' if val > 0 else '#00AA00' if val < 0 else '#FFFFFF'
            return f'color: {color}; font-weight: bold'

        st.subheader(f"📅 {selected_date} 全市場排行")
        st.table(
            res_df.style.format({
                '成交金額': '{:.1f} 億',
                '收盤價': '{:.2f}',
                '漲跌幅': '{:+.2f}%'
            }).applymap(style_price, subset=['收盤價', '漲跌幅'])
        )

st.caption("資料來源：TWSE、TPEx API | 註：若遇除權息，漲跌幅計算可能略有偏差。")
