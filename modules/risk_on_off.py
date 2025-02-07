import streamlit as st
import pandas as pd
import yfinance as yf

def show():
    st.title("⚖️ Risk ON/OFF Modell")
    
    # Hämta QQQ-data
    ticker = "QQQ"
    data = yf.download(ticker, start="1999-03-10")
    
    # Skapa Risk Score baserat på MA-struktur
    data["MA10"] = data["Close"].rolling(window=10).mean()
    data["MA20"] = data["Close"].rolling(window=20).mean()
    data["MA50"] = data["Close"].rolling(window=50).mean()
    data["MA200"] = data["Close"].rolling(window=200).mean()

    def risk_signal(row):
        if row["MA10"] > row["MA20"] > row["MA50"] > row["MA200"]:
            return "RISK ON"
        else:
            return "RISK OFF"

    data["Risk Signal"] = data.apply(risk_signal, axis=1)

    # Visa tabell och statistik
    st.write("**Risk ON/OFF per dag**")
    st.line_chart(data["Risk Signal"].astype("category").cat.codes)
    st.dataframe(data[["Date", "Close", "Risk Signal"]])
