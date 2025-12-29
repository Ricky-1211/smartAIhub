"""
Movie Recommendation Service
"""
from fastapi import FastAPI, HTTPException
from fastapi.middleware.cors import CORSMiddleware
from pydantic import BaseModel
from typing import List, Optional, Dict
import sys
import os
import pandas as pd
from sklearn.feature_extraction.text import TfidfVectorizer
from sklearn.metrics.pairwise import cosine_similarity
import numpy as np
import requests
from dotenv import load_dotenv

load_dotenv()

sys.path.append(os.path.join(os.path.dirname(__file__), '../..'))

from shared.config import ALLOWED_ORIGINS
from shared.utils import create_response, log_error

app = FastAPI(title="Movie Recommendation Service", version="1.0.0")

app.add_middleware(
    CORSMiddleware,
    allow_origins=ALLOWED_ORIGINS,
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# API Provider Configuration
# Options: "tmdb", "omdb", "tastedive", "local"
API_PROVIDER = os.getenv("MOVIE_API_PROVIDER", "tmdb").lower()

# TMDB API Configuration
TMDB_API_KEY = os.getenv("TMDB_API_KEY", "")
TMDB_BASE_URL = "https://api.themoviedb.org/3"
TMDB_IMAGE_BASE_URL = "https://image.tmdb.org/t/p/w500"

# OMDb API Configuration (Alternative - Free tier available)
OMDB_API_KEY = os.getenv("OMDB_API_KEY", "")
OMDB_BASE_URL = "http://www.omdbapi.com"

# TasteDive API Configuration (Alternative - Free tier available)
TASTEDIVE_API_KEY = os.getenv("TASTEDIVE_API_KEY", "")
TASTEDIVE_BASE_URL = "https://tastedive.com/api/similar"

# Local fallback movie dataset
LOCAL_MOVIES_DATASET = [
    {"id": 1, "title": "The Matrix", "genre": "Sci-Fi, Action", "rating": 8.7, "year": 1999, "overview": "A computer hacker learns about the true nature of reality"},
    {"id": 2, "title": "Inception", "genre": "Sci-Fi, Thriller", "rating": 8.8, "year": 2010, "overview": "A thief who enters people's dreams"},
    {"id": 3, "title": "The Dark Knight", "genre": "Action, Crime", "rating": 9.0, "year": 2008, "overview": "Batman faces the Joker"},
    {"id": 4, "title": "Pulp Fiction", "genre": "Crime, Drama", "rating": 8.9, "year": 1994, "overview": "Interconnected stories of crime"},
    {"id": 5, "title": "Fight Club", "genre": "Drama, Thriller", "rating": 8.8, "year": 1999, "overview": "An insomniac office worker starts a fight club"},
    {"id": 6, "title": "Interstellar", "genre": "Sci-Fi, Drama", "rating": 8.6, "year": 2014, "overview": "Explorers travel through a wormhole"},
    {"id": 7, "title": "The Shawshank Redemption", "genre": "Drama", "rating": 9.3, "year": 1994, "overview": "Two imprisoned men bond over years"},
    {"id": 8, "title": "Forrest Gump", "genre": "Drama, Romance", "rating": 8.8, "year": 1994, "overview": "The life story of Forrest Gump"},
    {"id": 9, "title": "The Godfather", "genre": "Crime, Drama", "rating": 9.2, "year": 1972, "overview": "The aging patriarch of a crime dynasty"},
    {"id": 10, "title": "Titanic", "genre": "Drama, Romance", "rating": 7.9, "year": 1997, "overview": "A love story aboard the Titanic"},
]

# Cache for movies (in production, use Redis or database)
movies_cache = {}
genre_cache = {}  # Cache for genre ID to name mapping
movies_df = None
vectorizer = None
tfidf_matrix = None


def search_movie_omdb(query: str) -> Optional[Dict]:
    """Search for a movie using OMDb API"""
    if not OMDB_API_KEY:
        return None
    
    try:
        url = OMDB_BASE_URL
        params = {
            "apikey": OMDB_API_KEY,
            "t": query,  # Title search
            "type": "movie"
        }
        response = requests.get(url, params=params, timeout=10)
        response.raise_for_status()
        data = response.json()
        
        if data.get("Response") == "True":
            return {
                "id": hash(data.get("imdbID", "")),  # Use hash as ID
                "title": data.get("Title"),
                "genre": data.get("Genre", "Unknown"),
                "rating": float(data.get("imdbRating", 0)) / 10.0 if data.get("imdbRating") != "N/A" else 0.0,
                "overview": data.get("Plot", ""),
                "release_date": data.get("Released", ""),
                "poster_path": data.get("Poster") if data.get("Poster") != "N/A" else None,
                "year": data.get("Year", ""),
                "director": data.get("Director", ""),
                "actors": data.get("Actors", "").split(", ") if data.get("Actors") else []
            }
    except Exception as e:
        log_error("movie-service", e, {"action": "omdb_search"})
    
    return None


def search_movie_tastedive(query: str) -> Optional[Dict]:
    """Search for a movie using TasteDive API"""
    if not TASTEDIVE_API_KEY:
        return None
    
    try:
        url = TASTEDIVE_BASE_URL
        params = {
            "q": query,
            "type": "movies",
            "limit": 1,
            "k": TASTEDIVE_API_KEY
        }
        response = requests.get(url, params=params, timeout=10)
        response.raise_for_status()
        data = response.json()
        
        if data.get("Similar") and data.get("Similar").get("Results"):
            result = data["Similar"]["Results"][0]
            return {
                "id": hash(result.get("Name", "")),
                "title": result.get("Name"),
                "genre": ", ".join(result.get("Type", [])),
                "rating": 0.0,  # TasteDive doesn't provide ratings
                "overview": "",
                "release_date": "",
                "poster_path": None
            }
    except Exception as e:
        log_error("movie-service", e, {"action": "tastedive_search"})
    
    return None


def search_movie_local(query: str) -> Optional[Dict]:
    """Search for a movie in local dataset"""
    query_lower = query.lower()
    for movie in LOCAL_MOVIES_DATASET:
        if query_lower in movie["title"].lower():
            return {
                "id": movie["id"],
                "title": movie["title"],
                "genre": movie["genre"],
                "rating": movie["rating"],
                "overview": movie.get("overview", ""),
                "release_date": str(movie.get("year", "")),
                "poster_path": None,
                "year": movie.get("year")
            }
    return None


def get_genre_list() -> Dict[int, str]:
    """Get genre list from TMDB and cache it"""
    global genre_cache
    
    if genre_cache:
        return genre_cache
    
    if not TMDB_API_KEY or API_PROVIDER != "tmdb":
        return {}
    
    try:
        url = f"{TMDB_BASE_URL}/genre/movie/list"
        params = {
            "api_key": TMDB_API_KEY,
            "language": "en-US"
        }
        response = requests.get(url, params=params, timeout=10)
        response.raise_for_status()
        data = response.json()
        
        genre_cache = {genre["id"]: genre["name"] for genre in data.get("genres", [])}
        return genre_cache
    except Exception as e:
        log_error("movie-service", e, {"action": "get_genres"})
        return {}


class RecommendationRequest(BaseModel):
    movie_title: str
    num_recommendations: int = 5


class MovieRecommendation(BaseModel):
    id: int
    title: str
    genre: str
    rating: float
    similarity_score: Optional[float] = None
    overview: Optional[str] = None
    release_date: Optional[str] = None
    poster_path: Optional[str] = None
    backdrop_path: Optional[str] = None
    vote_count: Optional[int] = None
    popularity: Optional[float] = None


def search_movie_tmdb(query: str) -> Optional[Dict]:
    """Search for a movie using TMDB API"""
    if not TMDB_API_KEY:
        return None
    
    try:
        url = f"{TMDB_BASE_URL}/search/movie"
        params = {
            "api_key": TMDB_API_KEY,
            "query": query,
            "language": "en-US"
        }
        response = requests.get(url, params=params, timeout=10)
        response.raise_for_status()
        data = response.json()
        
        if data.get("results") and len(data["results"]) > 0:
            return data["results"][0]  # Return first result
    except Exception as e:
        log_error("movie-service", e, {"action": "tmdb_search"})
    
    return None


def search_movie_unified(query: str) -> Optional[Dict]:
    """Search for a movie using the configured API provider with fallbacks"""
    # Try configured provider first
    if API_PROVIDER == "tmdb" and TMDB_API_KEY:
        result = search_movie_tmdb(query)
        if result:
            return result
    
    if API_PROVIDER == "omdb" and OMDB_API_KEY:
        result = search_movie_omdb(query)
        if result:
            return result
    
    if API_PROVIDER == "tastedive" and TASTEDIVE_API_KEY:
        result = search_movie_tastedive(query)
        if result:
            return result
    
    # Fallback chain: try other providers
    if API_PROVIDER != "tmdb" and TMDB_API_KEY:
        result = search_movie_tmdb(query)
        if result:
            return result
    
    if API_PROVIDER != "omdb" and OMDB_API_KEY:
        result = search_movie_omdb(query)
        if result:
            return result
    
    if API_PROVIDER != "tastedive" and TASTEDIVE_API_KEY:
        result = search_movie_tastedive(query)
        if result:
            return result
    
    # Final fallback: local dataset
    if API_PROVIDER == "local":
        result = search_movie_local(query)
        if result:
            return result
    
    # Last resort: try local dataset
    return search_movie_local(query)


def get_movie_details_tmdb(movie_id: int) -> Optional[Dict]:
    """Get detailed movie information from TMDB"""
    if not TMDB_API_KEY:
        return None
    
    try:
        url = f"{TMDB_BASE_URL}/movie/{movie_id}"
        params = {
            "api_key": TMDB_API_KEY,
            "language": "en-US",
            "append_to_response": "credits"
        }
        response = requests.get(url, params=params, timeout=10)
        response.raise_for_status()
        return response.json()
    except Exception as e:
        log_error("movie-service", e, {"action": "tmdb_details"})
    
    return None


def get_similar_movies_tmdb(movie_id: int, num_recommendations: int = 5) -> List[Dict]:
    """Get similar movies from TMDB"""
    if not TMDB_API_KEY:
        return []
    
    try:
        url = f"{TMDB_BASE_URL}/movie/{movie_id}/similar"
        params = {
            "api_key": TMDB_API_KEY,
            "language": "en-US",
            "page": 1
        }
        response = requests.get(url, params=params, timeout=10)
        response.raise_for_status()
        data = response.json()
        
        # Get genre mapping
        genre_map = get_genre_list()
        
        movies = []
        for movie in data.get("results", [])[:num_recommendations]:
            genre_ids = movie.get("genre_ids", [])
            genre_names = [genre_map.get(gid, "Unknown") for gid in genre_ids]
            movies.append({
                "id": movie.get("id"),
                "title": movie.get("title"),
                "genre": ", ".join(genre_names[:3]) if genre_names else "Unknown",  # Limit to 3 genres
                "rating": movie.get("vote_average", 0.0) / 10.0,  # Convert to 0-10 scale
                "overview": movie.get("overview"),
                "release_date": movie.get("release_date"),
                "poster_path": f"{TMDB_IMAGE_BASE_URL}{movie.get('poster_path', '')}" if movie.get("poster_path") else None,
                "backdrop_path": f"{TMDB_IMAGE_BASE_URL}{movie.get('backdrop_path', '')}" if movie.get("backdrop_path") else None,
                "vote_count": movie.get("vote_count"),
                "popularity": movie.get("popularity")
            })
        
        return movies
    except Exception as e:
        log_error("movie-service", e, {"action": "tmdb_similar"})
    
    return []


def initialize_model():
    """Initialize recommendation model (for fallback)"""
    global movies_df, vectorizer, tfidf_matrix
    
    # This is now a fallback - primary method uses TMDB API
    # Keep for backward compatibility
    pass


def get_recommendations_local(movie_title: str, num_recommendations: int = 5) -> List[dict]:
    """Get movie recommendations from local dataset using content similarity"""
    global movies_df, vectorizer, tfidf_matrix
    
    # Initialize local model if not done
    if movies_df is None:
        movies_df = pd.DataFrame(LOCAL_MOVIES_DATASET)
        movies_df['features'] = movies_df['title'] + ' ' + movies_df['genre']
        vectorizer = TfidfVectorizer(stop_words='english')
        tfidf_matrix = vectorizer.fit_transform(movies_df['features'])
    
    # Find movie
    movie_idx = movies_df[movies_df['title'].str.contains(movie_title, case=False, na=False)]
    
    if movie_idx.empty:
        return []
    
    movie_idx = movie_idx.index[0]
    
    # Calculate similarity
    movie_vector = tfidf_matrix[movie_idx:movie_idx+1]
    similarities = cosine_similarity(movie_vector, tfidf_matrix).flatten()
    
    # Get top similar movies (excluding the movie itself)
    similar_indices = similarities.argsort()[::-1][1:num_recommendations+1]
    
    recommendations = []
    for idx in similar_indices:
        movie = movies_df.iloc[idx]
        recommendations.append({
            "id": int(movie['id']),
            "title": movie['title'],
            "genre": movie['genre'],
            "rating": float(movie['rating']),
            "overview": movie.get('overview', ''),
            "release_date": str(movie.get('year', '')),
            "similarity_score": float(similarities[idx])
        })
    
    return recommendations


def get_recommendations(movie_title: str, num_recommendations: int = 5) -> List[dict]:
    """Get movie recommendations using configured API provider"""
    # Search for the movie
    movie_result = search_movie_unified(movie_title)
    
    if not movie_result:
        raise HTTPException(
            status_code=404,
            detail=f"Movie '{movie_title}' not found. Please check the spelling or try a different movie."
        )
    
    movie_id = movie_result.get("id")
    
    # Try TMDB similar movies if available
    if API_PROVIDER == "tmdb" and TMDB_API_KEY and isinstance(movie_id, int):
        recommendations = get_similar_movies_tmdb(movie_id, num_recommendations)
        if recommendations:
            return recommendations
    
    # Fallback to local recommendations
    recommendations = get_recommendations_local(movie_title, num_recommendations)
    
    if not recommendations:
        raise HTTPException(
            status_code=404,
            detail=f"Could not find similar movies for '{movie_title}'"
        )
    
    return recommendations


@app.on_event("startup")
async def startup():
    initialize_model()
    
    # Log configured API provider
    print(f"Movie Recommendation Service - API Provider: {API_PROVIDER}")
    
    # Check API keys based on provider
    if API_PROVIDER == "tmdb" and not TMDB_API_KEY:
        import warnings
        warnings.warn(
            "TMDB_API_KEY not configured. Please set TMDB_API_KEY in your environment variables. "
            "Get your free API key from: https://www.themoviedb.org/settings/api"
        )
    elif API_PROVIDER == "omdb" and not OMDB_API_KEY:
        import warnings
        warnings.warn(
            "OMDB_API_KEY not configured. Please set OMDB_API_KEY in your environment variables. "
            "Get your free API key from: http://www.omdbapi.com/apikey.aspx"
        )
    elif API_PROVIDER == "tastedive" and not TASTEDIVE_API_KEY:
        import warnings
        warnings.warn(
            "TASTEDIVE_API_KEY not configured. Please set TASTEDIVE_API_KEY in your environment variables. "
            "Get your free API key from: https://tastedive.com/read/api"
        )
    elif API_PROVIDER == "local":
        print("Using local movie dataset (no API key required)")
    
    # Pre-load genre list if using TMDB
    if API_PROVIDER == "tmdb" and TMDB_API_KEY:
        get_genre_list()


@app.get("/health")
async def health_check():
    return create_response(True, "Movie recommendation service is healthy")


@app.get("/movies")
async def get_movies(query: Optional[str] = None):
    """Search movies using configured API provider"""
    if not query:
        return create_response(True, "Please provide a search query", [])
    
    try:
        movies = []
        
        # Try TMDB search
        if TMDB_API_KEY:
            try:
                url = f"{TMDB_BASE_URL}/search/movie"
                params = {
                    "api_key": TMDB_API_KEY,
                    "query": query,
                    "language": "en-US",
                    "page": 1
                }
                response = requests.get(url, params=params, timeout=10)
                response.raise_for_status()
                data = response.json()
                
                genre_map = get_genre_list()
                
                for movie in data.get("results", [])[:20]:
                    genre_ids = movie.get("genre_ids", [])
                    genre_names = [genre_map.get(gid, "Unknown") for gid in genre_ids]
                    movies.append({
                        "id": movie.get("id"),
                        "title": movie.get("title"),
                        "genre": ", ".join(genre_names[:3]) if genre_names else "Unknown",
                        "rating": movie.get("vote_average", 0.0) / 10.0,
                        "overview": movie.get("overview"),
                        "release_date": movie.get("release_date"),
                        "poster_path": f"{TMDB_IMAGE_BASE_URL}{movie.get('poster_path', '')}" if movie.get("poster_path") else None,
                        "vote_count": movie.get("vote_count"),
                        "popularity": movie.get("popularity")
                    })
            except:
                pass
        
        # Fallback to local dataset if no results
        if not movies:
            query_lower = query.lower()
            for movie in LOCAL_MOVIES_DATASET:
                if query_lower in movie["title"].lower():
                    movies.append({
                        "id": movie["id"],
                        "title": movie["title"],
                        "genre": movie["genre"],
                        "rating": movie["rating"],
                        "overview": movie.get("overview", ""),
                        "release_date": str(movie.get("year", "")),
                        "poster_path": None
                    })
        
        if not movies:
            return create_response(
                False,
                f"No movies found for '{query}'. Please check your API keys or try a different search term.",
                []
            )
        
        return create_response(True, f"Found {len(movies)} movies", movies)
    except Exception as e:
        log_error("movie-service", e)
        raise HTTPException(status_code=500, detail="Movie search failed")


@app.get("/movie/{movie_id}")
async def get_movie_details(movie_id: int):
    """Get detailed movie information"""
    if not TMDB_API_KEY:
        raise HTTPException(status_code=500, detail="TMDB API key not configured")
    
    try:
        movie_details = get_movie_details_tmdb(movie_id)
        if not movie_details:
            raise HTTPException(status_code=404, detail="Movie not found")
        
        # Format response
        genres = [g["name"] for g in movie_details.get("genres", [])]
        cast = [c["name"] for c in movie_details.get("credits", {}).get("cast", [])[:5]]
        
        formatted_movie = {
            "id": movie_details.get("id"),
            "title": movie_details.get("title"),
            "genre": ", ".join(genres),
            "rating": movie_details.get("vote_average", 0.0) / 10.0,
            "overview": movie_details.get("overview"),
            "release_date": movie_details.get("release_date"),
            "poster_path": f"{TMDB_IMAGE_BASE_URL}{movie_details.get('poster_path', '')}" if movie_details.get("poster_path") else None,
            "backdrop_path": f"{TMDB_IMAGE_BASE_URL}{movie_details.get('backdrop_path', '')}" if movie_details.get("backdrop_path") else None,
            "vote_count": movie_details.get("vote_count"),
            "popularity": movie_details.get("popularity"),
            "runtime": movie_details.get("runtime"),
            "cast": cast,
            "director": next((c["name"] for c in movie_details.get("credits", {}).get("crew", []) if c.get("job") == "Director"), None)
        }
        
        return create_response(True, "Movie details retrieved", formatted_movie)
    except HTTPException:
        raise
    except Exception as e:
        log_error("movie-service", e)
        raise HTTPException(status_code=500, detail="Failed to get movie details")


@app.post("/recommend")
async def recommend_movies(request: RecommendationRequest):
    """Get movie recommendations"""
    try:
        recommendations = get_recommendations(
            request.movie_title,
            request.num_recommendations
        )
        
        # Get detailed info for the searched movie
        movie_result = search_movie_unified(request.movie_title)
        searched_movie_info = None
        
        if movie_result:
            # Try to get full details from TMDB if available
            if TMDB_API_KEY and isinstance(movie_result.get("id"), int):
                movie_details = get_movie_details_tmdb(movie_result.get("id"))
                if movie_details:
                    genres = [g["name"] for g in movie_details.get("genres", [])]
                    searched_movie_info = {
                        "id": movie_details.get("id"),
                        "title": movie_details.get("title"),
                        "genre": ", ".join(genres),
                        "rating": movie_details.get("vote_average", 0.0) / 10.0,
                        "overview": movie_details.get("overview"),
                        "release_date": movie_details.get("release_date"),
                        "poster_path": f"{TMDB_IMAGE_BASE_URL}{movie_details.get('poster_path', '')}" if movie_details.get("poster_path") else None,
                        "runtime": movie_details.get("runtime"),
                        "vote_count": movie_details.get("vote_count")
                    }
            
            # Fallback to basic info
            if not searched_movie_info:
                searched_movie_info = {
                    "id": movie_result.get("id"),
                    "title": movie_result.get("title"),
                    "genre": movie_result.get("genre", "Unknown"),
                    "rating": movie_result.get("rating", 0.0),
                    "overview": movie_result.get("overview", ""),
                    "release_date": movie_result.get("release_date", ""),
                    "poster_path": movie_result.get("poster_path")
                }
        
        return create_response(
            True,
            f"Recommendations for '{request.movie_title}'",
            {
                "searched_movie": searched_movie_info,
                "recommendations": recommendations,
                "api_provider": API_PROVIDER
            }
        )
    except HTTPException:
        raise
    except Exception as e:
        log_error("movie-service", e)
        raise HTTPException(status_code=500, detail="Recommendation failed")


@app.get("/recommend/{movie_title}")
async def recommend_by_title(movie_title: str, num: int = 5):
    """Get recommendations by movie title (GET endpoint)"""
    request = RecommendationRequest(movie_title=movie_title, num_recommendations=num)
    return await recommend_movies(request)


if __name__ == "__main__":
    import uvicorn
    uvicorn.run(app, host="0.0.0.0", port=8004)

