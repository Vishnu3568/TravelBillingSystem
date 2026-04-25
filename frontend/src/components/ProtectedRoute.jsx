import { Navigate } from "react-router-dom";
import { useAuth } from "../context/AuthContext.jsx";
import { dashboardPathForRole } from "../utils/routes.js";

export default function ProtectedRoute({ allowedRoles, children }) {
  const { isAuthenticated, role } = useAuth();

  if (!isAuthenticated) {
    return <Navigate to="/login" replace />;
  }

  if (!allowedRoles.includes(role)) {
    return <Navigate to={dashboardPathForRole(role)} replace />;
  }

  return children;
}
