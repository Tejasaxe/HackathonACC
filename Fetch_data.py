import yfinance as yf
import pandas as pd

def fetch_company_data(ticker_symbol):
    """
    Fetches key KPIs and historical data for a given ticker.
    Returns a dictionary containing all necessary data for the dashboard.
    """
    print(f"--- Fetching data for {ticker_symbol}... ---")
    
    # 1. Initialize the Ticker object
    stock = yf.Ticker(ticker_symbol)
    
    # 2. Get Fundamental Info (The "Vitals")
    # yfinance returns a big dictionary in .info, we pick just what we need
    info = stock.info
    
    # Safely get data (using .get() prevents crashing if data is missing)
    current_price = info.get('currentPrice')
    sector = info.get('sector')
    industry = info.get('industry')
    pe_ratio = info.get('trailingPE')
    market_cap = info.get('marketCap')
    summary = info.get('longBusinessSummary')
    
    # 3. Get Historical Data (The "Timeline")
    # We need the last 1 year (approx 252 trading days) to calculate things like
    # the 200-day Moving Average for our Buy/Sell logic later.
    history = stock.history(period="1y")
    
    # 4. Bundle it all into one 'Vibe' variable
    company_vibe = {
        "symbol": ticker_symbol.upper(),
        "current_price": current_price,
        "pe_ratio": pe_ratio,
        "sector": sector,
        "industry": industry,
        "market_cap": market_cap,
        "summary": summary,
        "history_df": history  # Storing the actual DataFrame here for math later
    }
    
    return company_vibe

# --- MAIN EXECUTION ---
if __name__ == "__main__":
    # We choose Apple (AAPL) for this prototype
    target_ticker = "AAPL"
    
    # This variable 'vibe_data' now holds EVERYTHING we need
    vibe_data = fetch_company_data(target_ticker)
    
    # Let's inspect what we captured
    print(f"\n✅ Data Successfully Fetched for {vibe_data['symbol']}")
    print(f"   Price: ${vibe_data['current_price']}")
    print(f"   Sector: {vibe_data['sector']}")
    print(f"   P/E Ratio: {vibe_data['pe_ratio']}")
    
    print("\n📊 Recent History (Last 5 days):")
    print(vibe_data['history_df'].tail())