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
    initial_sidebar_state="collapsed"
)

# --- 2. DATA UNIVERSE (S&P 500 + Location Parsing) ---
@st.cache_data
def load_universe_data():
    """
    Fetches S&P 500 data and parses Location into City/State.
    """
    try:
        url = "https://raw.githubusercontent.com/datasets/s-and-p-500-companies/master/data/constituents.csv"
        df = pd.read_csv(url)
        
        # 1. Standardize Column Names
        df = df.rename(columns={
            "Symbol": "Ticker",
            "Security": "Name",
            "GICS Sector": "Sector",
            "GICS Sub-Industry": "Industry",
            "Headquarters Location": "Location"
        })
        
        # 2. Parse "Location" (Format: "City, State")
        location_split = df['Location'].str.split(', ', n=1, expand=True)
        df['City'] = location_split[0]
        df['State'] = location_split[1] if 1 in location_split.columns else None
        
        # Drop unnecessary columns
        df = df.drop(columns=['Location', 'Founded', 'CIK', 'Date added'], errors='ignore')
        
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

# --- NEW: SMART SUMMARY GENERATOR ---
def generate_smart_summary(info):
    name = info.get('shortName', 'The company')
    industry = info.get('industry', 'various sectors')
    city = info.get('city', 'Unknown City')
    country = info.get('country', 'Unknown Country')
    full_summary = info.get('longBusinessSummary', '')
    
    intro = f"**{name}** is a major player in the **{industry}** sector, based in **{city}, {country}**."
    
    if full_summary:
        sentences = full_summary.split('. ')
        short_desc = ". ".join(sentences[:2])
        if not short_desc.endswith('.'):
            short_desc += "."
    else:
        short_desc = "No detailed business description available."
        
    return f"{intro} {short_desc}"

# --- 3. MAIN LOGIC ---
df_universe = load_universe_data()

if 'selected_ticker' not in st.session_state:
    st.session_state.selected_ticker = None

# --- VIEW 1: THE SEARCH GRID ---
if st.session_state.selected_ticker is None:
    st.title("⚡ Market Terminal")
    st.caption("Select a company from the grid to launch deep analysis.")

    # --- DYNAMIC CASCADING FILTERS ---
    st.subheader("Filter Market")
    
    # 1. SECTOR FILTER
    available_sectors = sorted(df_universe['Sector'].dropna().unique())
    c1, c2, c3, c4 = st.columns(4)
    
    with c1:
        selected_sectors = st.multiselect("Sector", options=available_sectors, placeholder="All Sectors")
        df_step1 = df_universe[df_universe['Sector'].isin(selected_sectors)] if selected_sectors else df_universe

    # 2. INDUSTRY FILTER
    available_industries = sorted(df_step1['Industry'].dropna().unique())
    with c2:
        selected_industries = st.multiselect("Industry", options=available_industries, placeholder="All Industries")
        df_step2 = df_step1[df_step1['Industry'].isin(selected_industries)] if selected_industries else df_step1

    # 3. STATE FILTER
    available_states = sorted(df_step2['State'].dropna().unique())
    with c3:
        selected_states = st.multiselect("State", options=available_states, placeholder="All States")
        df_step3 = df_step2[df_step2['State'].isin(selected_states)] if selected_states else df_step2

    # 4. CITY FILTER
    available_cities = sorted(df_step3['City'].dropna().unique())
    with c4:
        selected_cities = st.multiselect("City", options=available_cities, placeholder="All Cities")
        filtered_df = df_step3[df_step3['City'].isin(selected_cities)] if selected_cities else df_step3

    # --- SEARCH OVERRIDE ---
    search_query = st.text_input("Search Ticker or Name", placeholder="e.g. Nvidia...")
    if search_query:
        filtered_df = filtered_df[
            filtered_df['Ticker'].str.contains(search_query.upper()) | 
            filtered_df['Name'].str.contains(search_query, case=False)
        ]

    st.markdown(f"**Found {len(filtered_df)} companies**")
    
    # --- INTERACTIVE DATA TABLE ---
    selection = st.dataframe(
        filtered_df,
        column_order=["Ticker", "Name", "Sector", "Industry", "City", "State"],
        column_config={
            "Ticker": st.column_config.TextColumn("Ticker", width="small"),
            "Name": st.column_config.TextColumn("Name", width="medium"),
            "Sector": st.column_config.TextColumn("Sector", width="medium"),
            "Industry": st.column_config.TextColumn("Industry", width="medium"),
            "City": st.column_config.TextColumn("City", width="small"),
            "State": st.column_config.TextColumn("State", width="small"),
        },
        use_container_width=True,
        hide_index=True,
        height=500,
        on_select="rerun",
        selection_mode="single-row"
    )

    if selection.selection.rows:
        selected_index = selection.selection.rows[0]
        ticker_symbol = filtered_df.iloc[selected_index]['Ticker']
        st.session_state.selected_ticker = ticker_symbol
        st.rerun()

# --- VIEW 2: THE DEEP DIVE DASHBOARD ---
else:
    ticker = st.session_state.selected_ticker
    
    with st.container():
        c_nav1, c_nav2 = st.columns([1, 10])
        with c_nav1:
            if st.button("⬅ Back", use_container_width=True):
                st.session_state.selected_ticker = None
                st.rerun()
        with c_nav2:
            st.markdown(f"## {ticker} Analysis")
            
    with st.spinner(f"Analyzing {ticker}..."):
        raw_data, analysis = load_analysis(ticker)

    if raw_data and analysis:
        info = raw_data['info']
        metrics = analysis['metrics']
        val = analysis['valuation']
        tm = analysis['time_machine']
        
        # --- SMART SUMMARY ---
        st.info(generate_smart_summary(info), icon="ℹ️")

        # --- THE VERDICT SECTION (New Layout) ---
        st.subheader("⚖️ The Verdict")
        
        # Top Row: Recommendation | Alpha Check (Prediction vs CAPM)
        v_col1, v_col2 = st.columns(2)
        
        # 1. Recommendation
        verdict_text = val['Verdict']
        if "BUY" in verdict_text: v_color = "normal" 
        elif "SELL" in verdict_text or "EXIT" in verdict_text: v_color = "inverse"
        else: v_color = "off"

        v_col1.metric("Recommendation", verdict_text, 
                      delta=metrics['Signal Desc'], delta_color=v_color)
        
        # 2. CAPM Alpha Check (Forecast vs Risk)
        # Calculate if Analyst Upside > CAPM Required Return
        upside = val['Upside']
        capm_req = float(metrics['Expected Return'].strip('%')) / 100
        
        is_beat = upside > capm_req
        alpha_gap = (upside - capm_req) * 100
        
        v_col2.metric("Prediction vs CAPM", 
                      f"{'Beats' if is_beat else 'Lags'} Risk Profile",
                      help=f"Analysts forecast {upside*100:.1f}% growth. CAPM requires {capm_req*100:.1f}% for this risk level.",
                      delta=f"{alpha_gap:+.1f}% Excess Return (Alpha)",
                      delta_color="normal" if is_beat else "inverse")

        st.divider()

        # --- INVESTMENT TIME MACHINE TABLE ---
        st.subheader("⏳ Investment Time Machine")
        st.caption("Value of **$1.00 Invested**: Historical performance vs. Future analyst projection.")
        
        # Construct Table
        df_tm = pd.DataFrame({
            "Period": ["1 Month", "6 Months", "1 Year", "5 Years"],
            "Past (Actual History)": [
                tm['Past']['1 Month'], 
                tm['Past']['6 Months'], 
                tm['Past']['1 Year'], 
                tm['Past']['5 Years']
            ],
            "Future (Analyst Implied)": [
                tm['Future']['1 Month'], 
                tm['Future']['6 Months'], 
                tm['Future']['1 Year'], 
                tm['Future']['5 Years']
            ]
        })

        # Format Currency
        def fmt_curr(x): return f"${x:.2f}" if x else "N/A"
        df_tm["Past (Actual History)"] = df_tm["Past (Actual History)"].apply(fmt_curr)
        df_tm["Future (Analyst Implied)"] = df_tm["Future (Analyst Implied)"].apply(fmt_curr)
        
        # Display Transposed (Horizontal Timeline)
        st.dataframe(df_tm.set_index("Period").T, use_container_width=True)

        st.divider()

        # --- PLOTLY CHART ---
        st.subheader("Technical Chart")
        hist = analysis['history'].tail(300)
        fig = make_subplots(rows=2, cols=1, shared_xaxes=True, 
                            vertical_spacing=0.03, row_heights=[0.75, 0.25])

        # Price (Blue)
        fig.add_trace(go.Scatter(x=hist.index, y=hist['Close'], name='Price',
            line=dict(color='#00CCFF', width=2.5)), row=1, col=1)
        # SMA 50 (Green)
        fig.add_trace(go.Scatter(x=hist.index, y=hist['SMA_50'], name='SMA 50', 
            line=dict(color='#00FF00', width=1)), row=1, col=1)
        # SMA 200 (Red)
        fig.add_trace(go.Scatter(x=hist.index, y=hist['SMA_200'], name='SMA 200', 
            line=dict(color='#FF0055', width=1)), row=1, col=1)
        # Volume
        fig.add_trace(go.Bar(x=hist.index, y=hist['Volume'], name='Volume', 
            marker_color='rgba(255, 255, 255, 0.2)'), row=2, col=1)

        fig.update_layout(height=600, template="plotly_dark", 
            paper_bgcolor='rgba(0,0,0,0)', plot_bgcolor='rgba(0,0,0,0)',
            hovermode="x unified", xaxis_rangeslider_visible=False, 
            margin=dict(l=10, r=10, t=10, b=10))
        st.plotly_chart(fig, use_container_width=True)

        # --- FUNDAMENTALS & METRICS ---
        st.subheader("📚 Key Data")
        
        # Row 1: Top Metrics
        m1, m2, m3, m4 = st.columns(4)
        m1.metric("Current Price", f"${info.get('currentPrice', 0):.2f}")
        m2.metric("Beta (Risk)", metrics['Beta'], help="1.0 = Market Volatility")
        m3.metric("CAPM Req. Return", metrics['Expected Return'])
        m4.metric("Trend Signal", metrics['Signal'])

        st.divider()

        # Row 2: Tables
        f_col1, f_col2 = st.columns(2)
        with f_col1:
            st.markdown("**Valuation**")
            df_val = pd.DataFrame({
                "Metric": ["Trailing P/E", "Forward P/E", "PEG Ratio", "Price/Book"],
                "Value": [info.get('trailingPE'), info.get('forwardPE'), info.get('pegRatio'), info.get('priceToBook')]
            })
            st.dataframe(df_val, hide_index=True, use_container_width=True)
            
        with f_col2:
            st.markdown("**Financial Health**")
            df_health = pd.DataFrame({
                "Metric": ["Free Cash Flow", "Debt/Equity", "Return on Equity", "Profit Margin"],
                "Value": [
                    analysis['fundamentals']['Free Cash Flow'], 
                    analysis['fundamentals']['Debt/Equity'],
                    f"{info.get('returnOnEquity', 0)*100:.2f}%" if info.get('returnOnEquity') else "N/A",
                    f"{info.get('profitMargins', 0)*100:.2f}%" if info.get('profitMargins') else "N/A"
                ]
            })
            st.dataframe(df_health, hide_index=True, use_container_width=True)

    else:
        st.error("Could not fetch data. The ticker might be delisted or API is busy.")