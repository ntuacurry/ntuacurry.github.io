import streamlit as st
import pandas as pd
import requests
import datetime
import urllib3
import time

# 1. 基礎設定與 SSL 忽略
urllib3.disable_warnings(urllib3.exceptions.InsecureRequestWarning)
st.set_page_config(page_title="台股成值排行Top30", layout="wide")

HEADERS = {'User-Agent': 'Mozilla/5.0'}

# --- 資料處理函式 ---

def clean_num(val):
    if isinstance(val, str):
        val = val.replace(',', '').replace('--', '0').strip()
        return pd.to_numeric(val, errors='coerce')
    return val

def is_not_etf(code):
    code = str(code).strip()
    return len(code) == 4 and not (code.startswith('00') or code.startswith('01'))

@st.cache_data(ttl=3600)
def fetch_top_30_codes(date_obj):
    """
    抓取指定日期並回傳成交金額前 30 名的股票代碼集合
    """
    date_str = date_obj.strftime("%Y%m%d")
    # 上市
    twse_url = f"https://www.twse.com.tw/rwd/zh/afterTrading/MI_INDEX?date={date_str}&type=ALLBUT0999&response=json"
    # 上櫃
    minguo_date = f"{date_obj.year - 1911}/{date_obj.month:02d}/{date_obj.day:02d}"
    tpex_url = f"https://www.tpex.org.tw/web/stock/aftertrading/otc_quotes_no1430/stk_wn1430_result.php?l=zh-tw&d={minguo_date}&se=AL"
    
    combined_list = []
    
    # 抓取上市
    try:
        res = requests.get(twse_url, headers=HEADERS, verify=False, timeout=10)
        data = res.json()
        if data.get('stat') == 'OK':
            table = next((t for t in data['tables'] if "每日收盤行情" in t['title']), None)
            if table:
                df = pd.DataFrame(table['data'])
                df = df[df[0].apply(is_not_etf)]
                df['amt'] = df[4].apply(clean_num)
                # 儲存代碼、名稱、金額、收盤、漲跌價差、符號
                for _, r in df.iterrows():
                    combined_list.append({'code': r[0], 'name': r[1], 'amt': r['amt'], 'price': clean_num(r[8]), 'diff': clean_num(r[10]), 'sign': r[9], 'mkt': '市'})
    except: pass

    # 抓取上櫃
    try:
        res = requests.get(tpex_url, headers={**HEADERS, 'Referer': 'https://www.tpex.org.tw/'}, verify=False, timeout=10)
        data = res.json()
        if 'tables' in data and data['tables'][0].get('data'):
            df = pd.DataFrame(data['tables'][0]['data'])
            df = df[df[0].apply(is_not_etf)]
            df['amt'] = df[8].apply(clean_num)
            for _, r in df.iterrows():
                combined_list.append({'code': r[0], 'name': r[1], 'amt': r['amt'], 'price': clean_num(r[2]), 'diff': clean_num(r[3]), 'sign': None, 'mkt': '櫃'})
    except: pass

    if not combined_list: return None
    
    full_df = pd.DataFrame(combined_list)
    top_30 = full_df.sort_values(by='amt', ascending=False).head(30)
    return top_30

# --- UI 介面 ---

st.title("📊 台股成值排行Top30")

def get_default_date():
    d = datetime.date.today()
    if d.weekday() == 5: d -= datetime.timedelta(days=1)
    elif d.weekday() == 6: d -= datetime.timedelta(days=2)
    return d

selected_date = st.date_input("選擇基準日期", value=get_default_date())

# 1. 優先呈現當日排行榜
with st.status(f"正在載入 {selected_date} 排行榜...", expanded=True) as status:
    current_top_df = fetch_top_30_codes(selected_date)
    
    if current_top_df is None:
        st.error("此日期無資料（可能為休市日）。")
        st.stop()
    
    # 計算漲跌幅
    def calc_change(row):
        # 上市需要判斷符號
        diff = row['diff']
        if row['sign'] and 'green' in row['sign']: diff *= -1
        return (diff / (row['price'] - diff)) * 100 if (row['price'] - diff) != 0 else 0

    current_top_df['漲跌幅'] = current_top_df.apply(calc_change, axis=1)
    
    # 格式化呈現
    display_df = current_top_df[['code', 'name', 'mkt', 'amt', 'price', '漲跌幅']].copy()
    display_df.columns = ['代碼', '名稱', '市場', '成交金額', '收盤價', '漲跌幅']
    display_df['成交金額'] = (display_df['成交金額'] / 100_000_000).round(1)
    display_df.index = range(1, 31)

    def style_stock(row):
        color = '#FF3333' if row['漲跌幅'] > 0 else '#00AA00' if row['漲跌幅'] < 0 else ''
        style = f'color: {color}; font-weight: bold;' if color else 'font-weight: bold;'
        return [None, None, None, None, style, style]

    st.subheader(f"📅 {selected_date} 成交金額前 30 名 (不含 ETF)")
    st.table(display_df.style.format({'成交金額': '{:.1f} 億', '收盤價': '{:.2f}', '漲跌幅': '{:+.2f}%'}).apply(style_stock, axis=1))
    status.update(label="✅ 當日排行榜載入完成", state="complete")

# 2. 往回抓 20 天資料並處理進度
st.divider()
st.subheader("🚀 過去 20 個交易日「未上榜」之新面孔")
progress_text = st.empty()
my_bar = st.progress(0)

# 找出過去 20 個交易日的日期（跳過假日）
history_codes = set()
check_date = selected_date - datetime.timedelta(days=1)
days_found = 0
total_days_to_check = 20

with st.spinner("正在分析歷史數據..."):
    while days_found < total_days_to_check:
        # 跳過週末
        if check_date.weekday() < 5:
            hist_df = fetch_top_30_codes(check_date)
            if hist_df is not None:
                history_codes.update(hist_df['code'].tolist())
                days_found += 1
                # 更新進度條
                percent = int((days_found / total_days_to_check) * 100)
                my_bar.progress(percent)
                progress_text.text(f"分析進度：{percent}% (已檢查 {check_date})")
                time.sleep(0.1) # 稍微緩衝避免過快請求
        check_date -= datetime.timedelta(days=1)
        if (selected_date - check_date).days > 40: # 安全閥，避免無限迴圈
            break

# 3. 比對並顯示結果
current_codes = set(current_top_df['code'].tolist())
new_face_codes = current_codes - history_codes

if new_face_codes:
    new_faces_info = []
    # 保持原本排行榜的順序
    for _, row in current_top_df.iterrows():
        if row['code'] in new_face_codes:
            new_faces_info.append(f"{row['name']} ({row['code']})")
    
    st.success(f"偵測完成！共有 {len(new_faces_info)} 檔新上榜股票：")
    st.write("、".join(new_faces_info))
else:
    st.info("前 30 名的股票在過去 20 個交易日中都曾出現過。")

my_bar.empty()
progress_text.empty()
