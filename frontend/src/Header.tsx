import React, { useState } from 'react';
import { AppBar, Toolbar, Typography, Box, Avatar, Menu, MenuItem, IconButton, Tooltip } from '@mui/material';
import { useNavigate } from 'react-router-dom';

interface HeaderProps {
  userName: string;
  userEmail: string;
}

const Header: React.FC<HeaderProps> = ({ userName, userEmail }) => {
  const navigate = useNavigate();
  const [anchorEl, setAnchorEl] = useState<null | HTMLElement>(null);
  const open = Boolean(anchorEl);

  // Get user initials for the avatar
  const getInitials = () => {
    return userName ? userName.split(' ').map(n => n[0]).join('').toUpperCase() : userEmail ? userEmail[0].toUpperCase() : '?';
  };

  const handleClick = (event: React.MouseEvent<HTMLElement>) => {
    setAnchorEl(event.currentTarget);
  };

  const handleClose = () => {
    setAnchorEl(null);
  };

  const handleLogout = () => {
    localStorage.removeItem('token');
    navigate('/login');
  };

  return (
    <AppBar position="static" color="primary" elevation={1}>
      <Toolbar>
        <Typography variant="h6" component="div" sx={{ flexGrow: 1 }}>
          Gmail Bill Scanner
        </Typography>
        <Tooltip title="Click to logout">
          <Box sx={{ display: 'flex', alignItems: 'center', cursor: 'pointer' }} onClick={handleClick}>
            <Box sx={{ textAlign: 'right', mr: 1 }}>
              {userName && (
                <Typography variant="body1" sx={{ fontWeight: 'medium' }}>
                  {userName}
                </Typography>
              )}
              <Typography variant="body2" color="inherit" sx={{ opacity: 0.8 }}>
                {userEmail}
              </Typography>
            </Box>
            <IconButton size="small" edge="end" color="inherit" aria-label="user menu">
              <Avatar sx={{ width: 32, height: 32, bgcolor: 'secondary.main' }}>
                {getInitials()}
              </Avatar>
            </IconButton>
          </Box>
        </Tooltip>
        <Menu
          anchorEl={anchorEl}
          open={open}
          onClose={handleClose}
          onClick={handleClose}
          transformOrigin={{ horizontal: 'right', vertical: 'top' }}
          anchorOrigin={{ horizontal: 'right', vertical: 'bottom' }}
        >
          <MenuItem onClick={handleLogout}>Logout</MenuItem>
        </Menu>
      </Toolbar>
    </AppBar>
  );
};

export default Header;
