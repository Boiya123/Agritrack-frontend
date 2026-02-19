import React, { useState, useEffect, useContext } from 'react';
import { useParams, useSearchParams, useNavigate } from 'react-router-dom';
import { StoreContext } from '../../context/StoreContext';
import './ProductBatches.css';

const ProductBatches = () => {
  const { productId } = useParams();
  const [searchParams] = useSearchParams();
  const navigate = useNavigate();
  const productName = searchParams.get('name');
  const { authToken } = useContext(StoreContext);
  
  const [batches, setBatches] = useState([]);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState('');

  useEffect(() => {
    const fetchBatches = async () => {
      try {
        setLoading(true);
        setError('');
        
        // Fetch all batches and filter by product_id on frontend
        const response = await fetch(
          'http://127.0.0.1:8000/api/batches',
          {
            headers: {
              'Authorization': `Bearer ${authToken}`,
              'Content-Type': 'application/json'
            }
          }
        );

        if (response.ok) {
          const allBatches = await response.json();
          // Filter batches by product_id and status
          const filtered = allBatches.filter(
            batch => batch.product_id === productId && batch.status !== 'COMPLETED'
          );
          setBatches(filtered);
        } else if (response.status === 401) {
          setError('Session expired. Please log in again.');
        } else {
          setError('Failed to load batches.');
        }
      } catch (error) {
        console.error('Error fetching batches:', error);
        setError('Network error loading batches.');
      } finally {
        setLoading(false);
      }
    };

    if (authToken && productId) {
      fetchBatches();
    }
  }, [productId, authToken]);

  const getStatusColor = (status) => {
    switch (status) {
      case 'ACTIVE':
        return '#10b981';
      case 'CREATED':
        return '#f97316';
      case 'ARCHIVED':
        return '#9ca3af';
      default:
        return '#6ba537';
    }
  };

  if (loading) {
    return (
      <div className="product-batches-container">
        <div className="loading">Loading batches...</div>
      </div>
    );
  }

  return (
    <div className="product-batches-container">
      <div className="product-batches-header">
        <button className="back-button" onClick={() => navigate('/')}>
          ← Back to Home
        </button>
        <div>
          <h1>{productName} Batches</h1>
          <p className="subtitle">Active and recent batches for {productName}</p>
        </div>
      </div>

      {error && (
        <div className="error-message">
          ⚠ {error}
        </div>
      )}

      {batches.length === 0 ? (
        <div className="empty-state">
          <p>No active batches found for {productName}</p>
          <small>Check back soon or explore other products</small>
        </div>
      ) : (
        <div className="batches-grid">
          {batches.map(batch => (
            <div 
              key={batch.id} 
              className="batch-card"
              onClick={() => navigate(`/batch-detail/${batch.id}`)}
            >
              <div className="batch-header">
                <h3>{batch.batch_number}</h3>
                <span 
                  className="status-badge"
                  style={{ backgroundColor: getStatusColor(batch.status) }}
                >
                  {batch.status}
                </span>
              </div>

              <div className="batch-details">
                <div className="detail-row">
                  <span className="label">Quantity:</span>
                  <span className="value">{batch.quantity || 'N/A'} {batch.unit || 'units'}</span>
                </div>

                <div className="detail-row">
                  <span className="label">Created:</span>
                  <span className="value">
                    {batch.created_at 
                      ? new Date(batch.created_at).toLocaleDateString('en-US', {
                          year: 'numeric',
                          month: 'short',
                          day: 'numeric'
                        })
                      : 'N/A'
                    }
                  </span>
                </div>

                <div className="detail-row">
                  <span className="label">Description:</span>
                  <span className="value">{batch.description || 'No description'}</span>
                </div>
              </div>

              <div className="batch-actions">
                <button className="view-btn" onClick={(e) => {
                  e.stopPropagation();
                  navigate(`/batch-detail/${batch.id}`);
                }}>
                  View Details
                </button>
              </div>
            </div>
          ))}
        </div>
      )}
    </div>
  );
};

export default ProductBatches;
