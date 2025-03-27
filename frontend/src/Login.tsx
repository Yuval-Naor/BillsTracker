import React from 'react';
import { Container, Button, Typography, Box } from '@mui/material';

const Login: React.FC = () => {
  const handleGoogleSignIn = () => {
    window.location.href = `${process.env.REACT_APP_API_BASE_URL || "http://localhost:8000"}/auth/google`;
  };

  return (
    <Container maxWidth="sm" sx={{ textAlign: 'center', mt: 8 }}>
      <Typography variant="h4" gutterBottom>
        Welcome to Gmail Bill Scanner
      </Typography>
      <Typography variant="body1" gutterBottom>
        Please sign in with Google to continue.
      </Typography>
      <Box mt={4}>
        <Button variant="contained" size="large" onClick={handleGoogleSignIn}>
          Sign in with Google
        </Button>
      </Box>
    </Container>
  );
};

export default Login;
