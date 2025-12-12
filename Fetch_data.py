import yfinance as yf
import pandas as pd
import streamlit as st

def get_raw_data(ticker_symbol):
    """
    Fetches raw dataframes for the stock and the market (SPY).
    Includes error handling and ticker sanitization.
    """
    # FIX: Yahoo Finance expects 'BRK-B' not 'BRK.B'
    if "." in ticker_symbol:
        ticker_symbol = ticker_symbol.replace(".", "-")

    print(f"--- Fetching data for {ticker_symbol} ---")
    
    try:
        stock = yf.Ticker(ticker_symbol)
        
        # 1. Price History (5 Years for Time Machine)
        # We allow a fallback if 5y fails, we try 1y
        try:
            stock_history = stock.history(period="5y")
            if stock_history.empty:
                print(f"Warning: No history found for {ticker_symbol}")
                return None
        except Exception as e:
            print(f"Error fetching history: {e}")
            return None
        
        # 2. Market History (SPY) for Benchmarking (CAPM)
        try:
            spy = yf.Ticker("SPY")
            market_history = spy.history(period="5y")
        except Exception as e:
            print(f"Warning: Could not fetch SPY data ({e}). CAPM will be approximate.")
            # Create dummy market data if SPY fails so app doesn't crash
            market_history = stock_history.copy()
            market_history['Close'] = 1.0 # Flat market assumption fallback
        
        # 3. Financial Statements (with error handling)
        try:
            balance_sheet = stock.balance_sheet
            cash_flow = stock.cashflow
            income_stmt = stock.financials
        except:
            balance_sheet = pd.DataFrame()
            cash_flow = pd.DataFrame()
            income_stmt = pd.DataFrame()
        
        # 4. Basic Info
        # yfinance .info can sometimes fail or timeout
        try:
            info = stock.info
        except:
            info = {"symbol": ticker_symbol} # Minimal fallback

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