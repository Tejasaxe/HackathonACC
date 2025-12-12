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

# --- 2. DATA UNIVERSE ---
@st.cache_data
def load_universe_data():
    try:
        url = "https://raw.githubusercontent.com/datasets/s-and-p-500-companies/master/data/constituents.csv"
        df = pd.read_csv(url)
        
        df = df.rename(columns={
            "Symbol": "Ticker",
            "Security": "Name",
            "GICS Sector": "Sector",
            "GICS Sub-Industry": "Industry",
            "Headquarters Location": "Location"
        })
        
        location_split = df['Location'].str.split(', ', n=1, expand=True)
        df['City'] = location_split[0]
        df['State'] = location_split[1] if 1 in location_split.columns else None
        
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
    """
    Creates a concise 2-sentence summary using available metadata.
    """
    name = info.get('shortName', 'The company')
    industry = info.get('industry', 'various sectors')
    city = info.get('city', 'Unknown City')
    country = info.get('country', 'Unknown Country')
    full_summary = info.get('longBusinessSummary', '')
    
    # 1. Create the "Identity" Sentence
    intro = f"**{name}** is a major player in the **{industry}** sector, based in **{city}, {country}**."
    
    # 2. Extract the "Action" Sentence (First 2 sentences of the real summary)
    # We split by '. ' to find sentence boundaries.
    if full_summary:
        sentences = full_summary.split('. ')
        # Take first 2 sentences and add a period back if needed
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

    st.subheader("Filter Market")
    
    # Dynamic Filters
    available_sectors = sorted(df_universe['Sector'].dropna().unique())
    c1, c2, c3, c4 = st.columns(4)
    
    with c1:
        selected_sectors = st.multiselect("Sector", options=available_sectors, placeholder="All Sectors")
        df_step1 = df_universe[df_universe['Sector'].isin(selected_sectors)] if selected_sectors else df_universe

    available_industries = sorted(df_step1['Industry'].dropna().unique())
    with c2:
        selected_industries = st.multiselect("Industry", options=available_industries, placeholder="All Industries")
        df_step2 = df_step1[df_step1['Industry'].isin(selected_industries)] if selected_industries else df_step1

    available_states = sorted(df_step2['State'].dropna().unique())
    with c3:
        selected_states = st.multiselect("State", options=available_states, placeholder="All States")
        df_step3 = df_step2[df_step2['State'].isin(selected_states)] if selected_states else df_step2

    available_cities = sorted(df_step3['City'].dropna().unique())
    with c4:
        selected_cities = st.multiselect("City", options=available_cities, placeholder="All Cities")
        filtered_df = df_step3[df_step3['City'].isin(selected_cities)] if selected_cities else df_step3

    search_query = st.text_input("Search Ticker or Name", placeholder="e.g. Nvidia...")
    if search_query:
        filtered_df = filtered_df[
            filtered_df['Ticker'].str.contains(search_query.upper()) | 
            filtered_df['Name'].str.contains(search_query, case=False)
        ]

    st.markdown(f"**Found {len(filtered_df)} companies**")
    
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
        
        # --- SMART SUMMARY ---
        st.info(generate_smart_summary(info), icon="ℹ️")

        # --- THE VERDICT ---
        st.subheader("The Verdict")
        
        v_col1, v_col2, v_col3 = st.columns(3)
        
        # Dynamic Color Logic for the Verdict
        verdict_text = val['Verdict']
        if "BUY" in verdict_text:
            v_color = "normal" # Greenish in Streamlit default
        elif "SELL" in verdict_text or "EXIT" in verdict_text:
            v_color = "inverse" # Reddish
        else:
            v_color = "off" # Grey/Neutral

        v_col1.metric("Recommendation", verdict_text, 
                      delta=metrics['Signal Desc'], delta_color=v_color)
        
        upside_val = val['Upside'] * 100
        v_col2.metric("Fair Value Gap", f"{upside_val:.1f}%", 
                      help=f"Analyst Target: ${val['Target Price']}",
                      delta="Undervalued" if upside_val > 0 else "Overvalued")

        st.divider()

        # --- METRICS ROW ---
        k1, k2, k3, k4 = st.columns(4)
        k1.metric("Price", f"${info.get('currentPrice', 0):.2f}")
        k2.metric("Beta (Risk)", metrics['Beta'])
        k3.metric("Exp. Return (Ann.)", metrics['Expected Return'], help="Expected Annual Return based on CAPM model")
        k4.metric("Trend", metrics['Signal']) # Just Bullish/Bearish now

        # --- PLOTLY CHART ---
        st.subheader("Technical Chart")
        hist = analysis['history'].tail(300)
        
        fig = make_subplots(rows=2, cols=1, shared_xaxes=True, 
                            vertical_spacing=0.03, row_heights=[0.75, 0.25])

        # Price Line
        fig.add_trace(go.Scatter(
            x=hist.index, y=hist['Close'], name='Price',
            line=dict(color='#00CCFF', width=2) 
        ), row=1, col=1)

        # SMAs (Added specific tooltips)
        fig.add_trace(go.Scatter(
            x=hist.index, y=hist['SMA_50'], name='50-Day Avg (Fast)', 
            line=dict(color='#00FF00', width=1)
        ), row=1, col=1)
        
        fig.add_trace(go.Scatter(
            x=hist.index, y=hist['SMA_200'], name='200-Day Avg (Slow)', 
            line=dict(color='#FF0055', width=1)
        ), row=1, col=1)

        # Volume
        fig.add_trace(go.Bar(
            x=hist.index, y=hist['Volume'], name='Volume',
            marker_color='rgba(255, 255, 255, 0.2)'
        ), row=2, col=1)

        fig.update_layout(
            height=600,
            template="plotly_dark",
            paper_bgcolor='rgba(0,0,0,0)',
            plot_bgcolor='rgba(0,0,0,0)',
            hovermode="x unified",
            xaxis_rangeslider_visible=False,
            margin=dict(l=10, r=10, t=10, b=10),
            legend=dict(orientation="h", yanchor="bottom", y=1.02, xanchor="right", x=1)
        )
        st.plotly_chart(fig, use_container_width=True)
        
        # Help Text for Chart
        with st.expander("🎓 How to read this chart"):
            st.write("""
            * **Blue Line:** The actual price.
            * **Green Line (50-Day):** The short-term trend.
            * **Red Line (200-Day):** The long-term trend.
            * **Buy Signal:** When Green crosses ABOVE Red.
            * **Sell Signal:** When Green crosses BELOW Red.
            """)

        # --- FUNDAMENTALS ---
        st.subheader("📚 Fundamental Data")
        # [Keep your previous fundamental tables code here]
        f_col1, f_col2 = st.columns([1, 1])
        with f_col1:
            df_val = pd.DataFrame({
                "Metric": ["Trailing P/E", "Forward P/E", "PEG Ratio", "Price/Book"],
                "Value": [info.get('trailingPE'), info.get('forwardPE'), info.get('pegRatio'), info.get('priceToBook')]
            })
            st.dataframe(df_val, hide_index=True, use_container_width=True)
            
        with f_col2:
            # Safe parsing for percentages
            roe = info.get('returnOnEquity')
            pm = info.get('profitMargins')
            
            df_health = pd.DataFrame({
                "Metric": ["Free Cash Flow", "Debt/Equity", "Return on Equity", "Profit Margin"],
                "Value": [
                    f"${info.get('freeCashflow', 0)/1e9:.2f}B" if info.get('freeCashflow') else "N/A", 
                    info.get('debtToEquity'),
                    f"{roe*100:.2f}%" if roe else "N/A",
                    f"{pm*100:.2f}%" if pm else "N/A"
                ]
            })
            st.dataframe(df_health, hide_index=True, use_container_width=True)

    else:
        st.error("Could not fetch data.")