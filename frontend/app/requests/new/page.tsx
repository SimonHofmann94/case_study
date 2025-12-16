'use client';

import { useState } from 'react';
import { useRouter } from 'next/navigation';
import Link from 'next/link';
import { ArrowLeft } from 'lucide-react';

import { ProtectedRoute } from '@/components/ProtectedRoute';
import { RequestForm, RequestFormData } from '@/components/requests/RequestForm';
import { FileUpload } from '@/components/requests/FileUpload';
import { Button } from '@/components/ui/button';
import { Card, CardContent, CardDescription, CardHeader, CardTitle } from '@/components/ui/card';
import { Alert, AlertDescription } from '@/components/ui/alert';
import { useCreateRequest } from '@/hooks/useRequests';
import { ParsedOffer } from '@/lib/api';

function NewRequestContent() {
  const router = useRouter();
  const [parsedOffer, setParsedOffer] = useState<ParsedOffer | null>(null);
  const [error, setError] = useState<string | null>(null);
  const createRequest = useCreateRequest();

  const handleParsedOffer = (data: ParsedOffer) => {
    setParsedOffer(data);
    setError(null);
  };

  const handleSubmit = async (data: RequestFormData) => {
    setError(null);

    try {
      await createRequest.mutateAsync({
        title: data.title,
        vendor_name: data.vendor_name || undefined,
        vat_id: data.vat_id || undefined,
        commodity_group_id: data.commodity_group_id
          ? parseInt(data.commodity_group_id)
          : undefined,
        department: data.department || undefined,
        notes: data.notes || undefined,
        order_lines: data.order_lines.map((line) => ({
          description: line.description,
          unit_price: Number(line.unit_price),
          amount: Number(line.amount),
          unit: line.unit,
        })),
      });

      router.push('/requests');
    } catch (err) {
      const error = err as { response?: { data?: { detail?: string } } };
      setError(
        error.response?.data?.detail || 'Failed to create request. Please try again.'
      );
    }
  };

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

      <main className="container mx-auto px-4 py-8 max-w-4xl">
        <div className="mb-8">
          <h1 className="text-3xl font-bold tracking-tight">New Request</h1>
          <p className="text-muted-foreground mt-2">
            Upload a vendor offer to auto-fill the form, or enter details manually.
          </p>
        </div>

        {error && (
          <Alert variant="destructive" className="mb-6">
            <AlertDescription>{error}</AlertDescription>
          </Alert>
        )}

        <div className="space-y-8">
          <Card>
            <CardHeader>
              <CardTitle>Upload Vendor Offer (Optional)</CardTitle>
              <CardDescription>
                Upload a PDF or TXT file and our AI will extract the vendor information
                and order details automatically.
              </CardDescription>
            </CardHeader>
            <CardContent>
              <FileUpload onParsed={handleParsedOffer} />
            </CardContent>
          </Card>

          <Card>
            <CardHeader>
              <CardTitle>Request Details</CardTitle>
              <CardDescription>
                {parsedOffer
                  ? 'Review and edit the extracted information below.'
                  : 'Fill in the request details manually.'}
              </CardDescription>
            </CardHeader>
            <CardContent>
              <RequestForm
                onSubmit={handleSubmit}
                isLoading={createRequest.isPending}
                parsedOffer={parsedOffer}
              />
            </CardContent>
          </Card>
        </div>
      </main>
    </div>
  );
}

export default function NewRequestPage() {
  return (
    <ProtectedRoute>
      <NewRequestContent />
    </ProtectedRoute>
  );
}
