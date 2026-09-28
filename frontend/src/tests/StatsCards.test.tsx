import { render, screen, waitFor } from '@testing-library/react';
import { describe, it, expect, vi, beforeEach } from 'vitest';
import { StatsCards } from '../components/StatsCards';

describe('StatsCards', () => {
  beforeEach(() => {
    vi.clearAllMocks();
  });

  it('renders loading state initially', () => {
    // Mock fetch to delay so we can see loading state
    globalThis.fetch = vi.fn().mockImplementation(() => new Promise(resolve => setTimeout(resolve, 100)));
    
    render(<StatsCards />);
    expect(screen.getByTestId('loading-skeleton')).toBeInTheDocument();
  });

  it('renders stats after loading', async () => {
    globalThis.fetch = vi.fn().mockResolvedValue({
      ok: true,
      headers: new Headers({ 'X-Cache': 'MISS' }),
      json: () => Promise.resolve({
        total_complaints: 150,
        by_category: { water: 50 },
        by_priority: { high: 20 },
        by_status: { open: 10 }
      })
    });

    render(<StatsCards />);
    
    await waitFor(() => {
      expect(screen.queryByTestId('loading-skeleton')).not.toBeInTheDocument();
    });
    
    expect(screen.getByText('150')).toBeInTheDocument();
    expect(screen.getByText(/water/i)).toBeInTheDocument();
    expect(screen.getByText(/open/i)).toBeInTheDocument();
  });

  it('shows cache hit badge', async () => {
    globalThis.fetch = vi.fn().mockResolvedValue({
      ok: true,
      headers: new Headers({ 'X-Cache': 'HIT' }),
      json: () => Promise.resolve({
        total_complaints: 100,
        by_category: {},
        by_priority: {},
        by_status: {}
      })
    });

    render(<StatsCards />);
    
    await waitFor(() => {
      expect(screen.getByText(/hit/i)).toBeInTheDocument();
      // Test for visual cues like a green badge using specific classes if known, else check text
    });
  });

  it('shows cache miss badge', async () => {
    globalThis.fetch = vi.fn().mockResolvedValue({
      ok: true,
      headers: new Headers({ 'X-Cache': 'MISS' }),
      json: () => Promise.resolve({
        total_complaints: 100,
        by_category: {},
        by_priority: {},
        by_status: {}
      })
    });

    render(<StatsCards />);
    
    await waitFor(() => {
      expect(screen.getByText(/miss/i)).toBeInTheDocument();
    });
  });
});
