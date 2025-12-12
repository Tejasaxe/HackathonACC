import os
from groq import Groq 
from duckduckgo_search import DDGS 

# Use the latest supported model
CURRENT_MODEL = "llama-3.3-70b-versatile" 

def get_ai_long_term_analysis(api_key, ticker, analysis_data):
    # (Keep this function EXACTLY as it was)
    if not api_key: return "⚠️ Please enter a Groq API Key in the sidebar."
    try:
        client = Groq(api_key=api_key)
        val = analysis_data['valuation']
        info = analysis_data['info']
        fund = analysis_data['fundamentals']
        metrics = analysis_data['metrics']
        prompt = f"""Act as a senior quantitative analyst. Analyze {ticker}...""" # (Truncated for brevity)
        chat_completion = client.chat.completions.create(
            messages=[{"role": "user", "content": prompt}],
            model=CURRENT_MODEL, 
        )
        return chat_completion.choices[0].message.content
    except Exception as e:
        return f"Error: {e}"

def fetch_raw_news(ticker):
    """
    Scrapes news using DuckDuckGo (Past 24h).
    Returns a list of raw headlines with source links.
    """
    try:
        scrape_query = f"{ticker} stock news"
        results = list(DDGS().news(keywords=scrape_query, region="wt-wt", safesearch="off", timelimit="d", max_results=10))
        
        if not results:
            return []

        formatted_news = []
        for r in results:
            source = r.get('source', 'Unknown')
            title = r.get('title', 'No Title')
            url = r.get('url', '#')
            # Markdown format for UI
            formatted_news.append(f"**{source}:** {title}  \n[Read Source]({url})")

        return formatted_news
    except Exception as e:
        return [f"Error Scraper: {e}"]

def analyze_news_sentiment(api_key, ticker, news_list):
    """
    Takes the RAW NEWS list and uses AI to generate a sentiment verdict.
    """
    if not api_key:
        return "⚠️ Missing API Key"
    
    if not news_list:
        return "No news to analyze."

    try:
        client = Groq(api_key=api_key)
        
        # Combine the headlines into a single text block for the AI
        news_text = "\n".join(news_list)
        
        prompt = f"""
        You are a high-frequency trading algorithm. Analyze these news items released in the LAST 24 HOURS for {ticker}:
        {news_text}
        
        Task:
        1. Determine the overall Market Sentiment (POSITIVE, NEGATIVE, or NEUTRAL).
        2. Provide a 1-sentence "Vibe Check" summary of WHY.
        
        Return ONLY this format:
        SENTIMENT: [One Word] | VIBE: [Short Sentence]
        """
        
        chat_completion = client.chat.completions.create(
            messages=[{"role": "user", "content": prompt}],
            model=CURRENT_MODEL,
        )
        
        return chat_completion.choices[0].message.content

    except Exception as e:
        return f"AI Error: {e}"