import React from "react";
import ReactDOM from "react-dom/client";
import { Navigate, RouterProvider, createBrowserRouter } from "react-router-dom";
import App from "./App.jsx";
import { AuthProvider } from "./context/AuthContext.jsx";
import LoginPage from "./pages/LoginPage.jsx";
import DashboardPage from "./pages/DashboardPage.jsx";
import CreateBillPage from "./pages/CreateBillPage.jsx";
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
