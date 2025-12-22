'use client';

import { useQuery, useMutation, useQueryClient } from '@tanstack/react-query';
import {
  requestsApi,
  RequestStatus,
  RequestFilters,
  CreateRequestData,
  UpdateRequestData,
  ProcurementRequest,
} from '@/lib/api';

export function useRequests(params?: RequestFilters) {
  return useQuery({
    queryKey: ['requests', params],
    queryFn: () => requestsApi.list(params),
  });
}

export function useRequest(id: string) {
  return useQuery({
    queryKey: ['request', id],
    queryFn: () => requestsApi.get(id),
    enabled: !!id,
  });
}

export function useRequestHistory(id: string) {
  return useQuery({
    queryKey: ['request-history', id],
    queryFn: () => requestsApi.getHistory(id),
    enabled: !!id,
  });
}

export function useCreateRequest() {
  const queryClient = useQueryClient();

  return useMutation({
    mutationFn: (data: CreateRequestData) => requestsApi.create(data),
    onSuccess: () => {
      queryClient.invalidateQueries({ queryKey: ['requests'] });
    },
  });
}

export function useUpdateRequest() {
  const queryClient = useQueryClient();

  return useMutation({
    mutationFn: ({ id, data }: { id: string; data: UpdateRequestData }) =>
      requestsApi.update(id, data),
    onSuccess: (data: ProcurementRequest) => {
      queryClient.invalidateQueries({ queryKey: ['requests'] });
      queryClient.invalidateQueries({ queryKey: ['request', data.id] });
    },
  });
}

export function useUpdateRequestStatus() {
  const queryClient = useQueryClient();

  return useMutation({
    mutationFn: ({
      id,
      status,
      notes,
    }: {
      id: string;
      status: RequestStatus;
      notes?: string;
    }) => requestsApi.updateStatus(id, status, notes),
    onSuccess: (data: ProcurementRequest) => {
      queryClient.invalidateQueries({ queryKey: ['requests'] });
      queryClient.invalidateQueries({ queryKey: ['request', data.id] });
      queryClient.invalidateQueries({ queryKey: ['request-history', data.id] });
    },
  });
}

export function useDeleteRequest() {
  const queryClient = useQueryClient();

  return useMutation({
    mutationFn: (id: string) => requestsApi.delete(id),
    onSuccess: () => {
      queryClient.invalidateQueries({ queryKey: ['requests'] });
    },
  });
}

// Analytics hooks (procurement team only)
export function useRequestAnalytics() {
  return useQuery({
    queryKey: ['request-analytics'],
    queryFn: () => requestsApi.getAnalytics(),
  });
}

export function useFilterOptions() {
  return useQuery({
    queryKey: ['filter-options'],
    queryFn: () => requestsApi.getFilterOptions(),
  });
}

export function useAddProcurementNote() {
  const queryClient = useQueryClient();

  return useMutation({
    mutationFn: ({ id, notes }: { id: string; notes: string }) =>
      requestsApi.addNote(id, notes),
    onSuccess: (_, { id }) => {
      queryClient.invalidateQueries({ queryKey: ['request-history', id] });
      queryClient.invalidateQueries({ queryKey: ['requests'] });
    },
  });
}
