import requests
from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from vaderSentiment.vaderSentiment import SentimentIntensityAnalyzer
from datetime import date

# --- API Key ---
API_KEY = "4dbc17e007ab436fb66416009dfb59a8"

# --- Create the FastAPI app ---
app = FastAPI(
    title="ML-Powered News API",
    description="A proxy API to securely fetch and analyze news from NewsAPI."
)

# --- Add CORS ---
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["GET"],
    allow_headers=["*"],
)

# --- Initialize the Sentiment Analyzer ---
analyzer = SentimentIntensityAnalyzer()


def get_sentiment(text: str) -> str:
    if not text:
        return "Neutral"
    scores = analyzer.polarity_scores(text)
    compound = scores['compound']
    if compound >= 0.05:
        return "Positive"
    elif compound <= -0.05:
        return "Negative"
    else:
        return "Neutral"


# --- Define the API Endpoint ---
# We now use 'q' (query) and 'date'
@app.get("/api/news")
def get_news(q: str, news_date: str):
    # --- Use the /everything endpoint ---
    base_url = "https://newsapi.org/v2/everything"

    params = {
        "apiKey": API_KEY,
        "q": q,  # The search query (required)
        "from": news_date,  # The date to search from
        "sortBy": "publishedAt",  # Sort by most recently published
        "language": "en",  # Search for English articles
        "pageSize": 50
    }

    try:
        r = requests.get(base_url, params=params)
        r.raise_for_status()
        news_data = r.json()

        # --- ML Enhancement Loop ---
        if news_data.get("status") == "ok":
            for article in news_data.get("articles", []):
                text_to_analyze = article.get("description") or article.get("title", "")
                article['sentiment'] = get_sentiment(text_to_analyze)

        return news_data

    except requests.exceptions.HTTPError as e:
        return {"status": "error", "message": str(e)}
    except Exception as e:
        return {"status": "error", "message": f"An unexpected error occurred: {e}"}