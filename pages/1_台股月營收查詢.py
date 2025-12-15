import streamlit as st
import pandas as pd
import plotly.express as px
from datetime import datetime
import time
import requests
from io import BytesIO

# 設定網頁標題與排版
st.set_page_config(page_title="台股月營收查詢", layout="wide")

# ==========================================
# 1. 參數與設定
# ==========================================
REVENUE_DATA_URL = "https://docs.google.com/spreadsheets/d/e/2PACX-1vRxAhYyyPNAgvSGDDfFUM36dqwIC4KCxysWibJRyn7zvqiz-d351uaNNV7DekJiO58q4YrueFU_Sg4v/pub?gid=1569515531&single=true&output=csv"
STOCK_MAP_FILE = "../股票資料.csv"

# ==========================================
# 2. 資料讀取與處理函式
# ==========================================

@st.cache_data(ttl=3600, show_spinner=False)
def load_all_data():
    """
    載入營收資料與股票代號對照表。
    使用 cache_data 確保切換分頁時不會重新下載。
    """
    progress_bar = st.progress(0)
    status_text = st.empty()

    try:
        # --- 步驟 1: 讀取股票代號對照表 ---
        status_text.text("正在讀取股票代號對照表...")
        
        try:
            df_map_raw = pd.read_csv(STOCK_MAP_FILE, dtype=str, header=None)
        except UnicodeDecodeError:
            df_map_raw = pd.read_csv(STOCK_MAP_FILE, dtype=str, header=None, encoding='big5')
        
        if df_map_raw.shape[1] >= 3:
            df_map = pd.DataFrame()
            df_map['code'] = df_map_raw.iloc[:, 1]
            df_map['name'] = df_map_raw.iloc[:, 2]
            df_map['search_label'] = df_map['code'].astype(str) + " " + df_map['name'].astype(str)
        else:
            df_map = pd.DataFrame(columns=['code', 'name', 'search_label'])

        # --- 步驟 2: 下載月營收資料 ---
        status_text.text("正在下載月營收資料庫...")
        
        response = requests.get(REVENUE_DATA_URL, stream=True)
        response.raise_for_status()
        
        total_size = int(response.headers.get('content-length', 0))
        data_buffer = BytesIO()
        downloaded_size = 0
        chunk_size = 1024 * 1024 
        
        for chunk in response.iter_content(chunk_size=chunk_size):
            data_buffer.write(chunk)
            downloaded_size += len(chunk)
            
            if total_size > 0:
                percent = min(10 + int((downloaded_size / total_size) * 80), 90)
                progress_bar.progress(percent)
                status_text.text(f"正在下載月營收資料庫... ({downloaded_size / 1024 / 1024:.1f} MB)")
            else:
                status_text.text(f"正在下載月營收資料庫... 已下載 {downloaded_size / 1024 / 1024:.1f} MB")
                progress_bar.progress(50)

        data_buffer.seek(0)
        status_text.text("資料處理中...")
        progress_bar.progress(95)
        
        df_revenue = pd.read_csv(data_buffer, dtype={'公司代號': str})
        
        progress_bar.progress(100)
        time.sleep(0.5) 
        progress_bar.empty()
        status_text.empty()
        
        return df_map, df_revenue

    except Exception as e:
        progress_bar.empty()
        st.error(f"資料載入發生錯誤: {e}")
        return pd.DataFrame(), pd.DataFrame()

def get_sorted_date_columns(columns):
    """找出所有日期欄位並依照時間順序排列"""
    date_cols = [col for col in columns if '-' in col and col.split('-')[0].isdigit()]
    # 轉換成 (年, 月) tuple 進行排序
    date_cols.sort(key=lambda x: (int(x.split('-')[0]), int(x.split('-')[1])))
    return date_cols

def process_single_stock(df, stock_id):
    """處理單一公司資料 (用於個股查詢)"""
    stock_row = df[df['公司代號'] == stock_id]
    if stock_row.empty: return None

    date_columns = get_sorted_date_columns(df.columns)
    
    # 轉置
    revenue_data = stock_row[date_columns].T
    revenue_data.columns = ['營收']
    revenue_data.index.name = '日期字串'
    revenue_data = revenue_data.reset_index()

    processed_data = []
    for _, row in revenue_data.iterrows():
        date_str = row['日期字串']
        revenue_val = row['營收']
        try:
            roc_year, month = map(int, date_str.split('-'))
            ad_year = roc_year + 1911
            date_obj = datetime(ad_year, month, 1)
            # 換算百萬
            revenue_million = pd.to_numeric(revenue_val, errors='coerce') / 1000
            processed_data.append({
                '日期': date_obj, '西元年': ad_year, '月份': month, '營收(百萬)': revenue_million
            })
        except: continue

    result_df = pd.DataFrame(processed_data)
    if result_df.empty: return None
    
    result_df = result_df.sort_values('日期').reset_index(drop=True)
    result_df['去年同期營收'] = result_df['營收(百萬)'].shift(12)
    result_df['年增率(%)'] = ((result_df['營收(百萬)'] - result_df['去年同期營收']) / result_df['去年同期營收']) * 100
    
    return result_df

@st.cache_data(ttl=3600, show_spinner=True)
def calculate_rankings(df_revenue, df_map):
    """
    計算創新高排行榜 (批次處理)。
    使用 cache_data 確保切換回來時不用重新計算。
    """
    # 1. 取得排序後的日期欄位
    date_cols = get_sorted_date_columns(df_revenue.columns)
    if not date_cols: return pd.DataFrame()
    
    latest_col = date_cols[-1] # 最新月份
    
    # 2. 資料清洗：只取日期欄位與代號，並轉為數值
    # 為了效能，我們只處理需要的欄位
    process_cols = ['公司代號'] + date_cols
    df_calc = df_revenue[process_cols].copy()
    
    # 將所有營收欄位轉為數值 (除以1000換算百萬)
    for col in date_cols:
        df_calc[col] = pd.to_numeric(df_calc[col], errors='coerce') / 1000
    
    # 3. 找出創歷史新高
    # 歷史最大值 (跨所有時間欄位)
    df_calc['歷史最大'] = df_calc[date_cols].max(axis=1)
    
    # 篩選條件：最新月份營收 >= 歷史最大 且 最新月份營收 > 0
    record_high_df = df_calc[
        (df_calc[latest_col] >= df_calc['歷史最大']) & 
        (df_calc[latest_col] > 0)
    ].copy()
    
    # 4. 計算年增率
    # 找出去年同期的欄位
    latest_idx = date_cols.index(latest_col)
    if latest_idx >= 12:
        last_year_col = date_cols[latest_idx - 12]
        record_high_df['YoY'] = ((record_high_df[latest_col] - record_high_df[last_year_col]) / record_high_df[last_year_col]) * 100
    else:
        record_high_df['YoY'] = 0.0 # 資料不足一年
        
    # 5. 整理結果表格
    # 合併公司名稱
    if not df_map.empty:
        record_high_df = record_high_df.merge(df_map[['code', 'name']], left_on='公司代號', right_on='code', how='left')
        # 如果找不到名稱，用代號暫代
        record_high_df['name'] = record_high_df['name'].fillna(record_high_df['公司代號'])
    else:
        record_high_df['name'] = record_high_df['公司代號']
        
    # 選取並重新命名欄位
    final_df = record_high_df[['公司代號', 'name', latest_col, 'YoY']].copy()
    final_df.columns = ['公司代號', '公司名稱', '月營收(百萬)', '年增率(%)']
    
    # 依照年增率排序 (由高到低)
    final_df = final_df.sort_values('年增率(%)', ascending=False).reset_index(drop=True)
    
    return final_df, latest_col

# ==========================================
# 3. 網頁主程式介面
# ==========================================

st.title("📈 台股月營收戰情室")

# 1. 載入資料 (只會在第一次執行時跑，切換分頁不重跑)
df_map, df_revenue = load_all_data()

if not df_revenue.empty:
    
    # --- 側邊欄功能切換 ---
    st.sidebar.title("功能選單")
    app_mode = st.sidebar.radio("請選擇功能", ["個股查詢", "🔥 創新高排行榜"])
    st.sidebar.markdown("---")

    # ==========================
    # 功能 A: 個股查詢
    # ==========================
    if app_mode == "個股查詢":
        st.sidebar.header("🔍 查詢設定")
        
        # 製作搜尋選單
        if not df_map.empty:
            search_options = df_map['search_label'].tolist()
        else:
            search_options = df_revenue['公司代號'].unique().tolist()
            
        search_options.insert(0, "")
        selected_option = st.sidebar.selectbox("輸入股票代號或名稱搜尋", search_options)
        
        if selected_option:
            stock_id = selected_option.split(" ")[0]
            stock_name = selected_option.split(" ")[1] if len(selected_option.split(" ")) > 1 else stock_id
            
            chart_df = process_single_stock(df_revenue, stock_id)
            
            if chart_df is not None:
                # 篩選近五年
                last_date = chart_df['日期'].max()
                start_date = last_date.replace(year=last_date.year - 5)
                filtered_df = chart_df[chart_df['日期'] > start_date].copy()
                
                # 判斷創高
                latest_data = chart_df.iloc[-1]
                latest_rev = latest_data['營收(百萬)']
                hist_max = chart_df['營收(百萬)'].max()
                is_record_high = (latest_rev >= hist_max) and (latest_rev > 0)
                
                st.subheader(f"{stock_name} ({stock_id})")
                
                # --- 紅色醒目提醒 ---
                if is_record_high:
                    latest_str = latest_data['日期'].strftime('%Y年%m月')
                    # 使用 HTML/CSS 製作紅色區塊
                    st.markdown(f"""
                        <div style="padding: 15px; background-color: #ffe6e6; color: #cc0000; border-radius: 5px; border: 1px solid #ffcccc; margin-bottom: 15px;">
                            <h4 style="margin:0;">🔥 營收創歷史新高！</h4>
                            <p style="margin:0;">{latest_str} 營收: <strong>{latest_rev:,.1f}</strong> 百萬元</p>
                        </div>
                    """, unsafe_allow_html=True)
                
                # 長條圖
                fig = px.bar(
                    filtered_df, x='日期', y='營收(百萬)',
                    title=f"近五年單月營收趨勢",
                    labels={'營收(百萬)': '營收 (Mn NTD)', '日期': '年月'},
                    color='年增率(%)', 
                    color_continuous_scale=px.colors.diverging.Tealrose,
                    hover_data={'年增率(%)': ':.2f'}
                )
                fig.update_layout(xaxis_tickformat='%Y-%m', hovermode="x unified")
                st.plotly_chart(fig, use_container_width=True)
                
                # 詳細表格
                st.markdown("### 📊 詳細數據表 (含年增率)")
                display_df = filtered_df.copy()
                def format_cell(row):
                    rev = row['營收(百萬)']
                    yoy = row['年增率(%)']
                    if pd.isna(rev): return "-"
                    rev_str = f"{rev:,.1f}"
                    if pd.isna(yoy): return rev_str
                    symbol = "🔺" if yoy > 0 else "🔻" if yoy < 0 else ""
                    return f"{rev_str} ({symbol}{abs(yoy):.1f}%)"

                display_df['顯示文字'] = display_df.apply(format_cell, axis=1)
                pivot_table = display_df.pivot_table(index='月份', columns='西元年', values='顯示文字', aggfunc='first')
                pivot_table = pivot_table.reindex(range(1, 13))
                pivot_table = pivot_table.sort_index(axis=1, ascending=False)
                st.dataframe(pivot_table, use_container_width=True, height=460)
            else:
                st.warning("查無此公司營收資料。")
        else:
            st.info("👈 請從左側選單輸入代號或名稱。")

    # ==========================
    # 功能 B: 創新高排行榜
    # ==========================
    elif app_mode == "🔥 創新高排行榜":
        st.header("🏆 最新月營收創歷史新高排行榜")
        
        # 計算排行榜 (有快取，切換不重算)
        rank_df, latest_month_col = calculate_rankings(df_revenue, df_map)
        
        if not rank_df.empty:
            # 轉換最新月份標題 (例如 113-11 -> 民國113年11月)
            y, m = map(int, latest_month_col.split('-'))
            month_title = f"民國{y}年{m}月"
            
            st.markdown(f"統計月份：**{month_title}** | 共 **{len(rank_df)}** 家公司創歷史新高")
            st.markdown("依照 **年增率 (YoY)** 由高至低排序：")
            
            # 格式化顯示
            st.dataframe(
                rank_df.style.format({
                    "月營收(百萬)": "{:,.1f}",
                    "年增率(%)": "{:+.2f}%"
                }).background_gradient(subset=['年增率(%)'], cmap='Reds'),
                use_container_width=True,
                height=800
            )
        else:
            st.info("目前資料中沒有公司創歷史新高，或資料尚未更新。")

else:
    if st.button("重新載入"):
        st.experimental_rerun()
