import React, { useEffect, useState } from 'react';
import { Container, Tabs, Tab, Box, Typography, Button, Grid } from '@mui/material';
import { apiGet, apiPost } from './api';
import Filters from './Filters';
import Charts from './Charts';

interface Bill {
  id: number;
  vendor: string | null;
  date: string | null;
  due_date: string | null;
  amount: number | null;
  currency: string | null;
  category: string | null;
  status: string | null;
}

const Dashboard: React.FC = () => {
  const [bills, setBills] = useState<Bill[]>([]);
  const [tabValue, setTabValue] = useState(0);
  const [loading, setLoading] = useState(false);

  const fetchBills = async () => {
    setLoading(true);
    try {
      const data = await apiGet('/api/bills');
      setBills(data);
    } catch (error) {
      console.error("Failed to fetch bills:", error);
    } finally {
      setLoading(false);
    }
  };

  const handleSync = async () => {
    try {
      await apiPost('/api/sync');
      setTimeout(fetchBills, 5000);
    } catch (error) {
      console.error("Sync failed:", error);
    }
  };

  useEffect(() => {
    fetchBills();
  }, []);

  const handleTabChange = (event: React.SyntheticEvent, newValue: number) => {
    setTabValue(newValue);
  };

  const filteredBills = bills.filter(bill => {
    if (tabValue === 0) return bill.status?.toLowerCase() !== "paid";
    else return bill.status?.toLowerCase() === "paid";
  });

  return (
    <Container maxWidth="lg" sx={{ mt: 4, px: { xs: 2, sm: 3, md: 4 } }}>
      <Grid container spacing={2}>
        <Grid item xs={12} sm={8}>
          <Typography variant="h4">Your Bills</Typography>
        </Grid>
        <Grid item xs={12} sm={4} textAlign="right">
          <Button variant="contained" onClick={handleSync}>
            Sync Bills
          </Button>
        </Grid>
      </Grid>
      <Box mt={2}>
        <Filters bills={bills} onFilter={setBills} />
      </Box>
      <Box sx={{ borderBottom: 1, borderColor: 'divider', mt: 2 }}>
        <Tabs value={tabValue} onChange={handleTabChange} aria-label="bill status tabs">
          <Tab label="Unpaid Bills" />
          <Tab label="Paid Bills" />
        </Tabs>
      </Box>
      <Box mt={2}>
        {loading ? (
          <Typography>Loading bills...</Typography>
        ) : (
          <table style={{ width: '100%', borderCollapse: 'collapse' }}>
            <thead>
              <tr>
                <th style={{ borderBottom: '1px solid #ddd', padding: '8px' }}>Vendor</th>
                <th style={{ borderBottom: '1px solid #ddd', padding: '8px' }}>Date</th>
                <th style={{ borderBottom: '1px solid #ddd', padding: '8px' }}>Due Date</th>
                <th style={{ borderBottom: '1px solid #ddd', padding: '8px' }}>Amount</th>
                <th style={{ borderBottom: '1px solid #ddd', padding: '8px' }}>Category</th>
                <th style={{ borderBottom: '1px solid #ddd', padding: '8px' }}>Status</th>
              </tr>
            </thead>
            <tbody>
              {filteredBills.map(bill => (
                <tr key={bill.id} style={{ backgroundColor: bill.status?.toLowerCase() === 'paid' ? '#e0ffe0' : 'inherit' }}>
                  <td style={{ borderBottom: '1px solid #ddd', padding: '8px' }}>{bill.vendor || '-'}</td>
                  <td style={{ borderBottom: '1px solid #ddd', padding: '8px' }}>{bill.date || '-'}</td>
                  <td style={{ borderBottom: '1px solid #ddd', padding: '8px' }}>{bill.due_date || '-'}</td>
                  <td style={{ borderBottom: '1px solid #ddd', padding: '8px' }}>{bill.amount !== null ? bill.amount.toFixed(2) : '-'}</td>
                  <td style={{ borderBottom: '1px solid #ddd', padding: '8px' }}>{bill.category || '-'}</td>
                  <td style={{ borderBottom: '1px solid #ddd', padding: '8px' }}>{bill.status || '-'}</td>
                </tr>
              ))}
              {filteredBills.length === 0 && (
                <tr>
                  <td colSpan={6} style={{ textAlign: 'center', padding: '16px' }}>
                    No bills found.
                  </td>
                </tr>
              )}
            </tbody>
          </table>
        )}
      </Box>
      <Box mt={4}>
        <Charts bills={bills} />
      </Box>
    </Container>
  );
};

export default Dashboard;
