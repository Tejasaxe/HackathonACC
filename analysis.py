import pandas as pd
import numpy as np

def run_quant_analysis(data):
    """
    Takes raw data and calculates CAPM, Technicals, and Fundamental ratios.
    """
    if not data:
        return None

    stock_df = data['stock_history']
    market_df = data['market_history']
    bs = data['balance_sheet']
    cf = data['cash_flow']
    
    # --- 1. CAPM & RISK METRICS ---
    # Align dates and calculate daily % returns
    prices = pd.DataFrame({
        'Stock': stock_df['Close'],
        'Market': market_df['Close']
    }).dropna()
    
    returns = prices.pct_change().dropna()
    
    # Covariance Matrix to find Beta
    # Beta = Cov(Stock, Market) / Var(Market)
    covariance_matrix = returns.cov()
    cov_stock_market = covariance_matrix.loc['Stock', 'Market']
    market_variance = returns['Market'].var()
    
    beta = cov_stock_market / market_variance
    
    # Annualized Volatility (Standard Deviation * sqrt(252 trading days))
    volatility = returns['Stock'].std() * np.sqrt(252)
    
    # Expected Return (CAPM) -> E(R) = Rf + Beta(Rm - Rf)
    # Assumption: Risk Free (Rf) = 4% (0.04), Market Return (Rm) = 10% (0.10)
    rf = 0.04
    rm = 0.10
    expected_return = rf + beta * (rm - rf)

    # --- 2. TECHNICALS ---
    # Simple Moving Averages
    stock_df['SMA_50'] = stock_df['Close'].rolling(window=50).mean()
    stock_df['SMA_200'] = stock_df['Close'].rolling(window=200).mean()
    
    # Last Price vs SMA
    current_price = stock_df['Close'].iloc[-1]
    sma_50 = stock_df['SMA_50'].iloc[-1]
    sma_200 = stock_df['SMA_200'].iloc[-1]
    
    signal = "NEUTRAL"
    if sma_50 > sma_200:
        signal = "BULLISH (Golden Cross)"
    if sma_50 < sma_200:
        signal = "BEARISH (Death Cross)"

    # --- 3. FUNDAMENTALS (Safe Handling) ---
    # We use .get() or try/except because financial statements vary wildly by company
    try:
        # Free Cash Flow = Operating Cash Flow + Capital Expenditure
        # Note: CapEx is usually negative in cash flow statements
        operating_cash_flow = cf.loc['Operating Cash Flow'].iloc[0] # Most recent year
        capex = cf.loc['Capital Expenditure'].iloc[0] 
        fcf = operating_cash_flow + capex
    except:
        fcf = None

    try:
        # Debt to Equity
        total_debt = bs.loc['Total Debt'].iloc[0]
        total_equity = bs.loc['Stockholders Equity'].iloc[0]
        debt_to_equity = total_debt / total_equity
    except:
        debt_to_equity = None

    return {
        "metrics": {
            "Beta": round(beta, 2),
            "Volatility (Ann.)": f"{round(volatility * 100, 1)}%",
            "Expected Return (CAPM)": f"{round(expected_return * 100, 1)}%",
            "Signal": signal
        },
        "fundamentals": {
            "Free Cash Flow": f"${fcf:,.0f}" if fcf else "N/A",
            "Debt/Equity Ratio": round(debt_to_equity, 2) if debt_to_equity else "N/A"
        },
        "history": stock_df # Return dataframe with added SMA columns for plotting
    }