import { render, screen, fireEvent, waitFor } from '@testing-library/react';
import { describe, it, expect, vi, beforeEach } from 'vitest';
import { ComplaintTable } from '../components/ComplaintTable';

// Mock the entire api/client module
vi.mock('../api/client', () => ({
  api: {
    complaints: {
      list: vi.fn(),
      updateStatus: vi.fn(),
    },
  },
}));

// Import after mocking so we get the mocked version
import { api } from '../api/client';

const mockListResponse = {
  items: [
    {
      id: 'aaaaaaaa-0001-0000-0000-000000000001',
      text: 'Water leak on main road flooding the entire street since morning',
      location: 'Block A, Sector F-6',
      reporter_contact: null,
      category: 'water' as const,
      priority: 'high' as const,
      status: 'open' as const,
      ai_summary: 'Water main leak flooding street',
      triaged_by: 'rules',
      triage_latency_ms: 120,
      created_at: new Date().toISOString(),
      updated_at: new Date().toISOString(),
    },
    {
      id: 'aaaaaaaa-0002-0000-0000-000000000002',
      text: 'No electricity since sehri time and WAPDA is not responding to calls',
      location: 'Block B, Gulberg III',
      reporter_contact: null,
      category: 'electricity' as const,
      priority: 'normal' as const,
      status: 'in_progress' as const,
      ai_summary: 'Power outage since early morning',
      triaged_by: 'rules',
      triage_latency_ms: 80,
      created_at: new Date().toISOString(),
      updated_at: new Date().toISOString(),
    },
  ],
  total: 2,
  page: 1,
  page_size: 10,
  total_pages: 1,
};

describe('ComplaintTable', () => {
  beforeEach(() => {
    vi.clearAllMocks();
    vi.mocked(api.complaints.list).mockResolvedValue(mockListResponse);
  });

  it('renders complaint rows after loading', async () => {
    render(<ComplaintTable />);

    await waitFor(() => {
      expect(screen.getByText('Block A, Sector F-6')).toBeInTheDocument();
    });

    expect(screen.getByText('Block B, Gulberg III')).toBeInTheDocument();
  });

  it('shows Start button for open status complaints', async () => {
    render(<ComplaintTable />);

    await waitFor(() => {
      const startButtons = screen.getAllByRole('button', { name: /start/i });
      expect(startButtons.length).toBeGreaterThan(0);
    });
  });

  it('shows Resolve button for in_progress complaints', async () => {
    render(<ComplaintTable />);

    await waitFor(() => {
      const resolveButtons = screen.getAllByRole('button', { name: /resolve/i });
      expect(resolveButtons.length).toBeGreaterThan(0);
    });
  });

  it('shows 409 error verbatim when status transition fails', async () => {
    const errorDetail = 'Transition from open to resolved is not allowed';
    vi.mocked(api.complaints.updateStatus).mockRejectedValue({ detail: errorDetail });

    render(<ComplaintTable />);

    await waitFor(() => {
      expect(screen.getByText('Block A, Sector F-6')).toBeInTheDocument();
    });

    const startButton = screen.getAllByRole('button', { name: /start/i })[0];
    fireEvent.click(startButton);

    await waitFor(() => {
      expect(screen.getByText(errorDetail)).toBeInTheDocument();
    });
  });

  it('re-fetches after a successful status update', async () => {
    vi.mocked(api.complaints.updateStatus).mockResolvedValue({} as any);

    render(<ComplaintTable />);

    await waitFor(() => {
      expect(screen.getByText('Block A, Sector F-6')).toBeInTheDocument();
    });

    const startButton = screen.getAllByRole('button', { name: /start/i })[0];
    fireEvent.click(startButton);

    await waitFor(() => {
      // list should have been called at least twice (initial + after update)
      expect(vi.mocked(api.complaints.list).mock.calls.length).toBeGreaterThanOrEqual(2);
    });
  });
});
