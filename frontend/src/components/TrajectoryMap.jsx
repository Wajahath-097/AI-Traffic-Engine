import React, { useMemo, useRef } from 'react'
import { GoogleMap, Marker, Polyline, InfoWindow, useJsApiLoader } from '@react-google-maps/api'
import './TrajectoryMap.css'

const libraries = ['visualization'];

const mapContainerStyle = {
  width: '100%',
  height: '100%'
};

export default function TrajectoryMap({ geojson }) {
  const [activeMarker, setActiveMarker] = React.useState(null);
  const mapRef = useRef(null)
  
  const { isLoaded } = useJsApiLoader({
    id: 'google-map-script',
    googleMapsApiKey: "AIzaSyA6OMTdf0GLlzaZUE7S_LnpVdRVOfb3nMw",
    libraries: libraries,
    version: "3.64"
  })

  const defaultCenter = useMemo(() => ({ lat: 17.3850, lng: 78.4867 }), []);

  const points = geojson ? geojson.features.filter(f => f.geometry.type === 'Point') : [];
  const lines = geojson ? geojson.features.filter(f => f.geometry.type === 'LineString') : [];

  const onLoad = React.useCallback((map) => {
    mapRef.current = map;
    if (points.length > 0) {
      const bounds = new window.google.maps.LatLngBounds();
      points.forEach(pt => {
        bounds.extend({ lat: pt.geometry.coordinates[1], lng: pt.geometry.coordinates[0] });
      });
      map.fitBounds(bounds);
    }
  }, [points]);

  if (!geojson) return <div className="map-placeholder">No trajectory data available</div>;

  if (!isLoaded || !window.google) return <div className="trajectory-map-container" style={{display: 'flex', alignItems: 'center', justifyContent: 'center'}}>Initializing Map... (Check API Key)</div>

  return (
    <div className="trajectory-map-container">
      <GoogleMap
        mapContainerStyle={{ width: '100%', height: '100%' }}
        center={defaultCenter}
        zoom={13}
        onLoad={onLoad}
        options={{ disableDefaultUI: false }}
      >
        {points.map((pt, i) => {
          const position = { lat: pt.geometry.coordinates[1], lng: pt.geometry.coordinates[0] };
          const isCamera = pt.properties.type === 'camera';
          return (
            <Marker
              key={i}
              position={position}
              onClick={() => setActiveMarker(pt)}
              icon={isCamera ? 'http://maps.google.com/mapfiles/ms/icons/red-dot.png' : 'http://maps.google.com/mapfiles/ms/icons/blue-dot.png'}
            >
              {activeMarker === pt && (
                <InfoWindow
                  position={position}
                  onCloseClick={() => setActiveMarker(null)}
                >
                  <div className="map-popup" style={{ color: '#000' }}>
                    <strong>{isCamera ? 'Camera' : 'Detection'}</strong>
                    {!isCamera && (
                      <>
                        <br/>Sequence: {pt.properties.sequence}
                        <br/>Time: {new Date(pt.properties.timestamp).toLocaleString()}
                      </>
                    )}
                    {isCamera && (
                      <>
                        <br/>{pt.properties.name}
                      </>
                    )}
                  </div>
                </InfoWindow>
              )}
            </Marker>
          );
        })}

        {lines.map((line, i) => {
          const path = line.geometry.coordinates.map(coord => ({ lat: coord[1], lng: coord[0] }));
          return (
            <Polyline
              key={`line-${i}`}
              path={path}
              options={{
                strokeColor: '#3b82f6',
                strokeOpacity: 0.8,
                strokeWeight: 4,
              }}
            />
          );
        })}
      </GoogleMap>
    </div>
  )
}
