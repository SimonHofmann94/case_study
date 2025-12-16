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

export interface OrderLine {
  id?: number;
  description: string;
  unit_price: number;
  amount: number;
  unit: string;
  total_price?: number;
}

export interface CommodityGroup {
  id: number;
  category: string;
  name: string;
  description: string | null;
}

export interface ProcurementRequest {
  id: number;
  user_id: number;
  title: string;
  vendor_name: string | null;
  vat_id: string | null;
  commodity_group_id: number | null;
  commodity_group?: CommodityGroup;
  department: string | null;
  total_cost: number;
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
  commodity_group_id?: number;
  department?: string;
  notes?: string;
  order_lines: Omit<OrderLine, 'id' | 'total_price'>[];
}

export interface UpdateRequestData {
  title?: string;
  vendor_name?: string;
  vat_id?: string;
  commodity_group_id?: number;
  department?: string;
  notes?: string;
  order_lines?: Omit<OrderLine, 'id' | 'total_price'>[];
}

export interface RequestListResponse {
  items: ProcurementRequest[];
  total: number;
  page: number;
  page_size: number;
}

// Request API functions
export const requestsApi = {
  list: async (params?: {
    page?: number;
    page_size?: number;
    status?: RequestStatus;
    department?: string;
  }): Promise<RequestListResponse> => {
    const response = await api.get<RequestListResponse>('/requests', { params });
    return response.data;
  },

  get: async (id: number): Promise<ProcurementRequest> => {
    const response = await api.get<ProcurementRequest>(`/requests/${id}`);
    return response.data;
  },

  create: async (data: CreateRequestData): Promise<ProcurementRequest> => {
    const response = await api.post<ProcurementRequest>('/requests', data);
    return response.data;
  },

  update: async (id: number, data: UpdateRequestData): Promise<ProcurementRequest> => {
    const response = await api.patch<ProcurementRequest>(`/requests/${id}`, data);
    return response.data;
  },

  updateStatus: async (id: number, status: RequestStatus, notes?: string): Promise<ProcurementRequest> => {
    const response = await api.put<ProcurementRequest>(`/requests/${id}/status`, { status, notes });
    return response.data;
  },

  delete: async (id: number): Promise<void> => {
    await api.delete(`/requests/${id}`);
  },

  getHistory: async (id: number): Promise<Array<{
    id: number;
    status: RequestStatus;
    changed_by_user_id: number;
    changed_at: string;
    notes: string | null;
  }>> => {
    const response = await api.get(`/requests/${id}/history`);
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

  get: async (id: number): Promise<CommodityGroup> => {
    const response = await api.get<CommodityGroup>(`/commodity-groups/${id}`);
    return response.data;
  },
};

// Offer parsing types
export interface ParsedOrderLine {
  description: string;
  unit_price: number;
  amount: number;
  unit: string;
}

export interface ParsedOffer {
  vendor_name: string | null;
  vat_id: string | null;
  order_lines: ParsedOrderLine[];
}

export interface OfferParseResponse {
  success: boolean;
  data: ParsedOffer | null;
  metadata: {
    format_used: string;
    fallback_used: boolean;
    token_savings_percent?: number;
  };
  error: string | null;
}

export interface CommoditySuggestion {
  commodity_group_id: number;
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
    orderLines: ParsedOrderLine[]
  ): Promise<CommoditySuggestion> => {
    const response = await api.post<CommoditySuggestion>('/offers/suggest-commodity', {
      title,
      order_lines: orderLines,
    });
    return response.data;
  },
};

export default api;
