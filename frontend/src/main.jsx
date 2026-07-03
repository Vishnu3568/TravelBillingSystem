import React from "react";
import ReactDOM from "react-dom/client";
import { Navigate, RouterProvider, createBrowserRouter } from "react-router-dom";
import App from "./App.jsx";
import { AuthProvider } from "./context/AuthContext.jsx";
import LoginPage from "./pages/LoginPage.jsx";
import DashboardPage from "./pages/DashboardPage.jsx";
import CreateBillPage from "./pages/CreateBillPage.jsx";
import BillsPage from "./pages/BillsPage.jsx";
import BillViewPage from "./pages/BillViewPage.jsx";
import CompanyPage from "./pages/CompanyPage.jsx";
import VehiclePage from "./pages/VehiclePage.jsx";
import ReportsPage from "./pages/ReportsPage.jsx";
import UserManagementPage from "./pages/UserManagementPage.jsx";
import AuditLogPage from "./pages/AuditLogPage.jsx";
import EditBillPage from "./pages/EditBillPage.jsx";
import SettingsPage from "./pages/SettingsPage.jsx";
import ImportBillsPage from "./pages/ImportBillsPage.jsx";
import ProtectedRoute from "./components/ProtectedRoute.jsx";
import { Toaster } from "sonner";
import "./styles/index.css";

import MainLayout from "./ui/MainLayout.jsx";
import { useAuth } from "./context/AuthContext.jsx";
import { dashboardPathForRole } from "./utils/routes.js";

function HomeRedirect() {
  const { isAuthenticated, role } = useAuth();
  if (!isAuthenticated) return <Navigate to="/login" replace />;
  return <Navigate to={dashboardPathForRole(role)} replace />;
}

const router = createBrowserRouter([
  {
    path: "/",
    element: <App />,
    children: [
      { index: true, element: <HomeRedirect /> },
      { path: "login", element: <LoginPage /> },
      {
        element: <MainLayout />,
        children: [
          // ... all the routes ...
          {
            path: "owner-dashboard",
            element: (
              <ProtectedRoute allowedRoles={["OWNER"]}>
                <DashboardPage role="OWNER" />
              </ProtectedRoute>
            ),
          },
          {
            path: "owner-dashboard/import-bills",
            element: (
              <ProtectedRoute allowedRoles={["OWNER"]}>
                <ImportBillsPage />
              </ProtectedRoute>
            ),
          },

          {
            path: "create-bill",
            element: (
              <ProtectedRoute allowedRoles={["OWNER", "MANAGER", "EMPLOYEE"]}>
                <CreateBillPage />
              </ProtectedRoute>
            ),
          },
          {
            path: "bill-history",
            element: (
              <ProtectedRoute allowedRoles={["OWNER", "MANAGER", "EMPLOYEE"]}>
                <BillsPage />
              </ProtectedRoute>
            ),
          },
          {
            path: "bill-view/:id",
            element: (
              <ProtectedRoute allowedRoles={["OWNER", "MANAGER", "EMPLOYEE"]}>
                <BillViewPage />
              </ProtectedRoute>
            ),
          },
          {
            path: "edit-bill/:id",
            element: (
              <ProtectedRoute allowedRoles={["OWNER", "MANAGER"]}>
                <EditBillPage />
              </ProtectedRoute>
            ),
          },
          {
            path: "companies",
            element: (
              <ProtectedRoute allowedRoles={["OWNER", "MANAGER"]}>
                <CompanyPage />
              </ProtectedRoute>
            ),
          },
          {
            path: "vehicles",
            element: (
              <ProtectedRoute allowedRoles={["OWNER", "MANAGER"]}>
                <VehiclePage />
              </ProtectedRoute>
            ),
          },
          {
            path: "reports",
            element: (
              <ProtectedRoute allowedRoles={["OWNER", "MANAGER"]}>
                <ReportsPage />
              </ProtectedRoute>
            ),
          },
          {
            path: "users",
            element: (
              <ProtectedRoute allowedRoles={["OWNER"]}>
                <UserManagementPage />
              </ProtectedRoute>
            ),
          },

          {
            path: "audit-logs",
            element: (
              <ProtectedRoute allowedRoles={["OWNER"]}>
                <AuditLogPage />
              </ProtectedRoute>
            ),
          },
          {
            path: "manager-dashboard",
            element: (
              <ProtectedRoute allowedRoles={["MANAGER"]}>
                <DashboardPage role="MANAGER" />
              </ProtectedRoute>
            ),
          },
          {
            path: "employee-dashboard",
            element: (
              <ProtectedRoute allowedRoles={["EMPLOYEE"]}>
                <DashboardPage role="EMPLOYEE" />
              </ProtectedRoute>
            ),
          },
          {
            path: "settings",
            element: (
              <ProtectedRoute allowedRoles={["OWNER", "MANAGER", "EMPLOYEE"]}>
                <SettingsPage />
              </ProtectedRoute>
            ),
          },
          { path: "*", element: <Navigate to="/login" replace /> },
        ],
      },
    ],
  },
], {
  basename: import.meta.env.BASE_URL
});

ReactDOM.createRoot(document.getElementById("root")).render(
  <React.StrictMode>
    <AuthProvider>
      <RouterProvider router={router} />
      <Toaster position="top-right" richColors />
    </AuthProvider>
  </React.StrictMode>,
);
