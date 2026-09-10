import React, { useState } from 'react'
import { apiGet, apiPost } from '../services/api'
import TrajectoryMap from '../components/TrajectoryMap'

export default function TrackVehicle() {
  const [plate, setPlate] = useState('')
  const [results, setResults] = useState([])
  const [loading, setLoading] = useState(false)
  const [error, setError] = useState('')

  const [trajectoryData, setTrajectoryData] = useState(null)

  const handleSearch = async (event) => {
    event.preventDefault()
    setLoading(true)
    setError('')
    setTrajectoryData(null)

    try {
      const response = await apiGet(`/api/search/vehicles?plate=${encodeURIComponent(plate)}`)
      setResults(response.data?.results || [])
      
      try {
        const trajRes = await apiPost(`/api/trajectories/reconstruct?plate=${encodeURIComponent(plate)}`)
        if (trajRes.data && trajRes.data.trajectory) {
          const mapDataRes = await apiGet(`/api/trajectories/${trajRes.data.trajectory.id}/map-data`)
          setTrajectoryData(mapDataRes.data.geojson)
        }
      } catch (trajErr) {
        console.error("Could not fetch trajectory", trajErr)
      }
      
    } catch (err) {
      setError(err?.response?.data?.detail || 'No matching vehicle was found.')
      setResults([])
    } finally {
      setLoading(false)
    }
  }

  return (
    <div className="search-page">
      <div className="page-header">
        <div>
          <p className="eyebrow">Investigation</p>
          <h1>Track Vehicle Trajectory</h1>
        </div>
      </div>

      <form onSubmit={handleSearch} className="search-form card">
        <div className="form-group">
          <label htmlFor="plateSearch">Registration Number</label>
          <input
            id="plateSearch"
            type="text"
            placeholder="e.g., TS09AB1234"
            value={plate}
            onChange={(event) => setPlate(event.target.value)}
            required
          />
        </div>
        <button type="submit" className="primary" disabled={loading}>
          {loading ? 'Searching...' : 'Search'}
        </button>
      </form>

      {error && <div className="alert alert-danger">{error}</div>}

      {trajectoryData && (
        <div className="trajectory-section" style={{marginTop: '24px', marginBottom: '24px'}}>
          <h2>Vehicle Trajectory</h2>
          <TrajectoryMap geojson={trajectoryData} />
        </div>
      )}

      {results.length > 0 ? (
        <div className="results">
          <h2>Results</h2>
          <div className="results-list">
            {results.map((result, index) => (
              <div key={result.id || index} className="card result-card">
                <div className="result-header">
                  <strong>{result.plate_number || 'Unknown plate'}</strong>
                  <div>
                    <span className="badge badge-primary" style={{ marginRight: '8px' }}>
                      {result.vehicle_color ? result.vehicle_color.toUpperCase() : 'UNKNOWN COLOR'}
                    </span>
                    <span className="badge badge-primary" style={{ marginRight: '8px' }}>
                      {result.vehicle_model ? result.vehicle_model.toUpperCase() : 'UNKNOWN MODEL'}
                    </span>
                    <span className="badge badge-primary">
                      {result.vehicle_class ? result.vehicle_class.toUpperCase() : 'VEHICLE'}
                    </span>
                  </div>
                </div>
                <p>Camera ID: {result.camera_id}</p>
                <p>Detected: {new Date(result.detected_at).toLocaleString()}</p>
                <p>Confidence: {(result.plate_confidence || 0).toFixed(2)}</p>
              </div>
            ))}
          </div>
        </div>
      ) : (
        plate && !loading && !error ? <p className="empty-state">No results found for this plate.</p> : null
      )}
    </div>
  )
}
