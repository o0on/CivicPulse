import { Complaint, ComplaintCreate, ComplaintListResponse, ComplaintStatus, Category, Priority, StatsResponse, ApiError } from '../types';

const BASE = '/api';

async function request<T>(path: string, options?: RequestInit): Promise<T> {
  const response = await fetch(path, {
    ...options,
    headers: {
      'Content-Type': 'application/json',
      ...options?.headers,
    },
  });
  
  if (!response.ok) {
    const errorData = await response.json().catch(() => null);
    if (errorData && (errorData as ApiError).detail) {
      throw errorData;
    }
    throw { detail: `Request failed with status ${response.status}` } as ApiError;
  }
  
  return response.json();
}

export const api = {
  complaints: {
    create: (data: ComplaintCreate) => request<Complaint>(`${BASE}/complaints`, {
      method: 'POST',
      body: JSON.stringify(data),
    }),
    list: (params: { status?: ComplaintStatus, category?: Category, priority?: Priority, page?: number, page_size?: number }) => {
      const searchParams = new URLSearchParams();
      if (params.status) searchParams.append('status', params.status);
      if (params.category) searchParams.append('category', params.category);
      if (params.priority) searchParams.append('priority', params.priority);
      if (params.page) searchParams.append('page', params.page.toString());
      if (params.page_size) searchParams.append('page_size', params.page_size.toString());
      const qs = searchParams.toString();
      return request<ComplaintListResponse>(`${BASE}/complaints${qs ? '?' + qs : ''}`);
    },
    get: (id: string) => request<Complaint>(`${BASE}/complaints/${id}`),
    updateStatus: (id: string, status: ComplaintStatus) => request<Complaint>(`${BASE}/complaints/${id}/status`, {
      method: 'PATCH',
      body: JSON.stringify({ status }),
    }),
  },
  stats: {
    get: () => fetch(`${BASE}/stats`).then(async res => {
      const cached = res.headers.get('X-Cache') === 'HIT';
      if (!res.ok) {
        throw { detail: `Stats request failed with status ${res.status}` } as ApiError;
      }
      const data = await res.json() as Omit<StatsResponse, 'cached'>;
      return { ...data, cached } as StatsResponse;
    })
  }
};
