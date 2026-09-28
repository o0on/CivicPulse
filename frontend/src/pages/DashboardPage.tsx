import React from 'react';
import { ComplaintTable } from '../components/ComplaintTable';

export const DashboardPage: React.FC = () => {
  return (
    <div className="py-8">
      <h1 className="text-3xl font-bold text-center text-gray-900 mb-8">Complaint Dashboard</h1>
      <ComplaintTable />
    </div>
  );
};

// Layout: responsive container wrapper
