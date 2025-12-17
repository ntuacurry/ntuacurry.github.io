import streamlit as st
import pandas as pd
import requests
import re
import datetime

# 網頁配置
st.set_page_config(page_title="台股成交量 Top 30", layout="wide")

def get_latest_trading_day():
    """取得最近的交易日"""
    now = datetime.datetime.now()
    # 如果是週末，回推到週五
    if now.weekday() == 5: return now.date() - datetime.timedelta(days=1)
    if now.weekday() == 6: return now.date() - datetime.timedelta(days=2)
    return now.date()

def clean_num(val):
    """處理金額與價格中的逗號與字串轉浮點數"""
    if isinstance(val, str):
        val = val.replace(',', '')
        return pd.to_numeric(val, errors='coerce')
    return val

def fetch_twse(date_str):
    """上市股票資料抓取 (依據截圖 2)"""
    url = f"https://www.twse.com.tw/rwd/zh/afterTrading/MI_INDEX?date={date_str}&type=ALLBUT0999&response=json"
    res = requests.get(url)
    data = res.json()
    
    if data.get('stat') != 'OK':
        return None
        
    # 通常索引 8 或 9 為「每日收盤行情(全部(不含權證...))」
    target_table = None
    for table in data.get('tables', []):
        if "每日收盤行情" in table.get('title', ''):
            target_table = table
            break
    
    if not target_table: return None
    
    df = pd.DataFrame(target_table['data'])
    # 截圖 2 索引：0代號, 1名稱, 4成交金額, 8收盤價, 9漲跌符號, 10漲跌價差
    df = df[[0, 1, 4, 8, 9, 10]]
    df.columns = ['代碼', '名稱', '成交金額', '收盤價', '符號', '漲跌價差']
    
    # 解析漲跌正負號 (處理 HTML <p style=color:red>+</p>)
    def parse_sign(x):
        if '+' in x or 'red' in x: return 1
        if '-' in x or 'green' in x: return -1
        return 0
    
    df['漲跌價差'] = df['漲跌價差'].apply(clean_num) * df['符號'].apply(parse_sign)
    df['成交金額'] = df['成交金額'].apply(clean_num)
    df['收盤價'] = df['收盤價'].apply(clean_num)
    df['市場'] = '市'
    return df

def fetch_tpex(date_obj):
    """上櫃股票資料抓取 (依據截圖 1)"""
    minguo_date = f"{date_obj.year - 1911}/{date_obj.month:02d}/{date_obj.day:02d}"
    url = f"https://www.tpex.org.tw/web/stock/aftertrading/otc_quotes_no1430/stk_wn1430_result.php?l=zh-tw&d={minguo_date}&se=AL"
    headers = {'Referer': 'https://www.tpex.org.tw/'}
    res = requests.get(url, headers=headers)
    data = res.json()
    
    # 截圖 1 結構：tables[0].data
    if 'tables' not in data or not data['tables'][0].get('data'):
        return None
        
    df = pd.DataFrame(data['tables'][0]['data'])
    # 截圖 1 索引：0代號, 1名稱, 2收盤, 3漲跌, 8成交金額(元)
    df = df[[0, 1, 8, 2, 3]]
    df.columns = ['代碼', '名稱', '成交金額', '收盤價', '漲跌價差']
    
    df['成交金額'] = df['成交金額'].apply(clean_num)
    df['收盤價'] = df['收盤價'].apply(clean_num)
    df['漲跌價差'] = df['漲跌價差'].apply(clean_num)
    df['市場'] = '櫃'
    return df

# --- UI 部分 ---
st.title("🇹🇼 台股上市上櫃成交金額排行 (Top 30)")

# 選擇日期
selected_date = st.date_input("選擇日期", value=get_latest_trading_day())
date_str = selected_date.strftime("%Y%m%d")

if st.button("查詢數據"):
    with st.spinner('資料處理中...'):
        df_twse = fetch_twse(date_str)
        df_tpex = fetch_tpex(selected_date)
        
        if df_twse is None and df_tpex is None:
            st.warning("查無資料，可能為休市日或尚未開盤。")
        else:
            # 合併數據
            full_df = pd.concat([df_twse, df_tpex], ignore_index=True)
            
            # 計算漲跌幅 (現價 / (現價 - 漲跌) - 1)
            full_df['漲跌幅'] = (full_df['漲跌價差'] / (full_df['收盤價'] - full_df['漲跌價差'])) * 100
            
            # 排序並取前 30
            top_30 = full_df.sort_values(by='成交金額', ascending=False).head(30).copy()
            
            # 單位轉換：元 -> 億元
            top_30['成交金額'] = (top_30['成交金額'] / 100000000).round(1)
            
            # 整理欄位顯示
            display_df = top_30[['代碼', '名稱', '市場', '成交金額', '收盤價', '漲跌幅']]
            display_df.index = range(1, 31) # 排名

            # 顏色渲染邏輯
            def style_delta(val):
                color = '#ff4b4b' if val > 0 else '#00ad00' if val < 0 else '#cccccc'
                return f'color: {color}; font-weight: bold;'

            st.subheader(f"📅 {selected_date} 全市場成交金額排行榜")
            
            st.table(
                display_df.style.format({
                    '成交金額': '{:.1f} 億',
                    '收盤價': '{:.2f}',
                    '漲跌幅': '{:+.2f}%'
                }).applymap(style_delta, subset=['收盤價', '漲跌幅'])
            )

st.divider()
st.caption("資料來源：TWSE 證交所、TPEx 櫃買中心 API 整合查詢。")
