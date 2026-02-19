import React, { useContext, useEffect, useState } from 'react';
import './Operations.css';
import { StoreContext } from '../../context/StoreContext';
import { assets } from '../../assets/frontend_assets/assets';
import QRScanner from '../../components/QRScanner/QRScanner';
import {
  batchesApi,
  lifecycleApi,
  logisticsApi,
  processingApi,
  regulatoryApi
} from '../../api';

const toIsoString = (value) => !value ? null : new Date(value).toISOString();

// Quick action cards for each operation type
const OpCard = ({ icon, title, description, onClick, color }) => (
  <div className={`op-card op-card-${color}`} onClick={onClick}>
    <div className="op-card-icon">{icon}</div>
    <h3>{title}</h3>
    <p>{description}</p>
  </div>
);

// Modal form wrapper
const FormModal = ({ isOpen, onClose, title, children }) => {
  if (!isOpen) return null;
  return (
    <div className="modal-overlay" onClick={onClose}>
      <div className="modal-content" onClick={(e) => e.stopPropagation()}>
        <div className="modal-header">
          <h2>{title}</h2>
          <button className="modal-close" onClick={onClose}>✕</button>
        </div>
        <div className="modal-body">
          {children}
        </div>
      </div>
    </div>
  );
};

// Compact form fields
const Field = ({ label, type = 'text', value, onChange, placeholder, required, options }) => (
  <div className="form-field">
    <label>{label} {required && <span className="required">*</span>}</label>
    {type === 'select' ? (
      <select value={value} onChange={onChange} required={required}>
        <option value="">Select {label}...</option>
        {options?.map((opt) => (
          <option key={opt.value} value={opt.value}>{opt.label}</option>
        ))}
      </select>
    ) : type === 'checkbox' ? (
      <input type="checkbox" checked={value} onChange={onChange} />
    ) : type === 'textarea' ? (
      <textarea
        value={value}
        onChange={onChange}
        placeholder={placeholder}
        required={required}
      />
    ) : (
      <input
        type={type}
        value={value}
        onChange={onChange}
        placeholder={placeholder}
        required={required}
      />
    )}
  </div>
);

const Operations = () => {
  const { authToken, currentUser, products, loadProducts } = useContext(StoreContext);
  const [activeTab, setActiveTab] = useState('batches');
  const [notice, setNotice] = useState({ type: '', message: '' });

  // State for each operation type
  const [batches, setBatches] = useState([]);
  const [activeModal, setActiveModal] = useState(null);

  // Cleanup on unmount
  useEffect(() => {
    return () => {
      setActiveModal(null);
      setShowQRScanner(false);
    };
  }, []);

  // Batch form
  const [batchForm, setBatchForm] = useState({
    productId: '',
    batchNumber: '',
    quantity: '',
    startDate: '',
    expectedEndDate: '',
    location: '',
    notes: ''
  });

  // Lifecycle form
  const [lifecycleForm, setLifecycleForm] = useState({
    batchId: '',
    eventType: 'VACCINATION',
    description: '',
    eventDate: '',
    quantityAffected: '',
  });

  // Transport form
  const [transportForm, setTransportForm] = useState({
    batchId: '',
    toPartyId: '',
    vehicleId: '',
    driverName: '',
    departureTime: '',
    originLocation: '',
    destinationLocation: '',
    temperatureMonitored: false,
  });

  // Processing form
  const [processingForm, setProcessingForm] = useState({
    batchId: '',
    processingDate: '',
    facilityName: '',
    slaughterCount: '',
    yieldKg: '',
    qualityScore: '',
    notes: ''
  });

  // Additional forms for other operations
  const [batchUpdateForm, setBatchUpdateForm] = useState({
    batchId: '',
    status: '',
    location: '',
  });

  const [batchQrForm, setBatchQrForm] = useState({
    batchId: '',
    qrCode: ''
  });

  const [showQRScanner, setShowQRScanner] = useState(false);

  const [medicationForm, setMedicationForm] = useState({
    batchId: '',
    medicationName: '',
    dosage: '',
    quantityTreated: ''
  });

  const [weightForm, setWeightForm] = useState({
    batchId: '',
    averageWeight: '',
    sampleCount: ''
  });

  const [mortalityForm, setMortalityForm] = useState({
    batchId: '',
    mortalityCount: '',
    cause: ''
  });

  const [temperatureForm, setTemperatureForm] = useState({
    transportId: '',
    temperature: '',
    timestamp: '',
    location: ''
  });

  const [transportUpdateForm, setTransportUpdateForm] = useState({
    transportId: '',
    arrivalTime: '',
    status: ''
  });

  const [processingUpdateForm, setProcessingUpdateForm] = useState({
    recordId: '',
    qualityScore: '',
    notes: ''
  });

  const [certificationForm, setCertificationForm] = useState({
    processingRecordId: '',
    certType: ''
  });

  const showNotice = (type, message) => {
    setNotice({ type, message });
    setTimeout(() => setNotice({ type: '', message: '' }), 3000);
  };

  const requireAuth = () => {
    if (!authToken) {
      showNotice('error', 'Please sign in first.');
      return false;
    }
    return true;
  };

  const loadBatches = async () => {
    try {
      const data = await batchesApi.list(authToken);
      setBatches(data || []);
    } catch (error) {
      showNotice('error', 'Failed to load batches');
    }
  };

  useEffect(() => {
    loadProducts();
    if (authToken) loadBatches();
  }, [authToken, loadProducts]);

  const handleBatchCreate = async (e) => {
    e.preventDefault();
    if (!requireAuth()) return;
    try {
      await batchesApi.create(authToken, {
        product_id: batchForm.productId,
        batch_number: batchForm.batchNumber,
        quantity: Number(batchForm.quantity),
        start_date: toIsoString(batchForm.startDate),
        expected_end_date: toIsoString(batchForm.expectedEndDate),
        location: batchForm.location || null,
        notes: batchForm.notes || null
      });
      showNotice('success', '✓ Batch created successfully');
      setBatchForm({
        productId: '',
        batchNumber: '',
        quantity: '',
        startDate: '',
        expectedEndDate: '',
        location: '',
        notes: ''
      });
      setActiveModal(null);
      loadBatches();
    } catch (error) {
      showNotice('error', error.message || 'Batch creation failed');
    }
  };

  const handleLifecycleCreate = async (e) => {
    e.preventDefault();
    if (!requireAuth()) return;
    try {
      await lifecycleApi.create(authToken, {
        batch_id: lifecycleForm.batchId,
        event_type: lifecycleForm.eventType,
        description: lifecycleForm.description,
        event_date: toIsoString(lifecycleForm.eventDate),
        quantity_affected: lifecycleForm.quantityAffected ? Number(lifecycleForm.quantityAffected) : null,
      });
      showNotice('success', '✓ Event recorded');
      setLifecycleForm({
        batchId: '',
        eventType: 'VACCINATION',
        description: '',
        eventDate: '',
        quantityAffected: '',
      });
      setActiveModal(null);
    } catch (error) {
      showNotice('error', error.message || 'Failed to record event');
    }
  };

  const handleTransportCreate = async (e) => {
    e.preventDefault();
    if (!requireAuth()) return;
    try {
      await logisticsApi.createTransport(authToken, {
        batch_id: transportForm.batchId,
        to_party_id: transportForm.toPartyId,
        vehicle_id: transportForm.vehicleId || null,
        driver_name: transportForm.driverName || null,
        departure_time: toIsoString(transportForm.departureTime),
        origin_location: transportForm.originLocation,
        destination_location: transportForm.destinationLocation,
        temperature_monitored: Boolean(transportForm.temperatureMonitored),
      });
      showNotice('success', '✓ Transport manifest created');
      setTransportForm({
        batchId: '',
        toPartyId: '',
        vehicleId: '',
        driverName: '',
        departureTime: '',
        originLocation: '',
        destinationLocation: '',
        temperatureMonitored: false,
      });
      setActiveModal(null);
    } catch (error) {
      showNotice('error', error.message || 'Transport creation failed');
    }
  };

  const handleProcessingCreate = async (e) => {
    e.preventDefault();
    if (!requireAuth()) return;
    try {
      await processingApi.createRecord(authToken, {
        batch_id: processingForm.batchId,
        processing_date: toIsoString(processingForm.processingDate),
        facility_name: processingForm.facilityName,
        slaughter_count: processingForm.slaughterCount ? Number(processingForm.slaughterCount) : null,
        yield_kg: processingForm.yieldKg ? Number(processingForm.yieldKg) : null,
        quality_score: processingForm.qualityScore ? Number(processingForm.qualityScore) : null,
        notes: processingForm.notes || null
      });
      showNotice('success', '✓ Processing record created');
      setProcessingForm({
        batchId: '',
        processingDate: '',
        facilityName: '',
        slaughterCount: '',
        yieldKg: '',
        qualityScore: '',
        notes: ''
      });
      setActiveModal(null);
    } catch (error) {
      showNotice('error', error.message || 'Processing creation failed');
    }
  };

  const handleBatchUpdate = async (e) => {
    e.preventDefault();
    if (!requireAuth()) return;
    try {
      await batchesApi.update(authToken, batchUpdateForm.batchId, {
        status: batchUpdateForm.status || null,
        location: batchUpdateForm.location || null
      });
      showNotice('success', '✓ Batch updated');
      setBatchUpdateForm({ batchId: '', status: '', location: '' });
      setActiveModal(null);
      loadBatches();
    } catch (error) {
      showNotice('error', error.message || 'Batch update failed');
    }
  };

  const handleBatchLinkQr = async (e) => {
    e.preventDefault();
    if (!requireAuth()) return;
    try {
      await batchesApi.linkQr(authToken, batchQrForm.batchId, batchQrForm.qrCode);
      showNotice('success', '✓ QR code linked');
      setBatchQrForm({ batchId: '', qrCode: '' });
      setActiveModal(null);
      setShowQRScanner(false);
      loadBatches();
    } catch (error) {
      showNotice('error', error.message || 'QR link failed');
    }
  };

  const handleQRScanned = (qrCode) => {
    setBatchQrForm({ ...batchQrForm, qrCode });
    setShowQRScanner(false);
    showNotice('success', '✓ QR code scanned: ' + qrCode);
  };

  const handleMedicationSubmit = async (e) => {
    e.preventDefault();
    if (!requireAuth()) return;
    try {
      await lifecycleApi.recordMedication(authToken, {
        batch_id: medicationForm.batchId,
        medication_name: medicationForm.medicationName,
        dosage: medicationForm.dosage,
        quantity_treated: Number(medicationForm.quantityTreated)
      });
      showNotice('success', '✓ Medication recorded');
      setMedicationForm({ batchId: '', medicationName: '', dosage: '', quantityTreated: '' });
      setActiveModal(null);
    } catch (error) {
      showNotice('error', error.message || 'Medication record failed');
    }
  };

  const handleWeightSubmit = async (e) => {
    e.preventDefault();
    if (!requireAuth()) return;
    try {
      await lifecycleApi.recordWeight(authToken, {
        batch_id: weightForm.batchId,
        average_weight_kg: Number(weightForm.averageWeight),
        sample_count: Number(weightForm.sampleCount)
      });
      showNotice('success', '✓ Weight recorded');
      setWeightForm({ batchId: '', averageWeight: '', sampleCount: '' });
      setActiveModal(null);
    } catch (error) {
      showNotice('error', error.message || 'Weight record failed');
    }
  };

  const handleMortalitySubmit = async (e) => {
    e.preventDefault();
    if (!requireAuth()) return;
    try {
      await lifecycleApi.recordMortality(authToken, {
        batch_id: mortalityForm.batchId,
        mortality_count: Number(mortalityForm.mortalityCount),
        cause: mortalityForm.cause
      });
      showNotice('success', '✓ Mortality recorded');
      setMortalityForm({ batchId: '', mortalityCount: '', cause: '' });
      setActiveModal(null);
    } catch (error) {
      showNotice('error', error.message || 'Mortality record failed');
    }
  };

  const handleTemperatureSubmit = async (e) => {
    e.preventDefault();
    if (!requireAuth()) return;
    try {
      await logisticsApi.recordTemperature(authToken, {
        transport_id: temperatureForm.transportId,
        temperature: Number(temperatureForm.temperature),
        timestamp: toIsoString(temperatureForm.timestamp),
        location: temperatureForm.location || null
      });
      showNotice('success', '✓ Temperature logged');
      setTemperatureForm({ transportId: '', temperature: '', timestamp: '', location: '' });
      setActiveModal(null);
    } catch (error) {
      showNotice('error', error.message || 'Temperature log failed');
    }
  };

  const handleTransportUpdate = async (e) => {
    e.preventDefault();
    if (!requireAuth()) return;
    try {
      await logisticsApi.updateTransport(authToken, transportUpdateForm.transportId, {
        arrival_time: toIsoString(transportUpdateForm.arrivalTime),
        status: transportUpdateForm.status || null
      });
      showNotice('success', '✓ Transport updated');
      setTransportUpdateForm({ transportId: '', arrivalTime: '', status: '' });
      setActiveModal(null);
    } catch (error) {
      showNotice('error', error.message || 'Transport update failed');
    }
  };

  const handleProcessingUpdate = async (e) => {
    e.preventDefault();
    if (!requireAuth()) return;
    try {
      await processingApi.updateRecord(authToken, processingUpdateForm.recordId, {
        quality_score: processingUpdateForm.qualityScore ? Number(processingUpdateForm.qualityScore) : null,
        notes: processingUpdateForm.notes || null
      });
      showNotice('success', '✓ Quality updated');
      setProcessingUpdateForm({ recordId: '', qualityScore: '', notes: '' });
      setActiveModal(null);
    } catch (error) {
      showNotice('error', error.message || 'Quality update failed');
    }
  };

  const handleCertificationSubmit = async (e) => {
    e.preventDefault();
    if (!requireAuth()) return;
    try {
      await processingApi.createCertification(authToken, {
        processing_record_id: certificationForm.processingRecordId,
        cert_type: certificationForm.certType
      });
      showNotice('success', '✓ Certification requested');
      setCertificationForm({ processingRecordId: '', certType: '' });
      setActiveModal(null);
    } catch (error) {
      showNotice('error', error.message || 'Certification request failed');
    }
  };

  return (
    <div className="ops-new">
      {/* Hero Banner */}
      <div className="ops-banner">
        <img src={assets.header_img} alt="banner" className="ops-banner-bg" />
        <div className="ops-banner-overlay"></div>
        <div className="ops-banner-content">
          <div>
            <span className="ops-tag">Operations Hub</span>
            <h1>Supply Chain Control Center</h1>
            <p>Track batches, record events, manage logistics, and ensure compliance</p>
          </div>
          <div className="ops-user">
            <div className="avatar">{currentUser?.email?.[0].toUpperCase()}</div>
            <div>
              <span>Logged in as</span>
              <strong>{currentUser?.email || 'User'}</strong>
            </div>
          </div>
        </div>
      </div>

      {notice.message && (
        <div className={`notice notice-${notice.type}`}>
          {notice.message}
        </div>
      )}

      {/* Tab Navigation */}
      <div className="ops-tabs">
        <button
          className={`tab ${activeTab === 'batches' ? 'active' : ''}`}
          onClick={() => setActiveTab('batches')}
        >
          🌾 Batches
        </button>
        <button
          className={`tab ${activeTab === 'lifecycle' ? 'active' : ''}`}
          onClick={() => setActiveTab('lifecycle')}
        >
          📋 Lifecycle
        </button>
        <button
          className={`tab ${activeTab === 'transport' ? 'active' : ''}`}
          onClick={() => setActiveTab('transport')}
        >
          🚚 Transport
        </button>
        <button
          className={`tab ${activeTab === 'processing' ? 'active' : ''}`}
          onClick={() => setActiveTab('processing')}
        >
          ⚙️ Processing
        </button>
      </div>

      {/* Content Area */}
      <div className="ops-content">
        {/* Batches Tab */}
        {activeTab === 'batches' && (
          <div>
            <h2>Batch Management</h2>
            <div className="ops-grid">
              <OpCard
                icon="➕"
                title="Create Batch"
                description="Start a new batch (flock, harvest, etc.)"
                onClick={() => setActiveModal('batch-create')}
                color="green"
              />
              <OpCard
                icon="📍"
                title="Link QR Code"
                description="Link QR code for consumer transparency"
                onClick={() => setActiveModal('batch-qr')}
                color="blue"
              />
              <OpCard
                icon="✅"
                title="Update Status"
                description="Update batch location and status"
                onClick={() => setActiveModal('batch-update')}
                color="purple"
              />
            </div>

            {/* Batches List */}
            <div className="batch-list">
              <h3>Active Batches ({batches.length})</h3>
              {batches.length === 0 ? (
                <p className="empty">No batches yet. Create one to get started.</p>
              ) : (
                batches.map((batch) => (
                  <div key={batch.id} className="batch-item">
                    <div className="batch-info">
                      <h4>{batch.batch_number}</h4>
                      <p>{batch.quantity} units • {batch.status}</p>
                    </div>
                    <span className={`badge badge-${batch.status.toLowerCase()}`}>
                      {batch.status}
                    </span>
                  </div>
                ))
              )}
            </div>
          </div>
        )}

        {/* Lifecycle Tab */}
        {activeTab === 'lifecycle' && (
          <div>
            <h2>Batch Lifecycle Events</h2>
            <div className="ops-grid">
              <OpCard
                icon="💉"
                title="Record Vaccination"
                description="Log vaccine administration"
                onClick={() => setActiveModal('lifecycle-create')}
                color="green"
              />
              <OpCard
                icon="💊"
                title="Record Medication"
                description="Log treatment events"
                onClick={() => setActiveModal('lifecycle-medication')}
                color="orange"
              />
              <OpCard
                icon="📊"
                title="Record Weight"
                description="Log weight measurements"
                onClick={() => setActiveModal('lifecycle-weight')}
                color="blue"
              />
              <OpCard
                icon="⚠️"
                title="Record Mortality"
                description="Log mortality events"
                onClick={() => setActiveModal('lifecycle-mortality')}
                color="red"
              />
            </div>
          </div>
        )}

        {/* Transport Tab */}
        {activeTab === 'transport' && (
          <div>
            <h2>Logistics & Transport</h2>
            <div className="ops-grid">
              <OpCard
                icon="📦"
                title="Create Transport"
                description="Start a new shipment"
                onClick={() => setActiveModal('transport-create')}
                color="blue"
              />
              <OpCard
                icon="🌡️"
                title="Record Temperature"
                description="Log temperature reading"
                onClick={() => setActiveModal('transport-temp')}
                color="orange"
              />
              <OpCard
                icon="✔️"
                title="Mark Arrived"
                description="Complete transport manifest"
                onClick={() => setActiveModal('transport-update')}
                color="green"
              />
            </div>
          </div>
        )}

        {/* Processing Tab */}
        {activeTab === 'processing' && (
          <div>
            <h2>Processing & Quality</h2>
            <div className="ops-grid">
              <OpCard
                icon="🏭"
                title="Record Processing"
                description="Log facility processing data"
                onClick={() => setActiveModal('processing-create')}
                color="purple"
              />
              <OpCard
                icon="🎯"
                title="Update Quality"
                description="Set quality scores"
                onClick={() => setActiveModal('processing-update')}
                color="blue"
              />
              <OpCard
                icon="📜"
                title="Request Certification"
                description="Halal, Organic, Food Safety, etc."
                onClick={() => setActiveModal('certification')}
                color="green"
              />
            </div>
          </div>
        )}
      </div>

      {/* Modals */}

      {/* Create Batch Modal */}
      <FormModal
        isOpen={activeModal === 'batch-create'}
        onClose={() => setActiveModal(null)}
        title="Create New Batch"
      >
        <form onSubmit={handleBatchCreate}>
          <Field
            label="Product"
            type="select"
            value={batchForm.productId}
            onChange={(e) => setBatchForm({ ...batchForm, productId: e.target.value })}
            required
            options={products.map((p) => ({ value: p._id, label: p.name }))}
          />
          <Field
            label="Batch Number"
            value={batchForm.batchNumber}
            onChange={(e) => setBatchForm({ ...batchForm, batchNumber: e.target.value })}
            placeholder="e.g., BATCH-2024-001"
            required
          />
          <Field
            label="Quantity"
            type="number"
            value={batchForm.quantity}
            onChange={(e) => setBatchForm({ ...batchForm, quantity: e.target.value })}
            placeholder="Number of units"
            required
          />
          <Field
            label="Start Date"
            type="datetime-local"
            value={batchForm.startDate}
            onChange={(e) => setBatchForm({ ...batchForm, startDate: e.target.value })}
            required
          />
          <Field
            label="Expected End Date"
            type="datetime-local"
            value={batchForm.expectedEndDate}
            onChange={(e) => setBatchForm({ ...batchForm, expectedEndDate: e.target.value })}
          />
          <Field
            label="Location"
            value={batchForm.location}
            onChange={(e) => setBatchForm({ ...batchForm, location: e.target.value })}
            placeholder="Farm/house location"
          />
          <Field
            label="Notes"
            type="textarea"
            value={batchForm.notes}
            onChange={(e) => setBatchForm({ ...batchForm, notes: e.target.value })}
            placeholder="Any additional notes"
          />
          <button type="submit" className="btn-primary">Create Batch</button>
        </form>
      </FormModal>

      {/* Lifecycle Event Modal */}
      <FormModal
        isOpen={activeModal === 'lifecycle-create'}
        onClose={() => setActiveModal(null)}
        title="Record Lifecycle Event"
      >
        <form onSubmit={handleLifecycleCreate}>
          <Field
            label="Batch ID"
            value={lifecycleForm.batchId}
            onChange={(e) => setLifecycleForm({ ...lifecycleForm, batchId: e.target.value })}
            placeholder="Select batch"
            required
          />
          <Field
            label="Event Type"
            type="select"
            value={lifecycleForm.eventType}
            onChange={(e) => setLifecycleForm({ ...lifecycleForm, eventType: e.target.value })}
            options={[
              { value: 'VACCINATION', label: 'Vaccination' },
              { value: 'MEDICATION', label: 'Medication' },
              { value: 'WEIGHT_MEASUREMENT', label: 'Weight Measurement' },
              { value: 'MORTALITY', label: 'Mortality' },
            ]}
          />
          <Field
            label="Description"
            value={lifecycleForm.description}
            onChange={(e) => setLifecycleForm({ ...lifecycleForm, description: e.target.value })}
            placeholder="What happened"
            required
          />
          <Field
            label="Event Date"
            type="datetime-local"
            value={lifecycleForm.eventDate}
            onChange={(e) => setLifecycleForm({ ...lifecycleForm, eventDate: e.target.value })}
            required
          />
          <Field
            label="Quantity Affected"
            type="number"
            value={lifecycleForm.quantityAffected}
            onChange={(e) => setLifecycleForm({ ...lifecycleForm, quantityAffected: e.target.value })}
            placeholder="Number of units affected"
          />
          <button type="submit" className="btn-primary">Record Event</button>
        </form>
      </FormModal>

      {/* Transport Modal */}
      <FormModal
        isOpen={activeModal === 'transport-create'}
        onClose={() => setActiveModal(null)}
        title="Create Transport Manifest"
      >
        <form onSubmit={handleTransportCreate}>
          <Field
            label="Batch ID"
            value={transportForm.batchId}
            onChange={(e) => setTransportForm({ ...transportForm, batchId: e.target.value })}
            required
          />
          <Field
            label="Recipient ID"
            value={transportForm.toPartyId}
            onChange={(e) => setTransportForm({ ...transportForm, toPartyId: e.target.value })}
            required
          />
          <Field
            label="Vehicle ID"
            value={transportForm.vehicleId}
            onChange={(e) => setTransportForm({ ...transportForm, vehicleId: e.target.value })}
          />
          <Field
            label="Driver Name"
            value={transportForm.driverName}
            onChange={(e) => setTransportForm({ ...transportForm, driverName: e.target.value })}
          />
          <Field
            label="Departure Time"
            type="datetime-local"
            value={transportForm.departureTime}
            onChange={(e) => setTransportForm({ ...transportForm, departureTime: e.target.value })}
            required
          />
          <Field
            label="Origin Location"
            value={transportForm.originLocation}
            onChange={(e) => setTransportForm({ ...transportForm, originLocation: e.target.value })}
            required
          />
          <Field
            label="Destination Location"
            value={transportForm.destinationLocation}
            onChange={(e) => setTransportForm({ ...transportForm, destinationLocation: e.target.value })}
            required
          />
          <Field
            label="Monitor Temperature"
            type="checkbox"
            value={transportForm.temperatureMonitored}
            onChange={(e) => setTransportForm({ ...transportForm, temperatureMonitored: e.target.checked })}
          />
          <button type="submit" className="btn-primary">Create Transport</button>
        </form>
      </FormModal>

      {/* Processing Modal */}
      <FormModal
        isOpen={activeModal === 'processing-create'}
        onClose={() => setActiveModal(null)}
        title="Record Processing"
      >
        <form onSubmit={handleProcessingCreate}>
          <Field
            label="Batch ID"
            value={processingForm.batchId}
            onChange={(e) => setProcessingForm({ ...processingForm, batchId: e.target.value })}
            required
          />
          <Field
            label="Processing Date"
            type="datetime-local"
            value={processingForm.processingDate}
            onChange={(e) => setProcessingForm({ ...processingForm, processingDate: e.target.value })}
            required
          />
          <Field
            label="Facility Name"
            value={processingForm.facilityName}
            onChange={(e) => setProcessingForm({ ...processingForm, facilityName: e.target.value })}
            required
          />
          <Field
            label="Slaughter Count"
            type="number"
            value={processingForm.slaughterCount}
            onChange={(e) => setProcessingForm({ ...processingForm, slaughterCount: e.target.value })}
          />
          <Field
            label="Yield (kg)"
            type="number"
            value={processingForm.yieldKg}
            onChange={(e) => setProcessingForm({ ...processingForm, yieldKg: e.target.value })}
          />
          <Field
            label="Quality Score (0-100)"
            type="number"
            value={processingForm.qualityScore}
            onChange={(e) => setProcessingForm({ ...processingForm, qualityScore: e.target.value })}
          />
          <button type="submit" className="btn-primary">Record Processing</button>
        </form>
      </FormModal>

      {/* Batch QR Link Modal */}
      <FormModal
        isOpen={activeModal === 'batch-qr'}
        onClose={() => setActiveModal(null)}
        title="Link QR Code to Batch"
      >
        <form onSubmit={handleBatchLinkQr}>
          <Field
            label="Batch ID"
            value={batchQrForm.batchId}
            onChange={(e) => setBatchQrForm({ ...batchQrForm, batchId: e.target.value })}
            required
          />
          <Field
            label="QR Code"
            value={batchQrForm.qrCode}
            onChange={(e) => setBatchQrForm({ ...batchQrForm, qrCode: e.target.value })}
            placeholder="QR code value"
            required
          />
          <div style={{ display: 'flex', gap: '10px', marginTop: '15px' }}>
            <button type="submit" className="btn-primary" style={{ flex: 1 }}>Link QR Code</button>
            <button
              type="button"
              className="btn-primary"
              onClick={() => setShowQRScanner(true)}
              style={{ flex: 1, background: '#764ba2' }}
            >
              📱 Scan QR
            </button>
          </div>
        </form>
      </FormModal>

      {/* QR Scanner */}
      {showQRScanner && (
        <QRScanner
          onScan={handleQRScanned}
          onClose={() => setShowQRScanner(false)}
        />
      )}

      {/* Batch Update Modal */}
      <FormModal
        isOpen={activeModal === 'batch-update'}
        onClose={() => setActiveModal(null)}
        title="Update Batch"
      >
        <form onSubmit={handleBatchUpdate}>
          <Field
            label="Batch ID"
            value={batchUpdateForm.batchId}
            onChange={(e) => setBatchUpdateForm({ ...batchUpdateForm, batchId: e.target.value })}
            required
          />
          <Field
            label="Status"
            type="select"
            value={batchUpdateForm.status}
            onChange={(e) => setBatchUpdateForm({ ...batchUpdateForm, status: e.target.value })}
            options={[
              { value: 'ACTIVE', label: 'Active' },
              { value: 'COMPLETED', label: 'Completed' },
              { value: 'FAILED', label: 'Failed' }
            ]}
          />
          <Field
            label="Location"
            value={batchUpdateForm.location}
            onChange={(e) => setBatchUpdateForm({ ...batchUpdateForm, location: e.target.value })}
            placeholder="New location"
          />
          <button type="submit" className="btn-primary">Update Batch</button>
        </form>
      </FormModal>

      {/* Medication Modal */}
      <FormModal
        isOpen={activeModal === 'lifecycle-medication'}
        onClose={() => setActiveModal(null)}
        title="Record Medication"
      >
        <form onSubmit={handleMedicationSubmit}>
          <Field
            label="Batch ID"
            value={medicationForm.batchId}
            onChange={(e) => setMedicationForm({ ...medicationForm, batchId: e.target.value })}
            required
          />
          <Field
            label="Medication Name"
            value={medicationForm.medicationName}
            onChange={(e) => setMedicationForm({ ...medicationForm, medicationName: e.target.value })}
            placeholder="e.g., Amoxicillin"
            required
          />
          <Field
            label="Dosage"
            value={medicationForm.dosage}
            onChange={(e) => setMedicationForm({ ...medicationForm, dosage: e.target.value })}
            placeholder="e.g., 250mg"
            required
          />
          <Field
            label="Quantity Treated"
            type="number"
            value={medicationForm.quantityTreated}
            onChange={(e) => setMedicationForm({ ...medicationForm, quantityTreated: e.target.value })}
            required
          />
          <button type="submit" className="btn-primary">Record Medication</button>
        </form>
      </FormModal>

      {/* Weight Modal */}
      <FormModal
        isOpen={activeModal === 'lifecycle-weight'}
        onClose={() => setActiveModal(null)}
        title="Record Weight Measurement"
      >
        <form onSubmit={handleWeightSubmit}>
          <Field
            label="Batch ID"
            value={weightForm.batchId}
            onChange={(e) => setWeightForm({ ...weightForm, batchId: e.target.value })}
            required
          />
          <Field
            label="Average Weight (kg)"
            type="number"
            value={weightForm.averageWeight}
            onChange={(e) => setWeightForm({ ...weightForm, averageWeight: e.target.value })}
            required
          />
          <Field
            label="Sample Count"
            type="number"
            value={weightForm.sampleCount}
            onChange={(e) => setWeightForm({ ...weightForm, sampleCount: e.target.value })}
            required
          />
          <button type="submit" className="btn-primary">Record Weight</button>
        </form>
      </FormModal>

      {/* Mortality Modal */}
      <FormModal
        isOpen={activeModal === 'lifecycle-mortality'}
        onClose={() => setActiveModal(null)}
        title="Record Mortality"
      >
        <form onSubmit={handleMortalitySubmit}>
          <Field
            label="Batch ID"
            value={mortalityForm.batchId}
            onChange={(e) => setMortalityForm({ ...mortalityForm, batchId: e.target.value })}
            required
          />
          <Field
            label="Mortality Count"
            type="number"
            value={mortalityForm.mortalityCount}
            onChange={(e) => setMortalityForm({ ...mortalityForm, mortalityCount: e.target.value })}
            required
          />
          <Field
            label="Cause"
            value={mortalityForm.cause}
            onChange={(e) => setMortalityForm({ ...mortalityForm, cause: e.target.value })}
            placeholder="Disease, accident, etc."
            required
          />
          <button type="submit" className="btn-primary">Record Mortality</button>
        </form>
      </FormModal>

      {/* Temperature Modal */}
      <FormModal
        isOpen={activeModal === 'transport-temp'}
        onClose={() => setActiveModal(null)}
        title="Record Temperature"
      >
        <form onSubmit={handleTemperatureSubmit}>
          <Field
            label="Transport ID"
            value={temperatureForm.transportId}
            onChange={(e) => setTemperatureForm({ ...temperatureForm, transportId: e.target.value })}
            required
          />
          <Field
            label="Temperature (°C)"
            type="number"
            value={temperatureForm.temperature}
            onChange={(e) => setTemperatureForm({ ...temperatureForm, temperature: e.target.value })}
            placeholder="e.g., 4"
            required
          />
          <Field
            label="Timestamp"
            type="datetime-local"
            value={temperatureForm.timestamp}
            onChange={(e) => setTemperatureForm({ ...temperatureForm, timestamp: e.target.value })}
            required
          />
          <Field
            label="Location"
            value={temperatureForm.location}
            onChange={(e) => setTemperatureForm({ ...temperatureForm, location: e.target.value })}
            placeholder="GPS or checkpoint"
          />
          <button type="submit" className="btn-primary">Log Temperature</button>
        </form>
      </FormModal>

      {/* Transport Update Modal */}
      <FormModal
        isOpen={activeModal === 'transport-update'}
        onClose={() => setActiveModal(null)}
        title="Mark Transport Arrived"
      >
        <form onSubmit={handleTransportUpdate}>
          <Field
            label="Transport ID"
            value={transportUpdateForm.transportId}
            onChange={(e) => setTransportUpdateForm({ ...transportUpdateForm, transportId: e.target.value })}
            required
          />
          <Field
            label="Arrival Time"
            type="datetime-local"
            value={transportUpdateForm.arrivalTime}
            onChange={(e) => setTransportUpdateForm({ ...transportUpdateForm, arrivalTime: e.target.value })}
            required
          />
          <Field
            label="Status"
            type="select"
            value={transportUpdateForm.status}
            onChange={(e) => setTransportUpdateForm({ ...transportUpdateForm, status: e.target.value })}
            options={[
              { value: 'arrived', label: 'Arrived' },
              { value: 'completed', label: 'Completed' }
            ]}
          />
          <button type="submit" className="btn-primary">Update Transport</button>
        </form>
      </FormModal>

      {/* Processing Update Modal */}
      <FormModal
        isOpen={activeModal === 'processing-update'}
        onClose={() => setActiveModal(null)}
        title="Update Quality Score"
      >
        <form onSubmit={handleProcessingUpdate}>
          <Field
            label="Record ID"
            value={processingUpdateForm.recordId}
            onChange={(e) => setProcessingUpdateForm({ ...processingUpdateForm, recordId: e.target.value })}
            required
          />
          <Field
            label="Quality Score (0-100)"
            type="number"
            value={processingUpdateForm.qualityScore}
            onChange={(e) => setProcessingUpdateForm({ ...processingUpdateForm, qualityScore: e.target.value })}
            required
          />
          <Field
            label="Notes"
            type="textarea"
            value={processingUpdateForm.notes}
            onChange={(e) => setProcessingUpdateForm({ ...processingUpdateForm, notes: e.target.value })}
            placeholder="Quality observations"
          />
          <button type="submit" className="btn-primary">Update Quality</button>
        </form>
      </FormModal>

      {/* Certification Modal */}
      <FormModal
        isOpen={activeModal === 'certification'}
        onClose={() => setActiveModal(null)}
        title="Request Certification"
      >
        <form onSubmit={handleCertificationSubmit}>
          <Field
            label="Processing Record ID"
            value={certificationForm.processingRecordId}
            onChange={(e) => setCertificationForm({ ...certificationForm, processingRecordId: e.target.value })}
            required
          />
          <Field
            label="Certification Type"
            type="select"
            value={certificationForm.certType}
            onChange={(e) => setCertificationForm({ ...certificationForm, certType: e.target.value })}
            required
            options={[
              { value: 'halal', label: 'Halal' },
              { value: 'organic', label: 'Organic' },
              { value: 'food_safety', label: 'Food Safety' },
              { value: 'gmo_free', label: 'GMO Free' }
            ]}
          />
          <button type="submit" className="btn-primary">Request Certification</button>
        </form>
      </FormModal>
    </div>
  );
};

export default Operations;
