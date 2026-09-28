import { render, screen, fireEvent, waitFor } from '@testing-library/react';
import { describe, it, expect, vi, beforeEach } from 'vitest';
import { SubmitForm } from '../components/SubmitForm';

// Mock the API client
const mockCreate = vi.fn();
vi.mock('../api/client', () => ({
  default: {
    complaints: {
      create: (...args: any[]) => mockCreate(...args)
    }
  }
}));

describe('SubmitForm', () => {
  beforeEach(() => {
    vi.clearAllMocks();
  });

  it('renders form fields correctly', () => {
    render(<SubmitForm />);
    expect(screen.getByLabelText(/text/i)).toBeInTheDocument();
    expect(screen.getByLabelText(/location/i)).toBeInTheDocument();
    expect(screen.getByLabelText(/contact/i)).toBeInTheDocument();
  });

  it('shows validation error when text too short', async () => {
    render(<SubmitForm />);
    const textInput = screen.getByLabelText(/text/i);
    fireEvent.change(textInput, { target: { value: 'short' } });
    fireEvent.blur(textInput);
    
    const submitBtn = screen.getByRole('button', { name: /submit/i });
    fireEvent.click(submitBtn);

    await waitFor(() => {
      expect(screen.getByText(/at least 10 characters/i)).toBeInTheDocument();
    });
  });

  it('shows validation error when location too short', async () => {
    render(<SubmitForm />);
    const locationInput = screen.getByLabelText(/location/i);
    fireEvent.change(locationInput, { target: { value: 'A' } });
    fireEvent.blur(locationInput);
    
    const submitBtn = screen.getByRole('button', { name: /submit/i });
    fireEvent.click(submitBtn);

    await waitFor(() => {
      expect(screen.getByText(/at least 3 characters/i)).toBeInTheDocument();
    });
  });

  it('submit button disabled during loading', async () => {
    mockCreate.mockImplementation(() => new Promise(resolve => setTimeout(resolve, 100)));
    render(<SubmitForm />);
    
    fireEvent.change(screen.getByLabelText(/text/i), { target: { value: 'This is a sufficiently long description.' } });
    fireEvent.change(screen.getByLabelText(/location/i), { target: { value: 'Main Street' } });
    
    const submitBtn = screen.getByRole('button', { name: /submit/i });
    fireEvent.click(submitBtn);

    expect(submitBtn).toBeDisabled();
    
    await waitFor(() => {
      expect(submitBtn).not.toBeDisabled();
    });
  });

  it('calls api on valid submit', async () => {
    mockCreate.mockResolvedValue({ id: '123', category: 'water', priority: 'high' });
    render(<SubmitForm />);
    
    fireEvent.change(screen.getByLabelText(/text/i), { target: { value: 'This is a sufficiently long description.' } });
    fireEvent.change(screen.getByLabelText(/location/i), { target: { value: 'Main Street' } });
    
    fireEvent.click(screen.getByRole('button', { name: /submit/i }));

    await waitFor(() => {
      expect(mockCreate).toHaveBeenCalledWith({
        text: 'This is a sufficiently long description.',
        location: 'Main Street',
        reporter_contact: ''
      });
    });
  });

  it('shows success state after submit', async () => {
    mockCreate.mockResolvedValue({ 
      id: '123', 
      category: 'water', 
      priority: 'high',
      ai_summary: 'Water issue'
    });
    
    render(<SubmitForm />);
    
    fireEvent.change(screen.getByLabelText(/text/i), { target: { value: 'This is a sufficiently long description.' } });
    fireEvent.change(screen.getByLabelText(/location/i), { target: { value: 'Main Street' } });
    
    fireEvent.click(screen.getByRole('button', { name: /submit/i }));

    await waitFor(() => {
      expect(screen.getByText(/successfully/i)).toBeInTheDocument();
      expect(screen.getByText(/water/i)).toBeInTheDocument();
    });
  });

  it('shows error message on api failure', async () => {
    mockCreate.mockRejectedValue({ response: { data: { detail: 'Rate limit exceeded' } } });
    
    render(<SubmitForm />);
    
    fireEvent.change(screen.getByLabelText(/text/i), { target: { value: 'This is a sufficiently long description.' } });
    fireEvent.change(screen.getByLabelText(/location/i), { target: { value: 'Main Street' } });
    
    fireEvent.click(screen.getByRole('button', { name: /submit/i }));

    await waitFor(() => {
      expect(screen.getByText(/Rate limit exceeded/i)).toBeInTheDocument();
    });
  });
});
