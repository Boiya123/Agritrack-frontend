import { apiRequest } from './client';

export const authApi = {
  register: (payload) => apiRequest('/auth/register', { method: 'POST', body: payload }),
  login: (payload) => apiRequest('/auth/login', { method: 'POST', body: payload }),
  refresh: (token) => apiRequest('/auth/refresh', { method: 'POST', token }),
  validateRole: (token, requiredRole) => apiRequest(`/auth/validate-role/${requiredRole}`, { token }),
  logout: (token) => apiRequest('/auth/logout', { method: 'POST', token }),
  me: (token) => apiRequest('/auth/me', { token }),
  passwordReset: (email) => apiRequest('/auth/password-reset', { method: 'POST', query: { email } }),
  passwordChange: (token, oldPassword, newPassword) => apiRequest('/auth/password-change', {
    method: 'PUT',
    token,
    query: { old_password: oldPassword, new_password: newPassword }
  })
};

export const productsApi = {
  list: (token, params = {}) => apiRequest('/products', { token, query: params }),
  get: (token, productId) => apiRequest(`/products/${productId}`, { token }),
  create: (token, payload) => apiRequest('/products', { method: 'POST', token, body: payload }),
  update: (token, productId, payload) => apiRequest(`/products/${productId}`, { method: 'PUT', token, body: payload }),
  enable: (token, productId) => apiRequest(`/products/${productId}/enable`, { method: 'POST', token }),
  disable: (token, productId) => apiRequest(`/products/${productId}/disable`, { method: 'POST', token })
};

export const batchesApi = {
  list: (token, params = {}) => apiRequest('/batches', { token, query: params }),
  get: (token, batchId) => apiRequest(`/batches/${batchId}`, { token }),
  create: (token, payload) => apiRequest('/batches', { method: 'POST', token, body: payload }),
  update: (token, batchId, payload) => apiRequest(`/batches/${batchId}`, { method: 'PUT', token, body: payload }),
  linkQr: (token, batchId, qrCode) => apiRequest(`/batches/${batchId}/qr-link`, { method: 'POST', token, query: { qr_code: qrCode } }),
  archive: (token, batchId) => apiRequest(`/batches/${batchId}/archive`, { method: 'POST', token })
};

export const lifecycleApi = {
  listByBatch: (token, batchId, params = {}) => apiRequest(`/lifecycle/batches/${batchId}/events`, { token, query: params }),
  create: (token, payload) => apiRequest('/lifecycle', { method: 'POST', token, body: payload }),
  recordVaccination: (token, payload) => apiRequest('/lifecycle/record-vaccination', { method: 'POST', token, query: payload }),
  recordMedication: (token, payload) => apiRequest('/lifecycle/record-medication', { method: 'POST', token, query: payload }),
  recordMortality: (token, payload) => apiRequest('/lifecycle/record-mortality', { method: 'POST', token, query: payload }),
  recordWeight: (token, payload) => apiRequest('/lifecycle/record-weight', { method: 'POST', token, query: payload })
};

export const logisticsApi = {
  createTransport: (token, payload) => apiRequest('/logistics/transports', { method: 'POST', token, body: payload }),
  updateTransport: (token, transportId, payload) => apiRequest(`/logistics/transports/${transportId}`, { method: 'PUT', token, body: payload }),
  listTransportsByBatch: (token, batchId, params = {}) => apiRequest(`/logistics/batches/${batchId}/transports`, { token, query: params }),
  recordTemperature: (token, payload) => apiRequest('/logistics/temperature-logs', { method: 'POST', token, body: payload }),
  markTransportCompleted: (token, transportId) => apiRequest(`/logistics/transports/${transportId}/mark-completed`, { method: 'POST', token }),
  listTemperatureLogs: (token, transportId, params = {}) => apiRequest(`/logistics/transports/${transportId}/temperature-logs`, { token, query: params }),
  listTemperatureViolations: (token, transportId) => apiRequest(`/logistics/transports/${transportId}/temperature-violations`, { token })
};

export const processingApi = {
  createRecord: (token, payload) => apiRequest('/processing/records', { method: 'POST', token, body: payload }),
  listRecordsByBatch: (token, batchId, params = {}) => apiRequest(`/processing/batches/${batchId}/records`, { token, query: params }),
  createCertification: (token, payload) => apiRequest('/processing/certifications', { method: 'POST', token, body: payload }),
  updateRecord: (token, recordId, payload) => apiRequest(`/processing/records/${recordId}`, { method: 'PUT', token, body: payload }),
  listCertifications: (token, recordId) => apiRequest(`/processing/records/${recordId}/certifications`, { token }),
  updateCertification: (token, certId, payload) => apiRequest(`/processing/certifications/${certId}`, { method: 'PUT', token, body: payload }),
  approveCertification: (token, certId) => apiRequest(`/processing/certifications/${certId}/approve`, { method: 'POST', token }),
  rejectCertification: (token, certId, reason) => apiRequest(`/processing/certifications/${certId}/reject`, { method: 'POST', token, query: { reason } })
};

export const regulatoryApi = {
  createRecord: (token, payload) => apiRequest('/regulatory/records', { method: 'POST', token, body: payload }),
  listRecordsByBatch: (token, batchId, params = {}) => apiRequest(`/regulatory/batches/${batchId}/records`, { token, query: params }),
  approveRecord: (token, recordId) => apiRequest(`/regulatory/records/${recordId}/approve`, { method: 'POST', token }),
  rejectRecord: (token, recordId, reason) => apiRequest(`/regulatory/records/${recordId}/reject`, { method: 'POST', token, query: { reason } }),
  updateRecord: (token, recordId, payload) => apiRequest(`/regulatory/records/${recordId}`, { method: 'PUT', token, body: payload }),
  addAuditFlag: (token, recordId, flag) => apiRequest(`/regulatory/records/${recordId}/add-audit-flag`, { method: 'POST', token, query: { flag } }),
  complianceStatus: (token, farmerId) => apiRequest(`/regulatory/farmers/${farmerId}/compliance-status`, { token })
};
