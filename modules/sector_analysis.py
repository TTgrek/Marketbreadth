import streamlit as st
import yfinance as yf

def show():
    st.title("📊 Sektoranalys")
    
    # Lista av ETF:er för olika sektorer
    sectors = {
        "Tech": "XLK",
        "Healthcare": "XLV",
        "Energy": "XLE",
        "Financials": "XLF",
        "Industrials": "XLI",
        "Consumer Discretionary": "XLY"
    }
    
    sector_data = {}
    
    # Hämta data för varje sektor
    for name, ticker in sectors.items():
        df = yf.download(ticker, start="1999-03-10")["Close"]
        sector_data[name] = df

    # Skapa DataFrame med alla sektorer
    st.line_chart(sector_data)
    st.dataframe(sector_data)
