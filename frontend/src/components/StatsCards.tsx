import React, { useEffect, useState } from 'react';
import { api } from '../api/client';
import { StatsResponse } from '../types';

export const StatsCards: React.FC = () => {
  const [stats, setStats] = useState<StatsResponse | null>(null);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState<string | null>(null);

  const fetchStats = async () => {
    try {
      const data = await api.stats.get();
      setStats(data);
      setError(null);
    } catch (err) {
      setError('Failed to fetch stats');
      console.error(err);
    } finally {
      setLoading(false);
    }
  };

  useEffect(() => {
    fetchStats();
    const interval = setInterval(fetchStats, 30000);
    return () => clearInterval(interval);
  }, []);

  if (loading && !stats) return <div className="text-center mt-10">Loading stats...</div>;
  if (error && !stats) return <div className="text-center mt-10 text-red-500">{error}</div>;
  if (!stats) return null;

  return (
    <div className="max-w-6xl mx-auto mt-8 p-6">
      <div className="flex justify-between items-center mb-6">
        <h2 className="text-2xl font-bold text-gray-800">System Statistics</h2>
        <div>
          {stats.cached ? (
            <span className="inline-flex items-center px-3 py-1 rounded-full text-sm font-medium bg-green-100 text-green-800 border border-green-200">
              CACHE HIT
            </span>
          ) : (
            <span className="inline-flex items-center px-3 py-1 rounded-full text-sm font-medium bg-yellow-100 text-yellow-800 border border-yellow-200">
              CACHE MISS
            </span>
          )}
        </div>
      </div>

      <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-4 gap-6">
        <div className="bg-white rounded-lg shadow p-6 border-t-4 border-indigo-500">
          <h3 className="text-lg font-medium text-gray-500">Total Complaints</h3>
          <p className="mt-2 text-3xl font-bold text-gray-900">{stats.total}</p>
        </div>

        <div className="bg-white rounded-lg shadow p-6 border-t-4 border-blue-500">
          <h3 className="text-lg font-medium text-gray-500 mb-4">By Category</h3>
          <ul className="space-y-2">
            {Object.entries(stats.by_category).map(([cat, count]) => (
              <li key={cat} className="flex justify-between text-sm">
                <span className="capitalize text-gray-600">{cat}</span>
                <span className="font-semibold">{count}</span>
              </li>
            ))}
          </ul>
        </div>

        <div className="bg-white rounded-lg shadow p-6 border-t-4 border-red-500">
          <h3 className="text-lg font-medium text-gray-500 mb-4">By Priority</h3>
          <ul className="space-y-2">
            {Object.entries(stats.by_priority).map(([pri, count]) => (
              <li key={pri} className="flex justify-between text-sm">
                <span className="capitalize text-gray-600">{pri}</span>
                <span className="font-semibold">{count}</span>
              </li>
            ))}
          </ul>
        </div>

        <div className="bg-white rounded-lg shadow p-6 border-t-4 border-green-500">
          <h3 className="text-lg font-medium text-gray-500 mb-4">By Status</h3>
          <ul className="space-y-2">
            {Object.entries(stats.by_status).map(([stat, count]) => (
              <li key={stat} className="flex justify-between text-sm">
                <span className="capitalize text-gray-600">{stat.replace('_', ' ')}</span>
                <span className="font-semibold">{count}</span>
              </li>
            ))}
          </ul>
        </div>
      </div>
    </div>
  );
};
