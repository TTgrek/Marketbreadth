import streamlit as st
import pandas as pd
import yfinance as yf

def show():
    st.title("📈 Market Sentiment")
    
    # Hämta QQQ-data
    ticker = "QQQ"
    data = yf.download(ticker, start="1999-03-10")
    
    # Cycle Count
    data["Cycle Length"] = abs(data["Close"].diff().fillna(0))
    
    # Visa tabell och statistik
    st.write("**Snittlängd på cykler:**", round(data["Cycle Length"].mean(), 2))
    st.line_chart(data["Cycle Length"])
    st.dataframe(data)
