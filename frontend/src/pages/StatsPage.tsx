import React from 'react';
import { StatsCards } from '../components/StatsCards';

export const StatsPage: React.FC = () => {
  return (
    <div className="py-8">
      <h1 className="text-3xl font-bold text-center text-gray-900 mb-8">Platform Statistics</h1>
      <StatsCards />
    </div>
  );
};
