# Movie Recommendation Service

## Overview
This service provides movie search and recommendation functionality with support for multiple API providers. Users can search for any movie by name and get recommendations with detailed information including posters, ratings, overview, cast, and more.

## Features
- **Dynamic Movie Search**: Search for any movie by name (not limited to predefined list)
- **Movie Recommendations**: Get similar movies based on your search
- **Detailed Movie Information**: Includes poster, overview, ratings, release date, cast, director, and more
- **Multiple API Support**: Supports TMDB, OMDb, TasteDive, or local dataset
- **Automatic Fallback**: Automatically falls back to alternative APIs if primary fails
- **No API Key Required**: Can work with local dataset if no API keys are provided

## API Provider Options

### 1. TMDB (The Movie Database) - **Recommended**
- **Pros**: Most comprehensive database, high-quality images, detailed metadata
- **Cons**: Requires API key
- **Free Tier**: Unlimited requests (with rate limits)
- **Get API Key**: https://www.themoviedb.org/settings/api

### 2. OMDb (Open Movie Database)
- **Pros**: Simple API, good for basic movie info
- **Cons**: Limited free tier (1,000 requests/day)
- **Free Tier**: 1,000 requests per day
- **Get API Key**: http://www.omdbapi.com/apikey.aspx

### 3. TasteDive
- **Pros**: Good for recommendations, supports multiple media types
- **Cons**: Less detailed movie information
- **Free Tier**: Available
- **Get API Key**: https://tastedive.com/read/api

### 4. Local Dataset (No API Key Required)
- **Pros**: No API key needed, works offline, no rate limits
- **Cons**: Limited to ~10 predefined movies
- **Use Case**: Testing, development, or when API keys are unavailable

## Setup

### Option 1: Using TMDB (Recommended)

1. **Get TMDB API Key**
   - Visit [TMDB](https://www.themoviedb.org/)
   - Create a free account
   - Go to [API Settings](https://www.themoviedb.org/settings/api)
   - Request an API key (free tier is sufficient)
   - Copy your API key

2. **Configure Environment Variables**
   ```env
   MOVIE_API_PROVIDER=tmdb
   TMDB_API_KEY=your_tmdb_api_key_here
   ```

### Option 2: Using OMDb

1. **Get OMDb API Key**
   - Visit http://www.omdbapi.com/apikey.aspx
   - Sign up for free tier
   - Copy your API key

2. **Configure Environment Variables**
   ```env
   MOVIE_API_PROVIDER=omdb
   OMDB_API_KEY=your_omdb_api_key_here
   ```

### Option 3: Using TasteDive

1. **Get TasteDive API Key**
   - Visit https://tastedive.com/read/api
   - Sign up and get your API key

2. **Configure Environment Variables**
   ```env
   MOVIE_API_PROVIDER=tastedive
   TASTEDIVE_API_KEY=your_tastedive_api_key_here
   ```

### Option 4: Using Local Dataset (No API Key)

1. **Configure Environment Variables**
   ```env
   MOVIE_API_PROVIDER=local
   # No API keys needed!
   ```

### Complete Environment Setup

Create a `.env` file in `ai-services/movie-recommendation/`:

```env
SERVICE_PORT=8004
SERVICE_NAME=movie-recommendation
MOVIE_API_PROVIDER=tmdb

# Add API keys for your chosen provider
TMDB_API_KEY=your_tmdb_api_key_here
# OMDB_API_KEY=your_omdb_api_key_here
# TASTEDIVE_API_KEY=your_tastedive_api_key_here

ALLOWED_ORIGINS=http://localhost:3000,http://localhost:3001
LOG_LEVEL=INFO
```

Or copy from the example:
```bash
cp env-examples/movie-recommendation.env.example ai-services/movie-recommendation/.env
```

Then edit the `.env` file and configure your preferred provider.

### 3. Install Dependencies
```bash
cd ai-services/movie-recommendation
pip install -r requirements.txt
```

### 4. Run the Service
```bash
python main.py
```

Or using uvicorn:
```bash
uvicorn main:app --host 0.0.0.0 --port 8004
```

## API Endpoints

### Search Movies
```
GET /movies?query={movie_name}
```
Search for movies by name. Returns up to 20 results.

### Get Movie Details
```
GET /movie/{movie_id}
```
Get detailed information about a specific movie.

### Get Recommendations
```
POST /recommend
Body: {
  "movie_title": "The Matrix",
  "num_recommendations": 5
}
```
Get movie recommendations based on a movie title.

## Usage Example

### Search for Movies
```python
import requests

response = requests.get('http://localhost:8004/movies?query=Inception')
movies = response.json()['data']
```

### Get Recommendations
```python
response = requests.post('http://localhost:8004/recommend', json={
    'movie_title': 'The Matrix',
    'num_recommendations': 5
})
recommendations = response.json()['data']
```

## Frontend Integration
The frontend allows users to:
1. Type any movie name in the search box
2. See search results with posters and ratings
3. Click on a movie to get recommendations
4. View detailed movie information including overview, cast, and director

## Fallback Behavior

The service automatically falls back to alternative APIs if the primary one fails:
1. Tries configured provider first
2. Falls back to other available APIs
3. Finally uses local dataset if all APIs fail

This ensures the service works even if one API is down or rate-limited.

## Comparison Table

| Feature | TMDB | OMDb | TasteDive | Local |
|---------|------|------|-----------|-------|
| API Key Required | Yes | Yes | Yes | No |
| Movie Database Size | Very Large | Large | Medium | Small (10) |
| Recommendations | Excellent | Good | Excellent | Basic |
| Movie Details | Comprehensive | Good | Basic | Basic |
| Images/Posters | Yes | Yes | Limited | No |
| Rate Limits | 40/10s | 1,000/day | Varies | None |
| Offline Support | No | No | No | Yes |

## Notes
- The service requires an active internet connection for API providers (except local mode)
- API rate limits apply based on your chosen provider
- Genre information is cached on startup for better performance (TMDB only)
- Movie posters and images are served from provider CDNs
- Local dataset is perfect for testing and development

