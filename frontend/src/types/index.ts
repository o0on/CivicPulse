export type Category = 'water' | 'electricity' | 'sanitation' | 'roads' | 'streetlights' | 'other';
export type Priority = 'high' | 'normal' | 'low';
export type ComplaintStatus = 'open' | 'in_progress' | 'resolved' | 'rejected';

export interface Complaint {
  id: string;
  text: string;
  location: string;
  reporter_contact: string | null;
  category: Category;
  priority: Priority;
  status: ComplaintStatus;
  ai_summary: string | null;
  triaged_by: string | null;
  triage_latency_ms: number;
  created_at: string;
  updated_at: string;
}

export interface ComplaintListResponse {
  items: Complaint[];
  total: number;
  page: number;
  page_size: number;
  total_pages: number;
}

export interface ComplaintCreate {
  text: string;
  location: string;
  reporter_contact?: string;
}

export interface StatsResponse {
  by_category: Record<Category, number>;
  by_priority: Record<Priority, number>;
  by_status: Record<ComplaintStatus, number>;
  total: number;
  cached: boolean;
  cache_ttl: number;
}

export interface ApiError {
  detail: string;
  error_code?: string;
}

export interface TriageDisplay {
  category: Category;
  priority: Priority;
  ai_summary: string | null;
  triaged_by: string | null;
  triage_latency_ms: number;
  confidence?: number;
}
