import os
import yfinance as yf
import pandas as pd
import requests

# 金庫から鍵（LINEのパスワード）を取り出す
LINE_ACCESS_TOKEN = os.environ.get("LINE_ACCESS_TOKEN")
LINE_USER_ID = os.environ.get("LINE_USER_ID")

# 武器庫（セクター別・黄金比設定）
portfolio = {
    "🛡️ 銀行": {"tickers": ["8306.T", "8316.T", "8411.T", "8308.T", "8309.T", "7182.T", "8331.T"], "params": (15, 50)},
    "⚔️ 半導体": {"tickers": ["8035.T", "6857.T", "6146.T", "6723.T", "7735.T", "6920.T", "4063.T"], "params": (10, 25)},
    "槍 商社": {"tickers": ["8058.T", "8001.T", "8031.T", "8002.T", "8053.T", "2768.T", "8015.T"], "params": (15, 75)},
    "💣 重工": {"tickers": ["7011.T", "7012.T", "7013.T", "6503.T", "6301.T", "7721.T", "7004.T"], "params": (15, 50)}
}

def send_line_message(message):
    url = "https://api.line.me/v2/bot/message/push"
    headers = {"Content-Type": "application/json", "Authorization": f"Bearer {LINE_ACCESS_TOKEN}"}
    data = {"to": LINE_USER_ID, "messages": [{"type": "text", "text": message}]}
    requests.post(url, headers=headers, json=data)

def scan_markets():
    n225 = yf.Ticker("^N225").history(period="100d")
    n225_75ma = n225['Close'].rolling(window=75).mean().iloc[-1]
    n225_close = n225['Close'].iloc[-1]
    market_env = "◎ 安全" if n225_close > n225_75ma else "▲ 警戒"
    
    msg = f"🌐 【AI司令部：全セクター統合レーダー】\n市場環境: {market_env}\n--------------------\n"
    signals = []

    for sector, info in portfolio.items():
        s_ma, l_ma = info["params"]
        for ticker in info["tickers"]:
            df = yf.Ticker(ticker).history(period="100d")
            if len(df) < l_ma + 2: continue
            df['SMA_S'] = df['Close'].rolling(window=s_ma).mean()
            df['SMA_L'] = df['Close'].rolling(window=l_ma).mean()
            yday, today = df.iloc[-2], df.iloc[-1]
            if yday['SMA_S'] <= yday['SMA_L'] and today['SMA_S'] > today['SMA_L']:
                signals.append(f"🚀 【買】 {ticker} ({sector})")
            elif yday['SMA_S'] >= yday['SMA_L'] and today['SMA_S'] < today['SMA_L']:
                signals.append(f"⚠️ 【売】 {ticker} ({sector})")

    msg += "\n".join(signals) if signals else "本日の新規シグナルはありませんでした。"
    msg += "\n--------------------\nスキャン完了。明日の戦略に備えてください。"
    return msg

if __name__ == "__main__":
    result = scan_markets()
    send_line_message(result)
