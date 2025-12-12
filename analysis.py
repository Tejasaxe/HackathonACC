import pandas as pd
import numpy as np

def run_quant_analysis(data):
    """
    Calculates technicals, fundamental valuation, verdict, and time-machine projections.
    """
    if not data:
        return None

    stock_df = data['stock_history']
    market_df = data['market_history']
    info = data['info']
    
    # --- 1. CAPM & RISK METRICS ---
    # Create a combined dataframe to align dates
    prices = pd.DataFrame({
        'Stock': stock_df['Close'], 
        'Market': market_df['Close']
    }).dropna()
    
    returns = prices.pct_change().dropna()
    
    # Beta Calculation
    if not returns.empty:
        cov = returns.cov()
        market_var = returns['Market'].var()
        beta = cov.loc['Stock', 'Market'] / market_var
        
        # Annualized Volatility (Std Dev * sqrt(252 trading days))
        volatility = returns['Stock'].std() * np.sqrt(252)
    else:
        beta = 1.0
        volatility = 0.20 # Default fallback
    
    # CAPM Expected Return Formula
    # R = Rf + Beta * (Rm - Rf)
    rf = 0.045  # 4.5% Risk Free Rate
    rm = 0.10   # 10% Market Return
    expected_return = rf + beta * (rm - rf)

    # --- 2. TECHNICAL SIGNALS (SMART TREND) ---
    stock_df['SMA_50'] = stock_df['Close'].rolling(window=50).mean()
    stock_df['SMA_200'] = stock_df['Close'].rolling(window=200).mean()
    
    # Get latest values for logic
    # We check if we have enough data (at least 50 days)
    if len(stock_df) > 50:
        curr_price = stock_df['Close'].iloc[-1]
        sma_50 = stock_df['SMA_50'].iloc[-1]
        # Use SMA 200 if available, otherwise just use price vs SMA 50
        sma_200 = stock_df['SMA_200'].iloc[-1] if len(stock_df) > 200 else sma_50
        
        # Smart Trend Logic
        if sma_50 > sma_200 and curr_price > sma_50:
            trend = "BULLISH"
            trend_desc = "Strong Uptrend (Price > Green > Red)"
        elif sma_50 > sma_200 and curr_price < sma_50:
            trend = "WEAKENING"
            trend_desc = "Caution: Price dropped below Green"
        elif sma_50 < sma_200 and curr_price < sma_50:
            trend = "BEARISH"
            trend_desc = "Downtrend (Price < Green < Red)"
        elif sma_50 < sma_200 and curr_price > sma_50:
            trend = "RECOVERY"
            trend_desc = "Watch: Price reclaimed Green line"
        else:
            trend = "NEUTRAL"
            trend_desc = "Consolidating"
    else:
        curr_price = stock_df['Close'].iloc[-1]
        trend = "NEUTRAL"
        trend_desc = "Insufficient History"

    # --- 3. VALUATION (Analyst Upside) ---
    target_price = info.get('targetMeanPrice')
    
    if target_price:
        upside = (target_price - curr_price) / curr_price
    else:
        target_price = curr_price
        upside = 0

    # --- 4. THE VERDICT ---
    verdict = "HOLD"
    
    if trend == "BULLISH" and upside > 0:
        verdict = "LONG (BUY)"
    elif trend == "BEARISH":
        verdict = "SHORT (SELL)"
    elif trend == "WEAKENING":
        verdict = "EXIT / CAUTION"
    elif trend == "RECOVERY":
        verdict = "WATCH FOR ENTRY"

    # --- 5. INVESTMENT TIME MACHINE (Growth of $1) ---
    # PAST: Value of $1 invested N days ago
    def get_past_value(days):
        if len(stock_df) > days:
            past_price = stock_df['Close'].iloc[-days]
            return curr_price / past_price 
        return None

    # FUTURE: Projected value of $1 in N years based on Analyst Target
    if target_price:
        annual_growth_rate = (target_price - curr_price) / curr_price
        
        # Cap extreme growth rates for long-term projection (max 50% CAGR)
        capped_rate = min(annual_growth_rate, 0.50)
        
        fut_1mo = 1 * (1 + annual_growth_rate) ** (1/12)
        fut_6mo = 1 * (1 + annual_growth_rate) ** (0.5)
        fut_1yr = 1 * (1 + annual_growth_rate) ** (1.0)
        fut_5yr = 1 * (1 + capped_rate) ** (5.0) 
    else:
        fut_1mo = fut_6mo = fut_1yr = fut_5yr = None

    # --- 6. PACKAGING DATA ---
    return {
        "metrics": {
            "Beta": round(beta, 2),
            "Volatility": f"{round(volatility * 100, 1)}%",
            "Expected Return": f"{round(expected_return * 100, 1)}%",
            "Signal": trend,
            "Signal Desc": trend_desc
        },
        "valuation": {
            "Current Price": curr_price,
            "Target Price": target_price,
            "Upside": upside,
            "Verdict": verdict
        },
        # THIS IS THE MISSING KEY CAUSING YOUR ERROR
        "time_machine": {
            "Past": {
                "1 Month": get_past_value(21),
                "6 Months": get_past_value(126),
                "1 Year": get_past_value(252),
                "5 Years": get_past_value(1260)
            },
            "Future": {
                "1 Month": fut_1mo,
                "6 Months": fut_6mo,
                "1 Year": fut_1yr,
                "5 Years": fut_5yr
            }
        },
        "history": stock_df,
        "fundamentals": {
            "Free Cash Flow": f"${info.get('freeCashflow', 0)/1e9:.2f}B" if info.get('freeCashflow') else "N/A",
            "Debt/Equity": round(info.get('debtToEquity', 0), 2) if info.get('debtToEquity') else "N/A"
        }
    }