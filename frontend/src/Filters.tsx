import React, { useState } from 'react';
import { Box, TextField, FormControl, InputLabel, Select, MenuItem } from '@mui/material';

// Make sure this Bill interface matches the one in Dashboard.tsx
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

interface FiltersProps {
  bills: Bill[];
  onFilter: (filtered: Bill[]) => void;
}

const Filters: React.FC<FiltersProps> = ({ bills, onFilter }) => {
  const [vendor, setVendor] = useState("");
  const [month, setMonth] = useState("");
  const [category, setCategory] = useState("");

  const vendors = Array.from(new Set(bills.map(b => b.vendor).filter((v): v is string => v !== null)));
  const categories = Array.from(new Set(bills.map(b => b.category).filter(Boolean)));

  const handleFilterChange = React.useCallback(() => {
    const filtered = bills.filter(b => {
      const matchVendor = vendor ? b.vendor === vendor : true;
      const matchCategory = category ? b.category === category : true;
      const matchMonth = month ? (b.date && b.date.includes(month)) : true;
      return matchVendor && matchCategory && matchMonth;
    });
    onFilter(filtered);
  }, [bills, vendor, category, month, onFilter]);

  return (
    <Box sx={{ display: 'flex', gap: 2, flexWrap: 'wrap', mb: 2 }}>
      <TextField
        label="Month (e.g., 2025-03)"
        variant="outlined"
        size="small"
        value={month}
        onChange={(e) => { setMonth(e.target.value); handleFilterChange(); }}
      />
      <FormControl variant="outlined" size="small">
        <InputLabel>Vendor</InputLabel>
        <Select
          label="Vendor"
          value={vendor}
          onChange={(e) => { setVendor(e.target.value); handleFilterChange(); }}
        >
          <MenuItem value=""><em>All</em></MenuItem>
          {vendors.map(v => (
            <MenuItem key={v} value={v || ''}>{v || 'Unknown Vendor'}</MenuItem>
          ))}
        </Select>
      </FormControl>
      <FormControl variant="outlined" size="small">
        <InputLabel>Category</InputLabel>
        <Select
          label="Category"
          value={category}
          onChange={(e) => { setCategory(e.target.value); handleFilterChange(); }}
        >
          <MenuItem value=""><em>All</em></MenuItem>
          {categories.map(c => (
            <MenuItem key={c || 'unknown'} value={c || ''}>{c || 'Unknown Category'}</MenuItem>
          ))}
        </Select>
      </FormControl>
    </Box>
  );
};

export default Filters;
