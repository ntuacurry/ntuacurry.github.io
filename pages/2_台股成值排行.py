import streamlit as st
import pandas as pd
import requests
import datetime
from datetime import timedelta

# 設定網頁標題
st.set_page_config(page_title="台股成交金額排行榜", layout="wide")

def get_latest_trading_day():
    """取得最近一個可能的交易日（排除週六日）"""
    today = datetime.date.today()
    if today.weekday() == 5:  # 週六
        return today - timedelta(days=1)
    elif today.weekday() == 6:  # 週日
        return today - timedelta(days=2)
    return today

def fetch_twse_data(date_str):
    """抓取上市股票資料"""
    url = f"https://www.twse.com.tw/rwd/zh/afterTrading/MI_INDEX?date={date_str}&type=ALLBUT0999&response=json"
    try:
        res = requests.get(url, timeout=10)
        data = res.json()
        if data['stat'] != 'OK':
            return None
        
        # 尋找包含股票資訊的表格 (通常是最後一個或特定長度的表格)
        # 欄位：0證券代號, 1證券名稱, 4成交金額, 8收盤價, 9漲跌, 10漲跌價差
        df = pd.DataFrame(data['tables'][8]['data'])
        df = df[[0, 1, 4, 8, 9, 10]]
        df.columns = ['代碼', '名稱', '成交金額', '收盤價', '符號', '漲跌價差']
        df['市場'] = '市'
        return df
    except:
        return None

def fetch_tpex_data(date_obj):
    """抓取上櫃股票資料"""
    # 轉換為民國年格式
    minguo_date = f"{date_obj.year - 1911}/{date_obj.month:02d}/{date_obj.day:02d}"
    url = f"https://www.tpex.org.tw/web/stock/aftertrading/otc_quotes_no1430/stk_wn1430_result.php?l=zh-tw&d={minguo_date}&se=AL"
    headers = {'Referer': 'https://www.tpex.org.tw/'}
    
    try:
        res = requests.get(url, headers=headers, timeout=10)
        data = res.json()
        if not data.get('aaData'):
            return None
        
        # 欄位：0代號, 1名稱, 2收盤價, 3漲跌, 8成交金額(元)
        df = pd.DataFrame(data['aaData'])
        df = df[[0, 1, 8, 2, 3]]
        df.columns = ['代碼', '名稱', '成交金額', '收盤價', '漲跌價差']
        df['市場'] = '櫃'
        return df
    except:
        return None

def color_price(val):
    """台股配色邏輯：漲紅跌綠"""
    color = 'white'
    if val > 0:
        color = '#FF3333' # 紅色
    elif val < 0:
        color = '#00AA00' # 綠色
    return f'color: {color}; font-weight: bold'

# --- 網頁介面 ---
st.title("📊 台股成交金額前 30 名排行榜")
st.caption("整合上市、上櫃股票數據")

# 日期選擇器 (預設為最近交易日)
selected_date = st.date_input("選擇查詢日期", value=get_latest_trading_day())
date_str = selected_date.strftime("%Y%m%d")

if st.button("開始查詢"):
    with st.spinner('正在獲取雙市資料...'):
        twse_df = fetch_twse_data(date_str)
        tpex_df = fetch_tpex_data(selected_date)

        if twse_df is None and tpex_df is None:
            st.error(f"⚠️ {selected_date} 似乎是休市日或尚未產生資料。")
        else:
            # 1. 清理與轉換上市數據
            if twse_df is not None:
                twse_df['成交金額'] = twse_df['成交金額'].str.replace(',', '').astype(float)
                twse_df['收盤價'] = pd.to_numeric(twse_df['收盤價'].str.replace(',', ''), errors='coerce')
                twse_df['漲跌價差'] = pd.to_numeric(twse_df['漲跌價差'].str.replace(',', ''), errors='coerce')
                # 處理漲跌符號
                twse_df['符號'] = twse_df['符號'].str.extract(r'>(.*)<')
                twse_df.loc[twse_df['符號'] == '－', '漲跌價差'] *= -1
                twse_df['漲跌幅'] = (twse_df['漲跌價差'] / (twse_df['收盤價'] - twse_df['漲跌價差'])) * 100
                twse_df = twse_df[['代碼', '名稱', '市場', '成交金額', '收盤價', '漲跌幅']]

            # 2. 清理與轉換上櫃數據
            if tpex_df is not None:
                tpex_df['成交金額'] = tpex_df['成交金額'].str.replace(',', '').astype(float)
                tpex_df['收盤價'] = pd.to_numeric(tpex_df['收盤價'].str.replace(',', ''), errors='coerce')
                tpex_df['漲跌價差'] = pd.to_numeric(tpex_df['漲跌價差'].str.replace(',', ''), errors='coerce')
                tpex_df['漲跌幅'] = (tpex_df['漲跌價差'] / (tpex_df['收盤價'] - tpex_df['漲跌價差'])) * 100
                tpex_df = tpex_df[['代碼', '名稱', '市場', '成交金額', '收盤價', '漲跌幅']]

            # 合併
            final_df = pd.concat([twse_df, tpex_df], ignore_index=True)
            
            # 排序並取前 30
            final_df = final_df.sort_values(by='成交金額', ascending=False).head(30)
            
            # 格式化數值
            final_df['成交金額'] = (final_df['成交金額'] / 100_000_000).round(1) # 轉為億元
            
            # 重設索引從 1 開始
            final_df.index = range(1, 31)

            # 顯示表格
            st.subheader(f"📅 {selected_date} 成交金額 Top 30")
            
            styled_df = final_df.style.applymap(color_price, subset=['收盤價', '漲跌幅'])\
                .format({
                    '成交金額': '{:.1f} 億',
                    '收盤價': '{:.2f}',
                    '漲跌幅': '{:+.2f}%'
                })
            
            st.table(styled_df)

else:
    st.info("請點擊上方按鈕開始抓取資料。")

st.markdown("---")
st.caption("資料來源：臺灣證券交易所 (TWSE)、證券櫃檯買賣中心 (TPEx)")
