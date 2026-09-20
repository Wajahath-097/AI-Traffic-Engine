import React, { useState, useEffect } from 'react'
import api from '../services/api'

export default function Blacklist() {
  const [entries, setEntries] = useState([])
  const [loading, setLoading] = useState(true)
  const [error, setError] = useState('')
  
  const [newPlate, setNewPlate] = useState('')
  const [newReason, setNewReason] = useState('')
  const [newSeverity, setNewSeverity] = useState('high')
  const [adding, setAdding] = useState(false)

  const fetchBlacklist = async () => {
    setLoading(true)
    try {
      const res = await api.get('/api/blacklist')
      setEntries(res.data)
    } catch (err) {
      setError('Failed to fetch blacklist entries')
    } finally {
      setLoading(false)
    }
  }

  useEffect(() => {
    fetchBlacklist()
  }, [])

  const handleAdd = async (e) => {
    e.preventDefault()
    setAdding(true)
    setError('')
    try {
      await api.post('/api/blacklist', {
        plate_number: newPlate,
        reason: newReason,
        severity: newSeverity
      })
      setNewPlate('')
      setNewReason('')
      setNewSeverity('high')
      fetchBlacklist()
    } catch (err) {
      setError(err?.response?.data?.detail || 'Failed to add plate to blacklist')
    } finally {
      setAdding(false)
    }
  }

  const handleRemove = async (id) => {
    try {
      await api.delete(`/api/blacklist/${id}`)
      fetchBlacklist()
    } catch (err) {
      setError('Failed to remove entry')
    }
  }

  return (
    <div className="blacklist-page grid">
      <div className="page-header">
        <div>
          <p className="eyebrow">Enforcement</p>
          <h1>Blacklist Management</h1>
        </div>
      </div>

      {error && <div className="alert alert-danger">{error}</div>}

      <div className="card">
        <h3>Add New Plate</h3>
        <form onSubmit={handleAdd} className="search-form" style={{ marginTop: '16px', gridTemplateColumns: '1fr 2fr 1fr auto' }}>
          <div className="form-group">
            <label>Plate Number</label>
            <input type="text" placeholder="e.g. MH12AB1234" value={newPlate} onChange={e => setNewPlate(e.target.value)} required />
          </div>
          <div className="form-group">
            <label>Reason</label>
            <input type="text" placeholder="Wanted for..." value={newReason} onChange={e => setNewReason(e.target.value)} required />
          </div>
          <div className="form-group">
            <label>Severity</label>
            <select value={newSeverity} onChange={e => setNewSeverity(e.target.value)}>
              <option value="critical">Critical</option>
              <option value="high">High</option>
              <option value="medium">Medium</option>
            </select>
          </div>
          <button type="submit" className="primary" disabled={adding}>
            {adding ? 'Adding...' : 'Add Plate'}
          </button>
        </form>
      </div>

      <div className="card">
        <h3>Current Watchlist</h3>
        {loading ? (
          <p className="empty-state">Loading...</p>
        ) : entries.length === 0 ? (
          <p className="empty-state">No plates on the blacklist.</p>
        ) : (
          <div className="results-list" style={{ marginTop: '16px' }}>
            {entries.map(entry => (
              <div key={entry.id} className="card result-card" style={{ display: 'flex', justifyContent: 'space-between', alignItems: 'center' }}>
                <div>
                  <div style={{ display: 'flex', alignItems: 'center', gap: '12px' }}>
                    <strong style={{ fontSize: '18px' }}>{entry.plate_number.replace(/\s+/g, '')}</strong>
                    <span className={`status-badge ${entry.severity === 'critical' ? 'offline' : 'unknown'}`}>
                      {entry.severity}
                    </span>
                  </div>
                  <p style={{ margin: '8px 0 0 0', color: '#4b5563' }}>{entry.reason}</p>
                  <div style={{ display: 'flex', gap: '12px', marginTop: '8px', fontSize: '14px', color: 'var(--color-text-light)' }}>
                    <span><strong>Type:</strong> {entry.vehicle_class || 'Unknown'}</span>
                    <span><strong>Color:</strong> {entry.vehicle_color || 'Unknown'}</span>
                  </div>
                </div>
                <button onClick={() => handleRemove(entry.id)} style={{ background: '#c8102e', color: 'white', padding: '8px 16px', cursor: 'pointer', border: 'none', borderRadius: '4px' }}>
                  Remove
                </button>
              </div>
            ))}
          </div>
        )}
      </div>
    </div>
  )
}
