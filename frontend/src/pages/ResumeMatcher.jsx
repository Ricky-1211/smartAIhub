import React, { useState } from 'react'
import axios from 'axios'

const ResumeMatcher = () => {
  const [resumeText, setResumeText] = useState('')
  const [jobTitle, setJobTitle] = useState('')
  const [jobDescription, setJobDescription] = useState('')
  const [requiredSkills, setRequiredSkills] = useState('')
  const [result, setResult] = useState(null)
  const [loading, setLoading] = useState(false)

  const handleSubmit = async (e) => {
    e.preventDefault()
    setLoading(true)
    setResult(null)

    try {
      const skillsList = requiredSkills.split(',').map(s => s.trim()).filter(s => s)
      const response = await axios.post('/api/resume/match', {
        resume_text: resumeText,
        job_description: {
          title: jobTitle,
          description: jobDescription,
          required_skills: skillsList
        }
      })
      setResult(response.data.data)
    } catch (error) {
      console.error('Error:', error)
    } finally {
      setLoading(false)
    }
  }

  return (
    <div>
      <h1 className="text-3xl font-bold mb-6">Resume & Job Matching</h1>
      
      <div className="bg-white p-6 rounded-lg shadow-md mb-6">
        <form onSubmit={handleSubmit}>
          <div className="mb-4">
            <label className="block text-gray-700 font-bold mb-2">
              Resume Text
            </label>
            <textarea
              value={resumeText}
              onChange={(e) => setResumeText(e.target.value)}
              rows="8"
              className="w-full px-3 py-2 border border-gray-300 rounded"
              placeholder="Paste your resume text here..."
              required
            />
          </div>

          <div className="mb-4">
            <label className="block text-gray-700 font-bold mb-2">
              Job Title
            </label>
            <input
              type="text"
              value={jobTitle}
              onChange={(e) => setJobTitle(e.target.value)}
              className="w-full px-3 py-2 border border-gray-300 rounded"
              placeholder="e.g., Senior Software Engineer"
              required
            />
          </div>

          <div className="mb-4">
            <label className="block text-gray-700 font-bold mb-2">
              Job Description
            </label>
            <textarea
              value={jobDescription}
              onChange={(e) => setJobDescription(e.target.value)}
              rows="6"
              className="w-full px-3 py-2 border border-gray-300 rounded"
              placeholder="Enter job description..."
              required
            />
          </div>

          <div className="mb-4">
            <label className="block text-gray-700 font-bold mb-2">
              Required Skills (comma-separated)
            </label>
            <input
              type="text"
              value={requiredSkills}
              onChange={(e) => setRequiredSkills(e.target.value)}
              className="w-full px-3 py-2 border border-gray-300 rounded"
              placeholder="e.g., Python, React, SQL, Docker"
            />
          </div>

          <button
            type="submit"
            disabled={loading}
            className="bg-blue-500 text-white px-6 py-2 rounded hover:bg-blue-600 disabled:bg-gray-400"
          >
            {loading ? 'Matching...' : 'Match Resume'}
          </button>
        </form>
      </div>

      {result && (
        <div className="bg-white p-6 rounded-lg shadow-md">
          <h2 className="text-2xl font-bold mb-4">Match Results</h2>
          
          <div className="mb-4">
            <div className="bg-blue-100 p-4 rounded">
              <p className="text-sm text-gray-600">Match Score</p>
              <p className="text-4xl font-bold">{result.match_score}%</p>
            </div>
          </div>

          <div className="grid grid-cols-2 gap-4 mb-4">
            <div>
              <h3 className="font-bold mb-2">Matched Skills</h3>
              <ul className="list-disc list-inside">
                {result.matched_skills.map((skill, i) => (
                  <li key={i} className="text-green-600">{skill}</li>
                ))}
              </ul>
            </div>
            <div>
              <h3 className="font-bold mb-2">Missing Skills</h3>
              <ul className="list-disc list-inside">
                {result.missing_skills.map((skill, i) => (
                  <li key={i} className="text-red-600">{skill}</li>
                ))}
              </ul>
            </div>
          </div>

          {result.recommendations && result.recommendations.length > 0 && (
            <div>
              <h3 className="font-bold mb-2">Recommendations</h3>
              <ul className="list-disc list-inside">
                {result.recommendations.map((rec, i) => (
                  <li key={i}>{rec}</li>
                ))}
              </ul>
            </div>
          )}
        </div>
      )}
    </div>
  )
}

export default ResumeMatcher

