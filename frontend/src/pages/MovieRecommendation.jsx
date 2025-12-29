import React, { useState, useEffect } from 'react'
import axios from 'axios'

const MovieRecommendation = () => {
  const [movieInput, setMovieInput] = useState('')
  const [searchResults, setSearchResults] = useState([])
  const [selectedMovie, setSelectedMovie] = useState(null)
  const [recommendations, setRecommendations] = useState(null)
  const [loading, setLoading] = useState(false)
  const [searching, setSearching] = useState(false)

  const handleSearch = async (e) => {
    e.preventDefault()
    if (!movieInput.trim()) return

    setSearching(true)
    setSearchResults([])

    try {
      const response = await axios.get(`/api/movie/movies?query=${encodeURIComponent(movieInput)}`)
      setSearchResults(response.data.data || [])
    } catch (error) {
      console.error('Error:', error)
    } finally {
      setSearching(false)
    }
  }

  const handleRecommend = async (movieTitle) => {
    if (!movieTitle) return

    setLoading(true)
    setRecommendations(null)
    setSelectedMovie(movieTitle)

    try {
      const response = await axios.post('/api/movie/recommend', {
        movie_title: movieTitle,
        num_recommendations: 5
      })
      setRecommendations(response.data.data)
    } catch (error) {
      console.error('Error:', error)
      alert(error.response?.data?.detail || 'Failed to get recommendations')
    } finally {
      setLoading(false)
    }
  }

  return (
    <div>
      <h1 className="text-3xl font-bold mb-6">Movie Recommendation</h1>
      
      <div className="bg-white p-6 rounded-lg shadow-md mb-6">
        <form onSubmit={handleSearch}>
          <div className="mb-4">
            <label className="block text-gray-700 font-bold mb-2">
              Search for a Movie
            </label>
            <div className="flex gap-2">
              <input
                type="text"
                value={movieInput}
                onChange={(e) => setMovieInput(e.target.value)}
                className="flex-1 px-3 py-2 border border-gray-300 rounded"
                placeholder="Enter movie name (e.g., The Matrix, Inception)..."
                required
              />
              <button
                type="submit"
                disabled={searching || !movieInput.trim()}
                className="bg-blue-500 text-white px-6 py-2 rounded hover:bg-blue-600 disabled:bg-gray-400"
              >
                {searching ? 'Searching...' : 'Search'}
              </button>
            </div>
          </div>
        </form>

        {searchResults.length > 0 && (
          <div className="mt-4">
            <h3 className="font-bold mb-2">Search Results:</h3>
            <div className="space-y-2 max-h-60 overflow-y-auto">
              {searchResults.map((movie) => (
                <div
                  key={movie.id}
                  className="flex items-center justify-between p-2 border rounded hover:bg-gray-50 cursor-pointer"
                  onClick={() => handleRecommend(movie.title)}
                >
                  <div className="flex items-center gap-3">
                    {movie.poster_path && (
                      <img
                        src={movie.poster_path}
                        alt={movie.title}
                        className="w-12 h-16 object-cover rounded"
                      />
                    )}
                    <div>
                      <p className="font-semibold">{movie.title}</p>
                      {movie.release_date && (
                        <p className="text-sm text-gray-500">{new Date(movie.release_date).getFullYear()}</p>
                      )}
                      <p className="text-sm text-yellow-500">⭐ {movie.rating.toFixed(1)}</p>
                    </div>
                  </div>
                  <button
                    onClick={(e) => {
                      e.stopPropagation()
                      handleRecommend(movie.title)
                    }}
                    className="bg-green-500 text-white px-4 py-1 rounded hover:bg-green-600"
                  >
                    Get Recommendations
                  </button>
                </div>
              ))}
            </div>
          </div>
        )}
      </div>

      {loading && (
        <div className="bg-white p-6 rounded-lg shadow-md text-center">
          <p>Getting recommendations for "{selectedMovie}"...</p>
        </div>
      )}

      {recommendations && (
        <div className="space-y-6">
          {recommendations.searched_movie && (
            <div className="bg-white p-6 rounded-lg shadow-md">
              <h2 className="text-2xl font-bold mb-4">You Searched For</h2>
              <div className="flex gap-4">
                {recommendations.searched_movie.poster_path && (
                  <img
                    src={recommendations.searched_movie.poster_path}
                    alt={recommendations.searched_movie.title}
                    className="w-32 h-48 object-cover rounded"
                  />
                )}
                <div>
                  <h3 className="text-xl font-bold">{recommendations.searched_movie.title}</h3>
                  <p className="text-gray-600">{recommendations.searched_movie.genre}</p>
                  <p className="text-yellow-500">⭐ {recommendations.searched_movie.rating.toFixed(1)}</p>
                  {recommendations.searched_movie.release_date && (
                    <p className="text-sm text-gray-500">
                      Released: {new Date(recommendations.searched_movie.release_date).getFullYear()}
                    </p>
                  )}
                  {recommendations.searched_movie.runtime && (
                    <p className="text-sm text-gray-500">Runtime: {recommendations.searched_movie.runtime} min</p>
                  )}
                  {recommendations.searched_movie.overview && (
                    <p className="mt-2 text-sm">{recommendations.searched_movie.overview}</p>
                  )}
                </div>
              </div>
            </div>
          )}

          {recommendations.recommendations && recommendations.recommendations.length > 0 && (
            <div className="bg-white p-6 rounded-lg shadow-md">
              <h2 className="text-2xl font-bold mb-4">Recommended Movies</h2>
              <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-3 gap-4">
                {recommendations.recommendations.map((movie) => (
                  <div key={movie.id} className="border p-4 rounded hover:shadow-lg transition">
                    {movie.poster_path && (
                      <img
                        src={movie.poster_path}
                        alt={movie.title}
                        className="w-full h-64 object-cover rounded mb-2"
                      />
                    )}
                    <h3 className="font-bold text-lg">{movie.title}</h3>
                    <p className="text-gray-600 text-sm">{movie.genre}</p>
                    <p className="text-yellow-500">⭐ {movie.rating.toFixed(1)}</p>
                    {movie.release_date && (
                      <p className="text-xs text-gray-500">
                        {new Date(movie.release_date).getFullYear()}
                      </p>
                    )}
                    {movie.overview && (
                      <p className="text-xs text-gray-600 mt-2 line-clamp-3">{movie.overview}</p>
                    )}
                  </div>
                ))}
              </div>
            </div>
          )}
        </div>
      )}
    </div>
  )
}

export default MovieRecommendation

