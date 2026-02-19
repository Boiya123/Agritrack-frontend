import React, { useState, useContext, useEffect } from 'react'
import { useParams, useNavigate } from 'react-router-dom'
import './BatchDetail.css'
import { StoreContext } from '../../context/StoreContext'
import { batchesApi, lifecycleApi, logisticsApi, processingApi } from '../../api'

/**
 * Batch Detail Page
 * 
 * This page shows comprehensive details about a single batch:
 * - Basic batch info (ID, farmer, product, quantity, dates)
 * - Full lifecycle audit trail (all events that happened to this batch)
 * - Related transports and processing records
 * - QR code information
 * 
 * This gives you a complete "history" view of a batch from creation to final product.
 * Perfect for regulators and consumers to verify traceability.
 */

const BatchDetail = () => {
  const { batchId } = useParams()
  const navigate = useNavigate()
  const { authToken } = useContext(StoreContext)

  // State management
  const [batch, setBatch] = useState(null)
  const [events, setEvents] = useState([])
  const [transports, setTransports] = useState([])
  const [processing, setProcessing] = useState(null)
  const [loading, setLoading] = useState(true)
  const [error, setError] = useState('')

  // Fetch batch and related data on mount
  useEffect(() => {
    if (!authToken || !batchId) return

    const fetchData = async () => {
      setLoading(true)
      setError('')

      try {
        // Fetch batch details
        const batchData = await batchesApi.get(authToken, batchId)
        setBatch(batchData)

        // Fetch lifecycle events for this batch
        const eventsData = await lifecycleApi.listByBatch(authToken, batchId)
        setEvents(eventsData || [])

        // Fetch transports for this batch
        const transportsData = await logisticsApi.listTransportsByBatch(authToken, batchId)
        setTransports(transportsData || [])

        // Try to fetch processing records (they don't exist for all batches)
        try {
          const processingData = await processingApi.listRecordsByBatch(authToken, batchId)
          if (processingData && processingData.length > 0) {
            setProcessing(processingData[0]) // Get first processing record if exists
          }
        } catch (e) {
          // Processing records aren't critical, just skip if error
        }
      } catch (err) {
        setError(err.message || 'Failed to load batch details.')
      } finally {
        setLoading(false)
      }
    }

    fetchData()
  }, [authToken, batchId])

  // Show loading state
  if (loading) {
    return <div className='batch-detail'><div className='loading'>Loading batch details...</div></div>
  }

  // Show error state
  if (error || !batch) {
    return (
      <div className='batch-detail'>
        <div className='error-state'>
          <h2>❌ Error Loading Batch</h2>
          <p>{error || 'Batch not found.'}</p>
          <button onClick={() => navigate('/ops')}>Back to Operations</button>
        </div>
      </div>
    )
  }

  return (
    <div className='batch-detail'>
      <header className='batch-header'>
        <button className='back-btn' onClick={() => navigate('/ops')}>← Back</button>
        <div className='header-content'>
          <h1>Batch Details</h1>
          <p className='batch-id'>ID: {batch.id}</p>
        </div>
      </header>

      {/* Basic Batch Info */}
      <section className='batch-section'>
        <h2>📋 Batch Information</h2>
        <div className='info-grid'>
          <div className='info-item'>
            <span className='label'>Batch Number</span>
            <span className='value'>{batch.batch_number}</span>
          </div>
          <div className='info-item'>
            <span className='label'>Product</span>
            <span className='value'>{batch.product_id}</span>
          </div>
          <div className='info-item'>
            <span className='label'>Quantity</span>
            <span className='value'>{batch.quantity} units</span>
          </div>
          <div className='info-item'>
            <span className='label'>Status</span>
            <span className={`value badge ${batch.status.toLowerCase()}`}>
              {batch.status}
            </span>
          </div>
          <div className='info-item'>
            <span className='label'>Start Date</span>
            <span className='value'>
              {batch.start_date ? new Date(batch.start_date).toLocaleDateString() : 'N/A'}
            </span>
          </div>
          <div className='info-item'>
            <span className='label'>Expected End Date</span>
            <span className='value'>
              {batch.expected_end_date ? new Date(batch.expected_end_date).toLocaleDateString() : 'N/A'}
            </span>
          </div>
          <div className='info-item'>
            <span className='label'>Location</span>
            <span className='value'>{batch.location || 'Not specified'}</span>
          </div>
          <div className='info-item'>
            <span className='label'>QR Code</span>
            <span className='value'>{batch.qr_code || 'Not linked'}</span>
          </div>
        </div>
        {batch.notes && (
          <div className='notes'>
            <strong>Notes:</strong> {batch.notes}
          </div>
        )}
        {batch.blockchain_status && (
          <div className={`blockchain-status ${batch.blockchain_status}`}>
            🔗 Blockchain Status: <strong>{batch.blockchain_status}</strong>
          </div>
        )}
      </section>

      {/* Lifecycle Events Audit Trail */}
      <section className='batch-section'>
        <h2>📊 Lifecycle Audit Trail ({events.length} events)</h2>
        {events.length === 0 ? (
          <p className='empty'>No lifecycle events recorded yet.</p>
        ) : (
          <div className='timeline'>
            {events.map((event, index) => (
              <div key={event.id} className='timeline-item'>
                <div className='timeline-marker'>{index + 1}</div>
                <div className='timeline-content'>
                  <div className='event-type'>
                    <strong>{event.event_type}</strong>
                    <span className='event-date'>
                      {new Date(event.event_date).toLocaleDateString()}
                    </span>
                  </div>
                  <p>{event.description}</p>
                  {event.quantity_affected && (
                    <p className='meta'>Quantity affected: {event.quantity_affected}</p>
                  )}
                </div>
              </div>
            ))}
          </div>
        )}
      </section>

      {/* Transports */}
      <section className='batch-section'>
        <h2>🚚 Transports ({transports.length})</h2>
        {transports.length === 0 ? (
          <p className='empty'>No transports recorded.</p>
        ) : (
          <div className='transports-list'>
            {transports.map((transport) => (
              <div key={transport.id} className='transport-item'>
                <div className='transport-header'>
                  <span className='status-badge'>{transport.status}</span>
                  <span className='date'>
                    {new Date(transport.departure_time).toLocaleDateString()}
                  </span>
                </div>
                <p><strong>From:</strong> {transport.origin_location} → <strong>To:</strong> {transport.destination_location}</p>
                <p><strong>Driver:</strong> {transport.driver_name}</p>
                {transport.temperature_monitored && (
                  <p className='temp-monitored'>🌡️ Temperature monitored</p>
                )}
              </div>
            ))}
          </div>
        )}
      </section>

      {/* Processing Records */}
      {processing && (
        <section className='batch-section'>
          <h2>⚙️ Processing</h2>
          <div className='info-grid'>
            <div className='info-item'>
              <span className='label'>Processing Date</span>
              <span className='value'>
                {new Date(processing.processing_date).toLocaleDateString()}
              </span>
            </div>
            <div className='info-item'>
              <span className='label'>Facility</span>
              <span className='value'>{processing.facility_name}</span>
            </div>
            <div className='info-item'>
              <span className='label'>Slaughter Count</span>
              <span className='value'>{processing.slaughter_count}</span>
            </div>
            <div className='info-item'>
              <span className='label'>Yield</span>
              <span className='value'>{processing.yield_kg} kg</span>
            </div>
            <div className='info-item'>
              <span className='label'>Quality Score</span>
              <span className='value'>{processing.quality_score}</span>
            </div>
          </div>
        </section>
      )}
    </div>
  )
}

export default BatchDetail
