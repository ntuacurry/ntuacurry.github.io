import pandas as pd
import yfinance as yf
import requests
from bs4 import BeautifulSoup
from datetime import datetime, time as dt_time
from dateutil import parser
import pytz
import os
import sys

# --- 基礎設定 ---
TELEGRAM_TOKEN = os.getenv("8084420166:AAECDynF8YqH7UFFS4hxaYz0E2uOgy2Dupk", "")
TELEGRAM_CHAT_ID = os.getenv("7728537572", "")

# 資料源
STOCKS_INFO_URL = "https://docs.google.com/spreadsheets/d/e/2PACX-1vRxAhYyyPNAgvSGDDfFUM36dqwIC4KCxysWibJRyn7zvqiz-d351uaNNV7DekJiO58q4YrueFU_Sg4v/pub?gid=1675545769&single=true&output=csv"
DAILY_LIMIT_UP_URL = "https://docs.google.com/spreadsheets/d/e/2PACX-1vRxAhYyyPNAgvSGDDfFUM36dqwIC4KCxysWibJRyn7zvqiz-d351uaNNV7DekJiO58q4YrueFU_Sg4v/pub?gid=874373040&single=true&output=csv"

def main():
    # 檢查是否有設定變數
    if not TELEGRAM_TOKEN or not TELEGRAM_CHAT_ID:
        print("錯誤：找不到 Telegram 設定 (TG_TOKEN 或 TG_CHAT_ID)")
        sys.exit(1)

    def get_hot_group_news(stock_name):
        """搜尋今日新聞"""
        tw_tz = pytz.timezone('Asia/Taipei')
        now_tw = datetime.now(tw_tz)
        today_date = now_tw.date()
        target_start_time = dt_time(9, 30)
        
        query = f"{stock_name} 熱門族群 when:1d"
        rss_url = f"https://news.google.com/rss/search?q={query}&hl=zh-TW&gl=TW&ceid=TW:zh-Hant"
        
        try:
            response = requests.get(rss_url, timeout=10)
            soup = BeautifulSoup(response.content, 'xml')
            items = soup.find_all('item')
            for item in items:
                pub_date_dt = parser.parse(item.pubDate.text).astimezone(tw_tz)
                title = item.title.text
                if (pub_date_dt.date() == today_date and 
                    pub_date_dt.time() >= target_start_time and 
                    "熱門族群" in title):
                    return {"title": title, "link": item.link.text}
        except:
            pass
        return None

    def send_telegram(message):
        """發送訊息"""
        url = f"https://api.telegram.org/bot{TELEGRAM_TOKEN}/sendMessage"
        payload = {"chat_id": TELEGRAM_CHAT_ID, "text": message, "parse_mode": "Markdown"}
        requests.post(url, data=payload)

    def main():
        try:
            # 1. 讀取資料
            df_info = pd.read_csv(STOCKS_INFO_URL)
            df_daily = pd.read_csv(DAILY_LIMIT_UP_URL)
            
            if df_daily.empty:
                print("無漲停資料")
                return

            latest_data = df_daily.iloc[-1]
            date_val = latest_data['日期']
            count = int(latest_data['漲停家數'])
            ids = latest_data.iloc[3 : 3 + count].dropna().astype(int).astype(str).tolist()
            
            target_stocks = df_info[df_info['證券代號'].astype(str).str.strip().isin(ids)]
            
            results = []
            print(f"正在分析 {date_val} 的 {len(target_stocks)} 檔漲停股...")

            # 2. 篩選邏輯
            for _, row in target_stocks.iterrows():
                sid = str(row['證券代號']).strip()
                name = row['證券名稱']
                suffix = ".TW" if row['市場別'] == "上市" else ".TWO"
                
                try:
                    tk = yf.Ticker(sid + suffix)
                    hist = tk.history(period="1d")
                    if not hist.empty:
                        last = hist.iloc[-1]
                        vol_lots = last['Volume'] / 1000
                        turnover_val = (last['Close'] * vol_lots) / 10000 # 億
                        
                        # 門檻：1萬張 或 10億
                        if vol_lots >= 10000 or turnover_val >= 10:
                            news = get_hot_group_news(name)
                            if news:
                                results.append(f"📌 *{sid} {name}*\n💰 收盤: {last['Close']:.2f}\n📊 成交: {int(vol_lots)}張 ({turnover_val:.1f}億)\n📰 [{news['title']}]({news['link']})")
                except:
                    continue

            # 3. 推播
            if results:
                msg = f"🚀 *{date_val} 明日觀察標的*\n" + "\n".join(results)
                send_telegram(msg)
                print("推播成功")
            else:
                send_telegram(f"📅 {date_val}\n今日無符合量能與新聞門檻之漲停股。")
                print("今日無符合標的")

        except Exception as e:
            print(f"執行出錯: {e}")

    if __name__ == "__main__":
        main()
