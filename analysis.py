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
    
    # Check if we have enough data (at least 50 days)
    if len(stock_df) > 50:
        curr_price = stock_df['Close'].iloc[-1]
        sma_50 = stock_df['SMA_50'].iloc[-1]
        # Use SMA 200 if available, otherwise fallback to 50
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

    # --- 5. PACKAGING DATA ---
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
        "history": stock_df,
        "fundamentals": {
            "Free Cash Flow": f"${info.get('freeCashflow', 0)/1e9:.2f}B" if info.get('freeCashflow') else "N/A",
            "Debt/Equity": round(info.get('debtToEquity', 0), 2) if info.get('debtToEquity') else "N/A",
            
            # --- NEW METRICS (This fixes your error) ---
            "Dividend Yield": f"{info.get('dividendYield', 0)*100:.2f}%" if info.get('dividendYield') else "0.00%",
            "Revenue Growth": f"{info.get('revenueGrowth', 0)*100:.1f}%" if info.get('revenueGrowth') else "N/A"
        }
    }