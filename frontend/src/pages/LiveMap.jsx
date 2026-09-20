import React, { useEffect, useState, useMemo } from 'react'
import { apiGet } from '../services/api'
import { GoogleMap, HeatmapLayer, useJsApiLoader } from '@react-google-maps/api'

// Visualization library needed to match Dashboard config and prevent crashes
const libraries = ['visualization'];

export default function LiveMap() {
  const [rawHeatmap, setRawHeatmap] = useState([])
  const [loading, setLoading] = useState(true)

  const { isLoaded } = useJsApiLoader({
    id: 'google-map-script',
    googleMapsApiKey: "AIzaSyA6OMTdf0GLlzaZUE7S_LnpVdRVOfb3nMw",
    version: "3.64",
    libraries: libraries,
    language: "en",
    region: "US"
  })

  useEffect(() => {
    let isMounted = true;
    const fetchHeatmap = async () => {
      try {
        const response = await apiGet('/api/analytics/heatmap')
        if (Array.isArray(response.data) && isMounted) {
          setRawHeatmap(response.data)
        }
      } catch (err) {
        console.error('Heatmap error:', err)
      } finally {
        if (isMounted) setLoading(false)
      }
    }
    
    fetchHeatmap()
    
    return () => { isMounted = false }
  }, [])

  const heatmapData = useMemo(() => {
    if (!isLoaded) return [];
    return rawHeatmap.map(pt => ({
      lat: pt.lat || pt.latitude,
      lng: pt.lng || pt.longitude,
      weight: pt.intensity || pt.weight || 1
    }))
  }, [isLoaded, rawHeatmap])

  const defaultCenter = useMemo(() => ({ lat: 23.2156, lng: 72.6369 }), [])

  return (
    <div className="live-map-page" style={{ height: 'calc(100vh - 100px)', display: 'flex', flexDirection: 'column' }}>
      <div className="page-header" style={{ marginBottom: '16px' }}>
        <div>
          <p className="eyebrow">Real-Time Visualization</p>
          <h1>Traffic Congestion Heatmap</h1>
        </div>
      </div>
      <div className="card" style={{ flex: 1, padding: 0, overflow: 'hidden', position: 'relative' }}>
        {loading ? (
            <div className="loading-state" style={{ padding: '20px' }}>Loading Map Data...</div>
        ) : !(isLoaded && window.google) ? (
            <div className="loading-state" style={{ padding: '20px' }}>Initializing Map... (Check API Key)</div>
        ) : (
            <GoogleMap
              mapContainerStyle={{ width: '100%', height: '100%' }}
              center={defaultCenter}
              zoom={13}
              options={{
                styles: [
                  { elementType: "geometry", stylers: [{ color: "#242f3e" }] },
                  { elementType: "labels.text.stroke", stylers: [{ color: "#242f3e" }] },
                  { elementType: "labels.text.fill", stylers: [{ color: "#746855" }] },
                ],
                disableDefaultUI: false
              }}
            >
              {heatmapData.length > 0 && (
                <HeatmapLayer
                  data={heatmapData.map(pt => ({
                    location: new window.google.maps.LatLng(parseFloat(pt.lat), parseFloat(pt.lng)),
                    weight: pt.weight
                  }))}
                  options={{
                    radius: 35,
                    opacity: 0.8,
                    maxIntensity: Math.max(...heatmapData.map(d => d.weight)) || 10
                  }}
                />
              )}
            </GoogleMap>
        )}
      </div>
    </div>
  )
}
