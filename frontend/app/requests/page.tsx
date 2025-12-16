'use client';

import { useState } from 'react';
import Link from 'next/link';
import { ArrowLeft } from 'lucide-react';

import { ProtectedRoute } from '@/components/ProtectedRoute';
import { RequestList } from '@/components/requests/RequestList';
import { Button } from '@/components/ui/button';
import { RequestStatus } from '@/lib/api';

function RequestsContent() {
  const [statusFilter, setStatusFilter] = useState<RequestStatus | undefined>(undefined);

  return (
    <div className="min-h-screen bg-background">
      <header className="border-b">
        <div className="container mx-auto px-4 py-4">
          <Link href="/dashboard">
            <Button variant="ghost" size="sm">
              <ArrowLeft className="h-4 w-4 mr-2" />
              Back to Dashboard
            </Button>
          </Link>
        </div>
      </header>

      <main className="container mx-auto px-4 py-8">
        <div className="mb-8">
          <h1 className="text-3xl font-bold tracking-tight">Requests</h1>
          <p className="text-muted-foreground mt-2">
            View and manage procurement requests.
          </p>
        </div>

        <RequestList
          statusFilter={statusFilter}
          onStatusFilterChange={setStatusFilter}
        />
      </main>
    </div>
  );
}

export default function RequestsPage() {
  return (
    <ProtectedRoute>
      <RequestsContent />
    </ProtectedRoute>
  );
}
