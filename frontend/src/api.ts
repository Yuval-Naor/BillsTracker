const API_BASE = process.env.REACT_APP_API_BASE_URL || "http://localhost:8000";

export async function apiGet(path: string) {
  const token = localStorage.getItem('token');
  const res = await fetch(`${API_BASE}${path}`, {
    headers: {
      'Authorization': token ? `Bearer ${token}` : ''
    }
  });
  if (!res.ok) {
    throw new Error(`API GET failed: ${res.status}`);
  }
  return res.json();
}

export async function apiPost(path: string, body: any = null) {
  const token = localStorage.getItem('token');
  const res = await fetch(`${API_BASE}${path}`, {
    method: 'POST',
    headers: {
      'Authorization': token ? `Bearer ${token}` : '',
      'Content-Type': 'application/json'
    },
    body: body ? JSON.stringify(body) : null
  });
  if (!res.ok) {
    throw new Error(`API POST failed: ${res.status}`);
  }
  return res.json().catch(() => ({}));
}
