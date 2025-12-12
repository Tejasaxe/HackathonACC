import yfinance as yf
import pandas as pd

def get_raw_data(ticker_symbol):
    """
    Fetches raw dataframes for the stock and the market (SPY).
    """
    try:
        stock = yf.Ticker(ticker_symbol)
        
        # 1. Price History (Extended to 2y for better Beta calculation)
        stock_history = stock.history(period="2y")
        
        # 2. Market History (SPY) for Benchmarking
        spy = yf.Ticker("SPY")
        market_history = spy.history(period="2y")
        
        # 3. Financial Statements
        balance_sheet = stock.balance_sheet
        cash_flow = stock.cashflow
        income_stmt = stock.financials
        
        # 4. Basic Info
        info = stock.info

        if stock_history.empty:
            return None

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
        print(f"Error: {e}")
        return None