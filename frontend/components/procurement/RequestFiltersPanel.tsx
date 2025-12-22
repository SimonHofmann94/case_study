'use client';

import { Card, CardContent } from '@/components/ui/card';
import { Button } from '@/components/ui/button';
import { Input } from '@/components/ui/input';
import { Label } from '@/components/ui/label';
import {
  Select,
  SelectContent,
  SelectItem,
  SelectTrigger,
  SelectValue,
} from '@/components/ui/select';
import { RequestFilters, FilterOptions, RequestStatus, CommodityGroup } from '@/lib/api';
import { X, Search } from 'lucide-react';

interface RequestFiltersPanelProps {
  filters: RequestFilters;
  onChange: (filters: RequestFilters) => void;
  filterOptions?: FilterOptions;
  commodityGroups?: CommodityGroup[];
  isLoading?: boolean;
}

export function RequestFiltersPanel({
  filters,
  onChange,
  filterOptions,
  commodityGroups,
  isLoading,
}: RequestFiltersPanelProps) {
  const updateFilter = (key: keyof RequestFilters, value: string | number | undefined) => {
    const newFilters = { ...filters };
    if (value === undefined || value === '' || value === 'all') {
      delete newFilters[key];
    } else {
      (newFilters as Record<string, unknown>)[key] = value;
    }
    // Reset to page 1 when filters change
    newFilters.page = 1;
    onChange(newFilters);
  };

  const clearFilters = () => {
    onChange({ page: 1, page_size: filters.page_size || 10 });
  };

  const hasActiveFilters = Object.keys(filters).some(
    (key) => !['page', 'page_size'].includes(key) && filters[key as keyof RequestFilters]
  );

  return (
    <Card>
      <CardContent className="pt-6">
        <div className="grid gap-4 md:grid-cols-2 lg:grid-cols-4">
          {/* Search */}
          <div className="space-y-2">
            <Label htmlFor="search">Search</Label>
            <div className="relative">
              <Search className="absolute left-2.5 top-2.5 h-4 w-4 text-muted-foreground" />
              <Input
                id="search"
                placeholder="Title or vendor..."
                className="pl-8"
                value={filters.search || ''}
                onChange={(e) => updateFilter('search', e.target.value)}
              />
            </div>
          </div>

          {/* Status */}
          <div className="space-y-2">
            <Label>Status</Label>
            <Select
              value={filters.status || 'all'}
              onValueChange={(value) => updateFilter('status', value as RequestStatus)}
            >
              <SelectTrigger>
                <SelectValue placeholder="All statuses" />
              </SelectTrigger>
              <SelectContent>
                <SelectItem value="all">All statuses</SelectItem>
                <SelectItem value="open">Open</SelectItem>
                <SelectItem value="in_progress">In Progress</SelectItem>
                <SelectItem value="closed">Closed</SelectItem>
              </SelectContent>
            </Select>
          </div>

          {/* Department */}
          <div className="space-y-2">
            <Label>Department</Label>
            <Select
              value={filters.department || 'all'}
              onValueChange={(value) => updateFilter('department', value)}
            >
              <SelectTrigger>
                <SelectValue placeholder="All departments" />
              </SelectTrigger>
              <SelectContent>
                <SelectItem value="all">All departments</SelectItem>
                {filterOptions?.departments.map((dept) => (
                  <SelectItem key={dept} value={dept}>
                    {dept}
                  </SelectItem>
                ))}
              </SelectContent>
            </Select>
          </div>

          {/* Vendor */}
          <div className="space-y-2">
            <Label>Vendor</Label>
            <Select
              value={filters.vendor || 'all'}
              onValueChange={(value) => updateFilter('vendor', value)}
            >
              <SelectTrigger>
                <SelectValue placeholder="All vendors" />
              </SelectTrigger>
              <SelectContent>
                <SelectItem value="all">All vendors</SelectItem>
                {filterOptions?.vendors.map((vendor) => (
                  <SelectItem key={vendor} value={vendor}>
                    {vendor}
                  </SelectItem>
                ))}
              </SelectContent>
            </Select>
          </div>

          {/* Commodity Group */}
          <div className="space-y-2">
            <Label>Commodity Group</Label>
            <Select
              value={filters.commodity_group_id || 'all'}
              onValueChange={(value) => updateFilter('commodity_group_id', value)}
            >
              <SelectTrigger>
                <SelectValue placeholder="All groups" />
              </SelectTrigger>
              <SelectContent>
                <SelectItem value="all">All groups</SelectItem>
                {commodityGroups?.map((group) => (
                  <SelectItem key={group.id} value={group.id}>
                    {group.name}
                  </SelectItem>
                ))}
              </SelectContent>
            </Select>
          </div>

          {/* Requestor */}
          <div className="space-y-2">
            <Label>Requestor</Label>
            <Select
              value={filters.requestor_id || 'all'}
              onValueChange={(value) => updateFilter('requestor_id', value)}
            >
              <SelectTrigger>
                <SelectValue placeholder="All requestors" />
              </SelectTrigger>
              <SelectContent>
                <SelectItem value="all">All requestors</SelectItem>
                {filterOptions?.requestors.map((requestor) => (
                  <SelectItem key={requestor.id} value={requestor.id}>
                    {requestor.full_name}
                  </SelectItem>
                ))}
              </SelectContent>
            </Select>
          </div>

          {/* Date From */}
          <div className="space-y-2">
            <Label htmlFor="date_from">From Date</Label>
            <Input
              id="date_from"
              type="date"
              value={filters.date_from || ''}
              onChange={(e) => updateFilter('date_from', e.target.value)}
            />
          </div>

          {/* Date To */}
          <div className="space-y-2">
            <Label htmlFor="date_to">To Date</Label>
            <Input
              id="date_to"
              type="date"
              value={filters.date_to || ''}
              onChange={(e) => updateFilter('date_to', e.target.value)}
            />
          </div>

          {/* Min Cost */}
          <div className="space-y-2">
            <Label htmlFor="min_cost">Min Cost</Label>
            <Input
              id="min_cost"
              type="number"
              min="0"
              step="0.01"
              placeholder="0.00"
              value={filters.min_cost || ''}
              onChange={(e) =>
                updateFilter('min_cost', e.target.value ? parseFloat(e.target.value) : undefined)
              }
            />
          </div>

          {/* Max Cost */}
          <div className="space-y-2">
            <Label htmlFor="max_cost">Max Cost</Label>
            <Input
              id="max_cost"
              type="number"
              min="0"
              step="0.01"
              placeholder="No limit"
              value={filters.max_cost || ''}
              onChange={(e) =>
                updateFilter('max_cost', e.target.value ? parseFloat(e.target.value) : undefined)
              }
            />
          </div>

          {/* Clear Filters Button */}
          <div className="space-y-2 flex items-end lg:col-span-2">
            {hasActiveFilters && (
              <Button
                variant="outline"
                onClick={clearFilters}
                className="w-full md:w-auto"
              >
                <X className="mr-2 h-4 w-4" />
                Clear Filters
              </Button>
            )}
          </div>
        </div>
      </CardContent>
    </Card>
  );
}
