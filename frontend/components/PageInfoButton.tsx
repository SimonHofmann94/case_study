'use client';

import { HelpCircle } from 'lucide-react';
import { Tooltip } from '@/components/ui/tooltip';
import { Button } from '@/components/ui/button';

interface PageInfoButtonProps {
  title: string;
  description: string | React.ReactNode;
}

/**
 * A help/info button that displays page usage information in a tooltip.
 *
 * Use this component to provide contextual help for users on how to use
 * each page of the application.
 */
export function PageInfoButton({ title, description }: PageInfoButtonProps) {
  return (
    <Tooltip
      content={
        <div>
          <h4 className="font-semibold mb-2">{title}</h4>
          <div className="text-muted-foreground">{description}</div>
        </div>
      }
      side="bottom"
    >
      <Button
        variant="ghost"
        size="icon"
        className="h-8 w-8 text-muted-foreground hover:text-foreground"
        aria-label="Page help"
      >
        <HelpCircle className="h-5 w-5" />
      </Button>
    </Tooltip>
  );
}

// Pre-defined page info content for consistency
export const PAGE_INFO = {
  requestorDashboard: {
    title: 'Requestor Dashboard',
    description: (
      <ul className="list-disc list-inside space-y-1 text-sm">
        <li>Create new procurement requests</li>
        <li>View status of your submitted requests</li>
        <li>Upload vendor offers for automatic data extraction</li>
      </ul>
    ),
  },
  procurementDashboard: {
    title: 'Procurement Dashboard',
    description: (
      <ul className="list-disc list-inside space-y-1 text-sm">
        <li>View analytics for all requests</li>
        <li>Filter requests by status, vendor, or date</li>
        <li>Click a request to review details and change status</li>
        <li>Add notes to communicate with requestors</li>
      </ul>
    ),
  },
  requestOverview: {
    title: 'My Requests',
    description: (
      <ul className="list-disc list-inside space-y-1 text-sm">
        <li>View all your submitted requests</li>
        <li>Filter by status (Open, In Progress, Closed)</li>
        <li>Click "Show details" to see item descriptions</li>
        <li>Click a request to view full details</li>
      </ul>
    ),
  },
  newRequest: {
    title: 'Create New Request',
    description: (
      <ul className="list-disc list-inside space-y-1 text-sm">
        <li>Upload a PDF offer to auto-fill the form</li>
        <li>Or enter vendor and item details manually</li>
        <li>Add multiple order lines as needed</li>
        <li>Select the appropriate commodity group</li>
      </ul>
    ),
  },
  requestDetail: {
    title: 'Request Details',
    description: (
      <ul className="list-disc list-inside space-y-1 text-sm">
        <li>View complete request information</li>
        <li>See all order lines and pricing</li>
        <li>Check status history and notes</li>
        <li>Delete request if status is "Open"</li>
      </ul>
    ),
  },
  requestDetailProcurement: {
    title: 'Request Details',
    description: (
      <ul className="list-disc list-inside space-y-1 text-sm">
        <li>Review request from department</li>
        <li>Change status using the dropdown</li>
        <li>Add notes to communicate with requestor</li>
        <li>View offer terms and conditions</li>
      </ul>
    ),
  },
};
