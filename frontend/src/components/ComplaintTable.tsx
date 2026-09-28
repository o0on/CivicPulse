import { type FC, useEffect, useState } from 'react';
import { api } from '../api/client';
import { Complaint, ComplaintStatus, Category, Priority } from '../types';

export const ComplaintTable: FC = () => {
  const [complaints, setComplaints] = useState<Complaint[]>([]);
  const [total, setTotal] = useState(0);
  const [page, setPage] = useState(1);
  const [totalPages, setTotalPages] = useState(1);
  const [loading, setLoading] = useState(true);
  
  const [statusFilter, setStatusFilter] = useState<ComplaintStatus | ''>('');
  const [categoryFilter, setCategoryFilter] = useState<Category | ''>('');
  const [priorityFilter, setPriorityFilter] = useState<Priority | ''>('');
  
  const [errorMsg, setErrorMsg] = useState<string | null>(null);
  
  const pageSize = 10;

  const fetchComplaints = async () => {
    setLoading(true);
    try {
      const res = await api.complaints.list({
        page,
        page_size: pageSize,
        ...(statusFilter ? { status: statusFilter } : {}),
        ...(categoryFilter ? { category: categoryFilter } : {}),
        ...(priorityFilter ? { priority: priorityFilter } : {}),
      });
      setComplaints(res.items);
      setTotal(res.total);
      setTotalPages(res.total_pages);
    } catch (error) {
      console.error('Failed to fetch complaints', error);
    } finally {
      setLoading(false);
    }
  };

  useEffect(() => {
    fetchComplaints();
  }, [page, statusFilter, categoryFilter, priorityFilter]);

  const handleStatusChange = async (id: string, newStatus: ComplaintStatus) => {
    try {
      await api.complaints.updateStatus(id, newStatus);
      fetchComplaints();
    } catch (err: unknown) {
      const detail = (err as { detail?: string })?.detail ?? 'Conflict or error updating status';
      setErrorMsg(detail);
      setTimeout(() => setErrorMsg(null), 5000);
    }
  };

  const getActions = (complaint: Complaint) => {
    if (complaint.status === 'open') {
      return (
        <div className="flex space-x-2">
          <button onClick={() => handleStatusChange(complaint.id, 'in_progress')} className="text-xs bg-blue-500 text-white px-2 py-1 rounded hover:bg-blue-600">Start</button>
          <button onClick={() => handleStatusChange(complaint.id, 'rejected')} className="text-xs bg-red-500 text-white px-2 py-1 rounded hover:bg-red-600">Reject</button>
        </div>
      );
    }
    if (complaint.status === 'in_progress') {
      return (
        <div className="flex space-x-2">
          <button onClick={() => handleStatusChange(complaint.id, 'resolved')} className="text-xs bg-green-500 text-white px-2 py-1 rounded hover:bg-green-600">Resolve</button>
          <button onClick={() => handleStatusChange(complaint.id, 'rejected')} className="text-xs bg-red-500 text-white px-2 py-1 rounded hover:bg-red-600">Reject</button>
        </div>
      );
    }
    return <span className="text-gray-400 text-xs">No actions</span>;
  };

  return (
    <div className="w-full max-w-6xl mx-auto mt-8 bg-white p-6 shadow rounded-lg">
      {errorMsg && (
        <div className="mb-4 p-3 bg-red-100 text-red-800 border border-red-300 rounded shadow">
          {errorMsg}
        </div>
      )}
      
      <div className="flex flex-col md:flex-row gap-4 mb-6">
        <select value={statusFilter} onChange={e => {setStatusFilter(e.target.value as ComplaintStatus | ''); setPage(1);}} className="border p-2 rounded">
          <option value="">All Statuses</option>
          <option value="open">Open</option>
          <option value="in_progress">In Progress</option>
          <option value="resolved">Resolved</option>
          <option value="rejected">Rejected</option>
        </select>
        
        <select value={categoryFilter} onChange={e => {setCategoryFilter(e.target.value as Category | ''); setPage(1);}} className="border p-2 rounded">
          <option value="">All Categories</option>
          <option value="water">Water</option>
          <option value="electricity">Electricity</option>
          <option value="sanitation">Sanitation</option>
          <option value="roads">Roads</option>
          <option value="streetlights">Streetlights</option>
          <option value="other">Other</option>
        </select>

        <select value={priorityFilter} onChange={e => {setPriorityFilter(e.target.value as Priority | ''); setPage(1);}} className="border p-2 rounded">
          <option value="">All Priorities</option>
          <option value="high">High</option>
          <option value="normal">Normal</option>
          <option value="low">Low</option>
        </select>
      </div>

      <div className="overflow-x-auto">
        <table className="min-w-full divide-y divide-gray-200">
          <thead className="bg-gray-50">
            <tr>
              <th className="px-6 py-3 text-left text-xs font-medium text-gray-500 uppercase tracking-wider">ID</th>
              <th className="px-6 py-3 text-left text-xs font-medium text-gray-500 uppercase tracking-wider">Location</th>
              <th className="px-6 py-3 text-left text-xs font-medium text-gray-500 uppercase tracking-wider">Category</th>
              <th className="px-6 py-3 text-left text-xs font-medium text-gray-500 uppercase tracking-wider">Priority</th>
              <th className="px-6 py-3 text-left text-xs font-medium text-gray-500 uppercase tracking-wider">Status</th>
              <th className="px-6 py-3 text-left text-xs font-medium text-gray-500 uppercase tracking-wider">Created At</th>
              <th className="px-6 py-3 text-left text-xs font-medium text-gray-500 uppercase tracking-wider">Actions</th>
            </tr>
          </thead>
          <tbody className="bg-white divide-y divide-gray-200">
            {loading ? (
              <tr><td colSpan={7} className="px-6 py-4 text-center">Loading...</td></tr>
            ) : complaints.length === 0 ? (
              <tr><td colSpan={7} className="px-6 py-4 text-center">No complaints found.</td></tr>
            ) : (
              complaints.map(c => (
                <tr key={c.id}>
                  <td className="px-6 py-4 whitespace-nowrap text-sm text-gray-500" title={c.id}>{c.id.substring(0, 8)}...</td>
                  <td className="px-6 py-4 whitespace-nowrap text-sm text-gray-900">{c.location}</td>
                  <td className="px-6 py-4 whitespace-nowrap text-sm text-gray-900 capitalize">{c.category}</td>
                  <td className="px-6 py-4 whitespace-nowrap text-sm text-gray-900 capitalize">{c.priority}</td>
                  <td className="px-6 py-4 whitespace-nowrap text-sm text-gray-900 capitalize">{c.status.replace('_', ' ')}</td>
                  <td className="px-6 py-4 whitespace-nowrap text-sm text-gray-500">{new Date(c.created_at).toLocaleDateString()}</td>
                  <td className="px-6 py-4 whitespace-nowrap text-sm font-medium">
                    {getActions(c)}
                  </td>
                </tr>
              ))
            )}
          </tbody>
        </table>
      </div>

      <div className="flex items-center justify-between border-t border-gray-200 bg-white px-4 py-3 sm:px-6 mt-4">
        <div className="hidden sm:flex sm:flex-1 sm:items-center sm:justify-between">
          <div>
            <p className="text-sm text-gray-700">
              Showing <span className="font-medium">{(page - 1) * pageSize + 1}</span> to <span className="font-medium">{Math.min(page * pageSize, total)}</span> of <span className="font-medium">{total}</span> results
            </p>
          </div>
          <div>
            <nav className="isolate inline-flex -space-x-px rounded-md shadow-sm" aria-label="Pagination">
              <button
                onClick={() => setPage(p => Math.max(1, p - 1))}
                disabled={page === 1}
                className="relative inline-flex items-center rounded-l-md px-2 py-2 text-gray-400 ring-1 ring-inset ring-gray-300 hover:bg-gray-50 focus:z-20 focus:outline-offset-0 disabled:opacity-50"
              >
                Previous
              </button>
              <button
                onClick={() => setPage(p => Math.min(totalPages, p + 1))}
                disabled={page >= totalPages}
                className="relative inline-flex items-center rounded-r-md px-2 py-2 text-gray-400 ring-1 ring-inset ring-gray-300 hover:bg-gray-50 focus:z-20 focus:outline-offset-0 disabled:opacity-50"
              >
                Next
              </button>
            </nav>
          </div>
        </div>
      </div>
    </div>
  );
};
