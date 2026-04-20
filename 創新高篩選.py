import streamlit as st
import requests
import pandas as pd
import numpy as np
import urllib3
import yfinance as yf
import plotly.graph_objects as go
from plotly.subplots import make_subplots
from datetime import datetime, time
import pytz

urllib3.disable_warnings(urllib3.exceptions.InsecureRequestWarning)

st.set_page_config(page_title="強勢股篩選器", page_icon="📈", layout="wide")

st.markdown("""
<style>
@import url('https://fonts.googleapis.com/css2?family=Noto+Sans+TC:wght@400;500;600;700&family=JetBrains+Mono:wght@400;600&display=swap');
html, body, [class*="css"] { font-family: 'Noto Sans TC', sans-serif; }
.stApp { background: #080c10; color: #dde3ea; }
.page-header {
    background: linear-gradient(160deg, #0f1923 0%, #080c10 60%);
    border: 1px solid #1e2d3d; border-radius: 14px;
    padding: 32px 36px; margin-bottom: 32px;
    position: relative; overflow: hidden;
}
.page-header::after {
    content: ''; position: absolute; bottom: -60px; right: -30px;
    width: 220px; height: 220px;
    background: radial-gradient(circle, rgba(255,80,80,0.08) 0%, transparent 70%);
    border-radius: 50%;
}
.page-header h1 { font-size: 1.9rem; font-weight: 700; color: #ff5050; margin: 0 0 6px 0; letter-spacing: -0.5px; }
.page-header p  { color: #6b7d8e; font-size: 0.9rem; margin: 0; }
.metric-row { display: flex; gap: 14px; margin-bottom: 24px; flex-wrap: wrap; }
.metric-card {
    background: #0f1923; border: 1px solid #1e2d3d;
    border-radius: 10px; padding: 16px 22px; flex: 1; min-width: 130px;
}
.metric-card .lbl { font-size: 0.72rem; color: #6b7d8e; text-transform: uppercase; letter-spacing: 1.2px; margin-bottom: 6px; }
.metric-card .val { font-family: 'JetBrains Mono', monospace; font-size: 1.7rem; font-weight: 600; color: #ff5050; }
.metric-card .sub { font-size: 0.72rem; color: #3d5166; margin-top: 3px; }
.info-box {
    background: rgba(30,45,61,0.5); border: 1px solid #1e2d3d;
    border-radius: 8px; padding: 11px 16px;
    font-size: 0.82rem; color: #6b7d8e; margin-bottom: 20px;
}
.section-title {
    font-size: 0.95rem; font-weight: 600; color: #8fa8bf;
    margin-bottom: 14px; padding-bottom: 8px; border-bottom: 1px solid #1e2d3d;
}

/* ── 股票卡片 ── */
.stock-card {
    background: #0f1923;
    border: 1px solid #1e2d3d;
    border-radius: 12px;
    padding: 18px 20px;
    margin-bottom: 14px;
    transition: border-color 0.2s, box-shadow 0.2s;
    cursor: pointer;
    position: relative;
    overflow: hidden;
}
.stock-card:hover {
    border-color: #ff5050;
    box-shadow: 0 0 18px rgba(255,80,80,0.12);
}
.stock-card::before {
    content: '';
    position: absolute;
    top: 0; left: 0;
    width: 3px; height: 100%;
    background: #ff5050;
    border-radius: 3px 0 0 3px;
}
.card-header {
    display: flex;
    justify-content: space-between;
    align-items: flex-start;
    margin-bottom: 12px;
}
.card-code {
    font-family: 'JetBrains Mono', monospace;
    font-size: 1.0rem;
    font-weight: 600;
    color: #dde3ea;
    letter-spacing: 0.5px;
}
.card-name {
    font-size: 0.78rem;
    color: #6b7d8e;
    margin-top: 2px;
}
.card-market-badge {
    font-size: 0.68rem;
    padding: 3px 8px;
    border-radius: 20px;
    background: rgba(30,45,61,0.8);
    border: 1px solid #1e2d3d;
    color: #6b7d8e;
    letter-spacing: 0.5px;
}
.card-price {
    font-family: 'JetBrains Mono', monospace;
    font-size: 1.55rem;
    font-weight: 700;
    color: #ff5050;
    margin-bottom: 4px;
    line-height: 1;
}
.card-price-label {
    font-size: 0.68rem;
    color: #3d5166;
    text-transform: uppercase;
    letter-spacing: 1px;
    margin-bottom: 10px;
}
.card-divider {
    border: none;
    border-top: 1px solid #1a2535;
    margin: 10px 0;
}
.card-tags {
    display: flex;
    flex-wrap: wrap;
    gap: 6px;
    margin-top: 8px;
}
.card-tag {
    font-size: 0.70rem;
    padding: 3px 9px;
    border-radius: 20px;
    letter-spacing: 0.3px;
}
.tag-high {
    background: rgba(255,80,80,0.10);
    border: 1px solid rgba(255,80,80,0.3);
    color: #ff8080;
}
.tag-trigger {
    background: rgba(96,170,255,0.10);
    border: 1px solid rgba(96,170,255,0.3);
    color: #80c0ff;
}
.card-stats {
    display: flex;
    gap: 16px;
    margin-top: 10px;
}
.card-stat {
    display: flex;
    flex-direction: column;
}
.card-stat .stat-lbl {
    font-size: 0.65rem;
    color: #3d5166;
    text-transform: uppercase;
    letter-spacing: 1px;
    margin-bottom: 2px;
}
.card-stat .stat-val {
    font-family: 'JetBrains Mono', monospace;
    font-size: 0.85rem;
    color: #8fa8bf;
    font-weight: 600;
}
</style>
""", unsafe_allow_html=True)

st.markdown("""
<div class="page-header">
    <h1>🔥 強勢股篩選器</h1>
    <p>上市 + 上櫃 &nbsp;|&nbsp; 漲幅 &gt;7% &nbsp;|&nbsp; 創高 / 量能門檻 / 漲停續強</p>
</div>
""", unsafe_allow_html=True)


# ── 下午4點後首次開啟自動清除 cache ──────────────────────────────────────────
def auto_clear_cache_after_4pm():
    """
    每天下午 16:00（台灣時間）之後，若尚未清除過 cache，則清除一次。
    使用 st.session_state 記錄「本次 session 內的清除日期」。
    """
    tz = pytz.timezone("Asia/Taipei")
    now = datetime.now(tz)
    cutoff = now.replace(hour=16, minute=0, second=0, microsecond=0)

    cleared_key = "cache_cleared_date"
    today_str   = now.strftime("%Y-%m-%d")

    # 只有在 16:00 後、且今天尚未清除過，才清除
    if now >= cutoff:
        if st.session_state.get(cleared_key) != today_str:
            st.cache_data.clear()
            st.session_state[cleared_key] = today_str

auto_clear_cache_after_4pm()


# ── 工具函數 ──────────────────────────────────────────────────────────────────
def get_tick_size(price: float) -> float:
    if price < 10:     return 0.01
    elif price < 50:   return 0.05
    elif price < 100:  return 0.1
    elif price < 500:  return 0.5
    elif price < 1000: return 1.0
    else:              return 5.0

def calc_limit_up(ref: float) -> float:
    if ref <= 0: return 0.0
    raw   = ref * 1.1
    tick  = get_tick_size(raw)
    limit = round(int(raw / tick) * tick, 10)
    if limit > raw + 1e-9: limit -= tick
    return round(limit, 4)

def is_valid_code(code: str) -> bool:
    c = str(code).strip()
    return c.isdigit() and len(c) <= 4 and not c.startswith("0")

def fetch_json(url: str) -> list:
    r = requests.get(url, timeout=15, verify=False)
    r.raise_for_status()
    return r.json()

def to_float(val, default=0.0) -> float:
    try:
        return float(str(val).strip().replace(",", ""))
    except:
        return default


# ── Step 1：從 API 抓取並篩選漲幅 > 7% ──────────────────────────────────────
@st.cache_data(show_spinner=False)
def get_candidates():
    candidates = []

    # ── 上市 TWSE ────────────────────────────────────────────────────────────
    try:
        for row in fetch_json("https://openapi.twse.com.tw/v1/exchangeReport/TWT84U"):
            code = str(row.get("Code", "")).strip()
            if not is_valid_code(code):
                continue
            ref   = to_float(row.get("PreviousDayOpeningRefPrice"))
            close = to_float(row.get("PreviousDayPrice"))
            if ref <= 0 or close <= 0:
                continue
            chg_pct = (close - ref) / ref * 100
            if chg_pct <= 7:
                continue
            candidates.append({
                "code":      code,
                "name":      str(row.get("Name", "")).strip(),
                "market":    "上市",
                "suffix":    ".TW",
                "close":     close,
                "change_pct": round(chg_pct, 2),
                "prev_ref":  ref,
            })
    except Exception as e:
        st.warning(f"上市 API 異常：{e}")

    # ── 上櫃 TPEx ────────────────────────────────────────────────────────────
    try:
        rows = fetch_json("https://www.tpex.org.tw/openapi/v1/tpex_mainboard_daily_close_quotes")
        cc   = "SecuritiesCompanyCode" if rows and "SecuritiesCompanyCode" in rows[0] else (list(rows[0].keys())[0] if rows else "")
        for row in rows:
            code = str(row.get(cc, "")).strip()
            if not is_valid_code(code):
                continue
            close  = to_float(row.get("Close"))
            change = to_float(row.get("Change"))
            if close <= 0:
                continue
            ref     = close - change
            if ref <= 0:
                continue
            chg_pct = change / ref * 100
            if chg_pct <= 7:
                continue
            candidates.append({
                "code":       code,
                "name":       str(row.get("CompanyName", "")).strip(),
                "market":     "上櫃",
                "suffix":     ".TWO",
                "close":      close,
                "change_pct": round(chg_pct, 2),
                "prev_ref":   ref,
            })
    except Exception as e:
        st.warning(f"上櫃 API 異常：{e}")

    return candidates


# ── Step 2：yfinance 後續篩選 ─────────────────────────────────────────────────
@st.cache_data(show_spinner=False, ttl=3600)
def get_hist(ticker: str) -> pd.DataFrame:
    try:
        df = yf.download(ticker, period="5y", interval="1d",
                         auto_adjust=False, progress=False)
        if isinstance(df.columns, pd.MultiIndex):
            df.columns = df.columns.get_level_values(0)
        return df.dropna(subset=["Close"])
    except:
        return pd.DataFrame()


def screen_stock(row: dict) -> dict | None:
    ticker = row["code"] + row["suffix"]
    hist   = get_hist(ticker)
    if hist.empty or len(hist) < 5:
        return None

    hist           = hist.copy()
    hist["Vol_K"]  = hist["Volume"] / 1000
    hist["Amount"] = hist["Close"] * hist["Volume"]

    today = hist.iloc[-1]
    prev  = hist.iloc[-2]

    window240 = hist["Close"].iloc[-241:-1] if len(hist) >= 241 else hist["Close"].iloc[:-1]
    high240   = float(window240.max()) if len(window240) > 0 else float(today["Close"])
    all_high  = float(hist["Close"].iloc[:-1].max())
    close_f   = float(today["Close"])

    is_alltime_high  = close_f >= all_high
    is_240_high      = close_f >= high240
    is_near_240_high = close_f >= high240 * 0.8

    if not (is_alltime_high or is_240_high or is_near_240_high):
        return None

    vol_k_today = float(today["Vol_K"])
    amt_today   = float(today["Amount"])
    cond_21     = vol_k_today >= 10000 or amt_today >= 2_000_000_000

    prev_ref      = row["prev_ref"]
    prev_limit_up = calc_limit_up(prev_ref)
    prev_close_f  = float(prev["Close"])
    prev_was_zt   = abs(prev_close_f - prev_limit_up) < 1e-4

    prev_vol_ok   = float(prev["Vol_K"])  >= 10000
    prev_amt_ok   = float(prev["Amount"]) >= 2_000_000_000
    price_up      = close_f > prev_close_f
    vol_up        = vol_k_today > float(prev["Vol_K"])
    cond_22       = prev_was_zt and (prev_vol_ok or prev_amt_ok) and price_up and vol_up

    if not (cond_21 or cond_22):
        return None

    if is_alltime_high:
        high_tag = "歷史新高"
    elif is_240_high:
        high_tag = "240日新高"
    else:
        gap = (high240 - close_f) / high240 * 100
        high_tag = f"距240日高 -{gap:.1f}%"

    triggers = []
    if cond_21: triggers.append("量能達標")
    if cond_22: triggers.append("漲停續強")

    return {
        "市場":       row["market"],
        "代碼":       row["code"],
        "名稱":       row["name"],
        "今日收盤":   round(close_f, 2),
        "高點狀態":   high_tag,
        "成交量(張)": int(vol_k_today),
        "成交值(億)": round(amt_today / 1e8, 1),
        "觸發條件":   " / ".join(triggers),
        "_ticker":    ticker,
        "_hist":      hist,
    }


# ── K線圖 ─────────────────────────────────────────────────────────────────────
def draw_chart(name: str, hist: pd.DataFrame):
    df = hist.copy().tail(120)
    df["MA5"]  = df["Close"].rolling(5).mean()
    df["MA10"] = df["Close"].rolling(10).mean()
    df["MA20"] = df["Close"].rolling(20).mean()

    colors = ["#ff5050" if float(c) >= float(o) else "#33cc66"
              for c, o in zip(df["Close"], df["Open"])]

    fig = make_subplots(rows=2, cols=1, shared_xaxes=True,
                        row_heights=[0.7, 0.3], vertical_spacing=0.03)

    fig.add_trace(go.Candlestick(
        x=df.index, open=df["Open"], high=df["High"],
        low=df["Low"], close=df["Close"],
        increasing_line_color="#ff5050", increasing_fillcolor="#ff5050",
        decreasing_line_color="#33cc66", decreasing_fillcolor="#33cc66",
        name="K線", showlegend=False,
    ), row=1, col=1)

    for ma, color, w in [("MA5","#f0c040",1.2),("MA10","#60aaff",1.2),("MA20","#cc80ff",1.5)]:
        fig.add_trace(go.Scatter(
            x=df.index, y=df[ma], line=dict(color=color, width=w),
            name=ma, connectgaps=True,
        ), row=1, col=1)

    fig.add_trace(go.Bar(
        x=df.index, y=df["Volume"] / 1000,
        marker_color=colors, name="成交量(張)", showlegend=False,
    ), row=2, col=1)

    fig.update_layout(
        title=dict(text=f"{name}　日K線（近120日，無還原）",
                   font=dict(family="Noto Sans TC", size=14, color="#dde3ea")),
        paper_bgcolor="#0f1923", plot_bgcolor="#0a1018",
        font=dict(family="JetBrains Mono", color="#6b7d8e"),
        xaxis_rangeslider_visible=False,
        legend=dict(orientation="h", y=1.02, x=0,
                    font=dict(size=11), bgcolor="rgba(0,0,0,0)"),
        margin=dict(l=10, r=10, t=50, b=10),
        height=520,
    )
    fig.update_xaxes(gridcolor="#1a2535", showgrid=True,
                     rangebreaks=[dict(bounds=["sat","mon"])])
    fig.update_yaxes(gridcolor="#1a2535", showgrid=True)
    return fig


# ── 卡片 HTML 產生器 ───────────────────────────────────────────────────────────
def render_stock_card(r: dict) -> str:
    triggers_html = "".join(
        f'<span class="card-tag tag-trigger">{t}</span>'
        for t in r["觸發條件"].split(" / ") if t
    )
    return f"""
    <div class="stock-card">
        <div class="card-header">
            <div>
                <div class="card-code">{r['代碼']}</div>
                <div class="card-name">{r['名稱']}</div>
            </div>
            <span class="card-market-badge">{r['市場']}</span>
        </div>
        <div class="card-price">{r['今日收盤']:.2f}</div>
        <div class="card-price-label">今日收盤價（TWD）</div>
        <hr class="card-divider">
        <div class="card-stats">
            <div class="card-stat">
                <span class="stat-lbl">成交量</span>
                <span class="stat-val">{r['成交量(張)']:,} 張</span>
            </div>
            <div class="card-stat">
                <span class="stat-lbl">成交值</span>
                <span class="stat-val">{r['成交值(億)']:.1f} 億</span>
            </div>
        </div>
        <div class="card-tags" style="margin-top:10px;">
            <span class="card-tag tag-high">{r['高點狀態']}</span>
            {triggers_html}
        </div>
    </div>
    """


# ════════════════════════════════════════════════════════════════════════════
# 主流程
# ════════════════════════════════════════════════════════════════════════════
with st.spinner("從 TWSE / TPEx 取得資料並篩選漲幅 > 7%..."):
    candidates = get_candidates()

n_cand = len(candidates)

st.markdown(f"""
<div class="info-box">
    TWSE / TPEx API 初步篩選：漲幅 &gt;7% 共 <b>{n_cand}</b> 檔，
    點擊下方按鈕後將對這 {n_cand} 檔以 yfinance 進行創高 / 量能 / 漲停續強判斷。
</div>
""", unsafe_allow_html=True)

if n_cand == 0:
    st.info("今日無漲幅超過 7% 的個股（或 API 資料尚未更新）。")
    st.stop()

if st.button("🔍 開始進階篩選", type="primary", use_container_width=True):
    results = []
    prog    = st.progress(0, text="yfinance 篩選中...")
    for i, row in enumerate(candidates):
        prog.progress((i + 1) / n_cand,
                      text=f"篩選中... {i+1}/{n_cand}　{row['code']} {row['name']}")
        r = screen_stock(row)
        if r:
            results.append(r)
    prog.empty()
    st.session_state["results"] = results

# ── 顯示結果（卡片式）────────────────────────────────────────────────────────
if "results" in st.session_state:
    results   = st.session_state["results"]
    total_hit = len(results)
    hit_tw    = sum(1 for r in results if r["市場"] == "上市")
    hit_otc   = sum(1 for r in results if r["市場"] == "上櫃")

    st.markdown(f"""
    <div class="metric-row">
        <div class="metric-card">
            <div class="lbl">符合個股</div>
            <div class="val">{total_hit}</div>
            <div class="sub">上市 + 上櫃合計</div>
        </div>
        <div class="metric-card">
            <div class="lbl">上市</div>
            <div class="val">{hit_tw}</div>
            <div class="sub">TWSE</div>
        </div>
        <div class="metric-card">
            <div class="lbl">上櫃</div>
            <div class="val">{hit_otc}</div>
            <div class="sub">TPEx</div>
        </div>
    </div>
    """, unsafe_allow_html=True)

    if total_hit == 0:
        st.info("本次篩選無符合條件的個股。")
    else:
        st.markdown('<div class="section-title">🔥 符合條件個股列表</div>', unsafe_allow_html=True)

        # ── 每列3張卡片 ──
        cols_per_row = 3
        for row_start in range(0, total_hit, cols_per_row):
            cols = st.columns(cols_per_row)
            for col_idx, r_idx in enumerate(range(row_start, min(row_start + cols_per_row, total_hit))):
                r = results[r_idx]
                with cols[col_idx]:
                    st.markdown(render_stock_card(r), unsafe_allow_html=True)
                    # 展開 K 線圖按鈕
                    if st.button(f"📊 查看K線", key=f"btn_{r['代碼']}"):
                        st.session_state["chart_target"] = r_idx

        # ── K線圖 Dialog ──
        if "chart_target" in st.session_state:
            idx = st.session_state["chart_target"]
            r   = results[idx]

            @st.dialog(f"📊 {r['代碼']} {r['名稱']}")
            def show_chart():
                fig = draw_chart(f"{r['代碼']} {r['名稱']}", r["_hist"])
                st.plotly_chart(fig, use_container_width=True)

            show_chart()

        # ── CSV 下載 ──
        disp_cols = ["市場","代碼","名稱","今日收盤","高點狀態","成交量(張)","成交值(億)","觸發條件"]
        disp_df   = pd.DataFrame([{k: r[k] for k in disp_cols} for r in results])
        csv = disp_df.to_csv(index=False, encoding="utf-8-sig")
        st.download_button("⬇️ 下載篩選結果 CSV", data=csv,
                           file_name="strong_stocks.csv", mime="text/csv")
