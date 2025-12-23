'use client';

import Link from 'next/link';
import { FileText, PlusCircle, LogOut } from 'lucide-react';

import { useAuth } from '@/contexts/AuthContext';
import { ProtectedRoute } from '@/components/ProtectedRoute';
import { Button } from '@/components/ui/button';
import {
  Card,
  CardContent,
  CardDescription,
  CardHeader,
  CardTitle,
} from '@/components/ui/card';
import { ProcurementDashboard } from '@/components/procurement/ProcurementDashboard';
import { PageInfoButton, PAGE_INFO } from '@/components/PageInfoButton';

// Requestor Dashboard - for regular users
function RequestorDashboard() {
  const { user, logout } = useAuth();

  return (
    <div className="min-h-screen bg-background">
      <header className="border-b">
        <div className="container mx-auto px-4 py-4 flex items-center justify-between">
          <h1 className="text-xl font-bold">Procurement AI</h1>
          <div className="flex items-center gap-4">
            <span className="text-sm text-muted-foreground">
              {user?.full_name} (Requestor)
            </span>
            <Button variant="ghost" size="sm" onClick={logout}>
              <LogOut className="h-4 w-4 mr-2" />
              Sign out
            </Button>
          </div>
        </div>
      </header>

      <main className="container mx-auto px-4 py-8">
        <div className="mb-8">
          <div className="flex items-center gap-2">
            <h2 className="text-3xl font-bold tracking-tight">
              Welcome back, {user?.full_name?.split(' ')[0]}!
            </h2>
            <PageInfoButton {...PAGE_INFO.requestorDashboard} />
          </div>
          <p className="text-muted-foreground mt-2">
            Create and track your procurement requests.
          </p>
        </div>

        <div className="grid gap-6 md:grid-cols-2 lg:grid-cols-3">
          <Card>
            <CardHeader>
              <CardTitle className="flex items-center gap-2">
                <PlusCircle className="h-5 w-5" />
                New Request
              </CardTitle>
              <CardDescription>
                Create a new procurement request
              </CardDescription>
            </CardHeader>
            <CardContent>
              <p className="text-sm text-muted-foreground mb-4">
                Upload a vendor offer or manually enter request details.
              </p>
              <Link href="/requests/new">
                <Button className="w-full">Create Request</Button>
              </Link>
            </CardContent>
          </Card>

          <Card>
            <CardHeader>
              <CardTitle className="flex items-center gap-2">
                <FileText className="h-5 w-5" />
                My Requests
              </CardTitle>
              <CardDescription>
                View and manage your requests
              </CardDescription>
            </CardHeader>
            <CardContent>
              <p className="text-sm text-muted-foreground mb-4">
                Track the status of your submitted requests.
              </p>
              <Link href="/requests">
                <Button variant="outline" className="w-full">
                  View Requests
                </Button>
              </Link>
            </CardContent>
          </Card>
        </div>
      </main>
    </div>
  );
}

// Procurement Team Dashboard - with analytics and management features
function ProcurementTeamDashboard() {
  const { user, logout } = useAuth();

  return (
    <div className="min-h-screen bg-background">
      <header className="border-b">
        <div className="container mx-auto px-4 py-4 flex items-center justify-between">
          <h1 className="text-xl font-bold">Procurement AI</h1>
          <div className="flex items-center gap-4">
            <span className="text-sm text-muted-foreground">
              {user?.full_name} (Procurement Team)
            </span>
            <Button variant="ghost" size="sm" onClick={logout}>
              <LogOut className="h-4 w-4 mr-2" />
              Sign out
            </Button>
          </div>
        </div>
      </header>

      <main className="container mx-auto px-4 py-8">
        <div className="mb-8">
          <div className="flex items-center gap-2">
            <h2 className="text-3xl font-bold tracking-tight">
              Procurement Dashboard
            </h2>
            <PageInfoButton {...PAGE_INFO.procurementDashboard} />
          </div>
          <p className="text-muted-foreground mt-2">
            Review and manage procurement requests from all departments.
          </p>
        </div>

        <ProcurementDashboard />
      </main>
    </div>
  );
}

function DashboardContent() {
  const { user } = useAuth();

  // Show procurement dashboard for procurement team, regular dashboard for requestors
  if (user?.role === 'procurement_team') {
    return <ProcurementTeamDashboard />;
  }

  return <RequestorDashboard />;
}

export default function DashboardPage() {
  return (
    <ProtectedRoute>
      <DashboardContent />
    </ProtectedRoute>
  );
}
