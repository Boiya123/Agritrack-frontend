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
          <div className="empty-state" style={{textAlign:'center',padding:'32px 0',color:'#5b6a5d',fontSize:'16px'}}>No pending approvals.</div>
        ) : (
          <div style={{maxWidth:'900px',margin:'0 auto'}}>
            {pendingRecords.map(record => (
              <div key={record.id} style={{display:'flex',alignItems:'center',gap:'16px',padding:'8px 0',borderBottom:'1px solid #e5e7eb',background:'none'}}>
                <span className="status-badge pending" style={{minWidth:'60px'}}>Pending</span>
                <span style={{fontWeight:600,color:'#059669',fontSize:'13px'}}>{record.batch_number}</span>
                <span style={{color:'#5b6a5d',fontSize:'13px'}}>{record.record_type.replace('_',' ')}</span>
                {record.details && <span style={{color:'#7a8a7a',fontSize:'13px'}}>{record.details}</span>}
                <button
                  className="btn btn-approve"
                  style={{minWidth:70,fontWeight:500,fontSize:'12px',marginLeft:'auto'}}
                  onClick={() => handleApprove(record.id)}
                  disabled={actionLoading === record.id}
                >
                  {actionLoading === record.id ? '...' : 'Approve'}
                </button>
                <button
                  className="btn btn-decline"
                  style={{minWidth:70,fontWeight:500,fontSize:'12px'}}
                  onClick={() => setShowDeclineForm(showDeclineForm === record.id ? null : record.id)}
                  disabled={actionLoading === record.id}
                >
                  {showDeclineForm === record.id ? 'Cancel' : 'Decline'}
                </button>
                {showDeclineForm === record.id && (
                  <div style={{display:'flex',flexDirection:'column',gap:'6px',marginLeft:'16px',width:'220px'}}>
                    <textarea
                      placeholder="Rejection reason (required)"
                      value={declineReason}
                      onChange={(e) => setDeclineReason(e.target.value)}
                      className="decline-textarea"
                      autoFocus
                      style={{fontSize:'12px',padding:'8px'}}
                    />
                    <button
                      className="btn btn-reject-confirm"
                      style={{fontWeight:500,fontSize:'12px'}}
                      onClick={() => handleReject(record.id)}
                      disabled={actionLoading === record.id || !declineReason.trim()}
                    >
                      {actionLoading === record.id ? '...' : 'Confirm'}
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
          <div className="empty-state" style={{textAlign:'center',padding:'32px 0',color:'#5b6a5d',fontSize:'16px'}}>No approved records yet. Approve pending records to see them here.</div>
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
          <div className="empty-state" style={{textAlign:'center',padding:'32px 0',color:'#5b6a5d',fontSize:'16px'}}>No rejected records. Declined batches will appear here.</div>
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
