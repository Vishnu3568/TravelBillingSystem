import React from "react";
import ReactDOM from "react-dom/client";
import { Navigate, RouterProvider, createBrowserRouter } from "react-router-dom";
import App from "./App.jsx";
import { AuthProvider } from "./context/AuthContext.jsx";
import LoginPage from "./pages/LoginPage.jsx";
import DashboardPage from "./pages/DashboardPage.jsx";
import CreateBillPage from "./pages/CreateBillPage.jsx";
import BillHistoryPage from "./pages/BillHistoryPage.jsx";
import BillViewPage from "./pages/BillViewPage.jsx";
import CompanyPage from "./pages/CompanyPage.jsx";
import VehiclePage from "./pages/VehiclePage.jsx";
import ReportsPage from "./pages/ReportsPage.jsx";
import UserManagementPage from "./pages/UserManagementPage.jsx";
import ProtectedRoute from "./components/ProtectedRoute.jsx";
import "./styles/index.css";

const router = createBrowserRouter([
  {
    path: "/",
    element: <App />,
    children: [
      { index: true, element: <Navigate to="/login" replace /> },
      { path: "login", element: <LoginPage /> },
      {
        path: "owner-dashboard",
        element: (
          <ProtectedRoute allowedRoles={["OWNER"]}>
            <DashboardPage role="OWNER" />
          </ProtectedRoute>
        ),
      },
      {
        path: "create-bill",
        element: (
          <ProtectedRoute allowedRoles={["OWNER"]}>
            <CreateBillPage />
          </ProtectedRoute>
        ),
      },
      {
        path: "bill-history",
        element: (
          <ProtectedRoute allowedRoles={["OWNER", "MANAGER", "EMPLOYEE"]}>
            <BillHistoryPage />
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
      { path: "*", element: <Navigate to="/login" replace /> },
    ],
  },
]);

ReactDOM.createRoot(document.getElementById("root")).render(
  <React.StrictMode>
    <AuthProvider>
      <RouterProvider router={router} />
    </AuthProvider>
  </React.StrictMode>,
);
