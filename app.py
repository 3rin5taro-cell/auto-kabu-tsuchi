import streamlit as st
import yfinance as yf
import pandas as pd
import datetime

# 🎨 アプリの基本設定（全画面表示・タイトル）
st.set_page_config(page_title="AI Sniper Dashboard", layout="wide", page_icon="🎯")
st.title("🎯 AI Sniper Dashboard")

# 📱 左側のサイドバー（メニュー）
st.sidebar.header("メニュー")
menu = st.sidebar.radio("移動先", ["📊 ポートフォリオ監視", "📡 新規獲物レーダー"])

# 🧠 AI分析エンジン（MACD計算用）
def get_macd(df, fast=15, slow=50):
    df['EMA_F'] = df['Close'].ewm(span=fast, adjust=False).mean()
    df['EMA_S'] = df['Close'].ewm(span=slow, adjust=False).mean()
    df['MACD'] = df['EMA_F'] - df['EMA_S']
    df['Sig'] = df['MACD'].ewm(span=9, adjust=False).mean()
    return df

# ==========================================
# 画面1：ポートフォリオ監視（ディスコ ＆ 三菱商事）
# ==========================================
if menu == "📊 ポートフォリオ監視":
    st.header("📈 現在の陣容と動的売却シグナル")
    
    # 画面を左右2つに分割
    col1, col2 = st.columns(2)
    
    # ⚔️ 左画面：ディスコ（トレーリングストップ戦略）
    with col1:
        st.subheader("⚔️ ディスコ (6146.T)")
        st.caption("戦略: メガトレンド追従 (-25% トレーリングストップ)")
        
        # 4/13以降のデータを取得
        df_disco = yf.Ticker("6146.T").history(start="2026-04-13")
        if not df_disco.empty:
            current_price = df_disco['Close'].iloc[-1]
            highest_price = df_disco['Close'].max()
            stop_line = highest_price * 0.75 # -25%
            
            # 数値の表示
            st.metric(label="現在の株価", value=f"{current_price:,.0f}円", delta=f"防衛ラインまで: {(current_price - stop_line):,.0f}円")
            
            # AI判定
            if current_price > stop_line:
                st.success("🍏 判定：ガチホ推奨（トレンド継続中）")
            else:
                st.error("🚨 判定：防衛ライン突破（即売却！）")
            
            # 直感的なメーター表示
            buffer_pct = max(0, min(100, (current_price - stop_line) / stop_line * 100))
            st.progress(int(buffer_pct))
            st.write(f"最高値基準: {highest_price:,.0f}円")

    # 🏢 右画面：三菱商事（MACDデッドクロス戦略）
    with col2:
        st.subheader("🏢 三菱商事 (8058.T)")
        st.caption("戦略: サイクル波乗り (MACD 15/50 監視)")
        
        df_mitsu = yf.Ticker("8058.T").history(period="150d")
        if not df_mitsu.empty:
            df_mitsu = get_macd(df_mitsu, 15, 50)
            yday, today = df_mitsu.iloc[-2], df_mitsu.iloc[-1]
            
            current_price = today['Close']
            st.metric(label="現在の株価", value=f"{current_price:,.0f}円", delta=f"MACD値: {today['MACD']:.1f}")
            
            # AI判定
            if yday['MACD'] > yday['Sig'] and today['MACD'] <= today['Sig']:
                st.error("⚠️ 判定：デッドクロス発生（利確実行！）")
            elif today['MACD'] > today['Sig']:
                st.success("🍏 判定：上昇トレンド継続中（利確準備）")
            else:
                st.warning("📉 判定：下落トレンド中（手出し無用）")

# ==========================================
# 画面2：新規獲物レーダー
# ==========================================
elif menu == "📡 新規獲物レーダー":
    st.header("🔥 本日の激アツ銘柄（MACDゴールデンクロス）")
    st.write("主要銘柄の過去150日データをスキャンし、本日『買いサイン』が出たものをリストアップします。")
    
    # スキャン対象（今後、日経225銘柄などに増やせます）
    watch_list = {"8035.T": "東エレクトロン", "8306.T": "三菱UFJ", "9984.T": "ソフトバンクG", "7203.T": "トヨタ", "7011.T": "三菱重工"}
    
    found = False
    for ticker, name in watch_list.items():
        df = yf.Ticker(ticker).history(period="150d")
        if len(df) > 50:
            df = get_macd(df, 15, 50)
            yday, today = df.iloc[-2], df.iloc[-1]
            
            if yday['MACD'] <= yday['Sig'] and today['MACD'] > today['Sig'] and today['MACD'] < 0:
                st.info(f"🚀 {name} ({ticker}) : 大底ゴールデンクロス発生！")
                found = True
                
    if not found:
        st.write("本日は新規の買いシグナルは検出されませんでした。キャッシュ（現金）を温存してください。")
