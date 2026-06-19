import { auth } from './firebase';

export class ApiError extends Error {
  status: number;
  constructor(status: number, message: string) {
    super(message);
    this.status = status;
  }
}

export const apiFetch = async (endpoint: string, options: RequestInit = {}) => {
  let token = '';
  if (auth.currentUser) {
    // If we're using the mock user in dev mode, construct the mock token expected by the backend.
    if (auth.currentUser.uid === 'mock-user-123') {
      token = `mock-${auth.currentUser.email}`;
    } else {
      token = await auth.currentUser.getIdToken();
    }
  }

  const headers = new Headers(options.headers || {});
  if (token) {
    headers.set('Authorization', `Bearer ${token}`);
  }

  // Only set Content-Type for non-FormData bodies.
  // Letting the browser set it for FormData ensures the multipart boundary is included.
  if (!headers.has('Content-Type') && !(options.body instanceof FormData)) {
    headers.set('Content-Type', 'application/json');
  }

  const response = await fetch(`/api${endpoint}`, {
    ...options,
    headers,
  });

  if (!response.ok) {
    const errorText = await response.text();
    let errorMessage = errorText;
    try {
      const errorJson = JSON.parse(errorText);
      if (errorJson.detail) {
        errorMessage = typeof errorJson.detail === 'string' ? errorJson.detail : JSON.stringify(errorJson.detail);
      }
    } catch (e) {
      // Ignore JSON parse errors, just use the raw text
    }
    throw new ApiError(response.status, errorMessage);
  }

  // Handle 204 No Content responses (e.g. DELETE)
  if (response.status === 204) {
    return null;
  }

  return response.json();
};
