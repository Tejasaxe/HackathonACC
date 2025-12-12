import streamlit as st
import pandas as pd
import plotly.graph_objects as go
from plotly.subplots import make_subplots

# IMPORT YOUR MODULES
from fetch_data import get_raw_data
from analysis import run_quant_analysis
# IMPORT THE NEW FUNCTION
from ai_insights import get_ai_long_term_analysis, fetch_raw_news, analyze_news_sentiment

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
        df = df.rename(columns={"Symbol": "Ticker", "Security": "Name", "GICS Sector": "Sector", "GICS Sub-Industry": "Industry", "Headquarters Location": "Location"})
        location_split = df['Location'].str.split(', ', n=1, expand=True)
        df['City'] = location_split[0]
        df['State'] = location_split[1] if 1 in location_split.columns else None
        return df.drop(columns=['Location', 'Founded', 'CIK', 'Date added'], errors='ignore')
    except Exception as e:
        st.error(f"Data Connection Failed: {e}")
        return pd.DataFrame()

@st.cache_data
def load_analysis(ticker):
    raw = get_raw_data(ticker)
    if raw: return raw, run_quant_analysis(raw)
    return None, None

def generate_smart_summary(info):
    name = info.get('shortName', 'The company')
    industry = info.get('industry', 'various sectors')
    city = info.get('city', 'Unknown City')
    country = info.get('country', 'Unknown Country')
    full_summary = info.get('longBusinessSummary', '')
    intro = f"**{name}** is a major player in the **{industry}** sector, based in **{city}, {country}**."
    if full_summary:
        sentences = full_summary.split('. ')
        short_desc = ". ".join(sentences[:2]) + ("." if not sentences[:2][-1].endswith('.') else "")
    else:
        short_desc = "No detailed business description available."
    return f"{intro} {short_desc}"

# --- 3. MAIN LOGIC ---
df_universe = load_universe_data()

with st.sidebar:
    st.header("⚙️ Settings")
    groq_key = st.text_input("Groq API Key", type="password", help="Get it free at console.groq.com")
    st.caption("Powered by Llama 3 via Groq ⚡")

if 'selected_ticker' not in st.session_state:
    st.session_state.selected_ticker = None

# --- VIEW 1: SEARCH GRID ---
if st.session_state.selected_ticker is None:
    st.title("⚡ Market Terminal")
    st.caption("Select a company from the grid to launch deep analysis.")
    st.subheader("Filter Market")
    
    c1, c2, c3, c4 = st.columns(4)
    available_sectors = sorted(df_universe['Sector'].dropna().unique())
    with c1: selected_sectors = st.multiselect("Sector", options=available_sectors, placeholder="All Sectors")
    df_step1 = df_universe[df_universe['Sector'].isin(selected_sectors)] if selected_sectors else df_universe

    available_industries = sorted(df_step1['Industry'].dropna().unique())
    with c2: selected_industries = st.multiselect("Industry", options=available_industries, placeholder="All Industries")
    df_step2 = df_step1[df_step1['Industry'].isin(selected_industries)] if selected_industries else df_step1

    available_states = sorted(df_step2['State'].dropna().unique())
    with c3: selected_states = st.multiselect("State", options=available_states, placeholder="All States")
    df_step3 = df_step2[df_step2['State'].isin(selected_states)] if selected_states else df_step2

    available_cities = sorted(df_step3['City'].dropna().unique())
    with c4: selected_cities = st.multiselect("City", options=available_cities, placeholder="All Cities")
    filtered_df = df_step3[df_step3['City'].isin(selected_cities)] if selected_cities else df_step3

    search_query = st.text_input("Search Ticker or Name", placeholder="e.g. Nvidia...")
    if search_query:
        filtered_df = filtered_df[filtered_df['Ticker'].str.contains(search_query.upper()) | filtered_df['Name'].str.contains(search_query, case=False)]

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
        use_container_width=True, hide_index=True, height=500, on_select="rerun", selection_mode="single-row"
    )

    if selection.selection.rows:
        st.session_state.selected_ticker = filtered_df.iloc[selection.selection.rows[0]]['Ticker']
        st.rerun()

# --- VIEW 2: DASHBOARD ---
else:
    ticker = st.session_state.selected_ticker
    
    with st.container():
        c_nav1, c_nav2 = st.columns([1, 10])
        with c_nav1:
            if st.button("⬅ Back", use_container_width=True):
                st.session_state.selected_ticker = None
                st.rerun()
        with c_nav2: st.markdown(f"## {ticker} Analysis")
            
    with st.spinner(f"Analyzing {ticker}..."):
        raw_data = get_raw_data(ticker)
        if raw_data:
            analysis = run_quant_analysis(raw_data)
            ai_data_bundle = {'info': raw_data['info'], 'fundamentals': analysis['fundamentals'], 'valuation': analysis['valuation'], 'metrics': analysis['metrics']}
        else: analysis = None

    if raw_data and analysis:
        info = raw_data['info']
        metrics = analysis['metrics']
        val = analysis['valuation']
        
        st.info(generate_smart_summary(info), icon="ℹ️")

        st.subheader("📊 Key Metrics")
        m1, m2, m3, m4 = st.columns(4)
        m1.metric("Current Price", f"${info.get('currentPrice', 0):.2f}")
        m2.metric("Beta (Risk)", metrics['Beta'], help="1.0 = Market Volatility")
        m3.metric("CAPM Req. Return", metrics['Expected Return'])
        m4.metric("Trend Signal", metrics['Signal'])
        st.divider()

        st.subheader("⚖️ The Verdict")
        v_col1, v_col2 = st.columns(2)
        verdict_text = val['Verdict']
        v_color = "normal" if "BUY" in verdict_text else ("inverse" if "SELL" in verdict_text or "EXIT" in verdict_text else "off")
        v_col1.metric("Recommendation", verdict_text, delta=metrics['Signal Desc'], delta_color=v_color)
        upside_val = val['Upside'] * 100
        v_col2.metric("Fair Value Gap", f"{upside_val:.1f}%", delta="Undervalued" if upside_val > 0 else "Overvalued")
        st.divider()

        st.subheader("Technical Chart")
        hist = analysis['history'].tail(300)
        fig = make_subplots(rows=2, cols=1, shared_xaxes=True, vertical_spacing=0.03, row_heights=[0.75, 0.25])
        fig.add_trace(go.Scatter(x=hist.index, y=hist['Close'], name='Price', line=dict(color='#00CCFF', width=2.5)), row=1, col=1)
        fig.add_trace(go.Scatter(x=hist.index, y=hist['SMA_50'], name='SMA 50', line=dict(color='#00FF00', width=1)), row=1, col=1)
        fig.add_trace(go.Scatter(x=hist.index, y=hist['SMA_200'], name='SMA 200', line=dict(color='#FF0055', width=1)), row=1, col=1)
        fig.add_trace(go.Bar(x=hist.index, y=hist['Volume'], name='Volume', marker_color='rgba(255, 255, 255, 0.2)'), row=2, col=1)
        fig.update_layout(height=600, template="plotly_dark", paper_bgcolor='rgba(0,0,0,0)', plot_bgcolor='rgba(0,0,0,0)', hovermode="x unified", xaxis_rangeslider_visible=False, margin=dict(l=10, r=10, t=10, b=10), legend=dict(orientation="h", yanchor="bottom", y=1.02, xanchor="right", x=1))
        st.plotly_chart(fig, use_container_width=True)

        st.subheader("📚 Fundamental Deep Dive")
        f_col1, f_col2, f_col3 = st.columns(3)
        with f_col1:
            st.markdown("💰 **Valuation**")
            st.dataframe(pd.DataFrame({"Metric": ["P/E Ratio", "Forward P/E", "PEG Ratio", "Price/Book"], "Value": [info.get('trailingPE'), info.get('forwardPE'), info.get('pegRatio'), info.get('priceToBook')]}), hide_index=True, use_container_width=True)
        with f_col2:
            st.markdown("🏥 **Financial Health**")
            st.dataframe(pd.DataFrame({"Metric": ["Debt/Equity", "Free Cash Flow", "Profit Margin", "ROE"], "Value": [analysis['fundamentals']['Debt/Equity'], analysis['fundamentals']['Free Cash Flow'], f"{info.get('profitMargins', 0)*100:.2f}%" if info.get('profitMargins') else "N/A", f"{info.get('returnOnEquity', 0)*100:.2f}%" if info.get('returnOnEquity') else "N/A"]}), hide_index=True, use_container_width=True)
        with f_col3:
            st.markdown("🚀 **Growth & Income**")
            st.dataframe(pd.DataFrame({"Metric": ["Revenue Growth (YoY)", "Earnings Growth", "Dividend Yield", "Payout Ratio"], "Value": [analysis['fundamentals']['Revenue Growth'], f"{info.get('earningsGrowth', 0)*100:.1f}%" if info.get('earningsGrowth') else "N/A", analysis['fundamentals']['Dividend Yield'], f"{info.get('payoutRatio', 0)*100:.1f}%" if info.get('payoutRatio') else "N/A"]}), hide_index=True, use_container_width=True)

        # --- AI INTELLIGENCE & NEWS FEED ---
        st.divider()
        st.subheader("🧠 AI Intelligence Center")
        
        ai_col1, ai_col2 = st.columns(2)
        
        # 1. Strategy Column
        with ai_col1:
            st.markdown("### 🦉 Long-Term Strategy")
            if not groq_key: st.warning("⚠️ Enter Groq API Key for Strategy")
            else:
                with st.spinner("Consulting AI Analyst..."):
                    strategy_text = get_ai_long_term_analysis(groq_key, ticker, ai_data_bundle)
                    st.success(strategy_text)

        # 2. News Column (Scraping)
        with ai_col2:
            st.markdown("### 📰 Live News Feed (Past 24h)")
            st.caption("Raw data scraped from DuckDuckGo")
            
            with st.spinner("Scraping the web..."):
                raw_headlines = fetch_raw_news(ticker)
                
                if raw_headlines:
                    with st.container(height=300):
                        for news_item in raw_headlines:
                            st.markdown(news_item)
                            st.divider()
                else:
                    st.warning(f"No news found for {ticker} in the last 24h.")
        
        # --- NEW: SENTIMENT VERDICT ROW (Bottom) ---
        if raw_headlines and groq_key:
            st.divider()
            st.subheader("🤖 AI Sentiment Verdict")
            
            with st.spinner("Analyzing Sentiment from Headlines..."):
                sentiment_result = analyze_news_sentiment(groq_key, ticker, raw_headlines)
                
                # Check sentiment to assign color
                if "POSITIVE" in sentiment_result:
                    s_color = "green"
                    s_icon = "🚀"
                elif "NEGATIVE" in sentiment_result:
                    s_color = "red"
                    s_icon = "📉"
                else:
                    s_color = "gray"
                    s_icon = "😐"
                
                # Display in a big visible box
                st.markdown(f"""
                <div style="padding: 20px; border-radius: 10px; border: 1px solid #333; background-color: #0e1117; text-align: center;">
                    <h2 style='color: {s_color}; margin:0;'>{s_icon} {sentiment_result}</h2>
                </div>
                """, unsafe_allow_html=True)
        elif raw_headlines and not groq_key:
            st.info("ℹ️ Enter Groq API Key to see the Sentiment Verdict for this news.")

    else:
        st.error("Could not fetch data. The ticker might be delisted or API is busy.")