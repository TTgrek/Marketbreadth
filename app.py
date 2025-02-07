import streamlit as st
import modules.market_sentiment as market_sentiment
import modules.risk_on_off as risk_on_off
import modules.sector_analysis as sector_analysis

# 🔹 Skapa en sidomeny
st.sidebar.title("📊 Trading Analys")
selected_module = st.sidebar.radio("Välj analys:", [
    "Market Sentiment",
    "Risk ON/OFF",
    "Sector Leaders"
])

# 🔹 Ladda rätt modul baserat på val
if selected_module == "Market Sentiment":
    market_sentiment.show()
elif selected_module == "Risk ON/OFF":
    risk_on_off.show()
elif selected_module == "Sector Leaders":
    sector_analysis.show()
