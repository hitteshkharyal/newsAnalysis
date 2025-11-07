import streamlit as st
import requests
from datetime import datetime, timedelta
import time
from streamlit_mic_recorder import speech_to_text

# --- Page Configuration ---
st.set_page_config(page_title="News Dashboard", page_icon="📰", layout="wide")

# --- Backend API URL ---
BACKEND_API_URL = "http://127.0.0.1:8000/api/news"


# --- Helper Function to Display Articles (No changes) ---
def display_articles(articles):
    # This function now just displays the 10 articles it is given
    for article in articles:
        st.divider()
        col1, col2 = st.columns([1, 3])
        with col1:
            if article.get("urlToImage"):
                st.image(article["urlToImage"], use_container_width=True)
            else:
                st.image("", use_container_width=True,
                         caption="No Image Available")
        with col2:
            st.subheader(article["title"])
            sentiment = article.get("sentiment", "Neutral")
            if sentiment == "Positive":
                st.success("Sentiment: Positive 😃")
            elif sentiment == "Negative":
                st.error("Sentiment: Negative 😠")
            else:
                st.info("Sentiment: Neutral 😐")

            st.write(article.get("description", "No description available."))
            source = article.get("source", {}).get("name", "Unknown Source")
            date_str = article.get("publishedAt", "")
            if date_str:
                try:
                    date_obj = datetime.strptime(date_str, "%Y-%m-%dT%H:%M:%SZ")
                    date_display = date_obj.strftime("%d %B %Y, %H:%M")
                except ValueError:
                    date_display = date_str
            st.caption(f"Source: **{source}** | Published: **{date_display}**")
            st.link_button("Read Full Article ↗️", url=article["url"], use_container_width=True)


# --- Main Application UI ---
st.title("📰 ML-Powered News Dashboard")
st.write("Search for news on any topic. Try using the microphone in the sidebar!")

# --- Initialize Session State for query and pagination ---
if 'query_text' not in st.session_state:
    st.session_state.query_text = ""
if 'all_articles' not in st.session_state:
    st.session_state.all_articles = []
if 'page' not in st.session_state:
    st.session_state.page = 1
if 'total_results' not in st.session_state:
    st.session_state.total_results = 0

# --- Sidebar ---
st.sidebar.header("Configure Your News Feed")

st.sidebar.write("**Speak your query:**")


def stt_callback():
    if st.session_state.my_stt_output:
        st.session_state.query_text = st.session_state.my_stt_output


speech_to_text(
    key='my_stt',
    callback=stt_callback,
    language='en-US',
    start_prompt="Click to Speak 🎤",
    stop_prompt="Recording... Click to stop",
    just_once=False,
    use_container_width=True
)

st.sidebar.divider()

# --- Form for Text and Date ---
with st.sidebar.form(key="news_form"):
    st.write("**Or, type your topic:**")
    query = st.text_input(
        "e.g., 'Tesla', 'AI', 'Health'",
        key="query_text"
    )
    st.write("---")
    st.write("**Search for news from this date:**")
    default_date = datetime.now() - timedelta(days=3)
    news_date = st.date_input("Date", value=default_date)
    submit_button = st.form_submit_button(label="Get News")

# --- API Call Logic ---
if submit_button:
    if not query:
        st.error("Please enter a search topic. This is required.")
    else:
        # The 5-second debounce you requested
        time.sleep(5)
        params = {"q": query, "news_date": news_date.isoformat()}
        with st.spinner("Searching for and analyzing news..."):
            try:
                r = requests.get(BACKEND_API_URL, params=params)
                r.raise_for_status()
                news_data = r.json()
                if news_data.get("status") == "ok":
                    # --- PAGINATION: Store results, reset page ---
                    st.session_state.all_articles = news_data.get("articles", [])
                    st.session_state.total_results = news_data.get("totalResults", 0)
                    st.session_state.page = 1  # Reset to page 1 for every new search
                else:
                    st.error(f"Error from API: {news_data.get('message', 'Unknown error')}")
                    st.session_state.all_articles = []  # Clear old results on error
            except Exception as e:
                st.error(f"An unexpected error occurred: {e}")
                st.session_state.all_articles = []  # Clear old results on exception

# --- PAGINATION: Display Logic ---
# This part now runs *outside* the 'if submit_button' block
# so it can re-run when pagination buttons are clicked.

if st.session_state.all_articles:
    total_articles = st.session_state.total_results
    articles_per_page = 10

    # Calculate total pages
    total_pages = (total_articles + articles_per_page - 1) // articles_per_page

    st.success(f"Found and analyzed {total_articles} articles.")

    # Calculate start/end indices for the current page
    start_index = (st.session_state.page - 1) * articles_per_page
    end_index = min(st.session_state.page * articles_per_page, total_articles)

    # Get just the articles for this page
    articles_to_display = st.session_state.all_articles[start_index:end_index]

    # Display only the 10 articles
    display_articles(articles_to_display)

    st.divider()

    # --- PAGINATION: Controls (Previous, Page #, Next) ---
    col1, col2, col3 = st.columns([1, 2, 1])

    with col1:
        # Disable button if on page 1
        if st.session_state.page > 1:
            if st.button("⬅️ Previous Page"):
                st.session_state.page -= 1
                st.rerun()  # Re-run the script to show the previous page
        else:
            st.button("⬅️ Previous Page", disabled=True)

    with col2:
        st.write(f"Page **{st.session_state.page}** of **{total_pages}**")

    with col3:
        # Disable button if on the last page
        if st.session_state.page < total_pages:
            if st.button("Next Page ➡️"):
                st.session_state.page += 1
                st.rerun()  # Re-run the script to show the next page
        else:
            st.button("Next Page ➡️", disabled=True)

elif submit_button:  # Handle case where search was submitted but found 0 results
    st.warning("No articles found for your criteria. Please try different settings.")

else:
    st.info("Please enter a search topic and date in the sidebar.")