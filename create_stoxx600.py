import pandas as pd
import yfinance as yf
import requests
import time

def get_ticker_from_name(company_name):
    """
    Searches Yahoo Finance for a company name and returns the best Ticker.
    Prioritizes European listings (Paris, Frankfurt, London) for STOXX 600.
    """
    try:
        user_agent = {'User-Agent': 'Mozilla/5.0'}
        url = f"https://query2.finance.yahoo.com/v1/finance/search?q={company_name}"
        r = requests.get(url, headers=user_agent)
        data = r.json()
        
        quotes = data.get('quotes', [])
        if not quotes: return None
        
        # Logic: Look for European suffixes first (.DE, .PA, .L, .AS, .SW)
        # If none found, take the first Equity result.
        european_suffixes = ['.DE', '.PA', '.L', '.AS', '.SW', '.MI', '.MC', '.ST', '.CO', '.HE']
        
        for q in quotes:
            sym = q['symbol']
            if any(sym.endswith(suf) for suf in european_suffixes):
                return sym
                
        # Fallback: Just take the first Equity
        for q in quotes:
            if q.get('quoteType') == 'EQUITY':
                return q['symbol']
                
        return quotes[0]['symbol']
    except:
        return None

def build_stoxx_file():
    print("⏳ Reading 'stoxx_raw.csv'...")
    
    try:
        # Load the Investing.com file
        # Investing.com CSVs usually have a "Name" column
        df_raw = pd.read_csv("STOXX600.csv")
        
        if "Name" not in df_raw.columns:
            # Maybe it's "Company" or inside the first column?
            # Let's assume the first column is the name if "Name" is missing
            df_raw['Name'] = df_raw.iloc[:, 0]
        
        total_rows = len(df_raw)
        print(f"✅ Loaded {total_rows} companies. Starting enrichment...")
        print("☕ This will take a few minutes (fetching data for 540 companies)...")
        
        final_data = []
        
        # Loop through every company name
        for index, row in df_raw.iterrows():
            name = str(row['Name']).replace('"', '').strip()
            
            # 1. Find the Ticker
            ticker = get_ticker_from_name(name)
            
            if ticker:
                # 2. Fetch Sector/Industry/Country Details
                try:
                    stock = yf.Ticker(ticker)
                    # We use .info.get with 'fast_info' behavior or fallback
                    # Note: Fetching full .info is slow, but necessary for Sector/Country
                    info = stock.info
                    
                    data_row = {
                        "Ticker": ticker,
                        "Name": name,
                        "Sector": info.get('sector', 'N/A'),
                        "Industry": info.get('industry', 'N/A'),
                        "Country": info.get('country', 'N/A')
                    }
                    final_data.append(data_row)
                    
                    # Print progress every 10 stocks
                    if index % 10 == 0:
                        print(f"   [{index}/{total_rows}] Found: {name} -> {ticker} ({data_row['Country']})")
                        
                except Exception as e:
                    print(f"   ⚠️ Error fetching details for {ticker}")
            else:
                print(f"   ❌ Could not find ticker for: {name}")
                
            # Sleep slightly to avoid being blocked by Yahoo
            time.sleep(0.2)

        # 3. Save the final "Perfect" CSV
        df_final = pd.DataFrame(final_data)
        
        # Ensure we have the exact columns you asked for
        df_final = df_final[["Ticker", "Name", "Sector", "Industry", "Country"]]
        
        df_final.to_csv("stoxx600.csv", index=False)
        print("\n🎉 DONE! Created 'stoxx600.csv'.")
        print(df_final.head())
        
    except FileNotFoundError:
        print("❌ Error: Could not find 'stoxx_raw.csv' in this folder.")

if __name__ == "__main__":
    build_stoxx_file()