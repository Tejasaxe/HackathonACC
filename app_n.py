import streamlit as st
import pandas as pd
# IMPORT YOUR MODULES
from fetch_data import get_raw_data
from analysis import run_quant_analysis

st.set_page_config(page_title="Vibe Coding Dashboard", layout="centered")

# --- CONFIGURATION & CACHING ---
# We wrap the data fetching in cache so navigating doesn't re-download everything
@st.cache_data
def load_data(ticker):
    raw_data = get_raw_data(ticker)
    if raw_data:
        # Run the analysis immediately after fetching
        analysis = run_quant_analysis(raw_data)
        return raw_data, analysis
    return None, None

# --- LIST OF COMPANIES ---
TOP_10_COMPANIES = [
    {"ticker": "AAPL", "name": "Apple Inc."},
    {"ticker": "MSFT", "name": "Microsoft Corp."},
    {"ticker": "NVDA", "name": "NVIDIA Corp."},
    {"ticker": "GOOGL", "name": "Alphabet Inc."},
    {"ticker": "AMZN", "name": "Amazon.com Inc."},
    {"ticker": "META", "name": "Meta Platforms"},
    {"ticker": "TSLA", "name": "Tesla, Inc."},
    {"ticker": "BRK-B", "name": "Berkshire Hathaway"},
    {"ticker": "LLY", "name": "Eli Lilly and Co."},
    {"ticker": "AVGO", "name": "Broadcom Inc."}
]

# --- APP LOGIC ---
if 'selected_ticker' not in st.session_state:
    st.session_state.selected_ticker = None

def go_back():
    st.session_state.selected_ticker = None

def select_company(ticker):
    st.session_state.selected_ticker = ticker

# --- PAGE 1: LIST VIEW ---
if st.session_state.selected_ticker is None:
    st.title("📈 Market Vibe Check")
    st.write("Pick a company to analyze:")
    
    for company in TOP_10_COMPANIES:
        if st.button(f"🔍 {company['name']} ({company['ticker']})", use_container_width=True):
            select_company(company['ticker'])
            st.rerun()

# --- PAGE 2: DETAIL VIEW ---
else:
    ticker = st.session_state.selected_ticker
    
    if st.button("← Back to List"):
        go_back()
        st.rerun()

    with st.spinner(f"Fetching data for {ticker}..."):
        # Load both raw data and the calculated analysis
        raw_data, analysis = load_data(ticker)

    if raw_data and analysis:
        # Extract basic info for the header
        info = raw_data['info']
        name = info.get('shortName', ticker)
        current_price = info.get('currentPrice', 0)
        sector = info.get('sector', 'Unknown')
        
        st.title(f"{name} ({ticker})")
        
        # --- SECTION 1: HEADER METRICS ---
        c1, c2, c3 = st.columns(3)
        c1.metric("Price", f"${current_price:.2f}")
        c2.metric("P/E Ratio", f"{info.get('trailingPE', 'N/A')}")
        c3.metric("Sector", sector)

        st.divider()

        # --- SECTION 2: QUANT SCORECARD (The New Analysis) ---
        st.subheader("⚡ Quant Scorecard")
        
        m1, m2, m3, m4 = st.columns(4)
        m1.metric("Beta", analysis['metrics']['Beta'], help=">1 means volatile")
        m2.metric("Volatility", analysis['metrics']['Volatility (Ann.)'])
        m3.metric("CAPM Return", analysis['metrics']['Expected Return (CAPM)'])
        m4.metric("Signal", analysis['metrics']['Signal'])

        st.divider()

        # --- SECTION 3: TECHNICAL CHART (SMA) ---
        st.subheader("Technical Analysis")
        st.caption("White: Price | Green: SMA-50 | Red: SMA-200")
        
        # Prepare data for plotting
        # We slice the last 1 year to keep the chart readable
        chart_df = analysis['history'][['Close', 'SMA_50', 'SMA_200']].tail(252)
        st.line_chart(chart_df, color=["#ffffff", "#00ff00", "#ff0000"]) 

        st.divider()

        # --- SECTION 4: FUNDAMENTALS ---
        st.subheader("Fundamental Health")
        f1, f2 = st.columns(2)
        f1.metric("Free Cash Flow", analysis['fundamentals']['Free Cash Flow'])
        f2.metric("Debt/Equity Ratio", analysis['fundamentals']['Debt/Equity Ratio'])

        # --- SECTION 5: SUMMARY ---
        st.divider()
        st.subheader("About")
        st.info(info.get('longBusinessSummary', "No summary available."))
        
    else:
        st.error("Could not fetch data for this company. It might be delisted or the API is down.")