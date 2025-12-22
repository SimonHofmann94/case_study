'use client';

import { Card, CardContent, CardHeader, CardTitle } from '@/components/ui/card';
import { RequestAnalytics } from '@/lib/api';
import { Clock, Loader2, CheckCircle } from 'lucide-react';

interface AnalyticsCardsProps {
  analytics?: RequestAnalytics;
  isLoading?: boolean;
}

function formatCurrency(value: number): string {
  return new Intl.NumberFormat('de-DE', {
    style: 'currency',
    currency: 'EUR',
  }).format(value);
}

export function AnalyticsCards({ analytics, isLoading }: AnalyticsCardsProps) {
  if (isLoading) {
    return (
      <div className="grid gap-4 md:grid-cols-3">
        {[1, 2, 3].map((i) => (
          <Card key={i}>
            <CardHeader className="flex flex-row items-center justify-between space-y-0 pb-2">
              <CardTitle className="text-sm font-medium">Loading...</CardTitle>
            </CardHeader>
            <CardContent>
              <div className="h-8 w-24 bg-muted animate-pulse rounded" />
            </CardContent>
          </Card>
        ))}
      </div>
    );
  }

  const cards = [
    {
      title: 'Open Requests',
      count: analytics?.open_count ?? 0,
      value: analytics?.total_open_value ?? 0,
      icon: Clock,
      color: 'text-yellow-600',
      bgColor: 'bg-yellow-100',
    },
    {
      title: 'In Progress',
      count: analytics?.in_progress_count ?? 0,
      value: analytics?.total_in_progress_value ?? 0,
      icon: Loader2,
      color: 'text-blue-600',
      bgColor: 'bg-blue-100',
    },
    {
      title: 'Closed',
      count: analytics?.closed_count ?? 0,
      value: analytics?.total_closed_value ?? 0,
      icon: CheckCircle,
      color: 'text-green-600',
      bgColor: 'bg-green-100',
    },
  ];

  return (
    <div className="grid gap-4 md:grid-cols-3">
      {cards.map((card) => {
        const Icon = card.icon;
        return (
          <Card key={card.title}>
            <CardHeader className="flex flex-row items-center justify-between space-y-0 pb-2">
              <CardTitle className="text-sm font-medium">{card.title}</CardTitle>
              <div className={`p-2 rounded-full ${card.bgColor}`}>
                <Icon className={`h-4 w-4 ${card.color}`} />
              </div>
            </CardHeader>
            <CardContent>
              <div className="text-2xl font-bold">{card.count}</div>
              <p className="text-xs text-muted-foreground">
                {formatCurrency(card.value)} total value
              </p>
            </CardContent>
          </Card>
        );
      })}
    </div>
  );
}
