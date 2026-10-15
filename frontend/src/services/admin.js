import { get, post, patch, del } from "./api";

export const getStats = () => get("/admin/stats/");

export const adminRooms = (params) => get("/admin/rooms/", params);
export const createRoom = (formData) => post("/admin/rooms/", formData);
export const updateRoom = (id, formData) => patch(`/admin/rooms/${id}/`, formData);
export const deleteRoom = (id) => del(`/admin/rooms/${id}/`);
export const addRoomImages = (id, formData) => post(`/admin/rooms/${id}/images/`, formData);
export const deleteRoomImage = (id, imageId) => del(`/admin/rooms/${id}/images/${imageId}/`);

export const adminReservations = (params) => get("/admin/reservations/", params);
export const reservationAction = (id, action) => post(`/admin/reservations/${id}/${action}/`);

export const adminCustomers = (params) => get("/admin/customers/", params);
export const createCustomer = (payload) => post("/admin/customers/", payload);
export const adminCustomer = (id) => get(`/admin/customers/${id}/`);
export const setCustomerActive = (id, isActive) => patch(`/admin/customers/${id}/`, { is_active: isActive });

export const adminServices = (params) => get("/admin/services/", params);
export const createService = (formData) => post("/admin/services/", formData);
export const updateService = (id, formData) => patch(`/admin/services/${id}/`, formData);
export const deleteService = (id) => del(`/admin/services/${id}/`);
