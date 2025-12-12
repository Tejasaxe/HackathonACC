import streamlit as st
# IMPORT YOUR FILE HERE
from fetch_data import get_company_details 

st.set_page_config(page_title="Vibe Coding Dashboard", layout="centered")

# --- CONFIGURATION & CACHING ---
# We wrap your function with Streamlit's cache so it's fast
@st.cache_data
def load_data(ticker):
    return get_company_details(ticker)

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
        # CALL YOUR IMPORTED FUNCTION HERE
        data = load_data(ticker)

    if data:
        st.title(f"{data['name']} ({data['symbol']})")
        
        # Metrics
        c1, c2, c3 = st.columns(3)
        c1.metric("Price", f"${data['current_price']:.2f}")
        c2.metric("P/E", f"{data['pe_ratio']}" if data['pe_ratio'] else "N/A")
        c3.metric("Sector", data['sector'])

        st.divider()

        # Chart
        st.subheader("Price History")
        st.line_chart(data['history']['Close'])

        # Summary
        st.info(data['summary'])
    else:
        st.error("Could not fetch data for this company.")