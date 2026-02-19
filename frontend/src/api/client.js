const DEFAULT_BASE_URL = 'http://localhost:8000';

export const API_BASE_URL = import.meta.env.VITE_API_BASE_URL || DEFAULT_BASE_URL;

const buildUrl = (path, query) => {
  const url = new URL(path, API_BASE_URL);
  if (query) {
    const params = new URLSearchParams();
    Object.entries(query).forEach(([key, value]) => {
      if (value !== undefined && value !== null && value !== '') {
        params.append(key, String(value));
      }
    });
    url.search = params.toString();
  }
  return url.toString();
};

export const apiRequest = async (path, options = {}) => {
  const {
    method = 'GET',
    token,
    body,
    query
  } = options;

  const headers = {
    'Content-Type': 'application/json'
  };

  if (token) {
    headers.Authorization = `Bearer ${token}`;
  }

  const response = await fetch(buildUrl(path, query), {
    method,
    headers,
    body: body ? JSON.stringify(body) : undefined
  });

  if (response.status === 204) {
    return null;
  }

  const text = await response.text();
  let data = null;
  if (text) {
    try {
      data = JSON.parse(text);
    } catch (error) {
      data = { message: text };
    }
  }

  if (!response.ok) {
    const error = new Error(data?.detail || data?.message || 'Request failed');
    error.status = response.status;
    error.payload = data;
    throw error;
  }

  return data;
};
