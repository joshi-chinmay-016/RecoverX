import { createBrowserRouter, Navigate } from 'react-router-dom';
import { AppLayout } from '@/components/layout/AppLayout';
import { OverviewPage } from '@/features/overview/OverviewPage';
import { IntelligencePage } from '@/features/intelligence/IntelligencePage';
import { OpportunitiesPage } from '@/features/opportunities/OpportunitiesPage';
import { OpportunityDetailPage } from '@/features/opportunities/OpportunityDetailPage';
import { AgentStudioPage } from '@/features/agent/AgentStudioPage';
import { AgentRunDetailPage } from '@/features/agent/AgentRunDetailPage';
import { ActionsPage } from '@/features/actions/ActionsPage';
import { PoliciesPage } from '@/features/policies/PoliciesPage';
import { AuditPage } from '@/features/audit/AuditPage';

export const router = createBrowserRouter([
  {
    path: '/',
    element: <AppLayout />,
    children: [
      {
        index: true,
        element: <OverviewPage />,
      },
      {
        path: 'intelligence',
        element: <IntelligencePage />,
      },
      {
        path: 'opportunities',
        element: <OpportunitiesPage />,
      },
      {
        path: 'opportunities/:id',
        element: <OpportunityDetailPage />,
      },
      {
        path: 'agent',
        element: <AgentStudioPage />,
      },
      {
        path: 'agent/runs/:id',
        element: <AgentRunDetailPage />,
      },
      {
        path: 'actions',
        element: <ActionsPage />,
      },
      {
        path: 'policies',
        element: <PoliciesPage />,
      },
      {
        path: 'audit',
        element: <AuditPage />,
      },
      {
        path: '*',
        element: <Navigate to="/" replace />,
      },
    ],
  },
]);
