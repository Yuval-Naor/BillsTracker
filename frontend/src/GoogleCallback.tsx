import React, { useEffect } from 'react';
import { useLocation, useNavigate } from 'react-router-dom';
import { Container, Typography } from '@mui/material';

const GoogleCallback: React.FC = () => {
  const location = useLocation();
  const navigate = useNavigate();

  useEffect(() => {
    const params = new URLSearchParams(location.search);
    const token = params.get('token');
    if (token) {
      localStorage.setItem('token', token);
      navigate('/');
    }
  }, [location.search, navigate]);

  return (
    <Container sx={{ textAlign: 'center', mt: 8 }}>
      <Typography variant="h5">Signing in...</Typography>
    </Container>
  );
};

export default GoogleCallback;
