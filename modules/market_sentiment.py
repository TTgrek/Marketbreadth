import yfinance as yf
import pandas as pd
import numpy as np

# 🔹 Hämta data från Yahoo Finance och fixa formatet
def fetch_data():
    ticker = "QQQ"
    try:
        # Hämta data
        data = yf.download(ticker, start="1999-03-10")
        if data.empty:
            print("❌ Ingen data hämtades från Yahoo Finance!")
            return pd.DataFrame()

        data.reset_index(inplace=True)

        # 🔹 Hantera problem där Yahoo Finance skapar extra kolumnnivå
        if isinstance(data.columns, pd.MultiIndex):
            data.columns = data.columns.droplevel(0)  # Ta bort översta header-raden

        # 🔹 Rätta kolumnnamn om de har blivit omdöpta av yfinance
        correct_columns = ["Date", "Open", "High", "Low", "Close", "Adj Close", "Volume"]
        if len(data.columns) == len(correct_columns):
            data.columns = correct_columns

        # Kontrollera om "Close" nu finns
        if "Close" not in data.columns:
            print("❌ 'Close' saknas i datan! Här är kolumnerna:", data.columns)
            return pd.DataFrame()

        # Lägg till indikatorer
        data["MA20"] = data["Close"].rolling(window=20).mean()
        data["Cycle Peak"] = np.where((data["High"] == data["High"].rolling(50, center=True).max()), data["High"], np.nan)
        data["Cycle Bottom"] = np.where((data["Low"] == data["Low"].rolling(50, center=True).min()), data["Low"], np.nan)

        return data.dropna(subset=["Close"])  # Ta bort eventuella NaN-värden

    except Exception as e:
        print(f"⚠️ Fel vid hämtning av data: {e}")
        return pd.DataFrame()

# 🔹 Testa att hämta data
data = fetch_data()
print(data.head())  # Skriver ut de första raderna för att se om datan laddas korrekt
