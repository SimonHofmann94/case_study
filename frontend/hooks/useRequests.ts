'use client';

import { useQuery, useMutation, useQueryClient } from '@tanstack/react-query';
import {
  requestsApi,
  RequestStatus,
  CreateRequestData,
  UpdateRequestData,
  ProcurementRequest,
} from '@/lib/api';

export function useRequests(params?: {
  page?: number;
  page_size?: number;
  status?: RequestStatus;
  department?: string;
}) {
  return useQuery({
    queryKey: ['requests', params],
    queryFn: () => requestsApi.list(params),
  });
}

export function useRequest(id: number) {
  return useQuery({
    queryKey: ['request', id],
    queryFn: () => requestsApi.get(id),
    enabled: !!id,
  });
}

export function useRequestHistory(id: number) {
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
    mutationFn: ({ id, data }: { id: number; data: UpdateRequestData }) =>
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
      id: number;
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
    mutationFn: (id: number) => requestsApi.delete(id),
    onSuccess: () => {
      queryClient.invalidateQueries({ queryKey: ['requests'] });
    },
  });
}
