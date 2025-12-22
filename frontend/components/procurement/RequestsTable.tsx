'use client';

import Link from 'next/link';
import { Card, CardContent, CardHeader, CardTitle } from '@/components/ui/card';
import { Button } from '@/components/ui/button';
import { StatusBadge } from '@/components/requests/StatusBadge';
import { ProcurementRequest, RequestFilters } from '@/lib/api';
import { ChevronLeft, ChevronRight, Eye } from 'lucide-react';

interface RequestsTableProps {
  requests: ProcurementRequest[];
  total: number;
  page: number;
  pageSize: number;
  onPageChange: (page: number) => void;
  isLoading?: boolean;
}

function formatCurrency(value: number): string {
  return new Intl.NumberFormat('de-DE', {
    style: 'currency',
    currency: 'EUR',
  }).format(value);
}

function formatDate(dateString: string): string {
  return new Date(dateString).toLocaleDateString('de-DE', {
    year: 'numeric',
    month: 'short',
    day: 'numeric',
  });
}

export function RequestsTable({
  requests,
  total,
  page,
  pageSize,
  onPageChange,
  isLoading,
}: RequestsTableProps) {
  const totalPages = Math.ceil(total / pageSize);

  if (isLoading) {
    return (
      <Card>
        <CardHeader>
          <CardTitle>Request History</CardTitle>
        </CardHeader>
        <CardContent>
          <div className="space-y-4">
            {[1, 2, 3, 4, 5].map((i) => (
              <div key={i} className="h-16 bg-muted animate-pulse rounded" />
            ))}
          </div>
        </CardContent>
      </Card>
    );
  }

  return (
    <Card>
      <CardHeader className="flex flex-row items-center justify-between">
        <CardTitle>Request History</CardTitle>
        <span className="text-sm text-muted-foreground">
          {total} request{total !== 1 ? 's' : ''} found
        </span>
      </CardHeader>
      <CardContent>
        {requests.length === 0 ? (
          <div className="text-center py-8 text-muted-foreground">
            No requests found matching your filters.
          </div>
        ) : (
          <>
            <div className="overflow-x-auto">
              <table className="w-full">
                <thead>
                  <tr className="border-b">
                    <th className="text-left py-3 px-2 font-medium text-muted-foreground">Title</th>
                    <th className="text-left py-3 px-2 font-medium text-muted-foreground">Vendor</th>
                    <th className="text-left py-3 px-2 font-medium text-muted-foreground">Department</th>
                    <th className="text-left py-3 px-2 font-medium text-muted-foreground">Requestor</th>
                    <th className="text-right py-3 px-2 font-medium text-muted-foreground">Total</th>
                    <th className="text-center py-3 px-2 font-medium text-muted-foreground">Status</th>
                    <th className="text-left py-3 px-2 font-medium text-muted-foreground">Created</th>
                    <th className="text-center py-3 px-2 font-medium text-muted-foreground">Actions</th>
                  </tr>
                </thead>
                <tbody>
                  {requests.map((request) => (
                    <tr
                      key={request.id}
                      className="border-b hover:bg-muted/50 transition-colors"
                    >
                      <td className="py-3 px-2">
                        <Link
                          href={`/requests/${request.id}`}
                          className="font-medium hover:underline"
                        >
                          {request.title}
                        </Link>
                      </td>
                      <td className="py-3 px-2 text-muted-foreground">
                        {request.vendor_name || '-'}
                      </td>
                      <td className="py-3 px-2 text-muted-foreground">
                        {request.department || '-'}
                      </td>
                      <td className="py-3 px-2 text-muted-foreground">
                        {/* We don't have requestor name in the list response yet */}
                        -
                      </td>
                      <td className="py-3 px-2 text-right font-medium">
                        {formatCurrency(request.total_cost)}
                      </td>
                      <td className="py-3 px-2 text-center">
                        <StatusBadge status={request.status} />
                      </td>
                      <td className="py-3 px-2 text-muted-foreground">
                        {formatDate(request.created_at)}
                      </td>
                      <td className="py-3 px-2 text-center">
                        <Link href={`/requests/${request.id}`}>
                          <Button variant="ghost" size="sm">
                            <Eye className="h-4 w-4" />
                          </Button>
                        </Link>
                      </td>
                    </tr>
                  ))}
                </tbody>
              </table>
            </div>

            {/* Pagination */}
            {totalPages > 1 && (
              <div className="flex items-center justify-between mt-4 pt-4 border-t">
                <span className="text-sm text-muted-foreground">
                  Page {page} of {totalPages}
                </span>
                <div className="flex gap-2">
                  <Button
                    variant="outline"
                    size="sm"
                    onClick={() => onPageChange(page - 1)}
                    disabled={page <= 1}
                  >
                    <ChevronLeft className="h-4 w-4 mr-1" />
                    Previous
                  </Button>
                  <Button
                    variant="outline"
                    size="sm"
                    onClick={() => onPageChange(page + 1)}
                    disabled={page >= totalPages}
                  >
                    Next
                    <ChevronRight className="h-4 w-4 ml-1" />
                  </Button>
                </div>
              </div>
            )}
          </>
        )}
      </CardContent>
    </Card>
  );
}
