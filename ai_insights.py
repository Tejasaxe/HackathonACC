
#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
import os
from groq import Groq 
import yfinance as yf

# FIXED: Use the currently supported model
# You can also use "llama-3.1-8b-instant" for faster/cheaper results
CURRENT_MODEL = "llama-3.3-70b-versatile" 

def get_ai_long_term_analysis(api_key, ticker, analysis_data):
    """
    Sends financial metrics to Groq (Llama 3.3) to generate a strategic assessment.
    """
    if not api_key:
        return "⚠️ Please enter a Groq API Key in the sidebar."

    try:
        # 1. Configure Groq Client
        client = Groq(api_key=api_key)
        
        # 2. Unpack metrics
        val = analysis_data['valuation']
        info = analysis_data['info']
        fund = analysis_data['fundamentals']
        metrics = analysis_data['metrics']

        # 3. Create Prompt
        prompt = f"""
        Act as a senior quantitative analyst. Analyze {ticker} based on this data:
        - Current Price: ${val['Current Price']:.2f}
        - Analyst Upside: {val['Upside']*100:.1f}%
        - P/E Ratio: {info.get('trailingPE', 'N/A')}
        - Revenue Growth: {fund['Revenue Growth']}
        - Dividend Yield: {fund['Dividend Yield']}
        - Debt/Equity: {fund['Debt/Equity']}
        - Technical Trend: {metrics['Signal']}
        
        Task: Write a concise (3-4 sentences) Strategic Long-Term Assessment. 
        Focus on whether this is a "Value Trap", a "Growth Star", or a "Safe Haven". 
        Be direct and professional.
        """

        # 4. Generate with Llama 3.3
        chat_completion = client.chat.completions.create(
            messages=[
                {"role": "user", "content": prompt}
            ],
            model=CURRENT_MODEL, 
        )

        return chat_completion.choices[0].message.content

    except Exception as e:
        return f"Error generating analysis: {e}"

def get_news_sentiment(api_key, ticker):
    """
    Fetches latest news from Yahoo Finance and uses Groq to score sentiment.
    """
    if not api_key:
        return None, "Missing API Key"

    try:
        # 1. Fetch News
        stock = yf.Ticker(ticker)
        news_list = stock.news
        
        if not news_list:
            return None, "No recent news found."

        # 2. Prepare Headlines
        headlines = [f"- {n['title']}" for n in news_list[:5]]
        news_text = "\n".join(headlines)
        
        # 3. Ask Groq
        client = Groq(api_key=api_key)
        
        prompt = f"""
        Analyze these recent news headlines for {ticker} specifically for SHORT-TERM (Next 24h) price impact:
        {news_text}
        
        Return ONLY a single string in this exact format:
        SENTIMENT: [POSITIVE/NEGATIVE/NEUTRAL] | REASON: [One short sentence summary]
        """
        
        chat_completion = client.chat.completions.create(
            messages=[
                {"role": "user", "content": prompt}
            ],
            model=CURRENT_MODEL,
        )
        
        return headlines, chat_completion.choices[0].message.content

    except Exception as e:
        return None, f"Error: {e}"