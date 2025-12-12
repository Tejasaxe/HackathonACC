import yfinance as yf
import pandas as pd
import streamlit as st

def get_raw_data(ticker_symbol):
    """
    Fetches raw dataframes for the stock and the market (SPY).
    Fully compatible with Global Markets (e.g., 'RELIANCE.NS', '0700.HK').
    """
    
    # 1. Ticker Sanitization
    # Yahoo Finance requires dashes for US dual-class stocks, but keeps dots for international suffixes.
    # We fix the specific known US edge cases from the S&P 500 list.
    if ticker_symbol == "BRK.B":
         ticker_symbol = "BRK-B"
    elif ticker_symbol == "BF.B":
         ticker_symbol = "BF-B"
    
    print(f"--- Fetching data for {ticker_symbol} ---")
    
    try:
        stock = yf.Ticker(ticker_symbol)
        
        # 2. Price History (Chart & Volatility)
        # We attempt to fetch 5 years of data for the 'Time Machine' and long-term charts.
        try:
            stock_history = stock.history(period="5y")
            
            # Fallback 1: If 5y is empty (e.g., recent IPO), try 1 year.
            if stock_history.empty:
                print(f"Warning: 5y history empty for {ticker_symbol}, trying 1y...")
                stock_history = stock.history(period="1y")
                
            # Fallback 2: If still empty, the ticker might be delisted or invalid.
            if stock_history.empty:
                print(f"Error: No history found for {ticker_symbol}")
                return None
        except Exception as e:
            print(f"Error fetching history: {e}")
            return None
        
        # 3. Market Benchmark (SPY)
        # We use SPY as a global proxy for 'Market Risk' to calculate Beta.
        # This ensures we always have a baseline, even for foreign stocks.
        try:
            spy = yf.Ticker("SPY")
            market_history = spy.history(period="5y")
        except Exception as e:
            print(f"Warning: Could not fetch SPY data ({e}). CAPM will be approximate.")
            # Fallback: Create a flat line 'market' so the app doesn't crash
            market_history = stock_history.copy()
            market_history['Close'] = 1.0 
        
        # 4. Financial Statements (Balance Sheet, Cash Flow)
        # Essential for Debt/Equity and Free Cash Flow metrics.
        try:
            balance_sheet = stock.balance_sheet
            cash_flow = stock.cashflow
            income_stmt = stock.financials
        except:
            # Create empty DFs if data is missing (common for small intl. stocks)
            balance_sheet = pd.DataFrame()
            cash_flow = pd.DataFrame()
            income_stmt = pd.DataFrame()
        
        # 5. Basic Info (P/E, Description, Sector)
        # The .info dictionary is rich but can occasionally timeout.
        try:
            info = stock.info
        except:
            info = {"symbol": ticker_symbol} # Minimal fallback to prevent crash

        # 6. Return the Bundle
        return {
            "symbol": ticker_symbol,
            "info": info,
            "stock_history": stock_history,
            "market_history": market_history,
            "balance_sheet": balance_sheet,
            "cash_flow": cash_flow,
            "income_stmt": income_stmt
        }

    except Exception as e:
        print(f"CRITICAL ERROR fetching {ticker_symbol}: {e}")
        return None