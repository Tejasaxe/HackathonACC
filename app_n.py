import streamlit as st
import pandas as pd
import plotly.graph_objects as go
from plotly.subplots import make_subplots

# IMPORT YOUR MODULES
from fetch_data import get_raw_data
from analysis import run_quant_analysis

# --- 1. SETUP: PROFESSIONAL UI CONFIG ---
st.set_page_config(
    page_title="Quant Vibe Terminal", 
    layout="wide",  # Use full screen width
    initial_sidebar_state="expanded"
)

# --- 2. DATA SOURCE: THE "UNIVERSE" ---
@st.cache_data
def load_sp500_tickers():
    """
    Fetches a live list of S&P 500 companies from Wikipedia/GitHub.
    """
    try:
        url = "https://raw.githubusercontent.com/datasets/s-and-p-500-companies/master/data/constituents.csv"
        df = pd.read_csv(url)
        
        # FIX: The CSV uses "GICS Sector", so we rename it to just "Sector"
        # to match the rest of our code.
        if 'GICS Sector' in df.columns:
            df.rename(columns={'GICS Sector': 'Sector'}, inplace=True)
            
        return df
    except Exception as e:
        st.error(f"Error loading data: {e}")
        # Fallback data so the app doesn't crash
        return pd.DataFrame([
            {"Symbol": "AAPL", "Name": "Apple Inc.", "Sector": "Information Technology"},
            {"Symbol": "MSFT", "Name": "Microsoft Corp", "Sector": "Information Technology"},
            {"Symbol": "NVDA", "Name": "NVIDIA Corp", "Sector": "Information Technology"},
        ])

@st.cache_data
def load_data(ticker):
    raw_data = get_raw_data(ticker)
    if raw_data:
        analysis = run_quant_analysis(raw_data)
        return raw_data, analysis
    return None, None

# --- 3. STATE MANAGEMENT ---
if 'selected_ticker' not in st.session_state:
    st.session_state.selected_ticker = None

# --- 4. SIDEBAR: FILTERS & NAVIGATION ---
st.sidebar.title("🔍 Market Screener")

# Load the "Universe"
df_tickers = load_sp500_tickers()

# Feature: Filter by Sector
all_sectors = sorted(df_tickers['Sector'].unique().tolist())
selected_sector = st.sidebar.selectbox("Filter by Sector", ["All"] + all_sectors)

# Apply Filter
if selected_sector != "All":
    filtered_df = df_tickers[df_tickers['Sector'] == selected_sector]
else:
    filtered_df = df_tickers

# --- 5. MAIN PAGE LOGIC ---

# === VIEW 1: THE SCREENER (List of Companies) ===
if st.session_state.selected_ticker is None:
    st.title("🌎 Market Universe")
    st.markdown("Select a company to launch the **Deep Dive Analysis**.")

    # PROFESSIONAL TABLE
    # st.dataframe allows built-in Sorting (click headers) and Search (Cmd+F)
    # We add a 'Select' mechanism
    
    col1, col2 = st.columns([3, 1])
    with col1:
        st.dataframe(
            filtered_df, 
            use_container_width=True, 
            height=600,
            hide_index=True
        )
    with col2:
        st.info("👆 Use the table to find a Ticker.")
        st.write("### Quick Select")
        # Dropdown to actually pick the stock
        ticker_input = st.selectbox("Choose Ticker to Analyze:", filtered_df['Symbol'].tolist())
        
        if st.button("🚀 Launch Analysis", type="primary"):
            st.session_state.selected_ticker = ticker_input
            st.rerun()

# === VIEW 2: THE DASHBOARD (Detail View) ===
else:
    ticker = st.session_state.selected_ticker
    
    # Navigation Header
    col_nav1, col_nav2 = st.columns([1, 10])
    with col_nav1:
        if st.button("⬅ List"):
            st.session_state.selected_ticker = None
            st.rerun()
    with col_nav2:
        st.markdown(f"## {ticker} Analysis")

    with st.spinner(f"Crunching numbers for {ticker}..."):
        raw_data, analysis = load_data(ticker)

    if raw_data and analysis:
        info = raw_data['info']
        
        # --- HERO SECTION (Price & Vibe) ---
        # Using a container to group the top level metrics with a background
        with st.container():
            kpi1, kpi2, kpi3, kpi4, kpi5 = st.columns(5)
            
            # Helper for color formatting
            def color_val(val):
                return "green" if val > 0 else "red"

            kpi1.metric("Current Price", f"${info.get('currentPrice', 0):.2f}")
            kpi2.metric("Market Cap", f"${info.get('marketCap', 0)/1e9:.1f}B")
            kpi3.metric("Beta (Risk)", analysis['metrics']['Beta'])
            kpi4.metric("CAPM Exp. Return", analysis['metrics']['Expected Return (CAPM)'])
            kpi5.metric("Vibe Signal", analysis['metrics']['Signal'])

        st.divider()

        # --- ADVANCED CHARTING (Plotly) ---
        # We switch to Plotly for the "Blue Line" and Pro look
        
        # Create a subplot with 2 rows (Price on top, Volume/RSI potential on bottom)
        fig = make_subplots(rows=2, cols=1, shared_xaxes=True, 
                            vertical_spacing=0.05, row_heights=[0.7, 0.3])

        # 1. Candlestick Chart (Real Pro Mode) - OR Simple Blue Line as requested
        # Let's do the Blue Line but make it look premium
        history = analysis['history'].tail(252) # Last year
        
        fig.add_trace(go.Scatter(
            x=history.index, 
            y=history['Close'], 
            name='Price',
            line=dict(color='#0096FF', width=2) # <--- THE BLUE COLOR YOU WANTED
        ), row=1, col=1)

        # 2. Add SMAs
        fig.add_trace(go.Scatter(
            x=history.index, y=history['SMA_50'], name='SMA 50',
            line=dict(color='orange', width=1)
        ), row=1, col=1)
        fig.add_trace(go.Scatter(
            x=history.index, y=history['SMA_200'], name='SMA 200',
            line=dict(color='gray', width=1, dash='dot')
        ), row=1, col=1)

        # 3. Volume Bar Chart
        fig.add_trace(go.Bar(
            x=history.index, y=history['Volume'], name='Volume',
            marker_color='rgba(200, 200, 200, 0.5)'
        ), row=2, col=1)

        # Layout Update
        fig.update_layout(
            title=f"{ticker} Price Action & Technicals",
            xaxis_rangeslider_visible=False,
            height=600,
            template="plotly_dark", # <--- DARK MODE CHART
            margin=dict(l=20, r=20, t=50, b=20)
        )
        
        st.plotly_chart(fig, use_container_width=True)

        # --- FUNDAMENTALS & INFO ---
        col_fund1, col_fund2 = st.columns(2)
        
        with col_fund1:
            st.subheader("📊 Fundamental Health")
            df_fund = pd.DataFrame([
                {"Metric": "Trailing P/E", "Value": info.get('trailingPE')},
                {"Metric": "Forward P/E", "Value": info.get('forwardPE')},
                {"Metric": "PEG Ratio", "Value": info.get('pegRatio')},
                {"Metric": "Debt/Equity", "Value": analysis['fundamentals']['Debt/Equity Ratio']},
                {"Metric": "Free Cash Flow", "Value": analysis['fundamentals']['Free Cash Flow']},
            ])
            st.dataframe(df_fund, hide_index=True, use_container_width=True)

        with col_fund2:
            st.subheader("🏢 Company Profile")
            st.write(f"**Sector:** {info.get('sector')}")
            st.write(f"**Industry:** {info.get('industry')}")
            st.caption(info.get('longBusinessSummary', "No summary available."))

    else:
        st.error("Data unavailable. Please check the ticker.")