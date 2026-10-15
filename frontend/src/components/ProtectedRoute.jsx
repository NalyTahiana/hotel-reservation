import { Navigate, useLocation } from "react-router-dom";
import { useAuth } from "../context/AuthContext";
import Loader from "./Loader";

export default function ProtectedRoute({ children, admin = false }) {
  const { user, loading } = useAuth();
  const location = useLocation();
  if (loading) return <Loader />;
  if (!user) return <Navigate to="/connexion" replace state={{ from: location.pathname + location.search }} />;
  if (admin && !user.is_staff) return <Navigate to="/" replace />;
  return children;
}
