import axios, { AxiosError, InternalAxiosRequestConfig } from 'axios';

const API_URL = process.env.NEXT_PUBLIC_API_URL || 'http://localhost:8000';

export const api = axios.create({
  baseURL: API_URL,
  headers: {
    'Content-Type': 'application/json',
  },
});

// Add JWT token to requests
api.interceptors.request.use(
  (config: InternalAxiosRequestConfig) => {
    const token = typeof window !== 'undefined' ? localStorage.getItem('token') : null;
    if (token && config.headers) {
      config.headers.Authorization = `Bearer ${token}`;
    }
    return config;
  },
  (error) => Promise.reject(error)
);

// Handle 401 responses
api.interceptors.response.use(
  (response) => response,
  (error: AxiosError) => {
    if (error.response?.status === 401) {
      if (typeof window !== 'undefined') {
        localStorage.removeItem('token');
        localStorage.removeItem('user');
        window.location.href = '/auth/login';
      }
    }
    return Promise.reject(error);
  }
);

// Auth types
export interface User {
  id: number;
  email: string;
  full_name: string;
  role: 'requestor' | 'procurement_team';
  department: string | null;
  is_active: boolean;
  created_at: string;
}

export interface LoginRequest {
  email: string;
  password: string;
}

export interface RegisterRequest {
  email: string;
  password: string;
  full_name: string;
  role?: 'requestor' | 'procurement_team';
  department?: string;
}

export interface LoginResponse {
  access_token: string;
  token_type: string;
  user: User;
}

export interface ApiError {
  detail: string;
}

// Auth API functions
export const authApi = {
  login: async (data: LoginRequest): Promise<LoginResponse> => {
    const response = await api.post<LoginResponse>('/auth/login', data);
    return response.data;
  },

  register: async (data: RegisterRequest): Promise<User> => {
    const response = await api.post<User>('/auth/register', data);
    return response.data;
  },

  me: async (): Promise<User> => {
    const response = await api.get<User>('/auth/me');
    return response.data;
  },
};

// Request types
export type RequestStatus = 'open' | 'in_progress' | 'closed';
export type LineType = 'standard' | 'alternative' | 'optional';

export interface OrderLine {
  id?: string;
  line_type: LineType;
  description: string;
  detailed_description?: string;
  unit_price: number;
  amount: number;
  unit: string;
  discount_percent?: number;
  discount_amount?: number;
  total_price?: number;
}

export interface CommodityGroup {
  id: string;
  category: string;
  name: string;
  description: string | null;
}

export interface ProcurementRequest {
  id: string;
  user_id: string;
  title: string;
  vendor_name: string | null;
  vat_id: string | null;
  commodity_group_id: string | null;
  commodity_group?: CommodityGroup;
  department: string | null;
  currency: string;
  total_cost: number;
  subtotal_net?: number;
  discount_total?: number;
  delivery_cost_net?: number;
  delivery_tax_amount?: number;
  tax_rate?: number;
  tax_amount?: number;
  status: RequestStatus;
  notes: string | null;
  order_lines: OrderLine[];
  created_at: string;
  updated_at: string;
}

export interface CreateRequestData {
  title: string;
  vendor_name?: string;
  vat_id?: string;
  commodity_group_id?: string;
  department?: string;
  currency?: string;
  subtotal_net?: number;
  discount_total?: number;
  delivery_cost_net?: number;
  delivery_tax_amount?: number;
  tax_rate?: number;
  tax_amount?: number;
  notes?: string;
  order_lines: Omit<OrderLine, 'id' | 'total_price'>[];
}

export interface UpdateRequestData {
  title?: string;
  vendor_name?: string;
  vat_id?: string;
  commodity_group_id?: string;
  department?: string;
  currency?: string;
  subtotal_net?: number;
  discount_total?: number;
  delivery_cost_net?: number;
  delivery_tax_amount?: number;
  tax_rate?: number;
  tax_amount?: number;
  notes?: string;
  order_lines?: Omit<OrderLine, 'id' | 'total_price'>[];
}

export interface RequestListResponse {
  items: ProcurementRequest[];
  total: number;
  page: number;
  page_size: number;
}

// Analytics types
export interface RequestAnalytics {
  open_count: number;
  in_progress_count: number;
  closed_count: number;
  total_open_value: number;
  total_in_progress_value: number;
  total_closed_value: number;
}

export interface RequestorInfo {
  id: string;
  full_name: string;
  email: string;
}

export interface FilterOptions {
  departments: string[];
  vendors: string[];
  requestors: RequestorInfo[];
}

export interface RequestFilters {
  page?: number;
  page_size?: number;
  status?: RequestStatus;
  department?: string;
  search?: string;
  date_from?: string;
  date_to?: string;
  vendor?: string;
  commodity_group_id?: string;
  min_cost?: number;
  max_cost?: number;
  requestor_id?: string;
}

export interface StatusHistoryEntry {
  id: string;
  request_id: string;
  status: RequestStatus;
  changed_by_user_id: string | null;
  changed_at: string;
  notes: string | null;
  changed_by_name: string | null;
}

// Request API functions
export const requestsApi = {
  list: async (params?: RequestFilters): Promise<RequestListResponse> => {
    const response = await api.get<RequestListResponse>('/requests', { params });
    return response.data;
  },

  get: async (id: string): Promise<ProcurementRequest> => {
    const response = await api.get<ProcurementRequest>(`/requests/${id}`);
    return response.data;
  },

  create: async (data: CreateRequestData): Promise<ProcurementRequest> => {
    const response = await api.post<ProcurementRequest>('/requests', data);
    return response.data;
  },

  update: async (id: string, data: UpdateRequestData): Promise<ProcurementRequest> => {
    const response = await api.patch<ProcurementRequest>(`/requests/${id}`, data);
    return response.data;
  },

  updateStatus: async (id: string, status: RequestStatus, notes?: string): Promise<ProcurementRequest> => {
    const response = await api.put<ProcurementRequest>(`/requests/${id}/status`, { status, notes });
    return response.data;
  },

  delete: async (id: string): Promise<void> => {
    await api.delete(`/requests/${id}`);
  },

  getHistory: async (id: string): Promise<StatusHistoryEntry[]> => {
    const response = await api.get<StatusHistoryEntry[]>(`/requests/${id}/history`);
    return response.data;
  },

  // Analytics endpoints (procurement team only)
  getAnalytics: async (): Promise<RequestAnalytics> => {
    const response = await api.get<RequestAnalytics>('/requests/analytics');
    return response.data;
  },

  getFilterOptions: async (): Promise<FilterOptions> => {
    const response = await api.get<FilterOptions>('/requests/filter-options');
    return response.data;
  },

  addNote: async (id: string, notes: string): Promise<StatusHistoryEntry> => {
    const response = await api.post<StatusHistoryEntry>(`/requests/${id}/notes`, { notes });
    return response.data;
  },
};

// Commodity group API functions
export const commodityGroupsApi = {
  list: async (): Promise<CommodityGroup[]> => {
    const response = await api.get<CommodityGroup[]>('/commodity-groups');
    return response.data;
  },

  getCategories: async (): Promise<string[]> => {
    const response = await api.get<string[]>('/commodity-groups/categories');
    return response.data;
  },

  get: async (id: string): Promise<CommodityGroup> => {
    const response = await api.get<CommodityGroup>(`/commodity-groups/${id}`);
    return response.data;
  },
};

// Offer parsing types
export interface ParsedOrderLine {
  line_type: LineType;
  description: string;
  detailed_description?: string;
  unit_price: number;  // Backend returns this (alias)
  amount: number;
  unit: string;
  discount_percent?: number;
  discount_amount?: number;
  total_price?: number;  // Backend returns this (alias)
}

export interface ParsedOffer {
  vendor_name: string | null;
  vat_id: string | null;
  currency: string;
  order_lines: ParsedOrderLine[];
  subtotal_net?: number;
  discount_total?: number;
  delivery_cost_net?: number;
  delivery_tax_amount?: number;
  tax_rate?: number;
  tax_amount?: number;
  total_gross?: number;
}

export interface OfferParseResponse {
  vendor_name: string;
  vat_id: string | null;
  currency: string;
  order_lines: ParsedOrderLine[];
  subtotal_net?: number;
  discount_total?: number;
  delivery_cost_net?: number;
  delivery_tax_amount?: number;
  tax_rate?: number;
  tax_amount?: number;
  total_gross?: number;
  token_savings: {
    json_chars: number;
    toon_chars: number;
    savings_percent: number;
  } | null;
  format_used: string;
}

export interface CommoditySuggestion {
  commodity_group_id: string;
  category: string;
  name: string;
  confidence: number;
  explanation: string;
}

// Offer API functions
export const offersApi = {
  parse: async (file: File): Promise<OfferParseResponse> => {
    const formData = new FormData();
    formData.append('file', file);
    const response = await api.post<OfferParseResponse>('/offers/parse', formData, {
      headers: { 'Content-Type': 'multipart/form-data' },
    });
    return response.data;
  },

  parseText: async (text: string): Promise<OfferParseResponse> => {
    const response = await api.post<OfferParseResponse>('/offers/parse', { text });
    return response.data;
  },

  suggestCommodity: async (
    title: string,
    orderLines: Array<{ description: string; unit_price?: number; amount?: number }>,
    vendorName?: string
  ): Promise<CommoditySuggestion> => {
    const response = await api.post<CommoditySuggestion>('/offers/suggest-commodity', {
      title,
      order_lines: orderLines,
      vendor_name: vendorName,
    });
    return response.data;
  },
};

export default api;
