import streamlit as st
import pickle
import requests
from requests.adapters import HTTPAdapter
from requests.packages.urllib3.util.retry import Retry
import logging

# Configure logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

# Function to fetch the poster of the movie using The Movie Database API
def fetch_poster(movie_id):
    try:
        api_key = st.secrets["api"]["tmdb_key"]
        url = f"https://api.themoviedb.org/3/movie/{movie_id}?api_key={api_key}"

        # Set up retry strategy
        retry_strategy = Retry(
            total=3,  # Total number of retries
            status_forcelist=[429, 500, 502, 503, 504],  # Retry on these status codes
            allowed_methods=["HEAD", "GET", "OPTIONS"],  # Only retry on specified HTTP methods
            backoff_factor=1  # Exponential backoff factor
        )
        adapter = HTTPAdapter(max_retries=retry_strategy)
        http = requests.Session()
        http.mount("https://", adapter)
        http.mount("http://", adapter)

        # Log the URL being requested
        logger.info(f"Requesting URL: {url}")

        # Increase the timeout significantly to handle slower responses
        response = http.get(url, timeout=20)
        response.raise_for_status()
        data = response.json()
        poster_path = data.get('poster_path')
        if poster_path:
            full_path = f"https://image.tmdb.org/t/p/w500{poster_path}"
            return full_path
    except requests.exceptions.RequestException as e:
        st.error(f"Error fetching poster: {e}")
        logger.error(f"Error fetching poster: {e}")
    return None

# Load the movie list and similarity matrix from pickle files
movies = pickle.load(open("movies_list.pkl", 'rb'))
similarity = pickle.load(open("similarity.pkl", 'rb'))
movies_list = movies['title'].values

# Streamlit app header
st.header("Movie Recommender System")

# Dropdown for selecting a movie
selected_movie = st.selectbox("Select a movie:", movies_list, key='movie_select')

# Function to recommend movies based on similarity
def recommend(movie):
    index = movies[movies['title'] == movie].index[0]
    distances = sorted(list(enumerate(similarity[index])), reverse=True, key=lambda x: x[1])
    recommended_movies = []
    recommended_posters = []
    for i in distances[1:6]:
        movie_id = movies.iloc[i[0]].id
        recommended_movies.append(movies.iloc[i[0]].title)
        recommended_posters.append(fetch_poster(movie_id))
    return recommended_movies, recommended_posters

# Button to trigger the recommendation
if st.button("Recommend"):
    with st.spinner('Fetching recommendations...'):
        movie_names, movie_posters = recommend(selected_movie)
        cols = st.columns(5)
        for col, name, poster in zip(cols, movie_names, movie_posters):
            with col:
                st.text(name)
                if poster:
                    st.image(poster)
                else:
                    st.text("Poster not available")
