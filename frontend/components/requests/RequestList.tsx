'use client';

import Link from 'next/link';
import { FileText, Plus, Loader2 } from 'lucide-react';

import { Button } from '@/components/ui/button';
import { Card, CardContent, CardDescription, CardHeader, CardTitle } from '@/components/ui/card';
import {
  Select,
  SelectContent,
  SelectItem,
  SelectTrigger,
  SelectValue,
} from '@/components/ui/select';
import { StatusBadge } from './StatusBadge';
import { useRequests } from '@/hooks/useRequests';
import { RequestStatus, ProcurementRequest } from '@/lib/api';

interface RequestListProps {
  statusFilter?: RequestStatus;
  onStatusFilterChange?: (status: RequestStatus | undefined) => void;
}

export function RequestList({ statusFilter, onStatusFilterChange }: RequestListProps) {
  const { data, isLoading, error } = useRequests({
    status: statusFilter,
    page_size: 50,
  });

  if (isLoading) {
    return (
      <div className="flex items-center justify-center py-12">
        <Loader2 className="h-8 w-8 animate-spin text-primary" />
      </div>
    );
  }

  if (error) {
    return (
      <Card>
        <CardContent className="py-12 text-center">
          <p className="text-destructive">
            Failed to load requests. Please try again.
          </p>
        </CardContent>
      </Card>
    );
  }

  const requests = data?.items || [];

  return (
    <div className="space-y-6">
      <div className="flex items-center justify-between">
        <div className="flex items-center gap-4">
          <Select
            value={statusFilter || 'all'}
            onValueChange={(value) =>
              onStatusFilterChange?.(value === 'all' ? undefined : (value as RequestStatus))
            }
          >
            <SelectTrigger className="w-[180px]">
              <SelectValue placeholder="Filter by status" />
            </SelectTrigger>
            <SelectContent>
              <SelectItem value="all">All Statuses</SelectItem>
              <SelectItem value="open">Open</SelectItem>
              <SelectItem value="in_progress">In Progress</SelectItem>
              <SelectItem value="closed">Closed</SelectItem>
            </SelectContent>
          </Select>
          <span className="text-sm text-muted-foreground">
            {data?.total || 0} requests
          </span>
        </div>

        <Link href="/requests/new">
          <Button>
            <Plus className="h-4 w-4 mr-2" />
            New Request
          </Button>
        </Link>
      </div>

      {requests.length === 0 ? (
        <Card>
          <CardContent className="py-12 text-center">
            <FileText className="h-12 w-12 mx-auto text-muted-foreground mb-4" />
            <h3 className="text-lg font-medium mb-2">No requests found</h3>
            <p className="text-muted-foreground mb-4">
              {statusFilter
                ? `No requests with status "${statusFilter}"`
                : 'Get started by creating your first request'}
            </p>
            <Link href="/requests/new">
              <Button>
                <Plus className="h-4 w-4 mr-2" />
                Create Request
              </Button>
            </Link>
          </CardContent>
        </Card>
      ) : (
        <div className="space-y-4">
          {requests.map((request: ProcurementRequest) => (
            <RequestCard key={request.id} request={request} />
          ))}
        </div>
      )}
    </div>
  );
}

function RequestCard({ request }: { request: ProcurementRequest }) {
  return (
    <Link href={`/requests/${request.id}`}>
      <Card className="hover:border-primary/50 transition-colors cursor-pointer">
        <CardHeader className="pb-3">
          <div className="flex items-start justify-between">
            <div>
              <CardTitle className="text-lg">{request.title}</CardTitle>
              <CardDescription>
                {request.vendor_name || 'No vendor'} • {request.department || 'No department'}
              </CardDescription>
            </div>
            <StatusBadge status={request.status} />
          </div>
        </CardHeader>
        <CardContent>
          <div className="flex items-center justify-between text-sm">
            <div className="flex items-center gap-4 text-muted-foreground">
              <span>{request.order_lines?.length || 0} items</span>
              <span>
                Created {new Date(request.created_at).toLocaleDateString()}
              </span>
            </div>
            <div className="font-semibold">
              {request.total_cost.toLocaleString('de-DE', {
                style: 'currency',
                currency: 'EUR',
              })}
            </div>
          </div>
        </CardContent>
      </Card>
    </Link>
  );
}
