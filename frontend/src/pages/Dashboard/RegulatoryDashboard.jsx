import React, { useState, useEffect } from 'react';
import { useContext } from 'react';
import { StoreContext } from '../../context/StoreContext';
import './Dashboard.css';

const RegulatoryDashboard = () => {
  const { currentUser, authToken } = useContext(StoreContext);
  const token = authToken;
  const [pendingRecords, setPendingRecords] = useState([]);
  const [approvedRecords, setApprovedRecords] = useState([]);
  const [rejectedRecords, setRejectedRecords] = useState([]);
  const [loading, setLoading] = useState(true);
  const [actionLoading, setActionLoading] = useState(null);
  const [selectedRecord, setSelectedRecord] = useState(null);
  const [declineReason, setDeclineReason] = useState('');
  const [showDeclineForm, setShowDeclineForm] = useState(null);
  const [error, setError] = useState('');

  useEffect(() => {
    if (token) {
      fetchRegulatoryRecords();
      // Refresh every 10 seconds
      const interval = setInterval(fetchRegulatoryRecords, 10000);
      return () => clearInterval(interval);
    }
  }, [token]);

  const fetchRegulatoryRecords = async () => {
    try {
      setError('');
      const response = await fetch('http://127.0.0.1:8000/api/regulatory/records', {
        headers: {
          'Authorization': `Bearer ${token}`,
          'Content-Type': 'application/json'
        }
      });

      if (response.ok) {
        const data = await response.json();
        setPendingRecords(data.filter(r => r.status === 'pending') || []);
        setApprovedRecords(data.filter(r => r.status === 'approved') || []);
        setRejectedRecords(data.filter(r => r.status === 'rejected') || []);
      } else if (response.status === 401) {
        setError('Session expired. Please log in again.');
      } else {
        setError('Failed to load regulatory records.');
      }
    } catch (error) {
      console.error('Error fetching regulatory records:', error);
      setError('Network error. Please try again.');
    } finally {
      setLoading(false);
    }
  };

  const handleApprove = async (recordId) => {
    setActionLoading(recordId);
    try {
      const response = await fetch(`http://127.0.0.1:8000/api/regulatory/records/${recordId}/approve`, {
        method: 'POST',
        headers: {
          'Authorization': `Bearer ${token}`,
          'Content-Type': 'application/json'
        }
      });

      if (response.ok) {
        setPendingRecords(pendingRecords.filter(r => r.id !== recordId));
        await fetchRegulatoryRecords(); // Refresh to update counts
      } else {
        setError('Failed to approve record.');
      }
    } catch (error) {
      console.error('Error approving record:', error);
      setError('Error approving record. Please try again.');
    } finally {
      setActionLoading(null);
    }
  };

  const handleReject = async (recordId) => {
    if (!declineReason.trim()) {
      setError('Please provide a rejection reason');
      return;
    }

    setActionLoading(recordId);
    try {
      const response = await fetch(`http://127.0.0.1:8000/api/regulatory/records/${recordId}/reject?rejection_reason=${encodeURIComponent(declineReason)}`, {
        method: 'POST',
        headers: {
          'Authorization': `Bearer ${token}`,
          'Content-Type': 'application/json'
        }
      });

      if (response.ok) {
        setPendingRecords(pendingRecords.filter(r => r.id !== recordId));
        setDeclineReason('');
        setShowDeclineForm(null);
        await fetchRegulatoryRecords();
      } else {
        setError('Failed to reject record.');
      }
    } catch (error) {
      console.error('Error rejecting record:', error);
      setError('Error rejecting record. Please try again.');
    } finally {
      setActionLoading(null);
    }
  };

  if (loading) {
    return (
      <div className="dashboard-loading">
        Loading regulatory records...
      </div>
    );
  }

  return (
    <div className="regulatory-dashboard">
      <div className="dashboard-header">
        <h1>Regulatory Dashboard</h1>
        <p>Approve or reject batches for regulatory compliance</p>
      </div>

      {error && (
        <div style={{ maxWidth: '1200px', margin: '0 auto 24px', padding: '14px 16px', background: '#fee2e2', border: '1px solid #fecaca', borderRadius: '10px', color: '#991b1b', fontSize: '14px' }}>
          ⚠ {error}
        </div>
      )}

      {/* Pending Approvals */}
      <section className="dashboard-section pending">
        <div className="section-header">
          <h2>Pending Approvals</h2>
          <span className="badge pending-badge">{pendingRecords.length}</span>
        </div>

        {pendingRecords.length === 0 ? (
          <div className="empty-state">All records have been reviewed. No pending approvals.</div>
        ) : (
          <div className="records-grid">
            {pendingRecords.map(record => (
              <div key={record.id} className="record-card">
                <div className="record-header">
                  <h3>{record.record_type.replace('_', ' ').toUpperCase()}</h3>
                  <span className="status-badge pending">PENDING</span>
                </div>

                <div className="record-details">
                  <p><strong>Batch ID:</strong> {record.batch_number}</p>
                  <p><strong>Record Type:</strong> {record.record_type}</p>
                  <p><strong>Details:</strong> {record.details || 'No additional details'}</p>
                </div>

                <div className="record-actions">
                  <button
                    className="btn btn-approve"
                    onClick={() => handleApprove(record.id)}
                    disabled={actionLoading === record.id}
                  >
                    {actionLoading === record.id ? 'Processing...' : 'Approve'}
                  </button>

                  <button
                    className="btn btn-decline"
                    onClick={() => setShowDeclineForm(showDeclineForm === record.id ? null : record.id)}
                    disabled={actionLoading === record.id}
                  >
                    {showDeclineForm === record.id ? 'Cancel' : 'Decline'}
                  </button>
                </div>

                {showDeclineForm === record.id && (
                  <div className="decline-form">
                    <textarea
                      placeholder="Enter rejection reason (required)..."
                      value={declineReason}
                      onChange={(e) => setDeclineReason(e.target.value)}
                      className="decline-textarea"
                      autoFocus
                    />
                    <button
                      className="btn btn-reject-confirm"
                      onClick={() => handleReject(record.id)}
                      disabled={actionLoading === record.id || !declineReason.trim()}
                    >
                      {actionLoading === record.id ? 'Submitting...' : 'Confirm Rejection'}
                    </button>
                  </div>
                )}
              </div>
            ))}
          </div>
        )}
      </section>

      {/* Approved Records */}
      <section className="dashboard-section approved">
        <div className="section-header">
          <h2>Approved Records</h2>
          <span className="badge approved-badge">{approvedRecords.length}</span>
        </div>

        {approvedRecords.length === 0 ? (
          <div className="empty-state">No approved records yet. Approve pending records to see them here.</div>
        ) : (
          <div className="records-grid">
            {approvedRecords.map(record => (
              <div key={record.id} className="record-card">
                <div className="record-header">
                  <h3>{record.record_type.replace('_', ' ').toUpperCase()}</h3>
                  <span className="status-badge approved">APPROVED</span>
                </div>

                <div className="record-details">
                  <p><strong>Batch ID:</strong> {record.batch_number}</p>
                  <p><strong>Issued:</strong> {record.issued_date ? new Date(record.issued_date).toLocaleDateString('en-US', { year: 'numeric', month: 'short', day: 'numeric' }) : 'N/A'}</p>
                  <p><strong>Details:</strong> {record.details || 'No additional details'}</p>
                </div>
              </div>
            ))}
          </div>
        )}
      </section>

      {/* Rejected Records */}
      <section className="dashboard-section rejected">
        <div className="section-header">
          <h2>Rejected Records</h2>
          <span className="badge rejected-badge">{rejectedRecords.length}</span>
        </div>

        {rejectedRecords.length === 0 ? (
          <div className="empty-state">No rejected records. Declined batches will appear here.</div>
        ) : (
          <div className="records-grid">
            {rejectedRecords.map(record => (
              <div key={record.id} className="record-card">
                <div className="record-header">
                  <h3>{record.record_type.replace('_', ' ').toUpperCase()}</h3>
                  <span className="status-badge rejected">REJECTED</span>
                </div>

                <div className="record-details">
                  <p><strong>Batch ID:</strong> {record.batch_number}</p>
                  <p><strong>Rejection Reason:</strong> {record.rejection_reason || 'No reason provided'}</p>
                  <p><strong>Details:</strong> {record.details || 'No additional details'}</p>
                </div>
              </div>
            ))}
          </div>
        )}
      </section>
    </div>
  );
};

export default RegulatoryDashboard;
