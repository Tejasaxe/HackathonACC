import yfinance as yf
import pandas as pd

def get_company_details(ticker_symbol):
    """
    Fetches all data needed for the dashboard.
    Returns a dictionary or None if error.
    """
    try:
        # 1. Fetch Ticker
        stock = yf.Ticker(ticker_symbol)
        info = stock.info
        
        # 2. Fetch History (1 Year)
        history = stock.history(period="1y")
        
        # 3. Handle Missing Data gracefully
        if history.empty:
            return None

        # 4. Construct the Data Package
        data_package = {
            "symbol": ticker_symbol.upper(),
            "name": info.get('longName', ticker_symbol),
            "current_price": info.get('currentPrice', history['Close'].iloc[-1]), # Fallback to last close
            "pe_ratio": info.get('trailingPE'),
            "sector": info.get('sector', "Unknown"),
            "summary": info.get('longBusinessSummary', "No summary available."),
            "history": history
        }
        
        return data_package

    except Exception as e:
        print(f"Error fetching data: {e}")
        return None