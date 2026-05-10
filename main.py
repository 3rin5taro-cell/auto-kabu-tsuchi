import yfinance as yf
import pandas as pd
import requests

# 🔐 接続情報
LINE_ACCESS_TOKEN = 'lCWTCD14m4G8Eh2aLzyV6Cf04oS/5dcb4A7FEwAs40ZXc+Hf6iCtCcr8WXmRSKoIpwLuy/hNWOM1YAmFImENKJOcE+a9d7vPXddS/K1IElbGVR2OX6+G4f5dDyTKy2Uq6xpF5T4YyFPjaR7VxvY6MQdB04t89/1O/w1cDnyilFU='
LINE_USER_ID = 'U393d1c3e45fb547fb0fd5c772f56df2a'

# 🎖️ 現在の保有ポジション（かぶミニ監視用）
active_positions = [
    {"ticker": "6146.T", "name": "ディスコ", "buy_price": 66827, "stop": 25},
    {"ticker": "8058.T", "name": "三菱商事", "buy_price": 5231, "stop": 20},
    {"ticker": "8001.T", "name": "伊藤忠", "buy_price": 2009, "stop": 20}
]

# 🗂️ 武器庫：指定パラメータ (MACD期間 / ストップ幅%)
portfolio = {
    "🏦 銀行": {"fast": 15, "slow": 50, "stop": 15, "tickers": ["8306.T", "8316.T", "8411.T", "8308.T", "8309.T", "7182.T", "8331.T"]},
    "⚔️ 半導体": {"fast": 10, "slow": 25, "stop": 25, "tickers": ["8035.T", "6857.T", "6146.T", "6723.T", "7735.T", "6920.T", "4063.T"]},
    "🏢 商社": {"fast": 15, "slow": 75, "stop": 75, "tickers": ["8058.T", "8001.T", "8031.T", "8002.T", "8053.T", "2768.T", "8015.T"]},
    "💣 重工": {"fast": 15, "slow": 50, "stop": 50, "tickers": ["7011.T", "7012.T", "7013.T", "6503.T", "6301.T", "7721.T", "7004.T"]}
}

def send_line_message(message):
    url = "https://api.line.me/v2/bot/message/push"
    headers = {"Content-Type": "application/json", "Authorization": f"Bearer {LINE_ACCESS_TOKEN}"}
    data = {"to": LINE_USER_ID, "messages": [{"type": "text", "text": message}]}
    requests.post(url, headers=headers, json=data)

def scan_markets():
    # 🌍 市場環境チェック
    n225 = yf.Ticker("^N225").history(period="100d")
    n225_75ma = n225['Close'].rolling(window=75).mean().iloc[-1]
    n225_close = n225['Close'].iloc[-1]
    market_env = "◎ 安全（上昇中）" if n225_close > n225_75ma else "▲ 警戒（停滞中）"
    
    msg = f"🌐 【AI司令部：統合マスターレーダー】\n市場環境: {market_env}\n--------------------\n"
    
    # 🚨 1. 保有株の緊急監視
    pos_msg = "📈 【保有株ステータス】\n"
    for pos in active_positions:
        try:
            ticker_data = yf.Ticker(pos["ticker"]).history(period="2d")
            current_price = ticker_data['Close'].iloc[-1]
            stop_line = pos["buy_price"] * (1 - pos["stop"] / 100)
            dist_to_stop = current_price - stop_line
            
            status_icon = "🍏 安泰" if dist_to_stop > 0 else "🚨 突破（即売却！）"
            pos_msg += f"・{pos['name']}: {current_price:.0f}円 ({status_icon})\n  └ 防衛ラインまで: {dist_to_stop:.0f}円\n"
        except:
            pos_msg += f"・{pos['name']}: データ取得エラー\n"
            
    msg += pos_msg + "--------------------\n"
    
    # 🏹 2. 全28銘柄スキャン
    signals = []
    for sector, config in portfolio.items():
        for ticker in config["tickers"]:
            try:
                df = yf.Ticker(ticker).history(period="150d")
                if len(df) < config["slow"]: continue 
                
                df['EMA_F'] = df['Close'].ewm(span=config["fast"], adjust=False).mean()
                df['EMA_S'] = df['Close'].ewm(span=config["slow"], adjust=False).mean()
                df['MACD'] = df['EMA_F'] - df['EMA_S']
                df['Sig'] = df['MACD'].ewm(span=9, adjust=False).mean()
                
                yday, today = df.iloc[-2], df.iloc[-1]
                
                if yday['MACD'] <= yday['Sig'] and today['MACD'] > today['Sig']:
                    icon = "🔥【激アツ買】" if today['MACD'] < 0 else "🚀【買】"
                    signals.append(f"{icon} {ticker} ({sector})\n   👉 損切目安: -{config['stop']}%")
                elif yday['MACD'] >= yday['Sig'] and today['MACD'] < today['Sig']:
                    signals.append(f"⚠️【手仕舞い】 {ticker} ({sector})")
            except:
                continue

    msg += "\n".join(signals) if signals else "新規の売買サインはありません。"
    msg += "\n--------------------\n監視完了。手動取引の判断にご活用ください。"
    return msg

if __name__ == "__main__":
    report = scan_markets()
    send_line_message(report)
