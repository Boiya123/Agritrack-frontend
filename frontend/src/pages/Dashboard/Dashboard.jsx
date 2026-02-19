import React, { useEffect, useState } from 'react';
import './Dashboard.css';
import { authApi, batchesApi, productsApi, regulatoryApi } from '../../api';
import { StoreContext } from '../../context/StoreContext';
import {
  PieChart, Pie, Cell, LineChart, Line, XAxis, YAxis, CartesianGrid,
  Tooltip, Legend, ResponsiveContainer, BarChart, Bar, AreaChart, Area
} from 'recharts';

// Sample data for preview mode
const SAMPLE_BATCH_STATUS = [
  { name: 'Ready to Ship', value: 12, fill: '#10b981' },
  { name: 'In Processing', value: 8, fill: '#f59e0b' },
  { name: 'Quality Check', value: 5, fill: '#3b82f6' }
];

const SAMPLE_COMPLIANCE_DATA = [
  { month: 'Jan', approved: 45, pending: 12, rejected: 3 },
  { month: 'Feb', approved: 52, pending: 8, rejected: 2 },
  { month: 'Mar', approved: 48, pending: 15, rejected: 4 },
  { month: 'Apr', approved: 61, pending: 10, rejected: 1 },
  { month: 'May', approved: 55, pending: 18, rejected: 3 },
  { month: 'Jun', approved: 67, pending: 9, rejected: 2 }
];

const SAMPLE_PRODUCT_DATA = [
  { name: 'Chicken', batches: 24 },
  { name: 'Duck', batches: 18 },
  { name: 'Turkey', batches: 12 },
  { name: 'Quail', batches: 8 }
];

const SAMPLE_TRACEABILITY = [
  { week: 'W1', scanned: 120, verified: 115 },
  { week: 'W2', scanned: 145, verified: 142 },
  { week: 'W3', scanned: 110, verified: 108 },
  { week: 'W4', scanned: 160, verified: 158 }
];

// Dashboard is accessible to all authenticated users
// Shows role-specific data: farmers see their batches, admins see all
const Dashboard = () => {
  const { authToken, currentUser } = React.useContext(StoreContext);
  const [summary, setSummary] = useState({
    products: 0,
    batches: 0
  });
  const [loading, setLoading] = useState(false);
  const [error, setError] = useState('');
  const [complianceQuery, setComplianceQuery] = useState('');
  const [complianceStatus, setComplianceStatus] = useState(null);
  const [animatedStats, setAnimatedStats] = useState({
    batches: 0,
    products: 0,
    compliance: 0
  });

  // Animate counter on load
  useEffect(() => {
    if (!authToken) {
      setAnimatedStats({ batches: 24, products: 8, compliance: 142 });
      return;
    }
  }, [authToken]);

  useEffect(() => {
    // Design preview mode: show sample data when not logged in
    if (!authToken) {
      setSummary({
        products: 8,
        batches: 24
      });
      return;
    }
    setLoading(true);
    setError('');
    Promise.all([
      productsApi.list(authToken, { active_only: true }),
      batchesApi.list(authToken)
    ])
      .then(([products, batches]) => {
        setSummary({
          products: products?.length || 0,
          batches: batches?.length || 0
        });
      })
      .catch((err) => {
        setError(err.message || 'Unable to load dashboard stats.');
      })
      .finally(() => {
        setLoading(false);
      });
  }, [authToken]);

  const handleComplianceLookup = async () => {
    if (!authToken) {
      setError('Sign in to view compliance status.');
      return;
    }
    if (!complianceQuery) {
      setError('Enter a farmer ID.');
      return;
    }
    setError('');
    try {
      const data = await regulatoryApi.complianceStatus(authToken, complianceQuery);
      setComplianceStatus(data);
    } catch (err) {
      setError(err.message || 'Unable to load compliance status.');
    }
  };

  // Render dashboard accessible to all authenticated users + designer preview
  return (
    <div className='dash'>
      <header className='dash-hero'>
        <div>
          <p className='dash-kicker'>Command Center</p>
          <h1>Traceability Overview</h1>
          <p>Realtime operational stats across the supply chain.</p>
        </div>
        <div className='dash-profile'>
          <span>Signed in as</span>
          <strong>
            {authToken 
              ? (currentUser?.email || 'User')
              : '👁️ Designer Preview'
            }
          </strong>
        </div>
      </header>

      {error && <div className='dash-error'>{error}</div>}
      {loading && <div className='dash-loading'>
        <div className='dash-spinner'></div>
        Loading stats...
      </div>}

      {/* Key Metrics Cards */}
      <section className='dash-metrics'>
        <div className='metric-card metric-card-1'>
          <div className='metric-icon'>📦</div>
          <div className='metric-content'>
            <p className='metric-label'>Total Batches</p>
            <h2 className='metric-value'>{authToken ? summary.batches : animatedStats.batches}</h2>
            <span className='metric-trend'>↑ 12% from last month</span>
          </div>
        </div>
        <div className='metric-card metric-card-2'>
          <div className='metric-icon'>🍗</div>
          <div className='metric-content'>
            <p className='metric-label'>Product Types</p>
            <h2 className='metric-value'>{authToken ? summary.products : animatedStats.products}</h2>
            <span className='metric-trend'>↑ 2 new products</span>
          </div>
        </div>
        <div className='metric-card metric-card-3'>
          <div className='metric-icon'>✅</div>
          <div className='metric-content'>
            <p className='metric-label'>Compliance Score</p>
            <h2 className='metric-value'>{authToken ? (complianceStatus?.compliance_summary?.total ?? '—') : animatedStats.compliance}%</h2>
            <span className='metric-trend'>Excellent</span>
          </div>
        </div>
        <div className='metric-card metric-card-4'>
          <div className='metric-icon'>🔍</div>
          <div className='metric-content'>
            <p className='metric-label'>QR Scans</p>
            <h2 className='metric-value'>535</h2>
            <span className='metric-trend'>↑ 28 today</span>
          </div>
        </div>
      </section>

      {/* Charts Section */}
      <section className='dash-charts-grid'>
        {/* Batch Status Pie Chart */}
        <div className='dash-chart-card'>
          <h3>Batch Status Distribution</h3>
          <ResponsiveContainer width="100%" height={300}>
            <PieChart>
              <Pie
                data={SAMPLE_BATCH_STATUS}
                cx="50%"
                cy="50%"
                labelLine={false}
                label={({ name, value }) => `${name}: ${value}`}
                outerRadius={80}
                fill="#8884d8"
                dataKey="value"
              >
                {SAMPLE_BATCH_STATUS.map((entry, index) => (
                  <Cell key={`cell-${index}`} fill={entry.fill} />
                ))}
              </Pie>
              <Tooltip />
            </PieChart>
          </ResponsiveContainer>
        </div>

        {/* Compliance Trend Line Chart */}
        <div className='dash-chart-card'>
          <h3>Compliance Trend</h3>
          <ResponsiveContainer width="100%" height={300}>
            <LineChart data={SAMPLE_COMPLIANCE_DATA}>
              <CartesianGrid strokeDasharray="3 3" stroke="#e5e7eb" />
              <XAxis dataKey="month" />
              <YAxis />
              <Tooltip />
              <Legend />
              <Line type="monotone" dataKey="approved" stroke="#10b981" strokeWidth={2} />
              <Line type="monotone" dataKey="pending" stroke="#f59e0b" strokeWidth={2} />
              <Line type="monotone" dataKey="rejected" stroke="#ef4444" strokeWidth={2} />
            </LineChart>
          </ResponsiveContainer>
        </div>

        {/* Product Distribution Bar Chart */}
        <div className='dash-chart-card'>
          <h3>Batches by Product Type</h3>
          <ResponsiveContainer width="100%" height={300}>
            <BarChart data={SAMPLE_PRODUCT_DATA}>
              <CartesianGrid strokeDasharray="3 3" stroke="#e5e7eb" />
              <XAxis dataKey="name" />
              <YAxis />
              <Tooltip />
              <Bar dataKey="batches" fill="#6366f1" radius={[8, 8, 0, 0]} />
            </BarChart>
          </ResponsiveContainer>
        </div>

        {/* QR Traceability Area Chart */}
        <div className='dash-chart-card'>
          <h3>Weekly Scan Verification</h3>
          <ResponsiveContainer width="100%" height={300}>
            <AreaChart data={SAMPLE_TRACEABILITY}>
              <defs>
                <linearGradient id="colorScanned" x1="0" y1="0" x2="0" y2="1">
                  <stop offset="5%" stopColor="#3b82f6" stopOpacity={0.8}/>
                  <stop offset="95%" stopColor="#3b82f6" stopOpacity={0}/>
                </linearGradient>
                <linearGradient id="colorVerified" x1="0" y1="0" x2="0" y2="1">
                  <stop offset="5%" stopColor="#10b981" stopOpacity={0.8}/>
                  <stop offset="95%" stopColor="#10b981" stopOpacity={0}/>
                </linearGradient>
              </defs>
              <CartesianGrid strokeDasharray="3 3" stroke="#e5e7eb" />
              <XAxis dataKey="week" />
              <YAxis />
              <Tooltip />
              <Legend />
              <Area type="monotone" dataKey="scanned" stackId="1" stroke="#3b82f6" fillOpacity={1} fill="url(#colorScanned)" />
              <Area type="monotone" dataKey="verified" stackId="1" stroke="#10b981" fillOpacity={1} fill="url(#colorVerified)" />
            </AreaChart>
          </ResponsiveContainer>
        </div>
      </section>

      {/* Compliance Lookup Card */}
      <section className='dash-card dash-lookup'>
        <h2>Compliance Snapshot</h2>
        <p>Enter a farmer ID to inspect regulatory status.</p>
        <div className='dash-inline'>
          <input
            type='text'
            placeholder='Farmer UUID'
            value={complianceQuery}
            onChange={(event) => setComplianceQuery(event.target.value)}
            disabled={!authToken}
          />
          <button type='button' onClick={handleComplianceLookup} disabled={!authToken}>
            {authToken ? 'Lookup' : 'Sign In to Lookup'}
          </button>
        </div>
        {complianceStatus && (
          <div className='dash-compliance'>
            <div>
              <span>Approved</span>
              <strong>{complianceStatus.compliance_summary.approved}</strong>
            </div>
            <div>
              <span>Pending</span>
              <strong>{complianceStatus.compliance_summary.pending}</strong>
            </div>
            <div>
              <span>Rejected</span>
              <strong>{complianceStatus.compliance_summary.rejected}</strong>
            </div>
          </div>
        )}
      </section>
    </div>
  );
};

export default Dashboard;
