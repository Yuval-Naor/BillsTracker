import React from 'react';
import { Box, Typography } from '@mui/material';
import { ResponsiveContainer, BarChart, Bar, XAxis, YAxis, Tooltip, Legend, PieChart, Pie, Cell } from 'recharts';

interface Bill {
  date: string | null;
  amount: number | null;
  category: string | null;
}

interface ChartsProps {
  bills: Bill[];
}

const COLORS = ['#8884d8', '#82ca9d', '#ffc658', '#ff7f50', '#87cefa'];

const Charts: React.FC<ChartsProps> = ({ bills }) => {
  const monthlyData: { month: string; total: number }[] = [];
  bills.forEach(bill => {
    if (bill.date && bill.amount !== null) {
      const month = bill.date.substring(0, 7);
      const item = monthlyData.find(d => d.month === month);
      if (item) {
        item.total += Number(bill.amount);
      } else {
        monthlyData.push({ month, total: Number(bill.amount) });
      }
    }
  });
  monthlyData.sort((a, b) => a.month.localeCompare(b.month));

  const categoryData: { category: string; total: number }[] = [];
  bills.forEach(bill => {
    if (bill.category && bill.amount !== null) {
      const item = categoryData.find(d => d.category === bill.category);
      if (item) {
        item.total += Number(bill.amount);
      } else {
        categoryData.push({ category: bill.category, total: Number(bill.amount) });
      }
    }
  });

  return (
    <Box>
      <Typography variant="h5" gutterBottom>
        Monthly Expenses
      </Typography>
      <ResponsiveContainer width="100%" height={300}>
        <BarChart data={monthlyData}>
          <XAxis dataKey="month" />
          <YAxis />
          <Tooltip />
          <Legend />
          <Bar dataKey="total" fill="#3f51b5" name="Total Amount" />
        </BarChart>
      </ResponsiveContainer>
      <Typography variant="h5" gutterBottom sx={{ mt: 4 }}>
        Expenses by Category
      </Typography>
      <ResponsiveContainer width="100%" height={300}>
        <PieChart>
          <Pie
            data={categoryData}
            dataKey="total"
            nameKey="category"
            outerRadius={100}
            fill="#82ca9d"
            label
          >
            {categoryData.map((entry, index) => (
              <Cell key={`cell-${index}`} fill={COLORS[index % COLORS.length]} />
            ))}
          </Pie>
          <Tooltip />
          <Legend />
        </PieChart>
      </ResponsiveContainer>
    </Box>
  );
};

export default Charts;
