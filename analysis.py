import pandas as pd
import numpy as np

def run_quant_analysis(data):
    """
    Calculates technicals, fundamental valuation, and generates a verdict.
    """
    if not data:
        return None

    stock_df = data['stock_history']
    market_df = data['market_history']
    info = data['info']
    
    # --- 1. CAPM & RISK ---
    prices = pd.DataFrame({'Stock': stock_df['Close'], 'Market': market_df['Close']}).dropna()
    returns = prices.pct_change().dropna()
    
    cov = returns.cov()
    beta = cov.loc['Stock', 'Market'] / returns['Market'].var()
    
    # CAPM Formula: R = Rf + Beta * (Rm - Rf)
    rf = 0.045  # 4.5% Risk Free Rate (approx 10y Treasury)
    rm = 0.10   # 10% Expected Market Return
    expected_return = rf + beta * (rm - rf)
    
    volatility = returns['Stock'].std() * np.sqrt(252)

    # --- 2. TECHNICAL SIGNALS ---
    stock_df['SMA_50'] = stock_df['Close'].rolling(window=50).mean()
    stock_df['SMA_200'] = stock_df['Close'].rolling(window=200).mean()
    
    curr_price = stock_df['Close'].iloc[-1]
    sma_50 = stock_df['SMA_50'].iloc[-1]
    sma_200 = stock_df['SMA_200'].iloc[-1]
    
    # Vibe Signal Logic
    if sma_50 > sma_200:
        trend = "BULLISH"
        trend_desc = "Uptrend (Green > Red)"
    else:
        trend = "BEARISH"
        trend_desc = "Downtrend (Green < Red)"

    # --- 3. VALUATION (Price vs Expected) ---
    target_price = info.get('targetMeanPrice')
    
    # If no analyst target, assume fair value is current price (neutral)
    if target_price:
        upside = (target_price - curr_price) / curr_price
    else:
        target_price = curr_price
        upside = 0

    # --- 4. THE VERDICT (Long/Short/Hold) ---
    # Logic: Combine Technicals (Trend) + Fundamentals (Valuation)
    
    verdict = "HOLD"
    color = "yellow"
    
    if trend == "BULLISH" and upside > 0.10:
        verdict = "LONG (BUY)" # Rising trend + Cheap
        color = "green"
    elif trend == "BEARISH" and upside < -0.10:
        verdict = "SHORT (SELL)" # Falling trend + Expensive
        color = "red"
    elif trend == "BULLISH":
        verdict = "WATCH (Momentum Up)"
        color = "blue"
    elif trend == "BEARISH":
        verdict = "AVOID (Momentum Down)"
        color = "orange"

    # --- 5. POSITION SIZING (Money Management) ---
    # Rule of Thumb: Lower Volatility = Higher Allocation
    if volatility < 0.20:
        allocation = "High (5-7%)" # Safe stock (e.g. Coke)
    elif volatility < 0.40:
        allocation = "Medium (3-5%)" # Standard stock (e.g. Apple)
    elif volatility < 0.60:
        allocation = "Low (1-2%)" # Risky (e.g. Tesla)
    else:
        allocation = "Speculative (<1%)" # Crypto/Penny stocks

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
            "Upside": upside,  # float (e.g. 0.15 for 15%)
            "Verdict": verdict,
            "Verdict Color": color,
            "Allocation": allocation
        },
        "history": stock_df,
        "fundamentals": {
            "Free Cash Flow": info.get('freeCashflow'),
            "Debt/Equity": info.get('debtToEquity')
        }
    }