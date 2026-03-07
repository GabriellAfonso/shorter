import { createBrowserRouter, Navigate } from "react-router-dom";
import { Layout } from "@/shared/components/Layout";
import { ProtectedRoute } from "@/shared/components/ProtectedRoute";
import { ErrorBoundary } from "@/shared/components/ErrorBoundary";
import { LoginPage } from "@/features/auth/pages/LoginPage";
import { RegisterPage } from "@/features/auth/pages/RegisterPage";
import { DashboardPage } from "@/features/links/pages/DashboardPage";
import { LinksPage } from "@/features/links/pages/LinksPage";
import { AnalyticsPage } from "@/features/analytics/pages/AnalyticsPage";

export const router = createBrowserRouter(
  [
  {
    path: "/",
    element: <Layout />,
    children: [
      { index: true, element: <Navigate to="/dashboard" replace /> },
      { path: "login", element: <LoginPage /> },
      { path: "register", element: <RegisterPage /> },
      {
        element: <ProtectedRoute />,
        children: [
          {
            path: "dashboard",
            element: (
              <ErrorBoundary>
                <DashboardPage />
              </ErrorBoundary>
            ),
          },
          {
            path: "links",
            element: (
              <ErrorBoundary>
                <LinksPage />
              </ErrorBoundary>
            ),
          },
          {
            path: "links/:linkId/analytics",
            element: (
              <ErrorBoundary>
                <AnalyticsPage />
              </ErrorBoundary>
            ),
          },
        ],
      },
    ],
  },
  ],
  { basename: import.meta.env.BASE_URL.replace(/\/$/, "") || "/" }
);
