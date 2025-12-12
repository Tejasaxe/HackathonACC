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
    
    # Beta Calculation
    cov = returns.cov()
    if not returns.empty:
        beta = cov.loc['Stock', 'Market'] / returns['Market'].var()
        volatility = returns['Stock'].std() * np.sqrt(252)
    else:
        beta = 1.0
        volatility = 0.20
    
    # CAPM Formula
    rf = 0.045
    rm = 0.10
    expected_return = rf + beta * (rm - rf)

    # --- 2. TECHNICAL SIGNALS (THE FIX) ---
    stock_df['SMA_50'] = stock_df['Close'].rolling(window=50).mean()
    stock_df['SMA_200'] = stock_df['Close'].rolling(window=200).mean()
    
    # Get latest values
    curr_price = stock_df['Close'].iloc[-1]
    sma_50 = stock_df['SMA_50'].iloc[-1]
    sma_200 = stock_df['SMA_200'].iloc[-1]
    
    # --- NEW "SMART" LOGIC ---
    # We check the relationship between Price, Fast Avg (50), and Slow Avg (200)
    
    trend = "NEUTRAL"
    trend_desc = "Consolidating"
    
    # Scenario 1: Golden Cross AND Price is supported (Best Case)
    if sma_50 > sma_200 and curr_price > sma_50:
        trend = "BULLISH"
        trend_desc = "Strong Uptrend (Price > Green > Red)"
        
    # Scenario 2: Golden Cross BUT Price is falling (The "Trap" you saw)
    elif sma_50 > sma_200 and curr_price < sma_50:
        trend = "WEAKENING"
        trend_desc = "Caution: Price dropped below Green"
        
    # Scenario 3: Death Cross AND Price is falling (Worst Case)
    elif sma_50 < sma_200 and curr_price < sma_50:
        trend = "BEARISH"
        trend_desc = "Strong Downtrend (Price < Green < Red)"
        
    # Scenario 4: Death Cross BUT Price is rallying (Early Reversal)
    elif sma_50 < sma_200 and curr_price > sma_50:
        trend = "RECOVERY"
        trend_desc = "Watch: Price reclaimed Green line"

    # --- 3. VALUATION ---
    target_price = info.get('targetMeanPrice')
    if target_price:
        upside = (target_price - curr_price) / curr_price
    else:
        target_price = curr_price
        upside = 0

    # --- 4. THE VERDICT (Long/Short/Hold) ---
    verdict = "HOLD"
    
    # Logic: Only BUY if Trend is BULLISH or RECOVERY (with value)
    if trend == "BULLISH" and upside > 0:
        verdict = "LONG (BUY)"
    elif trend == "BEARISH":
        verdict = "SHORT (SELL)"
    elif trend == "WEAKENING":
        verdict = "EXIT / CAUTION"  # Get out before it drops more
    elif trend == "RECOVERY":
        verdict = "WATCH FOR ENTRY"

    # --- 5. POSITION SIZING ---
    if volatility < 0.20:
        allocation = "High (5-7%)"
    elif volatility < 0.40:
        allocation = "Medium (3-5%)"
    elif volatility < 0.60:
        allocation = "Low (1-2%)"
    else:
        allocation = "Speculative (<1%)"

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
            "Verdict": verdict,
            "Allocation": allocation
        },
        "history": stock_df,
        "fundamentals": {
            "Free Cash Flow": info.get('freeCashflow'),
            "Debt/Equity": info.get('debtToEquity')
        }
    }