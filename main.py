import os
import yfinance as yf
import pandas as pd
import requests

# 🔐 金庫から鍵を取り出す
LINE_ACCESS_TOKEN = os.environ.get("LINE_ACCESS_TOKEN")
LINE_USER_ID = os.environ.get("LINE_USER_ID")

# 🗂️ 武器庫：バックテストで導き出した「最適ストップ幅」を設定
portfolio = {
    "🏦 銀行": {"stop": 15, "tickers": ["8306.T", "8316.T", "8411.T", "8308.T", "8309.T", "7182.T", "8331.T"]},
    "⚔️ 半導体": {"stop": 25, "tickers": ["8035.T", "6857.T", "6146.T", "6723.T", "7735.T", "6920.T", "4063.T"]},
    "🏢 商社": {"stop": 20, "tickers": ["8058.T", "8001.T", "8031.T", "8002.T", "8053.T", "2768.T", "8015.T"]},
    "💣 重工": {"stop": 25, "tickers": ["7011.T", "7012.T", "7013.T", "6503.T", "6301.T", "7721.T", "7004.T"]}
}

def send_line_message(message):
    url = "https://api.line.me/v2/bot/message/push"
    headers = {"Content-Type": "application/json", "Authorization": f"Bearer {LINE_ACCESS_TOKEN}"}
    data = {"to": LINE_USER_ID, "messages": [{"type": "text", "text": message}]}
    requests.post(url, headers=headers, json=data)

def scan_markets():
    # 日経平均で相場全体の安全確認
    n225 = yf.Ticker("^N225").history(period="100d")
    n225_75ma = n225['Close'].rolling(window=75).mean().iloc[-1]
    n225_close = n225['Close'].iloc[-1]
    market_env = "◎ 安全（上昇トレンド）" if n225_close > n225_75ma else "▲ 警戒（相場全体が下落気味）"
    
    msg = f"🌐 【AI司令部：最適化スナイパー稼働】\n市場環境: {market_env}\n--------------------\n"
    signals = []

    for sector, data in portfolio.items():
        stop_pct = data["stop"]
        for ticker in data["tickers"]:
            df = yf.Ticker(ticker).history(period="100d")
            if len(df) < 35: continue 
            
            # ⚡ MACD計算
            df['EMA12'] = df['Close'].ewm(span=12, adjust=False).mean()
            df['EMA26'] = df['Close'].ewm(span=26, adjust=False).mean()
            df['MACD'] = df['EMA12'] - df['EMA26']
            df['Signal'] = df['MACD'].ewm(span=9, adjust=False).mean()
            
            yday, today = df.iloc[-2], df.iloc[-1]
            
            # 🔥 大底反発サイン（MACDが0以下でゴールデンクロス）
            if yday['MACD'] <= yday['Signal'] and today['MACD'] > today['Signal'] and today['MACD'] < 0:
                signals.append(f"🔥【激アツ買】 {ticker} ({sector})\n   👉 証券アプリで「-{stop_pct}%」の逆指値をセット推奨！")

    msg += "\n".join(signals) if signals else "本日の新規狙撃対象（激アツサイン）はありません。"
    msg += "\n--------------------\nスキャン完了。明日の戦略に備えてください。"
    return msg

if __name__ == "__main__":
    result = scan_markets()
    send_line_message(result)
