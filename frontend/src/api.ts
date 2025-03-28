const API_BASE = process.env.REACT_APP_API_BASE_URL || "http://localhost:8000";

export async function apiGet(path: string) {
  const token = localStorage.getItem('token');
  try {
    const res = await fetch(`${API_BASE}${path}`, {
      headers: {
        'Authorization': token ? `Bearer ${token}` : ''
      }
    });
    
    if (res.status === 401) {
      // Handle authentication error
      localStorage.removeItem('token'); // Clear invalid token
      window.location.href = '/login';
      throw new Error('Authentication failed - please login again');
    }
    
    if (!res.ok) {
      throw new Error(`API GET failed: ${res.status}`);
    }
    
    return res.json();
  } catch (error) {
    console.error(`API error (GET ${path}):`, error);
    throw error;
  }
}

export async function apiPost(path: string, body: any = null) {
  const token = localStorage.getItem('token');
  try {
    const res = await fetch(`${API_BASE}${path}`, {
      method: 'POST',
      headers: {
        'Authorization': token ? `Bearer ${token}` : '',
        'Content-Type': 'application/json'
      },
      body: body ? JSON.stringify(body) : null
    });
    
    if (res.status === 401) {
      // Handle authentication error
      localStorage.removeItem('token'); // Clear invalid token
      window.location.href = '/login';
      throw new Error('Authentication failed - please login again');
    }
    
    if (!res.ok) {
      throw new Error(`API POST failed: ${res.status}`);
    }
    
    return res.json().catch(() => ({})); // Handle empty response bodies
  } catch (error) {
    console.error(`API error (POST ${path}):`, error);
    throw error;
  }
}
