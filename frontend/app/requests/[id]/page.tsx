'use client';

import { use, useState } from 'react';
import Link from 'next/link';
import { useRouter } from 'next/navigation';
import {
  ArrowLeft,
  Loader2,
  Clock,
  Building,
  FileText,
  Trash2,
} from 'lucide-react';

import { ProtectedRoute } from '@/components/ProtectedRoute';
import { StatusBadge } from '@/components/requests/StatusBadge';
import { Button } from '@/components/ui/button';
import {
  Card,
  CardContent,
  CardDescription,
  CardHeader,
  CardTitle,
} from '@/components/ui/card';
import {
  Select,
  SelectContent,
  SelectItem,
  SelectTrigger,
  SelectValue,
} from '@/components/ui/select';
import { Alert, AlertDescription } from '@/components/ui/alert';
import { useAuth } from '@/contexts/AuthContext';
import {
  useRequest,
  useRequestHistory,
  useUpdateRequestStatus,
  useDeleteRequest,
} from '@/hooks/useRequests';
import { RequestStatus } from '@/lib/api';

const statusTransitions: Record<RequestStatus, RequestStatus[]> = {
  open: ['in_progress', 'closed'],
  in_progress: ['open', 'closed'],
  closed: ['open', 'in_progress'],
};

function RequestDetailContent({ id }: { id: number }) {
  const router = useRouter();
  const { user } = useAuth();
  const [error, setError] = useState<string | null>(null);

  const { data: request, isLoading, error: fetchError } = useRequest(id);
  const { data: history } = useRequestHistory(id);
  const updateStatus = useUpdateRequestStatus();
  const deleteRequest = useDeleteRequest();

  const isProcurementTeam = user?.role === 'procurement_team';
  const canDelete = request?.status === 'open';

  const handleStatusChange = async (newStatus: RequestStatus) => {
    setError(null);
    try {
      await updateStatus.mutateAsync({ id, status: newStatus });
    } catch (err) {
      const error = err as { response?: { data?: { detail?: string } } };
      setError(error.response?.data?.detail || 'Failed to update status');
    }
  };

  const handleDelete = async () => {
    if (!confirm('Are you sure you want to delete this request?')) {
      return;
    }

    setError(null);
    try {
      await deleteRequest.mutateAsync(id);
      router.push('/requests');
    } catch (err) {
      const error = err as { response?: { data?: { detail?: string } } };
      setError(error.response?.data?.detail || 'Failed to delete request');
    }
  };

  if (isLoading) {
    return (
      <div className="min-h-screen flex items-center justify-center">
        <Loader2 className="h-8 w-8 animate-spin text-primary" />
      </div>
    );
  }

  if (fetchError || !request) {
    return (
      <div className="min-h-screen bg-background">
        <header className="border-b">
          <div className="container mx-auto px-4 py-4">
            <Link href="/requests">
              <Button variant="ghost" size="sm">
                <ArrowLeft className="h-4 w-4 mr-2" />
                Back to Requests
              </Button>
            </Link>
          </div>
        </header>
        <main className="container mx-auto px-4 py-8">
          <Alert variant="destructive">
            <AlertDescription>Request not found or you don&apos;t have access.</AlertDescription>
          </Alert>
        </main>
      </div>
    );
  }

  const allowedTransitions = statusTransitions[request.status];

  return (
    <div className="min-h-screen bg-background">
      <header className="border-b">
        <div className="container mx-auto px-4 py-4 flex items-center justify-between">
          <Link href="/requests">
            <Button variant="ghost" size="sm">
              <ArrowLeft className="h-4 w-4 mr-2" />
              Back to Requests
            </Button>
          </Link>
          {canDelete && (
            <Button
              variant="destructive"
              size="sm"
              onClick={handleDelete}
              disabled={deleteRequest.isPending}
            >
              {deleteRequest.isPending ? (
                <Loader2 className="h-4 w-4 animate-spin" />
              ) : (
                <>
                  <Trash2 className="h-4 w-4 mr-2" />
                  Delete
                </>
              )}
            </Button>
          )}
        </div>
      </header>

      <main className="container mx-auto px-4 py-8 max-w-4xl">
        {error && (
          <Alert variant="destructive" className="mb-6">
            <AlertDescription>{error}</AlertDescription>
          </Alert>
        )}

        <div className="flex items-start justify-between mb-8">
          <div>
            <h1 className="text-3xl font-bold tracking-tight">{request.title}</h1>
            <p className="text-muted-foreground mt-2">
              Request #{request.id} • Created{' '}
              {new Date(request.created_at).toLocaleDateString()}
            </p>
          </div>
          <div className="flex items-center gap-4">
            <StatusBadge status={request.status} />
            {isProcurementTeam && (
              <Select
                value={request.status}
                onValueChange={(value) => handleStatusChange(value as RequestStatus)}
                disabled={updateStatus.isPending}
              >
                <SelectTrigger className="w-[160px]">
                  <SelectValue />
                </SelectTrigger>
                <SelectContent>
                  <SelectItem value={request.status} disabled>
                    {request.status.replace('_', ' ')}
                  </SelectItem>
                  {allowedTransitions.map((status) => (
                    <SelectItem key={status} value={status}>
                      Move to {status.replace('_', ' ')}
                    </SelectItem>
                  ))}
                </SelectContent>
              </Select>
            )}
          </div>
        </div>

        <div className="grid gap-6 md:grid-cols-2 mb-8">
          <Card>
            <CardHeader className="pb-3">
              <CardTitle className="text-sm font-medium flex items-center gap-2">
                <Building className="h-4 w-4" />
                Vendor Information
              </CardTitle>
            </CardHeader>
            <CardContent className="space-y-2 text-sm">
              <div>
                <span className="text-muted-foreground">Name:</span>{' '}
                {request.vendor_name || 'Not specified'}
              </div>
              <div>
                <span className="text-muted-foreground">VAT ID:</span>{' '}
                {request.vat_id || 'Not specified'}
              </div>
            </CardContent>
          </Card>

          <Card>
            <CardHeader className="pb-3">
              <CardTitle className="text-sm font-medium flex items-center gap-2">
                <FileText className="h-4 w-4" />
                Request Details
              </CardTitle>
            </CardHeader>
            <CardContent className="space-y-2 text-sm">
              <div>
                <span className="text-muted-foreground">Department:</span>{' '}
                {request.department || 'Not specified'}
              </div>
              <div>
                <span className="text-muted-foreground">Commodity Group:</span>{' '}
                {request.commodity_group
                  ? `${request.commodity_group.category} - ${request.commodity_group.name}`
                  : 'Not specified'}
              </div>
            </CardContent>
          </Card>
        </div>

        <Card className="mb-8">
          <CardHeader>
            <CardTitle>Order Lines</CardTitle>
            <CardDescription>
              {request.order_lines?.length || 0} items
            </CardDescription>
          </CardHeader>
          <CardContent>
            <div className="overflow-x-auto">
              <table className="w-full text-sm">
                <thead>
                  <tr className="border-b">
                    <th className="text-left py-3 pr-4 font-medium">Description</th>
                    <th className="text-right py-3 px-4 font-medium">Unit Price</th>
                    <th className="text-right py-3 px-4 font-medium">Amount</th>
                    <th className="text-center py-3 px-4 font-medium">Unit</th>
                    <th className="text-right py-3 pl-4 font-medium">Total</th>
                  </tr>
                </thead>
                <tbody>
                  {request.order_lines?.map((line, index) => (
                    <tr key={index} className="border-b last:border-0">
                      <td className="py-3 pr-4">{line.description}</td>
                      <td className="py-3 px-4 text-right">
                        {line.unit_price.toLocaleString('de-DE', {
                          style: 'currency',
                          currency: 'EUR',
                        })}
                      </td>
                      <td className="py-3 px-4 text-right">{line.amount}</td>
                      <td className="py-3 px-4 text-center">{line.unit}</td>
                      <td className="py-3 pl-4 text-right font-medium">
                        {(line.total_price || line.unit_price * line.amount).toLocaleString(
                          'de-DE',
                          { style: 'currency', currency: 'EUR' }
                        )}
                      </td>
                    </tr>
                  ))}
                </tbody>
                <tfoot>
                  <tr className="font-semibold">
                    <td colSpan={4} className="py-3 pr-4 text-right">
                      Total
                    </td>
                    <td className="py-3 pl-4 text-right">
                      {request.total_cost.toLocaleString('de-DE', {
                        style: 'currency',
                        currency: 'EUR',
                      })}
                    </td>
                  </tr>
                </tfoot>
              </table>
            </div>
          </CardContent>
        </Card>

        {request.notes && (
          <Card className="mb-8">
            <CardHeader>
              <CardTitle>Notes</CardTitle>
            </CardHeader>
            <CardContent>
              <p className="text-sm whitespace-pre-wrap">{request.notes}</p>
            </CardContent>
          </Card>
        )}

        <Card>
          <CardHeader>
            <CardTitle className="flex items-center gap-2">
              <Clock className="h-4 w-4" />
              Status History
            </CardTitle>
          </CardHeader>
          <CardContent>
            {history && history.length > 0 ? (
              <div className="space-y-4">
                {history.map((entry, index) => (
                  <div
                    key={entry.id}
                    className={`flex items-start gap-4 ${
                      index < history.length - 1 ? 'pb-4 border-b' : ''
                    }`}
                  >
                    <div className="flex-1">
                      <div className="flex items-center gap-2">
                        <StatusBadge status={entry.status} />
                        <span className="text-sm text-muted-foreground">
                          {new Date(entry.changed_at).toLocaleString()}
                        </span>
                      </div>
                      {entry.notes && (
                        <p className="text-sm text-muted-foreground mt-1">
                          {entry.notes}
                        </p>
                      )}
                    </div>
                  </div>
                ))}
              </div>
            ) : (
              <p className="text-sm text-muted-foreground">No status changes yet.</p>
            )}
          </CardContent>
        </Card>
      </main>
    </div>
  );
}

export default function RequestDetailPage({
  params,
}: {
  params: Promise<{ id: string }>;
}) {
  const resolvedParams = use(params);
  const id = parseInt(resolvedParams.id, 10);

  return (
    <ProtectedRoute>
      <RequestDetailContent id={id} />
    </ProtectedRoute>
  );
}
