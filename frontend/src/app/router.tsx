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
import { LearningPage } from '@/features/learning/LearningPage';
import { LoginPage } from '@/features/auth/LoginPage';
import { LandingPage } from '@/features/landing/LandingPage';
import { ProtectedRoute } from '@/features/auth/ProtectedRoute';

export const router = createBrowserRouter([
  // Public Routes
  {
    path: '/',
    element: <LandingPage />,
  },
  {
    path: '/landing',
    element: <LandingPage />,
  },
  {
    path: '/login',
    element: <LoginPage />,
  },
  {
    path: '/register',
    element: <LoginPage />,
  },
  // Protected Application Dashboard Routes
  {
    element: (
      <ProtectedRoute>
        <AppLayout />
      </ProtectedRoute>
    ),
    children: [
      {
        path: '/overview',
        element: <OverviewPage />,
      },
      {
        path: '/intelligence',
        element: <IntelligencePage />,
      },
      {
        path: '/opportunities',
        element: <OpportunitiesPage />,
      },
      {
        path: '/opportunities/:id',
        element: <OpportunityDetailPage />,
      },
      {
        path: '/agent',
        element: <AgentStudioPage />,
      },
      {
        path: '/agent/runs/:id',
        element: <AgentRunDetailPage />,
      },
      {
        path: '/actions',
        element: <ActionsPage />,
      },
      {
        path: '/learning',
        element: <LearningPage />,
      },
      {
        path: '/policies',
        element: <PoliciesPage />,
      },
      {
        path: '/audit',
        element: <AuditPage />,
      },
      {
        path: '*',
        element: <Navigate to="/" replace />,
      },
    ],
  },
  // Catch-all Fallback
  {
    path: '*',
    element: <Navigate to="/" replace />,
  },
]);
