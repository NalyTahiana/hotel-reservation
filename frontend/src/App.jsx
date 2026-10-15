import { Route, Routes } from "react-router-dom";
import ProtectedRoute from "./components/ProtectedRoute";
import AdminLayout from "./layouts/AdminLayout";
import PublicLayout from "./layouts/PublicLayout";
import Account from "./pages/Account";
import Booking from "./pages/Booking";
import Home from "./pages/Home";
import Login from "./pages/Login";
import MyReservations from "./pages/MyReservations";
import NotFound from "./pages/NotFound";
import Register from "./pages/Register";
import RoomDetail from "./pages/RoomDetail";
import Rooms from "./pages/Rooms";
import AdminCustomers from "./pages/admin/Customers";
import AdminDashboard from "./pages/admin/Dashboard";
import AdminReservations from "./pages/admin/Reservations";
import AdminRooms from "./pages/admin/Rooms";
import AdminServices from "./pages/admin/Services";

export default function App() {
  return (
    <Routes>
      <Route element={<PublicLayout />}>
        <Route path="/" element={<Home />} />
        <Route path="/chambres" element={<Rooms />} />
        <Route path="/chambres/:id" element={<RoomDetail />} />
        <Route path="/inscription" element={<Register />} />
        <Route path="/connexion" element={<Login />} />
        <Route path="/reservation/:roomId" element={<ProtectedRoute><Booking /></ProtectedRoute>} />
        <Route path="/compte" element={<ProtectedRoute><Account /></ProtectedRoute>} />
        <Route path="/compte/reservations" element={<ProtectedRoute><MyReservations /></ProtectedRoute>} />
        <Route path="*" element={<NotFound />} />
      </Route>
      <Route path="/admin" element={<ProtectedRoute admin><AdminLayout /></ProtectedRoute>}>
        <Route index element={<AdminDashboard />} />
        <Route path="reservations" element={<AdminReservations />} />
        <Route path="chambres" element={<AdminRooms />} />
        <Route path="clients" element={<AdminCustomers />} />
        <Route path="services" element={<AdminServices />} />
        <Route path="*" element={<NotFound />} />
      </Route>
    </Routes>
  );
}
