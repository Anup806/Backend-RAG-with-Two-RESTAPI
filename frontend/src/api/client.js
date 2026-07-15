const API_BASE = import.meta.env.VITE_API_BASE_URL || 'http://localhost:8000';

async function handleResponse(res) {
  const data = await res.json().catch(() => null);
  if (!res.ok) {
    // FastAPI's HTTPException puts the message in { detail: "..." } — surface that,
    // not a generic "request failed" string, so errors are actionable in the UI.
    throw new Error(data?.detail || `Request failed (${res.status})`);
  }
  return data;
}

/**
 * GET / — health check. Used to drive the connection status indicator.
 */
export async function checkHealth() {
  const res = await fetch(`${API_BASE}/`);
  return handleResponse(res);
}

/**
 * POST /ingest/upload — multipart upload with real progress events.
 * Uses XMLHttpRequest instead of fetch because fetch has no upload progress API.
 */
export function uploadDocument(file, strategy, onProgress) {
  return new Promise((resolve, reject) => {
    const formData = new FormData();
    formData.append('file', file);
    formData.append('strategy', strategy);

    const xhr = new XMLHttpRequest();
    xhr.open('POST', `${API_BASE}/ingest/upload`);

    xhr.upload.onprogress = (event) => {
      if (event.lengthComputable && onProgress) {
        onProgress(Math.round((event.loaded / event.total) * 100));
      }
    };

    xhr.onload = () => {
      let data = null;
      try {
        data = JSON.parse(xhr.responseText);
      } catch {
        // non-JSON body, leave data as null
      }
      if (xhr.status >= 200 && xhr.status < 300) {
        resolve(data);
      } else {
        reject(new Error(data?.detail || `Upload failed (${xhr.status})`));
      }
    };

    xhr.onerror = () => reject(new Error('Network error during upload. Is the backend running?'));

    xhr.send(formData);
  });
}

/**
 * POST /chat/message
 */
export async function sendMessage(sessionId, message) {
  const res = await fetch(`${API_BASE}/chat/message`, {
    method: 'POST',
    headers: { 'Content-Type': 'application/json' },
    body: JSON.stringify({ session_id: sessionId, message }),
  });
  return handleResponse(res);
}

/**
 * GET /chat/history/{session_id}
 */
export async function getHistory(sessionId) {
  const res = await fetch(`${API_BASE}/chat/history/${sessionId}`);
  return handleResponse(res);
}

/**
 * POST /chat/clear
 */
export async function clearHistory(sessionId) {
  const res = await fetch(`${API_BASE}/chat/clear`, {
    method: 'POST',
    headers: { 'Content-Type': 'application/json' },
    body: JSON.stringify({ session_id: sessionId }),
  });
  return handleResponse(res);
}

/**
 * GET /chat/bookings
 */
export async function getBookings() {
  const res = await fetch(`${API_BASE}/chat/bookings`);
  return handleResponse(res);
}

/**
 * DELETE /chat/bookings/{session_id}
 * Note: this deletes every booking tied to that session_id, not a single row.
 */
export async function deleteBookingsBySession(sessionId) {
  const res = await fetch(`${API_BASE}/chat/bookings/${sessionId}`, { method: 'DELETE' });
  return handleResponse(res);
}
