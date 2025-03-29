import React, { useState, useEffect } from 'react';
import { BrowserRouter as Router, Routes, Route, Navigate, useLocation } from 'react-router-dom';
import Login from './Login';
import GoogleCallback from './GoogleCallback';
import Dashboard from './Dashboard';
import Header from './Header';
import { Box } from '@mui/material';
import { apiGet } from './api';

interface AuthContextType {
  userName: string;
  userEmail: string;
  setUserInfo: (name: string, email: string) => void;
}

export const AuthContext = React.createContext<AuthContextType>({
  userName: '',
  userEmail: '',
  setUserInfo: () => {}
});

const AuthProvider: React.FC<{ children: React.ReactNode }> = ({ children }) => {
  // Initialize from localStorage if available
  const [userName, setUserName] = useState(() => localStorage.getItem('userName') || '');
  const [userEmail, setUserEmail] = useState(() => localStorage.getItem('userEmail') || '');
  
  const fetchUserInfo = async () => {
    // Only fetch if we have a token
    const token = localStorage.getItem('token');
    if (!token) return;
    
    try {
      const userData = await apiGet('/api/user/me');
      if (userData) {
        const name = userData.name || '';
        const email = userData.email || '';
        
        // Update state and localStorage
        setUserName(name);
        setUserEmail(email);
        localStorage.setItem('userName', name);
        localStorage.setItem('userEmail', email);
      }
    } catch (error) {
      console.error("Failed to fetch user info in AuthProvider:", error);
    }
  };
  
  // Fetch user info on mount and when token changes
  useEffect(() => {
    fetchUserInfo();
    // We don't need to add fetchUserInfo as a dependency as it's stable
  }, []);

  const setUserInfo = (name: string, email: string) => {
    setUserName(name);
    setUserEmail(email);
    // Store in localStorage for persistence
    localStorage.setItem('userName', name);
    localStorage.setItem('userEmail', email);
  };

  return (
    <AuthContext.Provider value={{ userName, userEmail, setUserInfo }}>
      {children}
    </AuthContext.Provider>
  );
};

const RequireAuth: React.FC<{ children: JSX.Element }> = ({ children }) => {
  const token = localStorage.getItem('token');
  const location = useLocation();
  const { userName, userEmail } = React.useContext(AuthContext);

  if (!token) {
    return <Navigate to="/login" state={{ from: location }} replace />;
  }

  return (
    <Box sx={{ display: 'flex', flexDirection: 'column', minHeight: '100vh' }}>
      <Header userName={userName} userEmail={userEmail} />
      <Box sx={{ flexGrow: 1 }}>
        {children}
      </Box>
    </Box>
  );
};

const App: React.FC = () => {
  return (
    <AuthProvider>
      <Router>
        <Routes>
          <Route path="/login" element={<Login />} />
          <Route path="/auth/callback" element={<GoogleCallback />} />
          <Route path="/" element={<RequireAuth><Dashboard /></RequireAuth>} />
        </Routes>
      </Router>
    </AuthProvider>
  );
};

export default App;
