import { Badge } from '@/components/ui/badge';
import { RequestStatus } from '@/lib/api';

interface StatusBadgeProps {
  status: RequestStatus;
}

const statusConfig: Record<
  RequestStatus,
  { label: string; variant: 'default' | 'secondary' | 'success' | 'warning' }
> = {
  open: { label: 'Open', variant: 'warning' },
  in_progress: { label: 'In Progress', variant: 'default' },
  closed: { label: 'Closed', variant: 'success' },
};

export function StatusBadge({ status }: StatusBadgeProps) {
  const config = statusConfig[status];

  return <Badge variant={config.variant}>{config.label}</Badge>;
}
