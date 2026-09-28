import React from 'react';
import { BrowserRouter, Routes, Route, NavLink } from 'react-router-dom';
import { SubmitPage } from './pages/SubmitPage';
import { DashboardPage } from './pages/DashboardPage';
import { StatsPage } from './pages/StatsPage';
import ErrorBoundary from './components/ErrorBoundary';

const App: React.FC = () => {
  return (
    <ErrorBoundary>
      <BrowserRouter>
        <div className="min-h-screen bg-gray-100 font-sans text-gray-900">
          <nav className="bg-indigo-600 text-white shadow-md">
            <div className="max-w-7xl mx-auto px-4 sm:px-6 lg:px-8">
              <div className="flex justify-between h-16">
                <div className="flex">
                  <div className="flex-shrink-0 flex items-center font-bold text-xl">
                    CivicPulse
                  </div>
                  <div className="ml-6 flex space-x-4">
                    <NavLink to="/" className={({isActive}) => `inline-flex items-center px-3 py-2 rounded-md text-sm font-medium ${isActive ? 'bg-indigo-700 text-white' : 'text-indigo-100 hover:bg-indigo-500'}`}>Submit</NavLink>
                    <NavLink to="/dashboard" className={({isActive}) => `inline-flex items-center px-3 py-2 rounded-md text-sm font-medium ${isActive ? 'bg-indigo-700 text-white' : 'text-indigo-100 hover:bg-indigo-500'}`}>Dashboard</NavLink>
                    <NavLink to="/stats" className={({isActive}) => `inline-flex items-center px-3 py-2 rounded-md text-sm font-medium ${isActive ? 'bg-indigo-700 text-white' : 'text-indigo-100 hover:bg-indigo-500'}`}>Stats</NavLink>
                  </div>
                </div>
              </div>
            </div>
          </nav>
          
          <main>
            <Routes>
              <Route path="/" element={<SubmitPage />} />
              <Route path="/dashboard" element={<DashboardPage />} />
              <Route path="/stats" element={<StatsPage />} />
            </Routes>
          </main>
        </div>
      </BrowserRouter>
    </ErrorBoundary>
  );
};

export default App;
