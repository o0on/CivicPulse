import React, { useState } from 'react';
import { api } from '../api/client';
import { Complaint } from '../types';

export const SubmitForm: React.FC = () => {
  const [text, setText] = useState('');
  const [location, setLocation] = useState('');
  const [contact, setContact] = useState('');
  
  const [loading, setLoading] = useState(false);
  const [error, setError] = useState<string | null>(null);
  const [result, setResult] = useState<Complaint | null>(null);

  const [validationErrors, setValidationErrors] = useState<{ text?: string, location?: string }>({});

  const validate = () => {
    const errs: { text?: string, location?: string } = {};
    if (text.length < 10 || text.length > 2000) errs.text = 'Text must be at least 10 characters (max 2000).';
    if (location.length < 3 || location.length > 200) errs.location = 'Location must be at least 3 characters (max 200).';
    setValidationErrors(errs);
    return Object.keys(errs).length === 0;
  };

  const handleSubmit = async (e: React.FormEvent) => {
    e.preventDefault();
    if (!validate()) return;
    
    setLoading(true);
    setError(null);
    try {
      const res = await api.complaints.create({
        text,
        location,
        reporter_contact: contact || '',
      });
      setResult(res);
    } catch (err: any) {
      const msg = err?.response?.data?.detail || err?.detail || (typeof err === 'string' ? err : err?.message) || 'An unknown error occurred';
      setError(msg);
    } finally {
      setLoading(false);
    }
  };

  const handleReset = () => {
    setResult(null);
    setText('');
    setLocation('');
    setContact('');
    setError(null);
    setValidationErrors({});
  };

  if (result) {
    return (
      <div className="max-w-xl mx-auto p-6 bg-white shadow rounded-lg mt-8">
        <h2 className="text-2xl font-bold mb-4 text-green-600">Complaint Submitted Successfully</h2>
        <div className="bg-gray-50 p-4 rounded-md border border-gray-200 space-y-3">
          <div>
            <span className="font-semibold text-gray-600">Category:</span>
            <span className="ml-2 inline-flex items-center px-2.5 py-0.5 rounded-full text-xs font-medium bg-blue-100 text-blue-800">
              {result.category}
            </span>
          </div>
          <div>
            <span className="font-semibold text-gray-600">Priority:</span>
            <span className={`ml-2 inline-flex items-center px-2.5 py-0.5 rounded-full text-xs font-medium ${
              result.priority === 'high' ? 'bg-red-100 text-red-800' :
              result.priority === 'normal' ? 'bg-yellow-100 text-yellow-800' : 'bg-green-100 text-green-800'
            }`}>
              {result.priority}
            </span>
          </div>
          {result.ai_summary && (
            <div>
              <span className="font-semibold text-gray-600 block mb-1">AI Summary:</span>
              <p className="text-sm text-gray-800 bg-white p-2 border rounded">{result.ai_summary}</p>
            </div>
          )}
          <div className="text-sm text-gray-500">
            Triaged by: {result.triaged_by || 'Unknown'} | Latency: {result.triage_latency_ms}ms
          </div>
        </div>
        <button
          onClick={handleReset}
          className="mt-6 w-full bg-indigo-600 text-white py-2 px-4 border border-transparent rounded-md shadow-sm text-sm font-medium hover:bg-indigo-700"
        >
          Submit Another
        </button>
      </div>
    );
  }

  return (
    <div className="max-w-xl mx-auto p-6 bg-white shadow rounded-lg mt-8">
      <h2 className="text-2xl font-bold mb-6 text-gray-900">Submit a Complaint</h2>
      {error && (
        <div className="mb-4 p-3 bg-red-50 text-red-700 rounded border border-red-200">
          {error}
        </div>
      )}
      <form onSubmit={handleSubmit} className="space-y-4">
        <div>
          <label htmlFor="text" className="block text-sm font-medium text-gray-700">Complaint Text</label>
          <textarea
            id="text"
            rows={4}
            className="mt-1 block w-full rounded-md border-gray-300 shadow-sm focus:border-indigo-500 focus:ring-indigo-500 sm:text-sm border p-2"
            value={text}
            onChange={e => setText(e.target.value)}
          />
          {validationErrors.text && <p className="mt-1 text-sm text-red-600">{validationErrors.text}</p>}
        </div>
        <div>
          <label htmlFor="location" className="block text-sm font-medium text-gray-700">Location</label>
          <input
            type="text"
            id="location"
            className="mt-1 block w-full rounded-md border-gray-300 shadow-sm focus:border-indigo-500 focus:ring-indigo-500 sm:text-sm border p-2"
            value={location}
            onChange={e => setLocation(e.target.value)}
          />
          {validationErrors.location && <p className="mt-1 text-sm text-red-600">{validationErrors.location}</p>}
        </div>
        <div>
          <label htmlFor="contact" className="block text-sm font-medium text-gray-700">Contact Email (Optional)</label>
          <input
            type="email"
            id="contact"
            className="mt-1 block w-full rounded-md border-gray-300 shadow-sm focus:border-indigo-500 focus:ring-indigo-500 sm:text-sm border p-2"
            value={contact}
            onChange={e => setContact(e.target.value)}
          />
        </div>
        <button
          type="submit"
          disabled={loading}
          className="w-full flex justify-center py-2 px-4 border border-transparent rounded-md shadow-sm text-sm font-medium text-white bg-indigo-600 hover:bg-indigo-700 focus:outline-none focus:ring-2 focus:ring-offset-2 focus:ring-indigo-500 disabled:opacity-50"
        >
          {loading ? 'Submitting...' : 'Submit'}
        </button>
      </form>
    </div>
  );
};
