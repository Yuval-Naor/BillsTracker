import React, { useEffect, useState } from 'react';
import { useLocation, useNavigate } from 'react-router-dom';
import { Container, Typography, CircularProgress } from '@mui/material';

const GoogleCallback: React.FC = () => {
  const location = useLocation();
  const navigate = useNavigate();
  const [error, setError] = useState<string | null>(null);

  useEffect(() => {
    const params = new URLSearchParams(location.search);
    const token = params.get('token');
    
    // Clear any existing tokens first
    localStorage.removeItem('token');
    
    if (token) {
      try {
        localStorage.setItem('token', token);
        navigate('/');
      } catch (error) {
        console.error("Error storing token:", error);
        setError("Failed to store authentication token");
        setTimeout(() => navigate('/login'), 3000);
      }
    } else {
      console.error("Token missing in callback URL");
      setError("Authentication failed - no token received");
      setTimeout(() => navigate('/login'), 3000);
    }
  }, [location.search, navigate]);

  return (
    <Container sx={{ textAlign: 'center', mt: 8 }}>
      {error ? (
        <Typography variant="h5" color="error">{error}</Typography>
      ) : (
        <>
          <CircularProgress size={40} sx={{ mb: 2 }} />
          <Typography variant="h5">Signing in...</Typography>
        </>
      )}
    </Container>
  );
};

export default GoogleCallback;
