import pandas as pd
import requests
import io

def generate_sp500_csv():
    print("⏳ Fetching S&P 500 data from Wikipedia...")
    
    url = "https://en.wikipedia.org/wiki/List_of_S%26P_500_companies"
    
    # 1. THE FIX: Add a 'User-Agent' header so we look like a real browser
    headers = {
        "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/91.0.4472.124 Safari/537.36"
    }
    
    try:
        # 2. Fetch HTML content using requests
        response = requests.get(url, headers=headers)
        response.raise_for_status() # Check if request was successful
        
        # 3. Read HTML tables from the response text
        # io.StringIO is needed to treat the text string as a file object
        tables = pd.read_html(io.StringIO(response.text))
        
        # The first table is usually the S&P 500 list
        df = tables[0]
        
        # 4. Clean and Format Data
        df = df.rename(columns={
            "Symbol": "Ticker",
            "Security": "Name",
            "GICS Sector": "Sector",
            "GICS Sub-Industry": "Industry",
            "Headquarters Location": "Location"
        })
        
        # Parse Location (City, State)
        location_split = df['Location'].str.split(', ', n=1, expand=True)
        df['City'] = location_split[0]
        
        if 1 in location_split.columns:
            df['State'] = location_split[1]
        else:
            df['State'] = "N/A"
            
        # Fix Tickers (Wikipedia uses dots, Yahoo uses dashes)
        df['Ticker'] = df['Ticker'].str.replace('.', '-', regex=False)
        
        # Select Columns
        final_df = df[['Ticker', 'Name', 'Sector', 'Industry', 'City', 'State']]
        
        # Save
        final_df.to_csv("sp500.csv", index=False)
        
        print(f"✅ Success! 'sp500.csv' created with {len(final_df)} companies.")
        print(final_df.head(3))
        
    except Exception as e:
        print(f"❌ Error: {e}")

if __name__ == "__main__":
    generate_sp500_csv()