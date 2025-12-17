import streamlit as st
import pandas as pd
import requests
import datetime
import urllib3
import re

# 1. 解決 SSL 驗證問題
urllib3.disable_warnings(urllib3.exceptions.InsecureRequestWarning)

st.set_page_config(page_title="台股成交排行榜 (剔除 ETF)", layout="wide")

# 設定請求標頭
HEADERS = {
    'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/91.0.4472.124 Safari/537.36'
}

def clean_num(val):
    """處理千分位逗號並轉為數字"""
    if isinstance(val, str):
        val = val.replace(',', '').replace('--', '0').strip()
        return pd.to_numeric(val, errors='coerce')
    return val

def is_not_etf(code):
    """
    過濾 ETF 邏輯：
    1. 台灣普通股代碼通常為 4 碼
    2. 剔除 00 開頭的代碼 (ETF/ETN)
    3. 剔除 01 開頭的代碼 (受益證券)
    """
    code = str(code).strip()
    # 僅保留長度為 4 且不是 00 或 01 開頭的代碼
    return len(code) == 4 and not (code.startswith('00') or code.startswith('01'))

@st.cache_data(ttl=600)
def fetch_twse(date_str):
    """抓取上市資料並剔除 ETF"""
    url = f"https://www.twse.com.tw/rwd/zh/afterTrading/MI_INDEX?date={date_str}&type=ALLBUT0999&response=json"
    try:
        # verify=False 解決 SSLError
        res = requests.get(url, headers=HEADERS, verify=False, timeout=15)
        data = res.json()
        if data.get('stat') != 'OK': return None
        
        target_table = next((t for t in data['tables'] if "每日收盤行情" in t['title']), None)
        if not target_table: return None
        
        df = pd.DataFrame(target_table['data'])
        # 欄位索引：0代碼, 1名稱, 4成交金額, 8收盤價, 9漲跌符號, 10漲跌價差
        df = df[[0, 1, 4, 8, 9, 10]]
        df.columns = ['代碼', '名稱', '成交金額', '收盤價', '符號', '漲跌價差']
        
        # 剔除 ETF
        df = df[df['代碼'].apply(is_not_etf)]
        
        def parse_sign(x):
            if 'red' in x or '+' in x: return 1
            if 'green' in x or '-' in x: return -1
            return 0
            
        df['漲跌價差'] = df['漲跌價差'].apply(clean_num) * df['符號'].apply(parse_sign)
        df['成交金額'] = df['成交金額'].apply(clean_num)
        df['收盤價'] = df['收盤價'].apply(clean_num)
        df['市場'] = '市'
        return df
    except:
        return None

@st.cache_data(ttl=600)
def fetch_tpex(date_obj):
    """抓取上櫃資料並剔除 ETF"""
    minguo_date = f"{date_obj.year - 1911}/{date_obj.month:02d}/{date_obj.day:02d}"
    url = f"https://www.tpex.org.tw/web/stock/aftertrading/otc_quotes_no1430/stk_wn1430_result.php?l=zh-tw&d={minguo_date}&se=AL"
    tpex_headers = {**HEADERS, 'Referer': 'https://www.tpex.org.tw/'}
    try:
        res = requests.get(url, headers=tpex_headers, verify=False, timeout=15)
        data = res.json()
        if 'tables' not in data or not data['tables'][0].get('data'): return None
        
        df = pd.DataFrame(data['tables'][0]['data'])
        # 欄位索引：0代碼, 1名稱, 2收盤, 3漲跌, 8成交金額
        df = df[[0, 1, 8, 2, 3]]
        df.columns = ['代碼', '名稱', '成交金額', '收盤價', '漲跌價差']
        
        # 剔除 ETF
        df = df[df['代碼'].apply(is_not_etf)]
        
        df['成交金額'] = df['成交金額'].apply(clean_num)
        df['收盤價'] = df['收盤價'].apply(clean_num)
        df['漲跌價差'] = df['漲跌價差'].apply(clean_num)
        df['市場'] = '櫃'
        return df
    except:
        return None

# --- UI 介面 ---
st.title("📊 台股成交金額前 30 名 (純股票排名)")
st.write("已自動剔除 ETF、ETN 及受益證券。")

# 預設日期處理 (排除周末)
def get_default_date():
    d = datetime.date.today()
    if d.weekday() == 5: d -= datetime.timedelta(days=1)
    elif d.weekday() == 6: d -= datetime.timedelta(days=2)
    return d

selected_date = st.date_input("選擇日期", value=get_default_date())
date_str = selected_date.strftime("%Y%m%d")

# 自動執行：只要日期變動，下方邏輯就會重新執行
with st.spinner(f'正在分析 {selected_date} 數據...'):
    df_twse = fetch_twse(date_str)
    df_tpex = fetch_tpex(selected_date)

    if df_twse is None and df_tpex is None:
        st.error(f"⚠️ 無法取得 {selected_date} 的成交資料。可能原因：休市日、尚未開盤或 API 暫時限制。")
    else:
        # 合併兩市資料
        dfs = [df for df in [df_twse, df_tpex] if df is not None]
        full_df = pd.concat(dfs, ignore_index=True)
        
        # 計算漲跌幅 (%)
        # 公式：漲跌 / (現價 - 漲跌)
        full_df['漲跌幅'] = (full_df['漲跌價差'] / (full_df['收盤價'] - full_df['漲跌價差'])) * 100
        
        # 依照成交金額排序取 Top 30
        top_30 = full_df.sort_values(by='成交金額', ascending=False).head(30).copy()
        
        # 單位轉換：元 -> 億元 (四捨五入到第一位)
        top_30['成交金額'] = (top_30['成交金額'] / 100_000_000).round(1)
        
        # 整理最終表格
        res_df = top_30[['代碼', '名稱', '市場', '成交金額', '收盤價', '漲跌幅']]
        res_df.index = range(1, len(res_df) + 1) # 設定排名

        # 台股配色邏輯
        def style_stock(row):
            # 漲跌幅大於 0 紅色，小於 0 綠色
            color = '#FF3333' if row['漲跌幅'] > 0 else '#00AA00' if row['漲跌幅'] < 0 else '#FFFFFF'
            return [None, None, None, None, f'color: {color}', f'color: {color}']

        st.subheader(f"📅 {selected_date} 全市場成交排行 (不含 ETF)")
        
        # 使用 Pandas Styler 進行美化
        styled_res = res_df.style.format({
            '成交金額': '{:.1f} 億',
            '收盤價': '{:.2f}',
            '漲跌幅': '{:+.2f}%'
        }).apply(style_stock, axis=1)

        st.table(styled_res)

st.divider()
st.caption("備註：本工具透過排除 '00' 開頭及非 4 位數代碼來過濾 ETF。資料來源：TWSE、TPEx。")
