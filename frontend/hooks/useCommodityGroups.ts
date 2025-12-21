'use client';

import { useQuery } from '@tanstack/react-query';
import { commodityGroupsApi } from '@/lib/api';

export function useCommodityGroups() {
  return useQuery({
    queryKey: ['commodity-groups'],
    queryFn: () => commodityGroupsApi.list(),
    staleTime: 5 * 60 * 1000, // 5 minutes - commodity groups rarely change
  });
}

export function useCommodityGroupCategories() {
  return useQuery({
    queryKey: ['commodity-group-categories'],
    queryFn: () => commodityGroupsApi.getCategories(),
    staleTime: 5 * 60 * 1000,
  });
}

export function useCommodityGroup(id: string) {
  return useQuery({
    queryKey: ['commodity-group', id],
    queryFn: () => commodityGroupsApi.get(id),
    enabled: !!id,
  });
}
