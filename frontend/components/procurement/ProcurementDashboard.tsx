'use client';

import { useState } from 'react';
import { useRequestAnalytics, useRequests, useFilterOptions } from '@/hooks/useRequests';
import { commodityGroupsApi, RequestFilters } from '@/lib/api';
import { useQuery } from '@tanstack/react-query';
import { AnalyticsCards } from './AnalyticsCards';
import { RequestFiltersPanel } from './RequestFiltersPanel';
import { RequestsTable } from './RequestsTable';

export function ProcurementDashboard() {
  const [filters, setFilters] = useState<RequestFilters>({
    page: 1,
    page_size: 10,
  });

  const { data: analytics, isLoading: analyticsLoading } = useRequestAnalytics();
  const { data: requestsData, isLoading: requestsLoading } = useRequests(filters);
  const { data: filterOptions, isLoading: filterOptionsLoading } = useFilterOptions();
  const { data: commodityGroups } = useQuery({
    queryKey: ['commodity-groups'],
    queryFn: () => commodityGroupsApi.list(),
  });

  const handlePageChange = (page: number) => {
    setFilters((prev) => ({ ...prev, page }));
  };

  return (
    <div className="space-y-6">
      {/* Analytics Cards */}
      <AnalyticsCards analytics={analytics} isLoading={analyticsLoading} />

      {/* Filters */}
      <RequestFiltersPanel
        filters={filters}
        onChange={setFilters}
        filterOptions={filterOptions}
        commodityGroups={commodityGroups}
        isLoading={filterOptionsLoading}
      />

      {/* Request Table */}
      <RequestsTable
        requests={requestsData?.items || []}
        total={requestsData?.total || 0}
        page={filters.page || 1}
        pageSize={filters.page_size || 10}
        onPageChange={handlePageChange}
        isLoading={requestsLoading}
      />
    </div>
  );
}
