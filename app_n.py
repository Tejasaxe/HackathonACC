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
    layout="wide",
    initial_sidebar_state="collapsed" # Collapsed for a cleaner entry
)

# --- 2. DATA UNIVERSE (S&P 500 Rich Data) ---
@st.cache_data
def load_universe_data():
    """
    Fetches S&P 500 data which includes 'Founded' and 'Location' metadata.
    We synthesize 'Continent' and 'Markets' since this is a US-heavy list.
    """
    try:
        url = "https://raw.githubusercontent.com/datasets/s-and-p-500-companies/master/data/constituents.csv"
        df = pd.read_csv(url)
        
        # 1. Standardize Column Names
        # The CSV comes with: Symbol, Security, GICS Sector, GICS Sub-Industry, Headquarters Location, Founded
        df = df.rename(columns={
            "Symbol": "Ticker",
            "Security": "Name",
            "GICS Sector": "Sector",
            "GICS Sub-Industry": "Sub-Sector",
            "Headquarters Location": "Location",
            "Founded": "Founded Date"
        })
        
        # 2. Enrich Data (Vibe Check)
        # S&P 500 is almost entirely North America / US Markets
        df["Continent"] = "North America" 
        df["Traded Markets"] = "NYSE / NASDAQ"
        
        return df
    except Exception as e:
        st.error(f"Data Connection Failed: {e}")
        return pd.DataFrame()

@st.cache_data
def load_analysis(ticker):
    raw = get_raw_data(ticker)
    if raw:
        return raw, run_quant_analysis(raw)
    return None, None

# --- 3. MAIN LOGIC ---

# Load Data
df_universe = load_universe_data()

# Initialize Session State
if 'selected_ticker' not in st.session_state:
    st.session_state.selected_ticker = None

# --- VIEW 1: THE SEARCH GRID ---
if st.session_state.selected_ticker is None:
    st.title("⚡ Market Terminal")
    st.caption("Select a company from the grid to launch deep analysis.")

    # --- FILTER BAR ---
    c1, c2, c3 = st.columns([2, 2, 1])
    with c1:
        # Search Box logic
        search_query = st.text_input("Search Ticker or Name", placeholder="e.g. Nvidia...")
    with c2:
        sector_filter = st.selectbox("Filter Sector", ["All Sectors"] + sorted(df_universe['Sector'].unique().tolist()))
    
    # Apply Filters
    filtered_df = df_universe.copy()
    if sector_filter != "All Sectors":
        filtered_df = filtered_df[filtered_df['Sector'] == sector_filter]
    
    if search_query:
        # Fuzzy search in Ticker OR Name
        filtered_df = filtered_df[
            filtered_df['Ticker'].str.contains(search_query.upper()) | 
            filtered_df['Name'].str.contains(search_query, case=False)
        ]

    # --- INTERACTIVE DATA TABLE ---
    # This is where the magic happens. We configure the table to act like a navigation menu.
    
    selection = st.dataframe(
        filtered_df,
        column_order=["Ticker", "Name", "Sector", "Sub-Sector", "Location", "Founded Date"],
        column_config={
            "Ticker": st.column_config.TextColumn("Ticker", help="Stock Symbol"),
            "Name": st.column_config.TextColumn("Company Name", width="medium"),
            "Sector": st.column_config.TextColumn("Sector", width="small"),
            "Sub-Sector": st.column_config.TextColumn("Industry", width="medium"),
            "Location": st.column_config.TextColumn("City/State", width="medium"),
            "Founded Date": st.column_config.TextColumn("Founded", width="small"),
        },
        use_container_width=True,
        hide_index=True,
        height=600,
        on_select="rerun",     # <--- TRIGGERS REFRESH ON CLICK
        selection_mode="single-row" # <--- ONLY ONE ROW ALLOWED
    )

    # CHECK SELECTION
    if selection.selection.rows:
        # Get the index of the selected row
        selected_index = selection.selection.rows[0]
        # Get the actual ticker from our filtered dataframe
        ticker_symbol = filtered_df.iloc[selected_index]['Ticker']
        
        st.session_state.selected_ticker = ticker_symbol
        st.rerun()

    # Manual Override (If they want to type a ticker not in the list)
    with st.expander("Not in the list? Search any ticker manually"):
        manual_ticker = st.text_input("Enter Ticker Symbol", max_chars=5)
        if st.button("Analyze Manual Ticker"):
            st.session_state.selected_ticker = manual_ticker.upper()
            st.rerun()

# --- VIEW 2: THE DEEP DIVE DASHBOARD ---
else:
    ticker = st.session_state.selected_ticker
    
    # Navbar
    with st.container():
        c_nav1, c_nav2 = st.columns([1, 10])
        with c_nav1:
            if st.button("⬅ Back", use_container_width=True):
                st.session_state.selected_ticker = None
                st.rerun()
        with c_nav2:
            st.markdown(f"## {ticker} Analysis")
            
    # Load Data
    with st.spinner(f"Analyzing {ticker}..."):
        raw_data, analysis = load_analysis(ticker)

    if raw_data and analysis:
        info = raw_data['info']
        metrics = analysis['metrics']
        
        # --- TOP LEVEL METRICS ---
        with st.container():
            # We use custom HTML/CSS cards for a "floating" vibe? 
            # Let's stick to Streamlit native for speed, but laid out cleanly.
            k1, k2, k3, k4 = st.columns(4)
            k1.metric("Price", f"${info.get('currentPrice', 0):.2f}", 
                      delta=f"{info.get('recommendationKey', '').upper()}")
            k2.metric("Beta", metrics['Beta'], help="Market Risk (1.0 = Market)")
            k3.metric("Exp. Return (CAPM)", metrics['Expected Return (CAPM)'])
            k4.metric("Vibe Signal", metrics['Signal'], 
                      delta_color="normal" if "HOLD" in metrics['Signal'] else "inverse")

        st.divider()

        # --- PLOTLY CHART (BLUE LINE) ---
        hist = analysis['history'].tail(300)
        
        fig = make_subplots(rows=2, cols=1, shared_xaxes=True, 
                            vertical_spacing=0.03, row_heights=[0.75, 0.25])

        # Price Line (Neon Blue)
        fig.add_trace(go.Scatter(
            x=hist.index, y=hist['Close'], name='Price',
            line=dict(color='#00CCFF', width=2.5) # Neon Blue
        ), row=1, col=1)

        # SMAs
        fig.add_trace(go.Scatter(x=hist.index, y=hist['SMA_50'], name='SMA 50', line=dict(color='#00FF00', width=1)), row=1, col=1)
        fig.add_trace(go.Scatter(x=hist.index, y=hist['SMA_200'], name='SMA 200', line=dict(color='#FF0055', width=1)), row=1, col=1)

        # Volume
        fig.add_trace(go.Bar(
            x=hist.index, y=hist['Volume'], name='Volume',
            marker_color='rgba(255, 255, 255, 0.2)'
        ), row=2, col=1)

        fig.update_layout(
            height=600,
            template="plotly_dark",
            paper_bgcolor='rgba(0,0,0,0)', # Transparent background
            plot_bgcolor='rgba(0,0,0,0)',
            hovermode="x unified",
            xaxis_rangeslider_visible=False,
            margin=dict(l=10, r=10, t=10, b=10)
        )
        st.plotly_chart(fig, use_container_width=True)

        # --- FUNDAMENTALS GRID ---
        st.subheader("📚 Fundamental Data")
        
        f_col1, f_col2 = st.columns([1, 1])
        with f_col1:
            # Table 1: Valuation
            df_val = pd.DataFrame({
                "Metric": ["Trailing P/E", "Forward P/E", "PEG Ratio", "Price/Book"],
                "Value": [info.get('trailingPE'), info.get('forwardPE'), info.get('pegRatio'), info.get('priceToBook')]
            })
            st.dataframe(df_val, hide_index=True, use_container_width=True)
            
        with f_col2:
             # Table 2: Health
            df_health = pd.DataFrame({
                "Metric": ["Free Cash Flow", "Debt/Equity", "Return on Equity", "Profit Margin"],
                "Value": [
                    analysis['fundamentals']['Free Cash Flow'], 
                    analysis['fundamentals']['Debt/Equity Ratio'],
                    f"{info.get('returnOnEquity', 0)*100:.2f}%",
                    f"{info.get('profitMargins', 0)*100:.2f}%"
                ]
            })
            st.dataframe(df_health, hide_index=True, use_container_width=True)

    else:
        st.error("Could not fetch data. The ticker might be delisted or API is busy.")